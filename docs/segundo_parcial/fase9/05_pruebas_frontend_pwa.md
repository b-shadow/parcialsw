# Pruebas de frontend, PWA y movil

## Frontend React

| Verificacion | Resultado |
|---|---|
| ESLint | Aprobado |
| Vitest | 14 archivos, 36 pruebas aprobadas |
| TypeScript + Vite | Build productivo aprobado |
| Playwright | 5 pruebas aprobadas |

Playwright ejecuta el build productivo mediante `vite preview`, no el servidor de desarrollo. Se validan 390x844, 768x1024 y 1440x1000 para el editor visual, el flujo de versiones y el shell offline.

## PWA

`phase9-pwa-shell.spec.ts` comprueba manifiesto, `display=standalone`, activacion del service worker, perdida de red y recarga de `/login` desde precache. Las API privadas siguen con estrategia `NetworkOnly`; no se presentan datos remotos como actuales cuando no existe conectividad.

Los E2E con API simulada bloquean service workers para que el worker no eluda el interceptor de Playwright. La prueba PWA usa el worker real.

## Rendimiento de carga

La carga diferida por ruta redujo el chunk inicial aproximado de 979.20 kB a 346.62 kB. `UmlEditorPage` y JointJS quedaron en un chunk lazy de 509.43 kB que solo se solicita al abrir el editor UML.

## Cliente Flutter movil

- `flutter analyze`: sin observaciones.
- `flutter test`: 4 pruebas aprobadas.
- `flutter build apk --debug`: aprobado.
- Artefacto local: `mobile/build/app/outputs/flutter-apk/app-debug.apk`.
- Dispositivos detectados: Windows, Chrome y Edge; no habia telefono Android/iOS conectado.

La decision vigente conserva `mobile/` como Flutter Android/iOS. No se agrego target web al proyecto movil; la PWA web corresponde al frontend React.

