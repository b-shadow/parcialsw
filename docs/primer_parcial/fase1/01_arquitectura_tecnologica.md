# Fase 1 - Arquitectura tecnologica

## Objetivo

Establecer la base tecnologica de la plataforma CASE inteligente antes del desarrollo funcional completo.

## Productos principales

1. Plataforma CASE colaborativa web.
2. Motor inteligente de analisis y generacion.
3. Motor de generacion automatica de software.

## Arquitectura distribuida

La arquitectura queda definida como una solucion distribuida compuesta por:

- Frontend React para la experiencia web.
- Backend FastAPI como API principal y coordinador modular.
- PostgreSQL como persistencia transaccional.
- WebSockets para colaboracion en tiempo real.
- Motor UML como representacion interna independiente del canvas.
- Motor IA local offline para texto, voz, imagen, validacion y asistencia.
- Generadores deterministas para Spring Boot y Flutter.

## Paquetes funcionales obligatorios

Toda implementacion debe organizarse alrededor de estos dominios:

1. Gestion de acceso, usuarios y seguimiento.
2. Gestion de proyectos y colaboracion.
3. Modelado UML inteligente.
4. Transformacion y generacion automatica de software.

## Decisiones principales

- Backend principal: Python 3.12 + FastAPI.
- Frontend principal: React + TypeScript + Vite.
- Estilos: Tailwind CSS.
- Estado frontend: Zustand.
- Comunicacion HTTP: Axios.
- Comunicacion colaborativa: WebSockets.
- Persistencia: PostgreSQL + SQLAlchemy + Alembic.
- Editor UML: React Flow como primera opcion tecnica.
- IA local: arquitectura preparada para Ollama, llama.cpp o Transformers.
- Backend generado: Spring Boot.
- Frontend generado: Flutter.

