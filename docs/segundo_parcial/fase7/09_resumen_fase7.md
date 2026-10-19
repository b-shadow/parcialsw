# Resumen de la Fase 7

La plataforma dispone de puntos de restauracion manuales completos e inmutables. Cada restauracion se representa como operacion independiente, admite reintentos idempotentes, conserva un respaldo previo y genera una revision activa nueva.

La actividad colaborativa usa cursor estable y semantica de dominio. La auditoria mantiene alcance administrativo y elimina secretos. La conversacion de IA no retrocede; recibe un mensaje de sistema que referencia la restauracion.

Las notificaciones ya no dependen de Web Push. La bandeja es la fuente persistente, el outbox controla entrega eventual y Push funciona como canal adicional. La UI incorpora campana, badge, rutas seguras, panel de actividad y dialogos de versionado.

La fase entrega a la Fase 8 contratos consumibles en movil: actividad paginada, bandeja, lectura sincronizada, deep links y eventos de invalidacion.

