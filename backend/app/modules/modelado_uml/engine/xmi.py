import re
from datetime import datetime, timezone
from xml.etree import ElementTree

from app.modules.modelado_uml.engine.internal_model import (
    UmlAttributeModel,
    UmlClassModel,
    UmlDiagramModel,
    UmlMethodModel,
    UmlVisualModel,
    UmlRelationshipModel,
)

XMI_NS = "http://www.omg.org/XMI"
UML_NS = "omg.org/UML1.3"
UML2_NS = "http://www.omg.org/spec/UML/20110701"
XMI_ID = f"{{{XMI_NS}}}id"
XMI_TYPE = f"{{{XMI_NS}}}type"
XMI_VERSION = f"{{{XMI_NS}}}version"

ElementTree.register_namespace("xmi", XMI_NS)
ElementTree.register_namespace("uml", UML2_NS)


def _xml_id(value: str | None, fallback: str) -> str:
    base = str(value or fallback).strip() or fallback
    normalized = re.sub(r"[^A-Za-z0-9_.-]", "_", base).replace("-", "_")
    if not re.match(r"[A-Za-z_]", normalized):
        normalized = f"id_{normalized}"
    return normalized


def _ea_id(value: str | None, fallback: str, prefix: str = "EAID") -> str:
    normalized = _xml_id(value, fallback)
    if normalized.startswith(("EAID_", "EAPK_", "MX_EAID_")):
        return normalized
    return f"{prefix}_{normalized}"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _xmi_attr(node: ElementTree.Element, name: str) -> str | None:
    return (
        node.attrib.get(f"{{{XMI_NS}}}{name}")
        or node.attrib.get(f"xmi:{name}")
        or node.attrib.get(f"xmi.{name}")
        or node.attrib.get(name)
    )


def _is_tag(node: ElementTree.Element, name: str) -> bool:
    return node.tag.endswith(name)


def _tagged_value(node: ElementTree.Element, tag: str) -> str | None:
    for child in node.iter():
        if _is_tag(child, "TaggedValue") and child.attrib.get("tag") == tag:
            return child.attrib.get("value")
    return None


def _direct_children(node: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in list(node) if _is_tag(child, name)]


