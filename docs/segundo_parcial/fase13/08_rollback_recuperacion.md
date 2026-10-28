# Rollback y recuperacion

## Rollback de lectura

1. Mantener `UML_DIAGRAMS_DUAL_WRITE_ENABLED=true`.
2. Establecer `UML_DIAGRAMS_MONGODB_READ_ENABLED=false`.
3. Reiniciar API y comprobar `/ready`.
4. Verificar editor, XMI, asistente y generadores desde la proyeccion SQL.

Si MongoDB solo esta temporalmente indisponible, `UML_DIAGRAMS_SQL_FALLBACK_ENABLED=true` realiza el cambio automaticamente. Si se desea integridad estricta, se desactiva el fallback y la API responde 503/409 en vez de usar datos dudosos.

## Recuperacion

Tras recuperar MongoDB se ejecuta `--verify-only`. Si hay faltantes o revisiones menores, se reanuda la migracion. Una revision igual con hash distinto requiere investigacion; no debe usarse `--reset-checkpoint` para forzar una sobrescritura. No se eliminan tablas SQL en fase 13.
