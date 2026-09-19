INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
VALUES
    ('00000000-0000-4000-8000-000000000001', 'ADMINISTRADOR', 'Rol global con administracion completa de la plataforma.', true, now(), now()),
    ('00000000-0000-4000-8000-000000000002', 'EDITOR', 'Rol global base para usuarios que crean y editan proyectos.', true, now(), now()),
    ('00000000-0000-4000-8000-000000000003', 'ORGANIZADOR', 'Rol de referencia para administracion dentro de proyectos colaborativos.', true, now(), now())
ON CONFLICT (name) DO NOTHING;

