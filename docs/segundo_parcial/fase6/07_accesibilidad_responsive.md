# Accesibilidad y responsive

## Validacion

Los pares semanticos se evalúan con luminancia relativa WCAG. Los diagnosticos incluyen ruta, relacion obtenida, umbral y sugerencia. Labels, controles nativos, mensajes con `role=status` y botones con nombre accesible permiten navegacion asistida.

## Geometria

El workspace usa tres columnas en escritorio y apila controles, preview y contexto en ancho reducido. El preview dispone de anchos movil, tablet y escritorio sin escalar tipografia por viewport. La escala de prueba es 100 %, 130 % o 160 %.

Las filas emplean `min-width: 0`, truncado o salto de palabra donde corresponde. Selectores y controles tienen altura estable. Playwright comprueba que el contenedor no presente overflow horizontal con etiquetas extensas en 390x844, 768x1024 y 1440x1000.
