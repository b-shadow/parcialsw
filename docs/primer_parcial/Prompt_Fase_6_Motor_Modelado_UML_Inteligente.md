# PROMPT FASE 6: DESARROLLO DEL MOTOR DE MODELADO UML INTELIGENTE Y EDITOR COLABORATIVO

## Contexto general de la fase

Esta fase corresponde al desarrollo del núcleo principal de la
plataforma CASE: el motor de modelado UML inteligente.

Este componente será responsable de permitir la creación, edición,
análisis, almacenamiento e intercambio de diagramas de clases UML.

La fase se enfoca exclusivamente en el módulo:

## Modelado UML inteligente

Este módulo debe permitir que un usuario pueda construir modelos UML
mediante diferentes mecanismos:

-   Edición manual mediante interfaz gráfica.
-   Generación mediante instrucciones de texto.
-   Generación mediante comandos de voz.
-   Generación mediante captura y procesamiento de imágenes.
-   Importación desde formatos UML externos.
-   Exportación hacia herramientas compatibles como Enterprise
    Architect.

Además debe funcionar integrado con:

-   Frontend React + Tailwind.
-   Backend FastAPI.
-   WebSockets para colaboración.
-   Base de datos PostgreSQL.
-   Motor de IA local offline.

------------------------------------------------------------------------

# Objetivo general de la fase

Diseñar e implementar un motor UML capaz de representar diagramas de
clases, permitir su modificación colaborativa y preparar dichos modelos
para procesos posteriores de generación automática de software.

El motor debe permitir:

-   Crear modelos UML.
-   Representar clases.
-   Representar atributos.
-   Representar métodos.
-   Representar relaciones.
-   Validar estructura UML.
-   Guardar versiones.
-   Sincronizar cambios.
-   Exportar e importar modelos.

------------------------------------------------------------------------

# 1. Definición del modelo interno UML

Antes de desarrollar el editor visual se debe definir una representación
interna del modelo UML.

El modelo interno debe ser independiente de la interfaz gráfica.

Debe permitir representar:

-   Elementos UML.
-   Relaciones.
-   Propiedades.
-   Metadatos.
-   Posiciones visuales.

------------------------------------------------------------------------

# 2. Entidades principales del modelo UML

## Diagrama UML

Debe representar un diagrama completo.

Información:

-   Identificador.
-   Nombre.
-   Proyecto asociado.
-   Usuario creador.
-   Fecha creación.
-   Estado.
-   Versión actual.

------------------------------------------------------------------------

## Clase UML

Representar:

-   Nombre.
-   Visibilidad.
-   Tipo.
-   Estereotipo.
-   Descripción.

Debe permitir:

-   Crear.
-   Editar.
-   Eliminar.

------------------------------------------------------------------------

## Atributo UML

Representar:

-   Nombre.
-   Tipo de dato.
-   Visibilidad.
-   Valor inicial.
-   Multiplicidad.

Ejemplo:

    -nombre: String
    -edad: Integer

------------------------------------------------------------------------

## Método UML

Representar:

-   Nombre.
-   Visibilidad.
-   Parámetros.
-   Tipo retorno.

Ejemplo:

    +calcularTotal(): Double

------------------------------------------------------------------------

## Relaciones UML

Soportar:

-   Asociación.
-   Herencia.
-   Implementación.
-   Dependencia.
-   Agregación.
-   Composición.

Debe almacenar:

-   Clase origen.
-   Clase destino.
-   Tipo relación.
-   Cardinalidad.
-   Dirección.

------------------------------------------------------------------------

# 3. Editor gráfico UML

Desarrollar el editor visual del diagrama.

Debe incluir:

## Área principal de trabajo

Características:

-   Canvas infinito.
-   Zoom.
-   Movimiento.
-   Selección múltiple.
-   Ajuste automático.

------------------------------------------------------------------------

## Barra de herramientas

Debe permitir:

-   Crear clase.
-   Crear relación.
-   Eliminar elemento.
-   Guardar.
-   Exportar.
-   Validar.
-   Generar código.

------------------------------------------------------------------------

## Panel de propiedades

Debe mostrar:

Cuando se selecciona una clase:

-   Nombre.
-   Atributos.
-   Métodos.
-   Relaciones.

------------------------------------------------------------------------

# 4. Librería de diagramación

Evaluar e implementar la librería más adecuada.

Analizar:

## React Flow

Evaluar:

-   Nodos personalizados.
-   Conexiones.
-   Eventos.
-   Rendimiento.
-   Personalización.

------------------------------------------------------------------------

## JointJS

Evaluar:

-   Soporte UML.
-   Modelado complejo.
-   Licencia.

------------------------------------------------------------------------

## GoJS

Evaluar:

-   Capacidades avanzadas.
-   Rendimiento.
-   Licenciamiento.

------------------------------------------------------------------------

## D3.js

Evaluar:

-   Bajo nivel.
-   Personalización.

------------------------------------------------------------------------

Seleccionar la librería considerando:

-   Compatibilidad React.
-   Diagramas UML.
-   Colaboración tiempo real.
-   Mantenimiento futuro.

------------------------------------------------------------------------

# 5. Creación manual de diagramas

Implementar flujo:

Usuario ingresa al editor.

↓

Selecciona crear clase.

↓

Define nombre.

↓

Agrega atributos.

↓

Agrega métodos.

↓

Define relaciones.

↓

Guarda modelo.

------------------------------------------------------------------------

Debe permitir:

