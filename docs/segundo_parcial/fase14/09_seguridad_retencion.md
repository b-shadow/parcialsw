# Seguridad y retencion

- Los respaldos contienen datos de usuarios, diagramas y conversaciones; deben cifrarse en reposo y limitarse a operadores autorizados.
- El ZIP no incluye secretos de entorno, contrasenas de base ni claves VAPID/JWT.
- Los logs de reconciliacion registran IDs, codigos y metricas, no contenido de mensajes ni diagramas.
- La retencion recomendada es diaria por 14 dias, semanal por 8 semanas y mensual por 12 meses.
- Antes de aplicar `d2f6a7b8c9d0` se conserva al menos un backup coordinado probado y fuera del host primario.
- La restauracion `--force` debe quedar asociada a una incidencia y a un hash de backup aprobado.
