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
