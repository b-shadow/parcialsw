import json
import re
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from xml.etree import ElementTree

from app.modules.modelado_uml.engine.modelo_interno import (
    ModeloAtributoUML,
    ModeloClaseUML,
    ModeloDiagramaUML,
    ModeloMetodoUML,
    ModeloParametroUML,
    ModeloRelacionUML,
    ModeloVisualUML,
)

XMI_NS = "http://www.omg.org/XMI"
UML_NS = "omg.org/UML1.3"
UML2_NS = "http://www.omg.org/spec/UML/20110701"
XMI_ID = f"{{{XMI_NS}}}id"
XMI_TYPE = f"{{{XMI_NS}}}type"
XMI_VERSION = f"{{{XMI_NS}}}version"

ElementTree.register_namespace("xmi", XMI_NS)
ElementTree.register_namespace("uml", UML2_NS)


def _id_xml(value: str | None, fallback: str) -> str:
    base = str(value or fallback).strip() or fallback
    normalized = re.sub(r"[^A-Za-z0-9_.-]", "_", base).replace("-", "_")
    if not re.match(r"[A-Za-z_]", normalized):
        normalized = f"id_{normalized}"
    return normalized


def _uuid_desde_semilla(value: str | None, fallback: str) -> UUID:
    seed = str(value or fallback).strip() or fallback
    candidate = seed.strip("{}")
    for prefix in ("MX_EAID_", "EAID_", "EAPK_"):
        if candidate.startswith(prefix):
            candidate = candidate[len(prefix) :]
            break
    candidate = candidate.replace("_", "-")
    try:
        return UUID(candidate)
    except ValueError:
        return uuid5(NAMESPACE_URL, seed)


def _fragmento_guid_ea(value: str | None, fallback: str) -> str:
    return str(_uuid_desde_semilla(value, fallback)).upper().replace("-", "_")


def _id_ea(value: str | None, fallback: str, prefix: str = "EAID") -> str:
    if str(value or "").startswith(("EAID_", "EAPK_", "MX_EAID_")):
        normalized = _id_xml(value, fallback)
    else:
        normalized = _fragmento_guid_ea(value, fallback)
    if normalized.startswith(("EAID_", "EAPK_", "MX_EAID_")):
        return normalized
    return f"{prefix}_{normalized}"


def _guid_ea(value: str | None, fallback: str) -> str:
    return f"{{{str(_uuid_desde_semilla(value, fallback)).upper()}}}"


def _guid_retorno_ea(value: str | None, fallback: str) -> str:
    operation_guid = str(_uuid_desde_semilla(value, fallback)).upper()
    return f"{{RETURNID-{operation_guid[9:]}}}"


def _marca_tiempo() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")


def _atributo_xmi(node: ElementTree.Element, name: str) -> str | None:
    return (
        node.attrib.get(f"{{{XMI_NS}}}{name}")
        or node.attrib.get(f"xmi:{name}")
        or node.attrib.get(f"xmi.{name}")
        or node.attrib.get(name)
    )


def _es_etiqueta(node: ElementTree.Element, name: str) -> bool:
    return node.tag.endswith(name)


def _valor_etiquetado(node: ElementTree.Element, tag: str) -> str | None:
    for child in node.iter():
        if _es_etiqueta(child, "TaggedValue") and child.attrib.get("tag") == tag:
            return child.attrib.get("value")
    return None


def _multiplicidad_desde_extremo(end: ElementTree.Element | None, fallback: str | None = None) -> str | None:
    if end is None:
        return fallback
    multiplicity = (
        end.attrib.get("multiplicity")
        or _valor_etiquetado(end, "multiplicity")
        or _valor_etiquetado(end, "cardinality")
    )
    lower = _valor_etiquetado(end, "lowerBound") or end.attrib.get("lower")
    upper = _valor_etiquetado(end, "upperBound") or end.attrib.get("upper")
    if lower and upper:
        multiplicity = upper if lower == upper else f"{lower}..{upper}"
    elif upper:
        multiplicity = upper
    return multiplicity or fallback


def _agregacion_desde_extremo(end: ElementTree.Element | None) -> str | None:
    if end is None:
        return None
    aggregation = (
        end.attrib.get("aggregation")
        or _valor_etiquetado(end, "aggregation")
        or ""
    ).strip().lower()
    if aggregation in {"shared", "aggregate", "aggregation"}:
        return "aggregation"
    if aggregation in {"composite", "composition"}:
        return "composition"
    return None


def _hijos_directos(node: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in list(node) if _es_etiqueta(child, name)]


