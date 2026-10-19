# Resumen de la fase 4

La fase transforma los metodos UML de simples firmas visuales a contratos funcionales consumibles. La semantica se mantiene separada de la firma, pero ambas se editan desde el metodo del diagrama actual.

## Resultado arquitectonico

- modelo uno a uno con revision optimista;
- vocabulario cerrado para reglas y plataformas;
- referencias por UUID dentro del diagrama;
- borradores compatibles con trabajo incremental;
- validacion estricta como puerta de generacion;
- IA basada en propuestas confirmables;
- colaboracion sin sobrescritura silenciosa;
- exportacion XMI y snapshots con conservacion semantica;
- modelo intermedio v2 compatible hacia atras.

## Impacto en generadores

Spring Boot recibe ruta, metodo, DTO, permisos, transaccion, errores y reglas. Flutter recibe interaccion, controles, selectores, campos visibles, confirmacion y refresco. Ambos comparten la misma especificacion, por lo que no deben inferir decisiones contradictorias.

## Compatibilidad

Los diagramas previos siguen abriendo. Sus metodos aparecen como `legacy` hasta recibir especificacion. El adaptador del modelo intermedio permite a los generadores aceptar transformaciones v1. XMI sin extension CASE continua siendo valido.

## Riesgos controlados

- concurrencia: revision y precondiciones HTTP;
- referencias rotas: validacion estructural al guardar;
- escritura de IA: confirmacion y transaccion;
- datos libres: modelos cerrados;
- importaciones externas: extension acotada y tolerante;
- regresion visual: compilacion y pruebas frontend.

