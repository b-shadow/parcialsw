# Proveedores de IA: Integración de Google AI Studio (Gemini)

## 1. Visión General

El sistema CASE Inteligente soporta tres proveedores de inferencia para el asistente de proyecto:
1. **Ollama (local)**: Proveedor predeterminado para entornos offline o con modelos locales como Qwen 2.5 Coder.
2. **Google AI Studio (Gemini)**: Proveedor opcional en la nube con alta capacidad y baja latencia, utilizando la API `generateContent`.
3. **Motor de Reglas Determinista (rule_engine)**: Fallback garantizado sin dependencias externas para operaciones críticas y validaciones de sintaxis UML.

## 2. Configuración de Gemini

Variables de entorno configurables en `.env`:

| Variable | Tipo | Valor por defecto | Descripción |
|---|---|---|---|
| `GEMINI_API_KEY` | `str \| None` | `None` | Clave API de Google AI Studio. Si está ausente, el proveedor se desactiva de forma segura |
| `GEMINI_MODEL` | `str` | `gemini-2.5-flash` | Modelo de Google Gemini a utilizar para inferencia estructurada |
| `GEMINI_BASE_URL` | `str` | `https://generativelanguage.googleapis.com` | Endpoint base REST de la API de Gemini |

## 3. Seguridad y Protocolo

- **Cabecera de autenticación**: La clave API se envía exclusivamente a través de la cabecera HTTP `x-goog-api-key`. Nunca se incluye en parámetros de URL, URLs de log ni excepciones.
- **Salida Estructurada**: Se utiliza `responseMimeType: "application/json"` en `generationConfig` y validación estricta con Pydantic (`UnifiedAiResult`).
- **Tolerancia a fallos**:
  - Reintentos automáticos (hasta 2) con feedback de corrección de esquema JSON si la respuesta no cumple el contrato.
  - Reintentos con backoff ante errores temporales de red, timeout o HTTP 429/5xx.
  - Degradación transparente: Si `GEMINI_API_KEY` no está configurada o se agotan los reintentos, el orquestador conmuta automáticamente al motor de reglas determinista sin emitir un error 500 al cliente.

## 4. Selección Dinámica del Proveedor

La función `select_provider(preferred: str, requested_model: str = "")` en `provider_factory.py`:
- Resuelve `GeminiProvider` si `preferred == "gemini"` y la clave está presente.
- Registra una advertencia y retorna `(None, "")` si se selecciona Gemini sin clave configurada, delegando al motor de reglas.
- Permite la configuración por proyecto a través de `PUT /api/v1/projects/{project_id}/ai/settings` restringida al rol `ORGANIZADOR` mediante el permiso `ai.settings`.
