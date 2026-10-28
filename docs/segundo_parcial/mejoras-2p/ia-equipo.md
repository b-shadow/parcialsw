# IA del Equipo: Sugerencias Proactivas y Conciencia Colaborativa

## 1. Visión General

La plataforma CASE Inteligente integra la Inteligencia Artificial como un **desarrollador más del equipo**:
- Observa activamente los cambios realizados en el diagrama y las versiones del proyecto a través de **Redis Streams** (`case:changelog:all`).
- Propone mejoras e identifica inconsistencias **por iniciativa propia** sin necesidad de invocación explícita por parte de los usuarios.
- Identifica la autoría de cada cambio para sintetizar resúmenes de actividad colaborativa.

## 2. Arquitectura del Consumidor y Asesor Proactivo

```
[ Mutaciones en Proyecto / Diagrama ]
                  │
                  ▼ (ProjectMutationGuard / Hooks)
     [ Redis Stream: case:changelog:all ]
                  │
                  ▼ (Grupo de Consumo: case-workers)
        ChangeLogConsumer (Workers)
         ├──> Difusión WebSocket: CHANGE_LOGGED (a todos los integrantes)
         └──> ProactiveAdvisorService.on_change(entry)
```

## 3. Disparadores de Sugerencias Proactivas

1. **Acumulación de Cambios (`min_changes`)**:
   - Cada cambio de usuarios (`source='ui'`) o de la propia IA (`source='ai'`) incrementa el contador de cambios pendientes.
   - Al alcanzar el umbral (`AI_PROACTIVE_MIN_CHANGES=5`), se analiza el modelo UML mediante `validate_internal_model`.
   - Si se detectan inconsistencias (e.g. clases sin atributos, visibilidades no reconocidas), se genera un mensaje proactivo con hasta 3 recomendaciones ordenadas por severidad.
   - Si el diagrama no presenta anomalías, la IA permanece en silencio para evitar ruido innecesario.
2. **Registro de Versión de Proyecto (`version`)**:
   - Al registrar una versión (`CREATE_PROJECT_VERSION`), la IA analiza el historial reciente en Redis y emite un resumen estructurado de las contribuciones de cada integrante.
3. **Importación XMI (`import`)**:
   - Al importar un archivo XMI (`IMPORT_XMI` o `IMPORT_XMI_REPLACE_DIAGRAM`), la IA evalúa la coherencia del diagrama importado y notifica observaciones de calidad de inmediato.

## 4. Control de Frecuencia y Prevención de Ciclos

- **Cooldown**: Tras emitir una sugerencia, se activa una clave con TTL en Redis (`case:proactive:cooldown:{project_id}`) equivalente a `AI_PROACTIVE_COOLDOWN_SECONDS=120`. Durante este intervalo no se emiten nuevas sugerencias.
- **Filtrado de Fuente**: Los cambios con `source='system'` son descartados para no generar bucles infinitos de retroalimentación.
- **Degradación Transparente**: Si el proyecto aún no tiene una conversación creada, el servicio captura la condición, registra un mensaje informativo en el log y continúa sin interrumpir el flujo.

## 5. Conciencia del Equipo: Autores y Actividad por Integrante (V2.2)

- **Atribución de Autores**: Cada mensaje reciente en el chat incluye `author_display_name` obtenido mediante `AssistantRepository.user_display_names`, permitiendo a la IA dirigirse a los integrantes por su nombre real.
- **Historial de Actividad del Equipo**: `ContextBuilder` agrupa las últimas 50 entradas de Redis Streams (o PostgreSQL fallback) por actor en `TeamActivityItem`, limitando a 10 acciones por persona y preservando el presupuesto `ContextBudget`.
- **Clasificación de Intención `coordinate_team`**: Expresiones como «¿Qué hizo cada uno?», «quién modificó el modelo», «resumen del equipo» u «organiza el trabajo» se clasifican con confianza 0.9.
- **Moderación y Coordinación**: `RuleEngineProvider` responde detallando la actividad reciente de cada persona y, si dos o más integrantes editaron la misma clase, emite una sugerencia proactiva de coordinación y reparto de tareas para prevenir sobreescrituras concurrentes.
