# RAG y Embeddings Locales

## Implementacion

Se implemento `LocalVectorStore` en:

`ai_engine/embedding/local_vector_store.py`

## Funcionamiento

- Tokenizacion local.
- Vectorizacion por frecuencia de terminos.
- Similitud coseno.
- Recuperacion de los top resultados.

## Conocimiento incluido

- diagramas de clases.
- relaciones UML.
- Spring Boot.
- Flutter.
- calidad de diseno.

## Uso en inferencia

`LocalAIEngine.generate_uml` consulta el vector store cuando `use_rag` esta activo. La respuesta incluye `knowledge_context` y observaciones sobre uso de RAG.
