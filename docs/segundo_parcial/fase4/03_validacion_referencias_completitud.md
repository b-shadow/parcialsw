# Validacion, referencias y completitud

## Modos

La plataforma permite guardar trabajo incompleto. Por ello se distinguen dos modos:

- borrador: conserva informacion parcial y bloquea solamente referencias estructurales invalidas;
- estricto: comprueba todo lo necesario antes de declarar el metodo listo para generar.

La ausencia de especificacion se clasifica como `legacy`. Una especificacion vacia es `empty`; una parcial es `draft`; una propuesta de IA es `needs_review`; una estricta con errores es `invalid`; una estricta valida es `ready`.

## Diagnostico

Cada diagnostico contiene codigo estable, severidad, ruta del campo, mensaje, sugerencia y elemento relacionado opcional. La interfaz no interpreta texto para decidir el estado: utiliza `status` y `ready_for_generation`.

## Validaciones estructurales

- clase relacionada dentro del mismo diagrama;
- nombre de clase no ambiguo cuando falta UUID;
- parametro perteneciente al metodo;
- atributo perteneciente a la clase;
- entidad origen existente;
- atributo visible existente en la entidad origen;
- objetivo de refresco dentro del diagrama;
- parametro de ruta presente en la firma.

Estas validaciones son bloqueantes incluso en borrador porque guardar una referencia ajena dañaria la integridad del contrato.

## Validaciones de completitud

- descripcion observable;
- contrato backend para exposicion API o accion de usuario;
- contrato Flutter para acciones visibles;
- todos los parametros visibles mapeados;
- confirmacion para eliminacion visible;
- metodo privado no expuesto;
- operacion mutante no representada por GET;
- codigos de regla unicos;
- coherencia entre tipo y control.

## Puerta de generacion

El modelo intermedio v2 incluye para cada metodo el resultado de validacion estricta. Los generadores reciben especificacion y diagnosticos sin volver a inferir semantica. Los metodos heredados se marcan `legacy`; esto conserva compatibilidad, pero deja explicito que no poseen un contrato funcional listo.

## Seguridad

No se evalua codigo, expresiones o plantillas suministradas por el usuario. Los catalogos son enumeraciones cerradas. Los patrones tienen longitud limitada. Las rutas backend son relativas. Pydantic rechaza campos inesperados y SQLAlchemy persiste unicamente valores normalizados.

