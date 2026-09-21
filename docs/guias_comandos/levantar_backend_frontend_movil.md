# Guia de comandos para levantar backend y app movil generados

Esta guia sirve para ejecutar un proyecto generado por CASE Inteligente sin modificar sus archivos. Asume que ya descargaste y descomprimiste los ZIP en una carpeta como `C:\Users\Dr Lider\Downloads\probando`.

## Requisitos

- Tener Java 17 disponible en `java -version`.
- Tener Docker abierto si quieres que el backend cree/levante PostgreSQL automaticamente.
- Tener Flutter SDK disponible en `flutter --version`.
- Tener Android SDK configurado.
- Tener el celular Android conectado con depuracion USB activa.
- Tener la PC y el celular en la misma red Wi-Fi si pruebas contra backend en la PC.

## 1. Levantar backend Spring Boot

Entrar al backend generado.

```powershell
cd "C:\Users\Dr Lider\Downloads\probando\appbackend"
```

Levantar backend y PostgreSQL con el script generado.

```powershell
.\scripts\run.ps1
```

Verificar Swagger en la PC.

```text
http://localhost:8080/swagger-ui.html
```

Verificar contenedor PostgreSQL si usas Docker.

```powershell
docker ps
```

El backend generado usa PostgreSQL en el puerto `55432` para evitar choque con instalaciones locales.

```text
jdbc:postgresql://127.0.0.1:55432/appbackend
```

## 2. Obtener IP de la PC

Buscar la IPv4 activa de la PC.

```powershell
ipconfig
```

Probar desde el navegador del celular reemplazando `IP_DE_TU_PC`.

```text
http://IP_DE_TU_PC:8080/swagger-ui.html
```

Ejemplo si tu PC tiene IP `192.168.1.20`.

```text
http://192.168.1.20:8080/swagger-ui.html
```

## 3. Levantar app Flutter en celular

Entrar al frontend movil generado.

```powershell
cd "C:\Users\Dr Lider\Downloads\probando\appmobile"
```

Verificar que Flutter detecta el celular.

```powershell
flutter devices
```

Descargar dependencias.

```powershell
flutter pub get
```

Revisar el proyecto generado.

```powershell
flutter analyze
```

Ejecutar en celular fisico apuntando al backend de la PC.

```powershell
flutter run --dart-define=API_BASE_URL=http://IP_DE_TU_PC:8080
```

Ejecutar en un dispositivo especifico si aparecen varios.

```powershell
flutter run -d ID_DEL_DISPOSITIVO --dart-define=API_BASE_URL=http://IP_DE_TU_PC:8080
```

Ejemplo con IP real.

```powershell
flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8080
```

## 4. Generar e instalar APK

Crear APK debug apuntando al backend de la PC.

```powershell
flutter build apk --debug --dart-define=API_BASE_URL=http://IP_DE_TU_PC:8080
```

Instalar APK en el celular conectado.

```powershell
flutter install
```

## 5. Emulador Android

Ejecutar en emulador Android usando `10.0.2.2` para llegar al backend de la PC.

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8080
```

## 6. Flujo completo recomendado

Entrar al backend.

```powershell
cd "C:\Users\Dr Lider\Downloads\probando\appbackend"
```

Levantar backend.

```powershell
.\scripts\run.ps1
```

Entrar al frontend movil en otra terminal.

```powershell
cd "C:\Users\Dr Lider\Downloads\probando\appmobile"
```

Preparar Flutter.

```powershell
flutter pub get
```

Ejecutar en celular.

```powershell
flutter run --dart-define=API_BASE_URL=http://IP_DE_TU_PC:8080
```

## 7. Notas importantes

- No cierres la terminal del backend mientras pruebas la app.
- Si usas celular fisico, no uses `localhost` ni `127.0.0.1` en `API_BASE_URL`; usa la IP de la PC.
- Si usas emulador Android, usa `http://10.0.2.2:8080`.
- Si el UML tiene una clase asociativa como `Inscripcion`, el backend generado crea campos como `estudianteId` y `cursoId`.
- El frontend generado muestra selectores para esas relaciones y envia los IDs al backend.
- Los campos `Date`/`DateTime` salen como selector de fecha y se envian en formato `yyyy-MM-dd`.