def _hijos_caracteristica(class_node: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    features = [child for child in class_node if _es_etiqueta(child, "Classifier.feature")]
    if not features:
        return [child for child in class_node if _es_etiqueta(child, name) or _es_etiqueta(child, f"owned{name}")]
    return [child for feature in features for child in feature if _es_etiqueta(child, name) or _es_etiqueta(child, f"owned{name}")]


def _analizar_geometria_diagrama(geometry: str | None) -> ModeloVisualUML | None:
    if not geometry:
        return None
    values: dict[str, float] = {}
    for part in geometry.split(";"):
        if "=" not in part:
            continue
        key, raw_value = part.split("=", 1)
        if key in {"Left", "Top", "Right", "Bottom"}:
            try:
                values[key] = float(raw_value)
            except ValueError:
                continue
    if not {"Left", "Top", "Right", "Bottom"}.issubset(values):
        return None
    return ModeloVisualUML(
        x=values["Left"],
        y=values["Top"],
        width=max(80, values["Right"] - values["Left"]),
        height=max(60, values["Bottom"] - values["Top"]),
    )


def _elementos_diagrama_clases(root: ElementTree.Element) -> tuple[str | None, set[str], dict[str, ModeloVisualUML]]:
    for diagram in root.iter():
        if not _es_etiqueta(diagram, "Diagram") or diagram.attrib.get("diagramType") != "ClassDiagram":
            continue
        subjects: set[str] = set()
        visuals: dict[str, ModeloVisualUML] = {}
        for diagram_element in diagram.iter():
            if not _es_etiqueta(diagram_element, "DiagramElement"):
                continue
            subject = diagram_element.attrib.get("subject")
            if not subject:
                continue
            subjects.add(subject)
            visual = _analizar_geometria_diagrama(diagram_element.attrib.get("geometry"))
            if visual is None:
                continue
            visuals[subject] = visual
        return diagram.attrib.get("name"), subjects, visuals
    return None, set(), {}


def _visuales_se_superponen_editor(classes: list[ModeloClaseUML]) -> bool:
    positioned_classes = [uml_class for uml_class in classes if uml_class.visual]
    if len(positioned_classes) < 3:
        return False
    for index, source in enumerate(positioned_classes):
        for target in positioned_classes[index + 1:]:
            same_row = abs(source.visual.y - target.visual.y) <= 120
            too_close = abs(source.visual.x - target.visual.x) < 320
            if same_row and too_close:
                return True
    return False


def _normalizar_visuales_editor(
    classes: list[ModeloClaseUML], relationships: list[ModeloRelacionUML]
) -> None:
    if not _visuales_se_superponen_editor(classes):
        return

    rows: list[list[ModeloClaseUML]] = []
    for uml_class in sorted(classes, key=lambda item: (item.visual.y, item.visual.x)):
        for row in rows:
            row_average_y = sum(item.visual.y for item in row) / len(row)
            if abs(uml_class.visual.y - row_average_y) <= 100:
                row.append(uml_class)
                break
        else:
            rows.append([uml_class])

    editor_class_width = 290
    column_gap = 180
    row_gap = 230
    origin_x = 60
    origin_y = 60

    for row_index, row in enumerate(rows):
        for column_index, uml_class in enumerate(sorted(row, key=lambda item: item.visual.x)):
            uml_class.visual.x = origin_x + column_index * (editor_class_width + column_gap)
            uml_class.visual.y = origin_y + row_index * row_gap
            uml_class.visual.width = max(uml_class.visual.width or 0, editor_class_width)

    class_by_external_id = {
        str(uml_class.id): uml_class
        for uml_class in classes
        if uml_class.id
    }
    class_by_name = {uml_class.name: uml_class for uml_class in classes}
    for relationship in relationships:
        association_class_id = relationship.metadata_json.get("association_class_id")
        association_class = class_by_external_id.get(str(association_class_id)) if association_class_id else None
        source_class = class_by_name.get(relationship.source_class_id)
        target_class = class_by_name.get(relationship.target_class_id)
        if not association_class or not source_class or not target_class:
            continue
        association_class.visual.x = (source_class.visual.x + target_class.visual.x) / 2
        association_class.visual.y = max(source_class.visual.y, target_class.visual.y) + row_gap
        association_class.visual.width = max(association_class.visual.width or 0, editor_class_width)


def _tipo_atributo_propio(attribute: ModeloAtributoUML) -> str:
    return attribute.data_type or "String"


def _tipo_retorno_operacion_propia(method: ModeloMetodoUML) -> str:
    return method.return_type or "void"


def _reunir_tipos_datos(diagram: ModeloDiagramaUML, export_token: str) -> dict[str, str]:
    data_types: list[str] = []
    for uml_class in diagram.classes:
        for attribute in uml_class.attributes:
            data_types.append(_tipo_atributo_propio(attribute))
        for method in uml_class.methods:
            data_types.append(_tipo_retorno_operacion_propia(method))
            for parameter in method.parameters:
                data_types.append(parameter.data_type)
    data_types.append("void")

    ids: dict[str, str] = {}
    for data_type in data_types:
        normalized = data_type.strip() or "String"
        if normalized not in ids:
            ids[normalized] = f"eaxmiid_{export_token}_{len(ids)}"
    return ids


def _valores_etiquetados(parent: ElementTree.Element, values: dict[str, str]) -> ElementTree.Element:
    tagged_values = ElementTree.SubElement(parent, "UML:ModelElement.taggedValue")
    for tag, value in values.items():
        ElementTree.SubElement(tagged_values, "UML:TaggedValue", {"tag": tag, "value": value})
    return tagged_values


def _referencia_tipo(parent: ElementTree.Element, wrapper_tag: str, type_id: str) -> None:
    wrapper = ElementTree.SubElement(parent, wrapper_tag)
    ElementTree.SubElement(wrapper, "UML:Classifier", {"xmi.idref": type_id})


def _id_exportacion_relacion(
    relationship: ModeloRelacionUML,
    source_id: str,
    target_id: str,
) -> str:
    return _id_ea(relationship.id, f"{source_id}_{target_id}_{relationship.relationship_type}")


def exportar_xmi(diagram: ModeloDiagramaUML) -> str:
    export_token = uuid4().hex[:12].upper()

    def exportar_id(value: str | None, fallback: str, prefix: str = "EAID") -> str:
        return _id_ea(f"{export_token}_{value or fallback}", fallback, prefix)

    def exportar_guid(value: str | None, fallback: str) -> str:
        return _guid_ea(f"{export_token}_{value or fallback}", fallback)

    def exportar_guid_retorno(value: str | None, fallback: str) -> str:
        return _guid_retorno_ea(f"{export_token}_{value or fallback}", fallback)

    package_id = exportar_id(diagram.id, f"package_{diagram.name}", "EAPK")
    model_id = f"MX_{package_id.replace('EAPK_', 'EAID_', 1)}"
    diagram_id = exportar_id(None, f"diagram_{diagram.name}")
    root_class_id = exportar_id(None, "EARootClass")
    data_type_ids = _reunir_tipos_datos(diagram, export_token)
    root = ElementTree.Element(
        "XMI",
        {
            "xmi.version": "1.1",
            "xmlns:UML": UML_NS,
            "timestamp": _marca_tiempo(),
        },
    )

    header = ElementTree.SubElement(root, "XMI.header")
    documentation = ElementTree.SubElement(header, "XMI.documentation")
    ElementTree.SubElement(documentation, "XMI.exporter").text = "Enterprise Architect"
    ElementTree.SubElement(documentation, "XMI.exporterVersion").text = "2.5"

    content = ElementTree.SubElement(root, "XMI.content")
    model = ElementTree.SubElement(
        content,
        "UML:Model",
        {
            "xmi.id": model_id,
            "name": "EA Model",
        },
    )
    model_owned_elements = ElementTree.SubElement(model, "UML:Namespace.ownedElement")
    ElementTree.SubElement(
            model_owned_elements,
            "UML:Class",
            {
                "xmi.id": root_class_id,
                "name": "EARootClass",
                "isRoot": "true",
            "isLeaf": "false",
            "isAbstract": "false",
        },
    )
    package = ElementTree.SubElement(
        model_owned_elements,
        "UML:Package",
        {
            "xmi.id": package_id,
            "name": diagram.name,
            "visibility": "public",
            "isRoot": "false",
            "isLeaf": "false",
            "isAbstract": "false",
        },
    )
    _valores_etiquetados(
        package,
        {
            "ea_package_id": "1",
            "created": _marca_tiempo(),
            "modified": _marca_tiempo(),
            "iscontrolled": "FALSE",
            "version": "1.0",
            "isprotected": "FALSE",
            "usedtd": "FALSE",
            "logxml": "FALSE",
            "packageFlags": "isModel=1;VICON=3;CRC=0;",
            "phase": "1.0",
            "status": "Proposed",
            "author": "CASE Inteligente",
            "complexity": "1",
            "ea_stype": "Public",
            "tpos": "0",
            "gentype": "Java",
        },
    )
    owned_elements = ElementTree.SubElement(package, "UML:Namespace.ownedElement")
    class_id_by_original: dict[str, str] = {}
    class_name_by_original: dict[str, str] = {}
    class_visuals: dict[str, tuple[int, int, int, int]] = {}
    relationship_id_by_original: dict[str, str] = {}
    attribute_local_id = 1
    operation_local_id = 1

    relationship_local_id = 1
    for relationship in diagram.relationships:
        source_id = exportar_id(relationship.source_class_id, "source")
        target_id = exportar_id(relationship.target_class_id, "target")
        relationship_id_by_original[relationship.id or f"{source_id}_{target_id}"] = (
            exportar_id(
                relationship.id,
                f"{source_id}_{target_id}_{relationship.relationship_type}",
            )
        )

    for index, uml_class in enumerate(diagram.classes, start=1):
        class_id = exportar_id(uml_class.id, uml_class.name)
        class_id_by_original[uml_class.id or uml_class.name] = class_id
        class_id_by_original[uml_class.name] = class_id
        class_name_by_original[uml_class.id or uml_class.name] = uml_class.name
        class_name_by_original[uml_class.name] = uml_class.name
        x = int(uml_class.visual.x or (120 + index * 40))
        y = int(uml_class.visual.y or (90 + index * 40))
        width = int(uml_class.visual.width or 220)
        height = int(uml_class.visual.height or 130)
        class_visuals[class_id] = (x, y, x + width, y + height)
        association_connector_id = next(
            (
                relationship_id_by_original.get(
                    relationship.id
                    or f"{relationship.source_class_id}_{relationship.target_class_id}"
                )
                for relationship in diagram.relationships
                if str(relationship.metadata_json.get("association_class_id"))
                in {str(uml_class.id), uml_class.name}
            ),
            None,
        )
        ea_ntype = str(uml_class.metadata_json.get("ea_ntype") or "17" if association_connector_id else "0")
        is_abstract = "true" if uml_class.element_type == "abstract_class" else "false"
        ea_stype = (
            "Interface"
            if uml_class.element_type == "interface"
            else "Enumeration"
            if uml_class.element_type == "enum"
            else "Class"
        )
        stereotype = (
            "interface"
            if uml_class.element_type == "interface"
            else "enumeration"
            if uml_class.element_type == "enum"
            else uml_class.stereotype
        )
        class_attributes = {
            "xmi.id": class_id,
            "name": uml_class.name,
            "visibility": uml_class.visibility,
            "namespace": package_id,
            "isSpecification": "false",
            "isRoot": "false",
            "isLeaf": "false",
            "isAbstract": is_abstract,
            "isActive": "false",
        }
        if stereotype:
            class_attributes["stereotype"] = stereotype
        class_node = ElementTree.SubElement(
            owned_elements,
            "UML:Class",
            class_attributes,
        )
        class_tagged_values = {
            "isSpecification": "false",
            "ea_stype": ea_stype,
            "ea_ntype": ea_ntype,
            "version": "1.0",
            "isActive": "false",
            "package": package_id,
            "date_created": _marca_tiempo(),
            "date_modified": _marca_tiempo(),
            "gentype": "Java",
            "tagged": "0",
            "package_name": diagram.name,
            "phase": "1.0",
            "author": "CASE Inteligente",
            "complexity": "1",
            "status": "Proposed",
            "tpos": "0",
            "ea_localid": str(index),
            "ea_eleType": "element",
            **({"conID": association_connector_id} if association_connector_id else {}),
            "style": (
                "BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;"
                "VSwimLanes=1;HSwimLanes=1;BorderStyle=0;"
            ),
        }
        if is_abstract == "true":
            class_tagged_values["isAbstract"] = "true"
        if stereotype:
            class_tagged_values["stereotype"] = stereotype
        _valores_etiquetados(class_node, class_tagged_values)
        features_node = ElementTree.SubElement(class_node, "UML:Classifier.feature")

        for attribute_index, attribute in enumerate(uml_class.attributes):
            attribute_type = _tipo_atributo_propio(attribute)
            attribute_node = ElementTree.SubElement(
                features_node,
                "UML:Attribute",
                {
                    "name": attribute.name,
                    "changeable": "none",
                    "visibility": attribute.visibility,
                    "ownerScope": "instance",
                    "targetScope": "instance",
                },
            )
            initial_value = ElementTree.SubElement(attribute_node, "UML:Attribute.initialValue")
            expression_attrs = {"body": attribute.initial_value} if attribute.initial_value else {}
            ElementTree.SubElement(initial_value, "UML:Expression", expression_attrs)
            _referencia_tipo(
                attribute_node,
                "UML:StructuralFeature.type",
                data_type_ids.get(attribute_type, data_type_ids["void"]),
            )
            _valores_etiquetados(
                attribute_node,
                {
                    "type": attribute_type,
                    "containment": "Not Specified",
                    "ordered": "0",
                    "static": "0",
                    "collection": "false",
                    "position": str(attribute.order_index),
                    "duplicates": "0",
                    "ea_guid": exportar_guid(attribute.id, f"{class_id}_{attribute.name}"),
                    "ea_localid": str(attribute_local_id),
                    "styleex": "volatile=0;",
                },
            )
            attribute_local_id += 1
        for method_index, method in enumerate(uml_class.methods):
            return_type = _tipo_retorno_operacion_propia(method)
            operation_node = ElementTree.SubElement(
                features_node,
                "UML:Operation",
                {
                    "name": method.name,
                    "visibility": method.visibility,
                    "ownerScope": "instance",
                    "isQuery": "false",
                    "concurrency": "sequential",
                },
            )
            _valores_etiquetados(
                operation_node,
                {
                    "type": return_type,
                    "const": "false",
                    "synchronised": "0",
                    "concurrency": "Sequential",
                    "position": str(method.order_index),
                    "pure": "0",
                    "ea_guid": exportar_guid(method.id, f"{class_id}_{method.name}"),
                    "ea_localid": str(operation_local_id),
                    **(
                        {
                            "case_method_specification_v1": json.dumps(
                                method.specification,
                                ensure_ascii=True,
                                separators=(",", ":"),
                                sort_keys=True,
                            )
                        }
                        if method.specification
                        else {}
                    ),
                },
            )
            operation_local_id += 1
            parameters_node = ElementTree.SubElement(
                operation_node,
                "UML:BehavioralFeature.parameter",
            )
            for parameter_index, parameter in enumerate(method.parameters, start=1):
                parameter_node = ElementTree.SubElement(
                    parameters_node,
                    "UML:Parameter",
                    {"name": parameter.name, "kind": "in", "visibility": "public"},
                )
                _referencia_tipo(
                    parameter_node,
                    "UML:Parameter.type",
                    data_type_ids.get(parameter.data_type, data_type_ids["void"]),
                )
                _valores_etiquetados(
                    parameter_node,
                    {
                        "pos": str(parameter.order_index or parameter_index),
                        "type": parameter.data_type,
                        "const": "0",
                        "ea_guid": exportar_guid(
                            parameter.id,
                            f"{class_id}_{method.name}_{parameter.name}",
                        ),
                    },
                )
                default_value = ElementTree.SubElement(
                    parameter_node,
                    "UML:Parameter.defaultValue",
                )
                expression_attrs = (
                    {"body": parameter.default_value} if parameter.default_value else {}
                )
                ElementTree.SubElement(default_value, "UML:Expression", expression_attrs)

            return_parameter = ElementTree.SubElement(
                parameters_node,
                "UML:Parameter",
                {"kind": "return", "visibility": "public"},
            )
            _referencia_tipo(
                return_parameter,
                "UML:Parameter.type",
                data_type_ids.get(return_type, data_type_ids["void"]),
            )
            _valores_etiquetados(
                return_parameter,
                {
                    "pos": "0",
                    "type": return_type,
                    "const": "0",
                    "ea_guid": exportar_guid_retorno(method.id, f"{class_id}_{method.name}"),
                },
            )
            default_value = ElementTree.SubElement(return_parameter, "UML:Parameter.defaultValue")
            ElementTree.SubElement(default_value, "UML:Expression")

    for relationship in diagram.relationships:
        source_id = class_id_by_original.get(
            relationship.source_class_id,
            exportar_id(relationship.source_class_id, "source"),
        )
        target_id = class_id_by_original.get(
            relationship.target_class_id,
            exportar_id(relationship.target_class_id, "target"),
        )
        relationship_id = exportar_id(
            relationship.id,
            f"{source_id}_{target_id}_{relationship.relationship_type}",
        )
        relationship_id_by_original[
            relationship.id or f"{relationship.source_class_id}_{relationship.target_class_id}"
        ] = relationship_id
        relationship_name = relationship.label or relationship.relationship_type
        relationship_type = relationship.relationship_type.lower()

        if relationship_type in {"inheritance", "generalization"}:
            generalization_node = ElementTree.SubElement(
                owned_elements,
                "UML:Generalization",
                {
                    "xmi.id": relationship_id,
                    "name": relationship_name,
                    "visibility": "public",
                    "subtype": source_id,
                    "supertype": target_id,
                },
            )
            generalization_values: dict[str, str] = {}
            if relationship.source_cardinality:
                generalization_values["sourceMultiplicity"] = relationship.source_cardinality
            if relationship.target_cardinality:
                generalization_values["targetMultiplicity"] = relationship.target_cardinality
            if generalization_values:
                _valores_etiquetados(generalization_node, generalization_values)
            continue

        if relationship_type in {"dependency", "realization", "implementation"}:
            tag = (
                "UML:Abstraction"
                if relationship_type in {"realization", "implementation"}
                else "UML:Dependency"
            )
            ElementTree.SubElement(
                owned_elements,
                tag,
                {
                    "xmi.id": relationship_id,
                    "name": relationship_name,
                    "visibility": "public",
                    "client": source_id,
                    "supplier": target_id,
                },
            )
            continue

        association_node = ElementTree.SubElement(
            owned_elements,
            "UML:Association",
            {
                "xmi.id": relationship_id,
                "name": relationship_name,
                "visibility": "public",
                "isRoot": "false",
                "isLeaf": "false",
                "isAbstract": "false",
            },
        )
        association_tagged_values = {
            "style": "3",
            "ea_type": "Association",
            "direction": "Unspecified",
            "linemode": "3",
            "linecolor": "-1",
            "linewidth": "0",
            "seqno": "0",
            "subtype": "Class",
            "headStyle": "0",
            "lineStyle": "0",
            "privatedata1": "4",
            "ea_localid": str(relationship_local_id),
            "ea_sourceName": class_name_by_original.get(
                relationship.source_class_id,
                relationship.source_class_id,
            ),
            "ea_targetName": class_name_by_original.get(
                relationship.target_class_id,
                relationship.target_class_id,
            ),
            "ea_sourceType": "Class",
            "ea_targetType": "Class",
            "virtualInheritance": "0",
        }
        association_class_id = relationship.metadata_json.get("association_class_id")
        if association_class_id:
            association_class_export_id = class_id_by_original.get(str(association_class_id))
            if association_class_export_id:
                association_tagged_values["associationclass"] = association_class_export_id
        if relationship.source_cardinality:
            association_tagged_values["lb"] = relationship.source_cardinality
            association_tagged_values["sourceMultiplicity"] = relationship.source_cardinality
        if relationship.target_cardinality:
            association_tagged_values["rb"] = relationship.target_cardinality
            association_tagged_values["targetMultiplicity"] = relationship.target_cardinality
        _valores_etiquetados(association_node, association_tagged_values)
        relationship_local_id += 1
        connection_node = ElementTree.SubElement(association_node, "UML:Association.connection")
        source_end_attributes = {
            "name": "",
            "type": source_id,
            "visibility": "public",
            "aggregation": "none",
            "isOrdered": "false",
            "targetScope": "instance",
            "changeable": "none",
            "isNavigable": "true",
        }
        if relationship.source_cardinality:
            source_end_attributes["multiplicity"] = relationship.source_cardinality
        target_end_attributes = {
            "name": "",
            "type": target_id,
            "visibility": "public",
            "aggregation": "none",
            "isOrdered": "false",
            "targetScope": "instance",
            "changeable": "none",
            "isNavigable": "true",
        }
        if relationship.target_cardinality:
            target_end_attributes["multiplicity"] = relationship.target_cardinality
        if relationship_type == "aggregation":
            target_end_attributes["aggregation"] = "shared"
        elif relationship_type == "composition":
            target_end_attributes["aggregation"] = "composite"

        source_end = ElementTree.SubElement(
            connection_node,
            "UML:AssociationEnd",
            source_end_attributes,
        )
        _valores_etiquetados(
            source_end,
            {
                "containment": "Unspecified",
                **({"multiplicity": relationship.source_cardinality} if relationship.source_cardinality else {}),
                **({"cardinality": relationship.source_cardinality} if relationship.source_cardinality else {}),
                "sourcestyle": (
                    "Union=0;Derived=0;AllowDuplicates=0;Owned=0;"
                    "Navigable=Unspecified;"
                ),
                "ea_end": "source",
            },
        )
        target_end = ElementTree.SubElement(
            connection_node,
            "UML:AssociationEnd",
            target_end_attributes,
        )
        _valores_etiquetados(
            target_end,
            {
                "containment": "Unspecified",
                **({"multiplicity": relationship.target_cardinality} if relationship.target_cardinality else {}),
                **({"cardinality": relationship.target_cardinality} if relationship.target_cardinality else {}),
                "deststyle": (
                    "Union=0;Derived=0;AllowDuplicates=0;Owned=0;"
                    "Navigable=Unspecified;"
                ),
                "ea_end": "target",
            },
        )

    for data_type, data_type_id in data_type_ids.items():
        ElementTree.SubElement(
            model_owned_elements,
            "UML:DataType",
            {
                "xmi.id": data_type_id,
                "name": data_type,
                "visibility": "private",
                "isRoot": "false",
                "isLeaf": "false",
                "isAbstract": "false",
            },
        )

    diagram_node = ElementTree.SubElement(
        content,
        "UML:Diagram",
        {
            "xmi.id": diagram_id,
            "name": diagram.name,
            "diagramType": "ClassDiagram",
            "owner": package_id,
            "toolName": "Enterprise Architect 2.5",
        },
    )
    _valores_etiquetados(
        diagram_node,
        {
            "version": "1.0",
            "author": "CASE Inteligente",
            "created_date": _marca_tiempo(),
            "modified_date": _marca_tiempo(),
            "package": package_id,
            "type": "Logical",
            "swimlanes": (
                "locked=false;orientation=0;width=0;inbar=false;names=false;color=-1;"
                "bold=false;fcol=0;tcol=-1;ofCol=-1;"
            ),
            "matrixitems": (
                "locked=false;matrixactive=false;swimlanesactive=true;"
                "kanbanactive=false;width=1;clrLine=0;"
            ),
            "ea_localid": "1",
            "EAStyle": (
                "ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;"
                "Border=1;HighlightForeign=1;PackageContents=1;ShowDetails=0;"
                "ConnectorNotation=UML 2.1;ShowOpRetType=1;ShowIcons=1;"
                "AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;"
            ),
            "styleex": (
                "ExcludeRTF=0;DocAll=0;HideQuals=0;AttPkg=1;SuppressFOC=1;"
                "TConnectorNotation=UML 2.1;AdvancedElementProps=1;"
                "AdvancedFeatureProps=1;AdvancedConnectorProps=1;"
            ),
        },
    )
    diagram_elements = ElementTree.SubElement(diagram_node, "UML:Diagram.element")
    for sequence, (class_id, geometry) in enumerate(class_visuals.items(), start=1):
        left, top, right, bottom = geometry
        ElementTree.SubElement(
            diagram_elements,
            "UML:DiagramElement",
            {
                "geometry": f"Left={left};Top={top};Right={right};Bottom={bottom};",
                "subject": class_id,
                "seqno": str(sequence),
                "style": f"DUID={_id_xml(None, f'duid_{sequence}')};",
            },
        )
    for relationship in diagram.relationships:
        source_id = class_id_by_original.get(
            relationship.source_class_id,
            exportar_id(relationship.source_class_id, "source"),
        )
        target_id = class_id_by_original.get(
            relationship.target_class_id,
            exportar_id(relationship.target_class_id, "target"),
        )
        relationship_id = exportar_id(
            relationship.id,
            f"{source_id}_{target_id}_{relationship.relationship_type}",
        )
        ElementTree.SubElement(
            diagram_elements,
            "UML:DiagramElement",
            {
                "geometry": (
                    "SX=0;SY=0;EX=0;EY=0;EDGE=2;$LLB=;LLT=;LMT=;LMB=;"
                    "LRT=;LRB=;IRHS=;ILHS=;Path=;"
                ),
                "subject": relationship_id,
                "style": "Mode=3;Color=-1;LWidth=0;Hidden=0;",
            },
        )

    ElementTree.SubElement(root, "XMI.difference")
    extensions = ElementTree.SubElement(
        root,
        "XMI.extensions",
        {"xmi.extender": "Enterprise Architect 2.5"},
    )
    ElementTree.SubElement(extensions, "EAModel.paramSub")

    ElementTree.indent(root, space="\t")
    return (
        '<?xml version="1.0" encoding="windows-1252"?>\n'
        + ElementTree.tostring(root, encoding="unicode")
    )


def importar_xmi(content: str, name: str = "Diagrama importado") -> ModeloDiagramaUML:
    root = ElementTree.fromstring(content)
    classes: list[ModeloClaseUML] = []
    relationships: list[ModeloRelacionUML] = []
    id_to_class_name: dict[str, str] = {}
    diagram_name, diagram_subjects, visual_by_subject = _elementos_diagrama_clases(root)
    has_class_diagram_filter = len(diagram_subjects) > 0

    for node in root.iter():
        node_type = _atributo_xmi(node, "type")
        is_class_node = (node.tag.endswith("packagedElement") and node_type == "uml:Class") or _es_etiqueta(node, "Class")
        if is_class_node:
            if node.attrib.get("name") == "EARootClass":
                continue
            class_id = _atributo_xmi(node, "id")
            if has_class_diagram_filter and class_id not in diagram_subjects:
                continue
            attributes = []
            for order_index, child in enumerate(_hijos_caracteristica(node, "Attribute")):
                lower_bound = _valor_etiquetado(child, "lowerBound")
                upper_bound = _valor_etiquetado(child, "upperBound")
                multiplicity = child.attrib.get("multiplicity")
                if upper_bound and upper_bound != "1":
                    multiplicity = upper_bound
                attributes.append(
                    ModeloAtributoUML(
                        id=_atributo_xmi(child, "id"),
                        name=child.attrib.get("name", "atributo"),
                        data_type=child.attrib.get("type") or _valor_etiquetado(child, "type") or "String",
                        visibility=child.attrib.get("visibility", "private"),
                        multiplicity=multiplicity,
                        is_required=lower_bound != "0",
                        order_index=int(_valor_etiquetado(child, "position") or order_index),
                    )
                )
            methods = []
            for order_index, child in enumerate(_hijos_caracteristica(node, "Operation")):
                parameters = []
                for parameter_index, parameter in enumerate(

                        item
                        for item in child.iter()
                        if _es_etiqueta(item, "Parameter")
                        and item.attrib.get("kind", "in") != "return"

                ):
                    default_value = next(
                        (
                            expression.attrib.get("body")
                            for expression in parameter.iter()
                            if _es_etiqueta(expression, "Expression")
                            and expression.attrib.get("body") is not None
                        ),
                        None,
                    )
                    parameters.append(
                        ModeloParametroUML(
                            id=_atributo_xmi(parameter, "id"),
                            name=parameter.attrib.get("name", f"parametro{parameter_index + 1}"),
                            data_type=parameter.attrib.get("type")
                            or _valor_etiquetado(parameter, "type")
                            or "String",
                            default_value=default_value,
                            order_index=int(
                                _valor_etiquetado(parameter, "pos") or parameter_index
                            ),
                        )
                    )
                specification = None
                raw_specification = _valor_etiquetado(child, "case_method_specification_v1")
                if raw_specification and len(raw_specification.encode("utf-8")) <= 64 * 1024:
                    try:
                        candidate = json.loads(raw_specification)
                        if isinstance(candidate, dict) and candidate.get("schema_version", 1) == 1:
                            specification = candidate
                    except (TypeError, ValueError, json.JSONDecodeError):
                        specification = None
                methods.append(
                    ModeloMetodoUML(
                        id=_atributo_xmi(child, "id"),
                        name=child.attrib.get("name", "operacion"),
                        return_type=child.attrib.get("returnType")
                        or _valor_etiquetado(child, "type")
                        or next(
                            (
                                parameter.attrib.get("type") or _valor_etiquetado(parameter, "type")
                                for parameter in child.iter()
                                if _es_etiqueta(parameter, "Parameter") and parameter.attrib.get("kind") == "return"
                            ),
                            None,
                        ),
                        visibility=child.attrib.get("visibility", "public"),
                        order_index=int(_valor_etiquetado(child, "position") or order_index),
                        parameters=parameters,
                        specification=specification,
                    )
                )
            class_name = node.attrib.get("name", "ClaseImportada")
            if class_id:
                id_to_class_name[class_id] = class_name
            class_metadata = {"external_xmi_id": class_id} if class_id else {}
            ea_ntype = _valor_etiquetado(node, "ea_ntype")
            con_id = _valor_etiquetado(node, "conID")
            if ea_ntype:
                class_metadata["ea_ntype"] = ea_ntype
            if con_id:
                class_metadata["conID"] = con_id

            is_abstract = (
                node.attrib.get("isAbstract", "").lower() == "true"
                or _valor_etiquetado(node, "isAbstract") == "true"
            )
            ea_stype = (_valor_etiquetado(node, "ea_stype") or "").strip().lower()
            raw_stereotype = (
                node.attrib.get("stereotype")
                or _valor_etiquetado(node, "stereotype")
                or ""
            ).strip().lower().strip("«»")

            if ea_stype == "interface" or raw_stereotype == "interface":
                element_type = "interface"
                stereotype = None
            elif ea_stype in {"enumeration", "enum"} or raw_stereotype in {"enumeration", "enum"}:
                element_type = "enum"
                stereotype = None
            elif is_abstract:
                element_type = "abstract_class"
                stereotype = raw_stereotype or None
            else:
                element_type = "class"
                stereotype = raw_stereotype or None

            classes.append(
                ModeloClaseUML(
                    id=class_id,
                    name=class_name,
                    visibility=node.attrib.get("visibility", "public"),
                    element_type=element_type,
                    stereotype=stereotype,
                    attributes=attributes,
                    methods=methods,
                    visual=visual_by_subject.get(class_id or "", ModeloVisualUML()),
                    metadata_json=class_metadata,
                )
            )

    for node in root.iter():
        node_type = _atributo_xmi(node, "type")
        if _es_etiqueta(node, "generalization") or _es_etiqueta(node, "Generalization"):
            source_id = node.attrib.get("source") or node.attrib.get("subtype", "")
            target_id = node.attrib.get("target") or node.attrib.get("general") or node.attrib.get("supertype", "")
            relationships.append(
                ModeloRelacionUML(
                    id=_atributo_xmi(node, "id"),
                    source_class_id=id_to_class_name.get(source_id, source_id),
                    target_class_id=id_to_class_name.get(target_id, target_id),
                    relationship_type="inheritance",
                    label=node.attrib.get("name"),
                    source_cardinality=_valor_etiquetado(node, "sourceMultiplicity"),
                    target_cardinality=_valor_etiquetado(node, "targetMultiplicity"),
                )
            )
        elif _es_etiqueta(node, "Association") or (node.tag.endswith("packagedElement") and node_type == "uml:Association"):
            relationship_id = _atributo_xmi(node, "id")
            if has_class_diagram_filter and relationship_id not in diagram_subjects:
                continue
            source_id = node.attrib.get("source", "")
            target_id = node.attrib.get("target", "")
            if not (source_id and target_id):
                ends = [child.attrib.get("type", "") for child in node.iter() if _es_etiqueta(child, "AssociationEnd") or _es_etiqueta(child, "ownedEnd")]
                if len(ends) >= 2:
                    source_id, target_id = ends[0], ends[1]
            if source_id not in id_to_class_name or target_id not in id_to_class_name:
                continue
            all_ends = [child for child in node.iter() if _es_etiqueta(child, "AssociationEnd") or _es_etiqueta(child, "ownedEnd")]
            source_end = next((end for end in all_ends if end.attrib.get("type") == source_id), None)
            target_end = next((end for end in all_ends if end.attrib.get("type") == target_id), None)
            if source_end is None:
                source_end = all_ends[0] if all_ends else None
            if target_end is None:
                target_end = all_ends[1] if len(all_ends) > 1 else None
            source_aggregation = _agregacion_desde_extremo(source_end)
            target_aggregation = _agregacion_desde_extremo(target_end)
            relationship_type = target_aggregation or source_aggregation or "association"
            if source_aggregation and not target_aggregation:
                source_id, target_id = target_id, source_id
                source_end, target_end = target_end, source_end
            source_multiplicity = _multiplicidad_desde_extremo(
                source_end,
                _valor_etiquetado(node, "sourceMultiplicity") or _valor_etiquetado(node, "lb"),
            )
            target_multiplicity = _multiplicidad_desde_extremo(
                target_end,
                _valor_etiquetado(node, "targetMultiplicity") or _valor_etiquetado(node, "rb"),
            )
            association_class_id = _valor_etiquetado(node, "associationclass")
            metadata = {"external_xmi_id": relationship_id}
            if association_class_id and association_class_id in id_to_class_name:
                metadata["association_class_id"] = association_class_id
            relationships.append(
                ModeloRelacionUML(
                    id=relationship_id,
                    source_class_id=id_to_class_name.get(source_id, source_id),
                    target_class_id=id_to_class_name.get(target_id, target_id),
                    relationship_type=relationship_type,
                    label=node.attrib.get("name"),
                    source_cardinality=source_multiplicity,
                    target_cardinality=target_multiplicity,
                    metadata_json=metadata,
                )
            )
        elif _es_etiqueta(node, "Dependency") or _es_etiqueta(node, "Abstraction") or (node.tag.endswith("packagedElement") and node_type and node_type != "uml:Class"):
            relationship_id = _atributo_xmi(node, "id")
            if has_class_diagram_filter and relationship_id not in diagram_subjects:
                continue
            source_id = node.attrib.get("source") or node.attrib.get("client", "")
            target_id = node.attrib.get("target") or node.attrib.get("supplier", "")
            if not source_id:
                for child in node.iter():
                    if _es_etiqueta(child, "client"):
                        ref = _atributo_xmi(child, "idref") or child.attrib.get("xmi.idref") or child.attrib.get("idref")
                        if not ref:
                            for sub in child.iter():
                                ref = _atributo_xmi(sub, "idref") or sub.attrib.get("xmi.idref")
                                if ref:
                                    break
                        if ref:
                            source_id = ref
                            break
            if not target_id:
                for child in node.iter():
                    if _es_etiqueta(child, "supplier"):
                        ref = _atributo_xmi(child, "idref") or child.attrib.get("xmi.idref") or child.attrib.get("idref")
                        if not ref:
                            for sub in child.iter():
                                ref = _atributo_xmi(sub, "idref") or sub.attrib.get("xmi.idref")
                                if ref:
                                    break
                        if ref:
                            target_id = ref
                            break
            if node_type == "uml:Association" and not (source_id and target_id):
                ends = [child.attrib.get("type", "") for child in node if child.tag.endswith("ownedEnd")]
                if len(ends) >= 2:
                    source_id, target_id = ends[0], ends[1]

            if node_type:
                clean_type = node_type.replace("uml:", "").lower()
            else:
                clean_type = "realization" if _es_etiqueta(node, "Abstraction") else "dependency"

            if clean_type in {"abstraction", "realization", "realisation", "implementation"}:
                relationship_type = "realization"
            elif clean_type in {"generalization", "inheritance"}:
                relationship_type = "inheritance"
            elif clean_type == "dependency":
                relationship_type = "dependency"
            else:
                relationship_type = clean_type

            src = id_to_class_name.get(source_id, source_id)
            tgt = id_to_class_name.get(target_id, target_id)
            if src and tgt:
                relationships.append(
                    ModeloRelacionUML(
                        id=relationship_id,
                        source_class_id=src,
                        target_class_id=tgt,
                        relationship_type=relationship_type,
                        label=node.attrib.get("name"),
                    )
                )
    _normalizar_visuales_editor(classes, relationships)
    return ModeloDiagramaUML(name=diagram_name or name, classes=classes, relationships=relationships)
