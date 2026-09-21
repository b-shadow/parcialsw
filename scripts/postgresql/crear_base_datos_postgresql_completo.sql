-- Script completo para crear la base de datos PostgreSQL de CASE Inteligente.
-- Archivo generado desde las migraciones Alembic del backend.
--
-- Uso recomendado desde psql como superusuario o usuario con permisos CREATEDB/CREATEROLE:
--   psql -U postgres -f scripts/postgresql/crear_base_datos_postgresql_completo.sql
--
-- Credenciales locales usadas por el proyecto:
--   Base de datos: case_inteligente
--   Usuario:       case_user
--   Password:      case_password
--
-- Nota: este script es para una instalacion limpia. Si la base ya existe con tablas,
-- eliminela antes o use migraciones Alembic sobre la base existente.

\set ON_ERROR_STOP on

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'case_user') THEN
        CREATE ROLE case_user LOGIN PASSWORD 'case_password';
    ELSE
        ALTER ROLE case_user WITH LOGIN PASSWORD 'case_password';
    END IF;
END
$$;

SELECT 'CREATE DATABASE case_inteligente OWNER case_user ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'case_inteligente')
\gexec

\connect case_inteligente

SET client_encoding = 'UTF8';
SET timezone = 'UTC';
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 3984b20ad386

