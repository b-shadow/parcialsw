data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name               = var.project_name
  public_subnets     = ["10.20.1.0/24", "10.20.2.0/24"]
  private_subnets    = ["10.20.11.0/24", "10.20.12.0/24"]
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)
  frontend_origin    = var.enable_cloudfront ? "https://${var.frontend_domain}" : var.frontend_external_url
  backend_cors_origins = join(",", distinct(concat(
    [local.frontend_origin],
    var.frontend_allowed_origins,
  )))
  ollama_endpoint = var.enable_aws_ollama ? "http://${aws_instance.ollama[0].private_ip}:11434" : var.ollama_base_url
}

resource "aws_vpc" "main" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${local.name}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name}-igw"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_subnets[count.index]
  availability_zone       = local.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name}-public-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_subnets[count.index]
  availability_zone = local.availability_zones[count.index]

  tags = {
    Name = "${local.name}-private-${count.index + 1}"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${local.name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "alb" {
  name        = "${local.name}-alb-sg"
  description = "Public HTTPS access"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "backend" {
  name        = "${local.name}-backend-sg"
  description = "Backend EC2 access from ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  dynamic "ingress" {
    for_each = var.enable_ssh ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [var.admin_ssh_cidr]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name        = "${local.name}-rds-sg"
  description = "PostgreSQL access from backend"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "postgres" {
  identifier                  = "${local.name}-postgres"
  engine                      = "postgres"
  engine_version              = "16"
  instance_class              = "db.t4g.micro"
  allocated_storage           = 20
  db_name                     = var.database_name
  username                    = var.database_username
  manage_master_user_password = true
  db_subnet_group_name        = aws_db_subnet_group.main.name
  vpc_security_group_ids      = [aws_security_group.rds.id]
  storage_encrypted           = true
  backup_retention_period     = var.rds_backup_retention_period
  skip_final_snapshot         = false
  final_snapshot_identifier   = "${local.name}-postgres-final"
  deletion_protection         = true
}

resource "aws_s3_bucket" "artifacts" {
  bucket        = var.artifacts_bucket_name
  force_destroy = false
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifact_backups" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "retener-respaldos-coordinados"
    status = "Enabled"
    filter {
      prefix = "backups/"
    }
    expiration {
      days = var.backup_archive_retention_days
    }
    noncurrent_version_expiration {
      noncurrent_days = var.backup_archive_retention_days
    }
  }

  depends_on = [aws_s3_bucket_versioning.artifacts]
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket" "frontend" {
  bucket        = var.frontend_bucket_name
  force_destroy = false
}

resource "aws_s3_bucket_ownership_controls" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ec2/${local.name}-backend"
  retention_in_days = 30
}

resource "aws_iam_role" "backend_ec2" {
  name = "${local.name}-backend-ec2"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backend_ecr_readonly" {
  role       = aws_iam_role.backend_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "backend_ssm" {
  role       = aws_iam_role.backend_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "backend_runtime" {
  name = "${local.name}-backend-runtime"
  role = aws_iam_role.backend_ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = compact([
          aws_db_instance.postgres.master_user_secret[0].secret_arn,
          var.jwt_secret_arn,
          var.mongodb_uri_secret_arn,
          var.redis_url_secret_arn,
        ])
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "backend" {
  name = "${local.name}-backend-profile"
  role = aws_iam_role.backend_ec2.name
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_acm_certificate" "api" {
  domain_name       = var.api_domain
  validation_method = "DNS"
}

resource "aws_route53_record" "api_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = var.route53_zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "api" {
  certificate_arn         = aws_acm_certificate.api.arn
  validation_record_fqdns = [for record in aws_route53_record.api_cert_validation : record.fqdn]
}

resource "aws_lb" "api" {
  name               = "${local.name}-api-alb"
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "backend" {
  name        = "${local.name}-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = aws_vpc.main.id

  health_check {
    path                = "/ready"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.api.arn
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = aws_acm_certificate_validation.api.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

locals {
  backend_user_data = <<-EOF
#!/bin/bash
set -euo pipefail

dnf update -y
dnf install -y docker awscli amazon-cloudwatch-agent
systemctl enable --now docker
usermod -aG docker ec2-user

mkdir -p /opt/case-inteligente /var/log/case-inteligente

python3 - <<'PY'
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import quote

def secret(arn):
    result = subprocess.run(
        ["aws", "secretsmanager", "get-secret-value", "--region", "${var.aws_region}",
         "--secret-id", arn, "--query", "SecretString", "--output", "text"],
        check=True, capture_output=True, text=True,
    )
    value = result.stdout.strip()
    if not value or "\n" in value:
        raise RuntimeError("El secreto debe ser un valor de una linea")
    return value

database_credentials = json.loads(secret("${aws_db_instance.postgres.master_user_secret[0].secret_arn}"))
database_url = (
    "postgresql+psycopg://"
    + quote(database_credentials["username"], safe="")
    + ":" + quote(database_credentials["password"], safe="")
    + "@${aws_db_instance.postgres.address}:5432/${var.database_name}"
)
values = {
    "APP_ENV": "production",
    "RUN_MIGRATIONS": "true",
    "DATABASE_URL": database_url,
    "MONGODB_URI": secret("${var.mongodb_uri_secret_arn}"),
    "MONGODB_DATABASE": "${var.mongodb_database}",
    "MONGODB_ENABLED": "true",
    "MONGODB_REQUIRED": "true",
    "NOSQL_CONSOLIDATED_MODE": "true",
    "JWT_SECRET_KEY": secret("${var.jwt_secret_arn}"),
    "CORS_ORIGINS": "${local.backend_cors_origins}",
    "ALLOWED_HOSTS": ",".join(dict.fromkeys([
        "${var.api_domain}", "localhost", "127.0.0.1",
        *subprocess.check_output(["hostname", "-I"], text=True).split(),
    ])),
    "OLLAMA_BASE_URL": "${local.ollama_endpoint}",
    "OLLAMA_AWS_BASE_URL": "${local.ollama_endpoint}",
    "OLLAMA_DEFAULT_SOURCE": "aws",
    "AWS_REGION": "${var.aws_region}",
    "S3_ARTIFACTS_BUCKET": "${aws_s3_bucket.artifacts.bucket}",
}
redis_secret_arn = "${var.redis_url_secret_arn != null ? var.redis_url_secret_arn : ""}"
if redis_secret_arn:
    values["REDIS_URL"] = secret(redis_secret_arn)
    values["REDIS_ENABLED"] = "true"
else:
    values["REDIS_ENABLED"] = "false"

path = Path("/opt/case-inteligente/backend.env")
path.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")
os.chmod(path, 0o600)
PY

aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${split("/", var.backend_image)[0]}
docker pull ${var.backend_image}
docker rm -f case-inteligente-backend || true
docker run -d \
  --name case-inteligente-backend \
  --restart unless-stopped \
  --env-file /opt/case-inteligente/backend.env \
  --log-driver awslogs \
  --log-opt awslogs-region=${var.aws_region} \
  --log-opt awslogs-group=${aws_cloudwatch_log_group.backend.name} \
  --log-opt awslogs-stream=backend \
  -p 8000:8000 \
  -v case_generated_artifacts:/storage/generated \
  -v case_coordinated_backups:/storage/backups \
  ${var.backend_image}

docker rm -f case-inteligente-outbox case-inteligente-reconciliation || true
docker run -d \
  --name case-inteligente-outbox \
  --restart unless-stopped \
  --env-file /opt/case-inteligente/backend.env \
  -e RUN_MIGRATIONS=false \
  --log-driver awslogs \
  --log-opt awslogs-region=${var.aws_region} \
  --log-opt awslogs-group=${aws_cloudwatch_log_group.backend.name} \
  --log-opt awslogs-stream=outbox \
  ${var.backend_image} python -m app.core.nosql.commands.distribuir_bandeja_salida --watch

docker run -d \
  --name case-inteligente-reconciliation \
  --restart unless-stopped \
  --env-file /opt/case-inteligente/backend.env \
  -e RUN_MIGRATIONS=false \
  --log-driver awslogs \
  --log-opt awslogs-region=${var.aws_region} \
  --log-opt awslogs-group=${aws_cloudwatch_log_group.backend.name} \
  --log-opt awslogs-stream=reconciliation \
  ${var.backend_image} python -m app.core.nosql.commands.conciliar --operational --watch --interval-seconds 300

cat >/opt/case-inteligente/backup.sh <<'BACKUP'
#!/bin/bash
set -euo pipefail
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
ARCHIVE="/storage/backups/case-$STAMP.zip"
docker exec case-inteligente-backend python -m app.core.nosql.commands.respaldo_coordinado create "$ARCHIVE"
BACKUP_DIR=$(docker volume inspect --format '{{.Mountpoint}}' case_coordinated_backups)
GENERATED_DIR=$(docker volume inspect --format '{{.Mountpoint}}' case_generated_artifacts)
aws s3 cp "$BACKUP_DIR/case-$STAMP.zip" "s3://${aws_s3_bucket.artifacts.bucket}/backups/case-$STAMP.zip" --region ${var.aws_region}
aws s3 sync "$GENERATED_DIR" "s3://${aws_s3_bucket.artifacts.bucket}/generated/" --region ${var.aws_region}
rm -- "$BACKUP_DIR/case-$STAMP.zip"
BACKUP
chmod 700 /opt/case-inteligente/backup.sh

cat >/etc/systemd/system/case-inteligente-backup.service <<'SERVICE'
[Unit]
Description=Coordinated CASE database and generated-artifact backup
After=docker.service
[Service]
Type=oneshot
ExecStart=/opt/case-inteligente/backup.sh
SERVICE

cat >/etc/systemd/system/case-inteligente-backup.timer <<'TIMER'
[Unit]
Description=Daily CASE backup
[Timer]
OnCalendar=*-*-* 03:00:00 UTC
Persistent=true
[Install]
WantedBy=timers.target
TIMER
systemctl daemon-reload
systemctl enable --now case-inteligente-backup.timer

cat >/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<'CWCONFIG'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/cloud-init-output.log",
            "log_group_name": "${aws_cloudwatch_log_group.backend.name}",
            "log_stream_name": "{instance_id}/cloud-init"
          }
        ]
      }
    }
  }
}
CWCONFIG
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
EOF
}

resource "aws_instance" "backend" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.ec2_instance_type
  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.backend.id]
  iam_instance_profile        = aws_iam_instance_profile.backend.name
  associate_public_ip_address = true
  key_name                    = var.ec2_key_name
  user_data_replace_on_change = true
  user_data                   = local.backend_user_data

  root_block_device {
    encrypted   = true
    volume_size = 30
    volume_type = "gp3"
  }

  tags = {
    Name = "${local.name}-backend-ec2"
  }

  depends_on = [
    aws_db_instance.postgres,
    aws_cloudwatch_log_group.backend,
    aws_iam_role_policy.backend_runtime,
    aws_iam_role_policy_attachment.backend_ecr_readonly,
    aws_iam_role_policy_attachment.backend_ssm
  ]
}

