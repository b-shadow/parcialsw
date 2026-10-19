# Ejecucion Flutter

## Requisitos

- Flutter 3.44 o compatible.
- Android Studio/SDK para Android.
- Xcode y CocoaPods para compilar iOS (solo macOS).
- Backend ejecutandose y accesible desde el dispositivo.

## Preparacion

```powershell
cd mobile
flutter pub get
flutter doctor -v
flutter devices
```

## Emulador Android

`10.0.2.2` apunta al host desde el emulador Android y ya es el valor predeterminado:

```powershell
flutter run -d <ID_EMULADOR>
```

## Telefono fisico

El telefono y la PC deben compartir red. Reemplazar `192.168.1.50` por la IPv4 de la PC y permitir el puerto 8081 en firewall:

```powershell
flutter run -d <ID_TELEFONO> --dart-define=API_BASE_URL=http://192.168.1.50:8081/api/v1
```

El backend debe escuchar en `0.0.0.0`, no solo `127.0.0.1`.

## APK

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://api.ejemplo.com/api/v1
```

Para produccion usar HTTPS. `usesCleartextTraffic` se mantiene para pruebas LAN y debe limitarse con una configuracion de seguridad de red antes de publicar en tienda.

## iOS

```bash
flutter run -d <ID_IPHONE> --dart-define=API_BASE_URL=https://api.ejemplo.com/api/v1
```

La compilacion iOS no puede verificarse desde Windows.
