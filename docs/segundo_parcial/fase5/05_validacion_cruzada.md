# Validacion cruzada

## Invariantes

Antes de publicar se comparan los inventarios emitidos con el plan:

- mismo `operation_id`;
- mismo verbo HTTP;
- misma ruta efectiva;
- mismos campos JSON de entrada y orden;
- una accion Flutter solo cuando corresponde;
- una ruta Spring para toda llamada Flutter.

## Mecanismo

Los emisores entregan inventarios estructurados en sus manifiestos. `validate_cross_contract` compara conjuntos y DTO sin analizar texto Java o Dart, lo cual evita falsos positivos por formato.

## Codigos

- `cross_contract_missing_route`
- `cross_contract_unplanned_route`
- `cross_contract_dto_mismatch`

Cualquier diagnostico de severidad error aborta staging. El test de deriva elimina intencionalmente una ruta Flutter y confirma que la publicacion se bloquea.

## Resultado del caso academico

`POST /api/inscripciones/registrar` fue emitido de forma identica en Spring Boot y Flutter, con `estudianteId`, `cursoId`, `fecha` y `notaFinal` en el body.
