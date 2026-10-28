# Integracion funcional

`UmlService._build_internal_model` es la puerta comun al agregado activo. La lectura Mongo-first alimenta:

- modelo completo del editor y posiciones visuales;
- validacion UML y referencias;
- exportacion XMI;
- contexto del asistente del proyecto;
- transformacion intermedia de generacion Spring Boot y Flutter.

Las importaciones XMI, texto, imagen e IA persisten primero la proyeccion transaccional y generan el evento documental. XMI mantiene asociaciones, clases asociativas, generalizacion/herencia, agregacion, composicion y multiplicidades. Los generadores registran la revision del proyecto utilizada, evitando presentar como actual un artefacto generado desde una revision anterior.

Las especificaciones de metodos forman parte de cada metodo dentro del documento; no se pierden precondiciones, poscondiciones, reglas, validaciones, permisos ni contratos backend/frontend.
