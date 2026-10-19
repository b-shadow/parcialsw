# Fase 6 - Editor visual y previsualizacion Flutter

## Objetivo cerrado

La fase convierte la maqueta inicial de estilos en una herramienta persistente. El usuario modifica un tema tipado, inspecciona pantallas derivadas del `ui_manifest` real y genera Flutter con el mismo contrato normalizado. No es un constructor libre de pantallas: la estructura funcional sigue perteneciendo al diagrama UML y al `GenerationPlan` de Fase 5.

## Documentos

1. `01_contrato_tema_v2.md`: tokens y restricciones.
2. `02_normalizacion_compatibilidad.md`: fuente autoritativa y v1.
3. `03_editor_visual.md`: arquitectura React y estado.
4. `04_preview_ui_manifest.md`: preview funcional real.
5. `05_integracion_flutter.md`: ThemeData y artefactos.
6. `06_presets_fuentes_assets.md`: presets y catalogo de fuentes.
7. `07_accesibilidad_responsive.md`: contraste y geometria.
8. `08_pruebas_fidelidad.md`: estrategia y evidencia.
9. `09_guia_usuario_editor_estilos.md`: operacion.
10. `10_resumen_fase6.md`: resultado arquitectonico.
11. `11_acta_cierre_fase6.md`: criterios de cierre.

## Implementacion principal

- `contracts/flutter_theme_v2.schema.json`
- `backend/app/modules/generacion_software/schemas/theme_contract.py`
- `backend/app/modules/generacion_software/coordinated_generator/contracts/ui_manifest.py`
- `frontend/src/modules/transformacion_generacion_software/components/FlutterStyleWorkspace.tsx`
- `backend/migrations/versions/a7b1c2d3e4f5_phase6_flutter_visual_editor.py`

La documentacion de `docs/segundo_parcial/previsualizar_frontend` queda como antecedente historico de la maqueta v1; este directorio define el comportamiento vigente.
