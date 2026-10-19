# Clasificacion de intenciones

## Catalogo

El contrato admite las intenciones:

- `answer_question`
- `explain_system`
- `explain_uml`
- `recommend`
- `review_uml`
- `validate_uml`
- `modify_uml`
- `generate_uml`
- `specify_method`
- `prepare_generation`
- `summarize_conversation`
- `summarize_project`
- `coordinate_team`
- `unknown`

## Clasificador determinista previo

`IntentClassifier` normaliza mayusculas, acentos, espacios y errores ortograficos frecuentes. Conserva todas las coincidencias unicas en el orden en que aparecen. Una pregunta explicita puede coexistir con revision, recomendacion o modificacion.

La negacion evita proponer una modificacion para expresiones como `no elimina clases`. Las referencias pronominales sin diagrama activo generan una aclaracion en vez de una accion inventada.

## Relacion con Qwen

Las intenciones previas se incluyen como datos en el prompt. Qwen puede devolver una lista validada por el mismo catalogo, pero no puede crear nombres de intencion nuevos. Si no devuelve intenciones, el orquestador conserva las detectadas localmente.

## Varias solicitudes

Una entrada como:

```text
Revisa el diagrama, agrega Matricula, relaciona Matricula con Curso y prepara Flutter.
```

puede producir `review_uml`, `modify_uml` y `prepare_generation`, junto con recomendaciones y varias acciones ordenadas. Cada accion posee un UUID temporal, orden y dependencias explicitas.

## Ambiguedad

El motor responde con `requires_user_input=true` y `clarification_question` cuando no puede resolver de manera segura expresiones como `conecta esa clase con la anterior` sin contexto activo.

## Evaluacion offline

`ai_engine/evaluation/phase2_cases.py` contiene casos en espanol para explicacion, revision, validacion, edicion, generacion, recomendacion, resumen y especificacion de metodo. La prueba exige recuerdo completo de las intenciones esperadas del conjunto actual.
