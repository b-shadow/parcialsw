# Guia del bundle generado

## Contenido

Al descargar el bundle se obtienen las carpetas `backend` y `frontend`, `generation-manifest.json` y en cada proyecto `generation-plan.json`.

## Backend

Requisitos: Java 17, Maven 3.9 o superior, Docker opcional y PostgreSQL 16.

```powershell
cd backend/project/<artefacto>
mvn test
docker compose up -d
mvn spring-boot:run
```

Swagger queda en `http://localhost:8080/swagger-ui.html`. Las rutas funcionales se listan en `openapi/functional-routes.json`.

## Flutter

Requisitos: Flutter estable con Dart compatible.

```powershell
cd frontend/project/<paquete>
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://localhost:8080
```

Para Android Emulator use `http://10.0.2.2:8080`. Para un celular fisico use la IP LAN de la computadora y exponga Spring Boot en la red local.

## Reproducibilidad

Compare el `plan_hash` del manifiesto con el `canonical_hash` de ambos planes. Deben ser iguales. No edite fuentes generadas para corregir un defecto del motor: corrija el generador y regenere.
