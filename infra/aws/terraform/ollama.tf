data "aws_ssm_parameter" "ollama_gpu_ami" {
  count = var.enable_aws_ollama ? 1 : 0
  name  = "/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-22.04/latest/ami-id"
}

resource "aws_security_group" "ollama" {
  count       = var.enable_aws_ollama ? 1 : 0
  name        = "${local.name}-ollama-sg"
  description = "Ollama API access only from the CASE backend"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 11434
    to_port         = 11434
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "ollama_ec2" {
  count = var.enable_aws_ollama ? 1 : 0
  name  = "${local.name}-ollama-ec2"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ollama_ssm" {
  count      = var.enable_aws_ollama ? 1 : 0
  role       = aws_iam_role.ollama_ec2[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ollama" {
  count = var.enable_aws_ollama ? 1 : 0
  name  = "${local.name}-ollama-profile"
  role  = aws_iam_role.ollama_ec2[0].name
}

resource "aws_instance" "ollama" {
  count                       = var.enable_aws_ollama ? 1 : 0
  ami                         = data.aws_ssm_parameter.ollama_gpu_ami[0].value
  instance_type               = var.ollama_instance_type
  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.ollama[0].id]
  iam_instance_profile        = aws_iam_instance_profile.ollama[0].name
  associate_public_ip_address = true
  user_data_replace_on_change = true
  user_data                   = <<-EOF
#!/bin/bash
set -euo pipefail
apt-get update -y
apt-get install -y curl
nvidia-smi
curl -fsSL https://ollama.com/install.sh | sh
mkdir -p /etc/systemd/system/ollama.service.d
cat >/etc/systemd/system/ollama.service.d/case.conf <<'SERVICE'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
SERVICE
systemctl daemon-reload
systemctl enable --now ollama
systemctl restart ollama
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; then break; fi
  sleep 2
done
curl -fsS http://127.0.0.1:11434/api/tags >/dev/null
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:1.5b
ollama pull qwen3-vl:2b-instruct
EOF

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    encrypted   = true
    volume_size = 100
    volume_type = "gp3"
  }

  tags = {
    Name = "${local.name}-ollama-gpu"
  }

  depends_on = [aws_iam_role_policy_attachment.ollama_ssm]
}

resource "aws_cloudwatch_metric_alarm" "ollama_status" {
  count               = var.enable_aws_ollama ? 1 : 0
  alarm_name          = "${local.name}-ollama-status"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Maximum"
  threshold           = 1
  treat_missing_data  = "breaching"
  dimensions = {
    InstanceId = aws_instance.ollama[0].id
  }
  alarm_actions = [aws_sns_topic.operations.arn]
}