def _feature_children(class_node: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    features = [child for child in class_node if _is_tag(child, "Classifier.feature")]
    if not features:
        return [child for child in class_node if _is_tag(child, name) or _is_tag(child, f"owned{name}")]
    return [child for feature in features for child in feature if _is_tag(child, name) or _is_tag(child, f"owned{name}")]


def _parse_diagram_geometry(geometry: str | None) -> UmlVisualModel | None:
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
    return UmlVisualModel(
        x=values["Left"],
        y=values["Top"],
        width=max(80, values["Right"] - values["Left"]),
        height=max(60, values["Bottom"] - values["Top"]),
    )


def _class_diagram_subjects(root: ElementTree.Element) -> tuple[str | None, set[str], dict[str, UmlVisualModel]]:
    for diagram in root.iter():
        if not _is_tag(diagram, "Diagram") or diagram.attrib.get("diagramType") != "ClassDiagram":
            continue
        subjects: set[str] = set()
        visuals: dict[str, UmlVisualModel] = {}
        for diagram_element in diagram.iter():
            if not _is_tag(diagram_element, "DiagramElement"):
                continue
            subject = diagram_element.attrib.get("subject")
            if not subject:
                continue
            subjects.add(subject)
            visual = _parse_diagram_geometry(diagram_element.attrib.get("geometry"))
            if visual is None:
                continue
            visuals[subject] = visual
        return diagram.attrib.get("name"), subjects, visuals
    return None, set(), {}


def _visuals_overlap_for_editor(classes: list[UmlClassModel]) -> bool:
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


def _normalize_visuals_for_editor(
    classes: list[UmlClassModel], relationships: list[UmlRelationshipModel]
) -> None:
    if not _visuals_overlap_for_editor(classes):
        return

    rows: list[list[UmlClassModel]] = []
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


def _owned_attribute_type(attribute: UmlAttributeModel) -> str:
    return attribute.data_type or "String"


def _owned_operation_return_type(method: UmlMethodModel) -> str:
    return method.return_type or "void"


def _tagged_values(parent: ElementTree.Element, values: dict[str, str]) -> ElementTree.Element:
    tagged_values = ElementTree.SubElement(parent, "UML:ModelElement.taggedValue")
    for tag, value in values.items():
        ElementTree.SubElement(tagged_values, "UML:TaggedValue", {"tag": tag, "value": value})
    return tagged_values


def export_xmi(diagram: UmlDiagramModel) -> str:
    package_id = _ea_id(diagram.id, f"package_{diagram.name}", "EAPK")
    model_id = f"MX_{package_id.replace('EAPK_', 'EAID_', 1)}"
    diagram_id = _ea_id(None, f"diagram_{diagram.name}")
    root = ElementTree.Element(
        "XMI",
        {
            "xmi.version": "1.1",
            "xmlns:UML": UML_NS,
            "timestamp": _timestamp(),
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
            "xmi.id": "EAID_11111111_5487_4080_A7F4_41526CB0AA00",
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
    _tagged_values(
        package,
        {
            "ea_package_id": "1",
            "created": _timestamp(),
            "modified": _timestamp(),
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
    class_visuals: dict[str, tuple[int, int, int, int]] = {}

    for index, uml_class in enumerate(diagram.classes, start=1):
        class_id = _ea_id(uml_class.id, uml_class.name)
        class_id_by_original[uml_class.id or uml_class.name] = class_id
        class_id_by_original[uml_class.name] = class_id
        x = int(uml_class.visual.x or (120 + index * 40))
        y = int(uml_class.visual.y or (90 + index * 40))
        width = int(uml_class.visual.width or 220)
        height = int(uml_class.visual.height or 130)
        class_visuals[class_id] = (x, y, x + width, y + height)
        class_node = ElementTree.SubElement(
            owned_elements,
            "UML:Class",
            {
                "xmi.id": class_id,
                "name": uml_class.name,
                "visibility": uml_class.visibility,
                "namespace": package_id,
                "isSpecification": "false",
                "isRoot": "false",
                "isLeaf": "false",
                "isAbstract": "false",
                "isActive": "false",
            },
        )
        _tagged_values(
            class_node,
            {
                "isSpecification": "false",
                "ea_stype": "Class",
                "ea_ntype": "0",
                "version": "1.0",
                "isActive": "false",
                "package": package_id,
                "date_created": _timestamp(),
                "date_modified": _timestamp(),
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
                "style": "BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;",
            },
        )
        features_node = ElementTree.SubElement(class_node, "UML:Classifier.feature")

        for attribute in uml_class.attributes:
            ElementTree.SubElement(
                features_node,
                "UML:Attribute",
                {
                    "xmi.id": _xml_id(attribute.id, f"{class_id}_{attribute.name}"),
                    "name": attribute.name,
                    "type": _owned_attribute_type(attribute),
                    "visibility": attribute.visibility,
                    "ownerScope": "instance",
                    "changeability": "changeable",
                },
            )
        for method in uml_class.methods:
            operation_node = ElementTree.SubElement(
                features_node,
                "UML:Operation",
                {
                    "xmi.id": _xml_id(method.id, f"{class_id}_{method.name}"),
                    "name": method.name,
                    "visibility": method.visibility,
                    "returnType": _owned_operation_return_type(method),
                    "ownerScope": "instance",
                    "isQuery": "false",
                },
            )
            parameters_node = ElementTree.SubElement(operation_node, "UML:BehavioralFeature.parameter")
            ElementTree.SubElement(
                parameters_node,
                "UML:Parameter",
                {
                    "xmi.id": _xml_id(None, f"{class_id}_{method.name}_return"),
                    "name": "return",
                    "kind": "return",
                    "type": _owned_operation_return_type(method),
                },
            )

    for relationship in diagram.relationships:
        source_id = class_id_by_original.get(relationship.source_class_id, _ea_id(relationship.source_class_id, "source"))
        target_id = class_id_by_original.get(relationship.target_class_id, _ea_id(relationship.target_class_id, "target"))
        relationship_id = _ea_id(relationship.id, f"{source_id}_{target_id}_{relationship.relationship_type}")
        relationship_name = relationship.label or relationship.relationship_type
        relationship_type = relationship.relationship_type.lower()

        if relationship_type in {"inheritance", "generalization"}:
            ElementTree.SubElement(
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
            continue

        if relationship_type in {"dependency", "realization", "implementation"}:
            tag = "UML:Abstraction" if relationship_type in {"realization", "implementation"} else "UML:Dependency"
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
            "direction": "Source -> Destination",
            "linemode": "3",
            "linecolor": "-1",
            "linewidth": "0",
            "seqno": "0",
            "headStyle": "0",
            "lineStyle": "0",
            "ea_sourceName": relationship.source_class_id,
            "ea_targetName": relationship.target_class_id,
            "ea_sourceType": "Class",
            "ea_targetType": "Class",
            "virtualInheritance": "0",
        }
        association_class_id = relationship.metadata_json.get("association_class_id")
        if association_class_id:
            association_class_export_id = class_id_by_original.get(str(association_class_id))
            if association_class_export_id:
                association_tagged_values["associationclass"] = association_class_export_id
        _tagged_values(association_node, association_tagged_values)
        connection_node = ElementTree.SubElement(association_node, "UML:Association.connection")
        source_end_attributes = {
            "name": "",
            "type": source_id,
            "visibility": "public",
            "aggregation": "none",
            "isOrdered": "false",
            "targetScope": "instance",
            "changeable": "none",
            "isNavigable": "false",
        }
        if relationship.source_cardinality:
            source_end_attributes["multiplicity"] = relationship.source_cardinality
        if relationship_type == "aggregation":
            source_end_attributes["aggregation"] = "shared"
        elif relationship_type == "composition":
            source_end_attributes["aggregation"] = "composite"

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

        source_end = ElementTree.SubElement(connection_node, "UML:AssociationEnd", source_end_attributes)
        _tagged_values(
            source_end,
            {
                "containment": "Unspecified",
                "sourcestyle": "Union=0;Derived=0;AllowDuplicates=0;Owned=0;Navigable=Non-Navigable;",
                "ea_end": "source",
            },
        )
        target_end = ElementTree.SubElement(connection_node, "UML:AssociationEnd", target_end_attributes)
        _tagged_values(
            target_end,
            {
                "containment": "Unspecified",
                "deststyle": "Union=0;Derived=0;AllowDuplicates=0;Owned=0;Navigable=Navigable;",
                "ea_end": "target",
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
    _tagged_values(
        diagram_node,
        {
            "version": "1.0",
            "author": "CASE Inteligente",
            "created_date": _timestamp(),
            "modified_date": _timestamp(),
            "package": package_id,
            "type": "Logical",
            "ea_localid": "1",
            "EAStyle": "ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;ConnectorNotation=UML 2.1;ShowOpRetType=1;",
            "styleex": "AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;",
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
                "style": f"DUID={_xml_id(None, f'duid_{sequence}')};",
            },
        )
    for relationship in diagram.relationships:
        source_id = class_id_by_original.get(relationship.source_class_id, _ea_id(relationship.source_class_id, "source"))
        target_id = class_id_by_original.get(relationship.target_class_id, _ea_id(relationship.target_class_id, "target"))
        relationship_id = _ea_id(relationship.id, f"{source_id}_{target_id}_{relationship.relationship_type}")
        ElementTree.SubElement(
            diagram_elements,
            "UML:DiagramElement",
            {
                "geometry": "SX=0;SY=0;EX=0;EY=0;EDGE=2;$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path=;",
                "subject": relationship_id,
                "style": "Mode=3;Color=-1;LWidth=0;Hidden=0;",
            },
        )

    ElementTree.SubElement(root, "XMI.difference")
    ElementTree.SubElement(root, "XMI.extensions", {"xmi.extender": "Enterprise Architect 2.5"})

    ElementTree.indent(root, space="\t")
    return '<?xml version="1.0" encoding="windows-1252"?>\n' + ElementTree.tostring(root, encoding="unicode")


def import_xmi(content: str, name: str = "Diagrama importado") -> UmlDiagramModel:
    root = ElementTree.fromstring(content)
    classes: list[UmlClassModel] = []
    relationships: list[UmlRelationshipModel] = []
    id_to_class_name: dict[str, str] = {}
    diagram_name, diagram_subjects, visual_by_subject = _class_diagram_subjects(root)
    has_class_diagram_filter = len(diagram_subjects) > 0

    for node in root.iter():
        node_type = _xmi_attr(node, "type")
        is_class_node = (node.tag.endswith("packagedElement") and node_type == "uml:Class") or _is_tag(node, "Class")
        if is_class_node:
            if node.attrib.get("name") == "EARootClass":
                continue
            class_id = _xmi_attr(node, "id")
            if has_class_diagram_filter and class_id not in diagram_subjects:
                continue
            attributes = []
            for order_index, child in enumerate(_feature_children(node, "Attribute")):
                attributes.append(
                    UmlAttributeModel(
                        id=_xmi_attr(child, "id"),
                        name=child.attrib.get("name", "atributo"),
                        data_type=child.attrib.get("type") or _tagged_value(child, "type") or "String",
                        visibility=child.attrib.get("visibility", "private"),
                        multiplicity=child.attrib.get("multiplicity"),
                        order_index=int(_tagged_value(child, "position") or order_index),
                    )
                )
            methods = []
            for order_index, child in enumerate(_feature_children(node, "Operation")):
                methods.append(
                    UmlMethodModel(
                        id=_xmi_attr(child, "id"),
                        name=child.attrib.get("name", "operacion"),
                        return_type=child.attrib.get("returnType")
                        or _tagged_value(child, "type")
                        or next(
                            (
                                parameter.attrib.get("type") or _tagged_value(parameter, "type")
                                for parameter in child.iter()
                                if _is_tag(parameter, "Parameter") and parameter.attrib.get("kind") == "return"
                            ),
                            None,
                        ),
                        visibility=child.attrib.get("visibility", "public"),
                        order_index=int(_tagged_value(child, "position") or order_index),
                    )
                )
            class_name = node.attrib.get("name", "ClaseImportada")
            if class_id:
                id_to_class_name[class_id] = class_name
            classes.append(
                UmlClassModel(
                    id=class_id,
                    name=class_name,
                    visibility=node.attrib.get("visibility", "public"),
                    attributes=attributes,
                    methods=methods,
                    visual=visual_by_subject.get(class_id or "", UmlVisualModel()),
                    metadata_json={"external_xmi_id": class_id} if class_id else {},
                )
            )

    for node in root.iter():
        node_type = _xmi_attr(node, "type")
        if _is_tag(node, "generalization") or _is_tag(node, "Generalization"):
            source_id = node.attrib.get("source") or node.attrib.get("subtype", "")
            target_id = node.attrib.get("target") or node.attrib.get("general") or node.attrib.get("supertype", "")
            relationships.append(
                UmlRelationshipModel(
                    id=_xmi_attr(node, "id"),
                    source_class_id=id_to_class_name.get(source_id, source_id),
                    target_class_id=id_to_class_name.get(target_id, target_id),
                    relationship_type="inheritance",
                    label=node.attrib.get("name"),
                )
            )
        elif _is_tag(node, "Association") or (node.tag.endswith("packagedElement") and node_type == "uml:Association"):
            relationship_id = _xmi_attr(node, "id")
            if has_class_diagram_filter and relationship_id not in diagram_subjects:
                continue
            source_id = node.attrib.get("source", "")
            target_id = node.attrib.get("target", "")
            if not (source_id and target_id):
                ends = [child.attrib.get("type", "") for child in node.iter() if _is_tag(child, "AssociationEnd") or _is_tag(child, "ownedEnd")]
                if len(ends) >= 2:
                    source_id, target_id = ends[0], ends[1]
            if source_id not in id_to_class_name or target_id not in id_to_class_name:
                continue
            source_end = next((child for child in node.iter() if _is_tag(child, "AssociationEnd") or _is_tag(child, "ownedEnd")), None)
            all_ends = [child for child in node.iter() if _is_tag(child, "AssociationEnd") or _is_tag(child, "ownedEnd")]
            target_end = all_ends[1] if len(all_ends) > 1 else None
            association_class_id = _tagged_value(node, "associationclass")
            metadata = {"external_xmi_id": relationship_id}
            if association_class_id and association_class_id in id_to_class_name:
                metadata["association_class_id"] = association_class_id
            relationships.append(
                UmlRelationshipModel(
                    id=relationship_id,
                    source_class_id=id_to_class_name.get(source_id, source_id),
                    target_class_id=id_to_class_name.get(target_id, target_id),
                    relationship_type="association",
                    label=node.attrib.get("name"),
                    source_cardinality=source_end.attrib.get("multiplicity") if source_end is not None else None,
                    target_cardinality=target_end.attrib.get("multiplicity") if target_end is not None else None,
                    metadata_json=metadata,
                )
            )
        elif _is_tag(node, "Dependency") or _is_tag(node, "Abstraction") or (node.tag.endswith("packagedElement") and node_type and node_type != "uml:Class"):
            source_id = node.attrib.get("source") or node.attrib.get("client", "")
            target_id = node.attrib.get("target") or node.attrib.get("supplier", "")
            if node_type == "uml:Association" and not (source_id and target_id):
                ends = [child.attrib.get("type", "") for child in node if child.tag.endswith("ownedEnd")]
                if len(ends) >= 2:
                    source_id, target_id = ends[0], ends[1]
            relationship_type = node_type.replace("uml:", "").lower()
            if relationship_type == "generalization":
                relationship_type = "inheritance"
            relationships.append(
                UmlRelationshipModel(
                    id=_xmi_attr(node, "id"),
                    source_class_id=id_to_class_name.get(source_id, source_id),
                    target_class_id=id_to_class_name.get(target_id, target_id),
                    relationship_type=relationship_type,
                    label=node.attrib.get("name"),
                )
            )
    _normalize_visuals_for_editor(classes, relationships)
    return UmlDiagramModel(name=diagram_name or name, classes=classes, relationships=relationships)