CREATE TABLE roles (
    name VARCHAR(50) NOT NULL, 
    description TEXT, 
    is_system BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_roles_name ON roles (name);

CREATE TABLE users (
    full_name VARCHAR(150) NOT NULL, 
    email VARCHAR(180) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    last_access_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE projects (
    owner_id UUID NOT NULL, 
    name VARCHAR(160) NOT NULL, 
    description TEXT, 
    status VARCHAR(40) NOT NULL, 
    settings JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(owner_id) REFERENCES users (id)
);

CREATE INDEX ix_projects_owner_id ON projects (owner_id);

CREATE INDEX ix_projects_status ON projects (status);

CREATE TABLE user_roles (
    user_id UUID NOT NULL, 
    role_id UUID NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(role_id) REFERENCES roles (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    CONSTRAINT uq_user_roles_user_role UNIQUE (user_id, role_id)
);

CREATE INDEX ix_user_roles_role_id ON user_roles (role_id);

CREATE INDEX ix_user_roles_user_id ON user_roles (user_id);

CREATE TABLE user_sessions (
    user_id UUID NOT NULL, 
    refresh_token_hash VARCHAR(255), 
    ip_address VARCHAR(80), 
    user_agent VARCHAR(255), 
    revoked_at TIMESTAMP WITH TIME ZONE, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_user_sessions_user_id ON user_sessions (user_id);

CREATE TABLE audit_logs (
    user_id UUID, 
    project_id UUID, 
    module VARCHAR(80) NOT NULL, 
    action VARCHAR(120) NOT NULL, 
    result VARCHAR(40) NOT NULL, 
    detail TEXT, 
    metadata_json JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_audit_logs_action ON audit_logs (action);

CREATE INDEX ix_audit_logs_module ON audit_logs (module);

CREATE TABLE project_invitations (
    project_id UUID NOT NULL, 
    invited_by_user_id UUID NOT NULL, 
    invited_user_id UUID, 
    invited_email VARCHAR(180) NOT NULL, 
    project_role VARCHAR(40) NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE, 
    responded_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(invited_by_user_id) REFERENCES users (id), 
    FOREIGN KEY(invited_user_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_project_invitations_invited_email ON project_invitations (invited_email);

CREATE INDEX ix_project_invitations_project_id ON project_invitations (project_id);

CREATE INDEX ix_project_invitations_status ON project_invitations (status);

CREATE TABLE project_members (
    project_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    project_role VARCHAR(40) NOT NULL, 
    joined_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    CONSTRAINT uq_project_members_project_user UNIQUE (project_id, user_id)
);

CREATE INDEX ix_project_members_project_id ON project_members (project_id);

CREATE INDEX ix_project_members_project_role ON project_members (project_role);

CREATE INDEX ix_project_members_user_id ON project_members (user_id);

CREATE TABLE project_versions (
    project_id UUID NOT NULL, 
    created_by_user_id UUID NOT NULL, 
    version_number INTEGER NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    description TEXT, 
    snapshot JSONB NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by_user_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    CONSTRAINT uq_project_versions_project_number UNIQUE (project_id, version_number)
);

CREATE INDEX ix_project_versions_project_id ON project_versions (project_id);

CREATE TABLE uml_diagrams (
    project_id UUID NOT NULL, 
    created_by_user_id UUID NOT NULL, 
    name VARCHAR(160) NOT NULL, 
    diagram_type VARCHAR(50) NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    current_version INTEGER NOT NULL, 
    description TEXT, 
    metadata_json JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by_user_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_uml_diagrams_project_id ON uml_diagrams (project_id);

CREATE INDEX ix_uml_diagrams_status ON uml_diagrams (status);

CREATE TABLE ai_processes (
    user_id UUID NOT NULL, 
    project_id UUID, 
    diagram_id UUID, 
    process_type VARCHAR(80) NOT NULL, 
    model_provider VARCHAR(80) NOT NULL, 
    model_name VARCHAR(120), 
    input_payload JSONB NOT NULL, 
    output_payload JSONB NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    error_detail TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(diagram_id) REFERENCES uml_diagrams (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_ai_processes_process_type ON ai_processes (process_type);

CREATE INDEX ix_ai_processes_status ON ai_processes (status);

CREATE INDEX ix_ai_processes_user_id ON ai_processes (user_id);

CREATE TABLE collaboration_events (
    project_id UUID NOT NULL, 
    diagram_id UUID, 
    user_id UUID NOT NULL, 
    event_type VARCHAR(80) NOT NULL, 
    element_type VARCHAR(80), 
    element_id UUID, 
    base_version INTEGER, 
    payload JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(diagram_id) REFERENCES uml_diagrams (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_collaboration_events_event_type ON collaboration_events (event_type);

CREATE INDEX ix_collaboration_events_project_id ON collaboration_events (project_id);

CREATE INDEX ix_collaboration_events_user_id ON collaboration_events (user_id);

CREATE TABLE project_permissions (
    member_id UUID NOT NULL, 
    permission_code VARCHAR(80) NOT NULL, 
    is_allowed BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(member_id) REFERENCES project_members (id), 
    CONSTRAINT uq_project_permissions_member_code UNIQUE (member_id, permission_code)
);

CREATE INDEX ix_project_permissions_member_id ON project_permissions (member_id);

CREATE INDEX ix_project_permissions_permission_code ON project_permissions (permission_code);

CREATE TABLE uml_classes (
    diagram_id UUID NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    visibility VARCHAR(20) NOT NULL, 
    element_type VARCHAR(40) NOT NULL, 
    stereotype VARCHAR(80), 
    description TEXT, 
    metadata_json JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(diagram_id) REFERENCES uml_diagrams (id)
);

CREATE INDEX ix_uml_classes_diagram_id ON uml_classes (diagram_id);

CREATE INDEX ix_uml_classes_name ON uml_classes (name);

CREATE TABLE uml_transformations (
    project_id UUID NOT NULL, 
    diagram_id UUID NOT NULL, 
    requested_by_user_id UUID NOT NULL, 
    source_version VARCHAR(80), 
    target_platform VARCHAR(80) NOT NULL, 
    intermediate_model JSONB NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    error_detail TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(diagram_id) REFERENCES uml_diagrams (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(requested_by_user_id) REFERENCES users (id)
);

CREATE INDEX ix_uml_transformations_diagram_id ON uml_transformations (diagram_id);

CREATE INDEX ix_uml_transformations_project_id ON uml_transformations (project_id);

CREATE INDEX ix_uml_transformations_requested_by_user_id ON uml_transformations (requested_by_user_id);

CREATE INDEX ix_uml_transformations_status ON uml_transformations (status);

CREATE TABLE uml_visual_elements (
    diagram_id UUID NOT NULL, 
    element_type VARCHAR(50) NOT NULL, 
    element_id UUID NOT NULL, 
    position_x FLOAT NOT NULL, 
    position_y FLOAT NOT NULL, 
    width FLOAT, 
    height FLOAT, 
    style JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(diagram_id) REFERENCES uml_diagrams (id), 
    CONSTRAINT uq_visual_element_ref UNIQUE (diagram_id, element_type, element_id)
);

CREATE INDEX ix_uml_visual_elements_diagram_id ON uml_visual_elements (diagram_id);

CREATE TABLE xmi_exchanges (
    diagram_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    exchange_type VARCHAR(30) NOT NULL, 
    tool_name VARCHAR(120), 
    file_name VARCHAR(255) NOT NULL, 
    file_path VARCHAR(500), 
    status VARCHAR(40) NOT NULL, 
    error_detail TEXT, 
    metadata_json JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(diagram_id) REFERENCES uml_diagrams (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_xmi_exchanges_diagram_id ON xmi_exchanges (diagram_id);

CREATE INDEX ix_xmi_exchanges_exchange_type ON xmi_exchanges (exchange_type);

CREATE INDEX ix_xmi_exchanges_status ON xmi_exchanges (status);

CREATE INDEX ix_xmi_exchanges_user_id ON xmi_exchanges (user_id);

CREATE TABLE generated_backends (
    project_id UUID NOT NULL, 
    transformation_id UUID NOT NULL, 
    generated_by_user_id UUID NOT NULL, 
    name VARCHAR(160) NOT NULL, 
    technology VARCHAR(80) NOT NULL, 
    language VARCHAR(40) NOT NULL, 
    database_engine VARCHAR(80) NOT NULL, 
    version_label VARCHAR(80) NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    artifact_path VARCHAR(500), 
    manifest JSONB NOT NULL, 
    error_detail TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(generated_by_user_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(transformation_id) REFERENCES uml_transformations (id)
);

CREATE INDEX ix_generated_backends_generated_by_user_id ON generated_backends (generated_by_user_id);

CREATE INDEX ix_generated_backends_project_id ON generated_backends (project_id);

CREATE INDEX ix_generated_backends_status ON generated_backends (status);

CREATE INDEX ix_generated_backends_transformation_id ON generated_backends (transformation_id);

CREATE TABLE uml_attributes (
    class_id UUID NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    data_type VARCHAR(120) NOT NULL, 
    visibility VARCHAR(20) NOT NULL, 
    initial_value VARCHAR(255), 
    multiplicity VARCHAR(40), 
    is_required BOOLEAN NOT NULL, 
    order_index INTEGER NOT NULL, 
    constraints JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(class_id) REFERENCES uml_classes (id)
);

CREATE INDEX ix_uml_attributes_class_id ON uml_attributes (class_id);

CREATE TABLE uml_methods (
    class_id UUID NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    return_type VARCHAR(120), 
    visibility VARCHAR(20) NOT NULL, 
    order_index INTEGER NOT NULL, 
    metadata_json JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(class_id) REFERENCES uml_classes (id)
);

CREATE INDEX ix_uml_methods_class_id ON uml_methods (class_id);

CREATE TABLE uml_relationships (
    diagram_id UUID NOT NULL, 
    source_class_id UUID NOT NULL, 
    target_class_id UUID NOT NULL, 
    relationship_type VARCHAR(50) NOT NULL, 
    source_cardinality VARCHAR(40), 
    target_cardinality VARCHAR(40), 
    direction VARCHAR(40) NOT NULL, 
    label VARCHAR(120), 
    metadata_json JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(diagram_id) REFERENCES uml_diagrams (id), 
    FOREIGN KEY(source_class_id) REFERENCES uml_classes (id), 
    FOREIGN KEY(target_class_id) REFERENCES uml_classes (id)
);

CREATE INDEX ix_uml_relationships_diagram_id ON uml_relationships (diagram_id);

CREATE INDEX ix_uml_relationships_relationship_type ON uml_relationships (relationship_type);

CREATE INDEX ix_uml_relationships_source_class_id ON uml_relationships (source_class_id);

CREATE INDEX ix_uml_relationships_target_class_id ON uml_relationships (target_class_id);

CREATE TABLE generated_frontends (
    project_id UUID NOT NULL, 
    transformation_id UUID NOT NULL, 
    generated_by_user_id UUID NOT NULL, 
    backend_id UUID, 
    name VARCHAR(160) NOT NULL, 
    technology VARCHAR(80) NOT NULL, 
    language VARCHAR(40) NOT NULL, 
    version_label VARCHAR(80) NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    artifact_path VARCHAR(500), 
    manifest JSONB NOT NULL, 
    error_detail TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(backend_id) REFERENCES generated_backends (id), 
    FOREIGN KEY(generated_by_user_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(transformation_id) REFERENCES uml_transformations (id)
);

CREATE INDEX ix_generated_frontends_generated_by_user_id ON generated_frontends (generated_by_user_id);

CREATE INDEX ix_generated_frontends_project_id ON generated_frontends (project_id);

CREATE INDEX ix_generated_frontends_status ON generated_frontends (status);

CREATE INDEX ix_generated_frontends_transformation_id ON generated_frontends (transformation_id);

CREATE TABLE uml_parameters (
    method_id UUID NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    data_type VARCHAR(120) NOT NULL, 
    default_value VARCHAR(255), 
    order_index INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(method_id) REFERENCES uml_methods (id)
);

CREATE INDEX ix_uml_parameters_method_id ON uml_parameters (method_id);

CREATE TABLE generated_artifacts (
    project_id UUID NOT NULL, 
    generated_backend_id UUID, 
    generated_frontend_id UUID, 
    artifact_type VARCHAR(60) NOT NULL, 
    file_name VARCHAR(255) NOT NULL, 
    file_path VARCHAR(500) NOT NULL, 
    checksum VARCHAR(128), 
    metadata_json JSONB NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(generated_backend_id) REFERENCES generated_backends (id), 
    FOREIGN KEY(generated_frontend_id) REFERENCES generated_frontends (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_generated_artifacts_artifact_type ON generated_artifacts (artifact_type);

CREATE INDEX ix_generated_artifacts_project_id ON generated_artifacts (project_id);

INSERT INTO alembic_version (version_num) VALUES ('3984b20ad386') RETURNING alembic_version.version_num;

-- Running upgrade 3984b20ad386 -> c081b7d17f22

INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
        VALUES
            ('00000000-0000-4000-8000-000000000001', 'ADMINISTRADOR', 'Rol global con administracion completa de la plataforma.', true, now(), now()),
            ('00000000-0000-4000-8000-000000000002', 'EDITOR', 'Rol global base para usuarios que crean y editan proyectos.', true, now(), now()),
            ('00000000-0000-4000-8000-000000000003', 'ORGANIZADOR', 'Rol de referencia para administracion dentro de proyectos colaborativos.', true, now(), now())
        ON CONFLICT (name) DO NOTHING;;

UPDATE alembic_version SET version_num='c081b7d17f22' WHERE alembic_version.version_num = '3984b20ad386';

COMMIT;


