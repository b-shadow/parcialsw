# CASE Inteligente Mobile

Cliente Flutter de consulta para Android e iOS. La documentacion completa esta en `docs/segundo_parcial/fase8/`.

```powershell
flutter pub get
flutter run -d <DISPOSITIVO> --dart-define=API_BASE_URL=http://<IP_PC>:8081/api/v1
```

La aplicacion movil no edita UML, no restaura versiones y no inicia generaciones pesadas.

El icono de sol o luna en la barra superior cambia entre tema claro y oscuro; la elección se conserva al cerrar la aplicación. El visor UML respeta las posiciones y tamaños del diagrama, muestra atributos y firmas de métodos con parámetros, y dibuja las relaciones desde el borde de las clases con cardinalidades y terminaciones UML.