-   Crear clases.
-   Editar clases.
-   Eliminar clases.
-   Mover elementos.
-   Cambiar propiedades.

------------------------------------------------------------------------

# 6. Generación UML mediante texto

Preparar integración con IA.

Flujo:

Usuario escribe descripción.

Ejemplo:

"Crear sistema de biblioteca con libros, usuarios y préstamos"

↓

IA interpreta requerimiento.

↓

Genera estructura UML.

↓

Usuario revisa.

↓

Guarda modelo.

------------------------------------------------------------------------

Debe soportar:

-   Crear clases.
-   Crear atributos.
-   Crear métodos.
-   Crear relaciones.

------------------------------------------------------------------------

# 7. Generación UML mediante voz

Preparar integración con reconocimiento de voz.

Flujo:

Usuario habla.

↓

Sistema convierte voz a texto.

↓

Modelo IA interpreta.

↓

Genera UML.

------------------------------------------------------------------------

Considerar:

-   Captura audio.
-   Conversión texto.
-   Procesamiento.
-   Validación.

------------------------------------------------------------------------

# 8. Generación UML mediante imágenes

Implementar procesamiento de diagramas existentes.

Flujo:

Usuario carga imagen.

↓

Sistema procesa imagen.

↓

Detecta elementos UML.

↓

Construye modelo interno.

↓

Muestra diagrama editable.

------------------------------------------------------------------------

Debe reconocer:

-   Clases.
-   Nombres.
-   Atributos.
-   Métodos.
-   Relaciones.

------------------------------------------------------------------------

# 9. Validación inteligente UML

Implementar módulo de validación.

Debe detectar:

## Errores estructurales

Ejemplo:

-   Clases sin nombre.
-   Relaciones incompletas.
-   Métodos inválidos.

------------------------------------------------------------------------

## Problemas de diseño

Ejemplo:

-   Relaciones inconsistentes.
-   Dependencias excesivas.
-   Mala organización.

------------------------------------------------------------------------

Debe generar:

-   Errores.
-   Advertencias.
-   Recomendaciones.

------------------------------------------------------------------------

# 10. Importación y exportación XMI

Implementar compatibilidad UML.

Debe permitir:

## Exportar

Generar:

-   Archivo XMI.
-   Modelo compatible.

------------------------------------------------------------------------

## Importar

Procesar:

-   Archivo XMI externo.
-   Modelo Enterprise Architect.

------------------------------------------------------------------------

Debe conservar:

-   Clases.
-   Atributos.
-   Métodos.
-   Relaciones.

------------------------------------------------------------------------

# 11. Colaboración en tiempo real

Integrar WebSockets.

El editor debe trabajar con proyectos colaborativos.

Flujo:

Usuario modifica elemento.

↓

Frontend envía evento.

↓

Backend valida permisos.

↓

Actualiza modelo.

↓

Distribuye cambio.

------------------------------------------------------------------------

Eventos:

-   CREATE_CLASS.
-   UPDATE_CLASS.
-   DELETE_CLASS.
-   CREATE_ATTRIBUTE.
-   UPDATE_ATTRIBUTE.
-   CREATE_METHOD.
-   CREATE_RELATION.
-   MOVE_ELEMENT.

------------------------------------------------------------------------

# 12. Control de conflictos

Definir estrategia para múltiples usuarios.

Considerar:

-   Versionamiento.
-   Control optimista.
-   Orden de eventos.

Registrar:

-   Usuario.
-   Fecha.
-   Acción.
-   Elemento afectado.

------------------------------------------------------------------------

# 13. Persistencia del modelo UML

Integrar con PostgreSQL.

Guardar:

-   Diagramas.
-   Clases.
-   Atributos.
-   Métodos.
-   Relaciones.
-   Posiciones gráficas.

Permitir:

-   Recuperar modelo.
-   Restaurar versión.
-   Comparar cambios.

------------------------------------------------------------------------

# 14. Preparación para generación automática

El modelo UML debe ser compatible con:

## Generador Spring Boot

Debe proporcionar:

-   Clases.
-   Atributos.
-   Métodos.
-   Relaciones.

------------------------------------------------------------------------

## Generador Flutter

Debe proporcionar:

-   Entidades.
-   Campos.
-   Pantallas necesarias.

------------------------------------------------------------------------

# 15. Pruebas del motor UML

Realizar:

## Pruebas funcionales

-   Crear diagramas.
-   Editar elementos.
-   Exportar.
-   Importar.

## Pruebas colaborativas

-   Usuarios simultáneos.
-   Sincronización.

## Pruebas IA

-   Texto.
-   Voz.
-   Imagen.

------------------------------------------------------------------------

# 16. Documentación técnica

Generar:

-   Arquitectura del motor UML.
-   Modelo interno.
-   Eventos WebSocket.
-   Integración frontend/backend.
-   Formato XMI.
-   Guía uso editor.

------------------------------------------------------------------------

# Entregables de la fase

-   Motor UML funcional.
-   Editor gráfico.
-   Modelo interno UML.
-   Integración WebSocket.
-   Importación/exportación XMI.
-   Validación UML.
-   Preparación IA.
-   Documentación técnica.

------------------------------------------------------------------------

# Casos de uso relacionados

-   CU-10 Crear y editar diagramas de clases UML.
-   CU-11 Generar diagramas de clases UML mediante procesamiento de
    imágenes.
-   CU-12 Importar y exportar modelos UML.
-   CU-13 Validar diagramas de clases UML.

------------------------------------------------------------------------

# Detallar casos de uso

Pegar detallar casos de uso.