resource "aws_lb_target_group_attachment" "backend" {
  target_group_arn = aws_lb_target_group.backend.arn
  target_id        = aws_instance.backend.id
  port             = 8000

  depends_on = [aws_lb_listener.https]
}

resource "aws_route53_record" "api" {
  zone_id = var.route53_zone_id
  name    = var.api_domain
  type    = "A"

  alias {
    name                   = aws_lb.api.dns_name
    zone_id                = aws_lb.api.zone_id
    evaluate_target_health = true
  }
}

resource "aws_sns_topic" "operations" {
  name = "${local.name}-operations"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email == null ? 0 : 1
  topic_arn = aws_sns_topic.operations.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

resource "aws_cloudwatch_metric_alarm" "backend_unhealthy" {
  alarm_name          = "${local.name}-backend-unhealthy"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Minimum"
  threshold           = 1
  treat_missing_data  = "breaching"
  dimensions = {
    LoadBalancer = aws_lb.api.arn_suffix
    TargetGroup  = aws_lb_target_group.backend.arn_suffix
  }
  alarm_actions = [aws_sns_topic.operations.arn]
}

resource "aws_cloudwatch_metric_alarm" "ec2_status" {
  alarm_name          = "${local.name}-ec2-status"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Maximum"
  threshold           = 1
  treat_missing_data  = "breaching"
  dimensions = {
    InstanceId = aws_instance.backend.id
  }
  alarm_actions = [aws_sns_topic.operations.arn]
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${local.name}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 2147483648
  treat_missing_data  = "missing"
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }
  alarm_actions = [aws_sns_topic.operations.arn]
}
