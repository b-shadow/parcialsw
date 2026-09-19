# Fase 1 - Contexto asimilado del proyecto

## Documentacion analizada

Antes de iniciar desarrollo se revisaron todos los archivos Markdown ubicados en `docs/`:

- `Contexto_General_Proyecto_CASE_Inteligente.md`
- `Prompt_Fase_1_Arquitectura_Tecnologica.md`
- `Prompt_Fase_2_Ingenieria_Requisitos_Arquitectura.md`
- `Prompt_Fase_3_Diseno_Base_Datos_Modelo_Persistencia.md`
- `Prompt_Fase_4_Backend_Modular_Por_Paquetes.md`
- `Prompt_Fase_5_Frontend_React_Tailwind_Arquitectura_Modular.md`
- `Prompt_Fase_6_Motor_Modelado_UML_Inteligente.md`
- `Prompt_Fase_7_IA_Local_Offline.md`
- `Prompt_Fase_8_Generador_Backend_SpringBoot.md`
- `Prompt_Fase_9_Generador_Frontend_Flutter.md`
- `Prompt_Fase_10_IA_Local_Offline_Especializada.md`
- `Prompt_Fase_11_Integracion_AWS_Seguridad_Operacion.md`

## Comprension general

El proyecto consiste en una plataforma CASE inteligente, colaborativa y modular para crear, editar, validar y transformar diagramas de clases UML en software funcional. El flujo final esperado es:

1. El usuario crea una cuenta.
2. Crea o ingresa a un proyecto colaborativo.
3. Modela diagramas UML manualmente o mediante texto, voz o imagen.
4. El sistema almacena, versiona y sincroniza el modelo.
5. La IA local offline valida o genera estructuras UML.
6. El modelo UML se transforma en una estructura intermedia.
7. Se genera un backend Spring Boot.
8. Se genera un frontend movil Flutter.
9. Se registran generaciones, versiones y bitacora.

## Arquitectura principal definida

La arquitectura debe respetar cuatro paquetes funcionales:

1. Gestion de acceso, usuarios y seguimiento.
2. Gestion de proyectos y colaboracion.
3. Modelado UML inteligente.
4. Transformacion y generacion automatica de software.

Esta separacion por dominio aplica al backend FastAPI, al frontend React y a los componentes generadores. No se debe reemplazar por una organizacion arbitraria basada solo en capas tecnicas.

## Tecnologias base

- Frontend web principal: React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide React, Zustand, Axios y WebSockets.
- Backend principal: Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT y WebSockets.
- Base de datos: PostgreSQL, con uso de UUID, JSONB, indices, restricciones y migraciones.
- Editor UML: React Flow como candidato principal, evaluando compatibilidad con nodos UML, relaciones y colaboracion.
- Motor UML: modelo interno independiente de la interfaz grafica.
- IA local offline: modelos locales como Llama, Mistral, Qwen o DeepSeek mediante Ollama, llama.cpp, Transformers u otra opcion local.
- Backend generado: Spring Boot, Java, Spring Web, Spring Data JPA, Spring Security, PostgreSQL, DTO, servicios, controladores y repositorios.
- Frontend generado: Flutter y Dart, con arquitectura modular, modelos, servicios API, pantallas, formularios y navegacion.
- Despliegue final: AWS, con opciones como EC2/ECS, RDS PostgreSQL, S3, CloudFront, Docker, CI/CD y monitoreo.

## Restricciones y decisiones rectoras

- La solucion final no debe depender de servicios externos de inteligencia artificial.
- Las APIs externas solo pueden usarse en investigacion, entrenamiento, pruebas o comparacion.
- La IA final debe funcionar localmente y offline.
- La generacion base de Spring Boot y Flutter debe ser determinista; la IA puede asistir, mejorar o sugerir, pero no debe ser la unica base del generador.
- El modelo UML persistido debe ser reconstruible y versionable.
- El modelo interno UML debe estar desacoplado del canvas visual.
- Cada cambio colaborativo debe registrarse como evento con usuario, fecha, proyecto y elemento afectado.
- Se debe diferenciar entre backend principal de la plataforma, desarrollado en FastAPI, y backend generado, desarrollado en Spring Boot.
- Se debe diferenciar entre rol global y rol interno de proyecto.

## Datos y persistencia esperada

La base de datos debe soportar:

- Usuarios, roles globales, sesiones y bitacora.
- Proyectos, integrantes, permisos internos, versiones y eventos colaborativos.
- Diagramas UML, clases, atributos, metodos, relaciones y posiciones visuales.
- Importaciones/exportaciones XMI.
- Procesos de IA.
- Transformaciones UML.
- Registros de backend y frontend generados.

La estrategia esperada es hibrida: tablas normalizadas para elementos principales y JSONB para configuraciones dinamicas o datos visuales flexibles.

## Colaboracion en tiempo real

La colaboracion debe implementarse mediante WebSockets. Eventos base:

- `CREATE_CLASS`
- `UPDATE_CLASS`
- `DELETE_CLASS`
- `CREATE_ATTRIBUTE`
- `UPDATE_ATTRIBUTE`
- `CREATE_METHOD`
- `CREATE_RELATION`
- `MOVE_ELEMENT`
- `SAVE_VERSION`
- `RESTORE_VERSION`

El backend debe validar permisos, actualizar el modelo, persistir eventos y distribuir cambios a usuarios conectados.

## Documentacion por fases

Todo avance posterior debe documentarse dentro de la carpeta de fase correspondiente:

- `docs/fase1/`
- `docs/fase2/`
- `docs/fase3/`
- y asi sucesivamente.

Cada resumen de fase debe registrar:

- Que se implemento.
- Archivos creados o modificados.
- Decisiones tecnicas tomadas.
- Cambios realizados en arquitectura o base de datos.
- Pendientes para la siguiente fase.

## Estado actual

No se ha iniciado implementacion funcional. Este documento registra unicamente la lectura y consolidacion del contexto tecnico inicial.

