# Editor UML Colaborativo — Nuevos Elementos y Visibilidades

Documentación de las extensiones al editor UML colaborativo para el 2.º Parcial (CASE Inteligente).

---

## 1. Clasificadores Soportados (`element_type`)

| Tipo | Representación visual | Reglas de visualización |
| :--- | :--- | :--- |
| **`class`** | Encabezado estándar con nombre en negrita | Atributos y métodos estándar |
| **`interface`** | Estereotipo `«interface»` sobre el nombre | Atributos y firmas de métodos |
| **`enum`** | Estereotipo `«enumeration»` sobre el nombre | Sin compartimento de métodos; atributos editados como literales |
| **`abstract_class`** | Nombre de la clase en estilo cursiva (`italic`) | Atributos y métodos estándar |

El componente [`ElementTypeSelect.tsx`](file:///frontend/src/modules/modelado_uml_inteligente/components/ElementTypeSelect.tsx) permite conmutar el clasificador desde el panel de propiedades mediante `PATCH /uml/classes/{id}`.

---

## 2. Visibilidades Soportadas

| Visibilidad | Símbolo UML |
| :--- | :---: |
| `public` | `+` |
| `private` | `-` |
| `protected` | `#` |
| `package` | `~` |

Disponibles tanto para atributos como para métodos, dibujadas de forma estándar en el lienzo SVG y JointJS.

---

## 3. Tipos de Relación

Se incorporan formalmente a la paleta y al lienzo:
- **`dependency`**: línea punteada (`stroke-dasharray="8 6"`) con flecha abierta (`#uml-dependency`).
- **`realization`**: línea punteada (`stroke-dasharray="8 6"`) con triángulo hueco (`#uml-realization`). Se acepta e interoperabiliza con el identificador backend `implementation`.

---

## 4. Bloqueo de Elementos (`lockedElements`)

El lienzo recibe la propiedad opcional `lockedElements: Record<string, ElementLock>`. Cuando un clasificador está bloqueado por otro usuario:
- Se dibuja con borde punteado ámbar (`border-2 border-dashed border-amber-500`).
- Se despliega una píldora indicando el candado `🔒` y `{display_name} editando`.
