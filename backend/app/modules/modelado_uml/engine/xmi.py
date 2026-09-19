from xml.etree import ElementTree

from app.modules.modelado_uml.engine.internal_model import (
    UmlAttributeModel,
    UmlClassModel,
    UmlDiagramModel,
    UmlMethodModel,
    UmlRelationshipModel,
)


def export_xmi(diagram: UmlDiagramModel) -> str:
    root = ElementTree.Element(
        "xmi:XMI",
        {
            "xmlns:xmi": "http://www.omg.org/XMI",
            "xmlns:uml": "http://www.eclipse.org/uml2/5.0.0/UML",
            "version": "2.1",
        },
    )
    model = ElementTree.SubElement(root, "uml:Model", {"name": diagram.name, "type": diagram.diagram_type})
    for uml_class in diagram.classes:
        class_node = ElementTree.SubElement(
            model,
            "packagedElement",
            {
                "xmi:type": "uml:Class",
                "xmi:id": uml_class.id or uml_class.name,
                "name": uml_class.name,
                "visibility": uml_class.visibility,
            },
        )
        for attribute in uml_class.attributes:
            ElementTree.SubElement(
                class_node,
                "ownedAttribute",
                {
                    "xmi:id": attribute.id or f"{uml_class.name}_{attribute.name}",
                    "name": attribute.name,
                    "type": attribute.data_type,
                    "visibility": attribute.visibility,
                },
            )
        for method in uml_class.methods:
            ElementTree.SubElement(
                class_node,
                "ownedOperation",
                {
                    "xmi:id": method.id or f"{uml_class.name}_{method.name}",
                    "name": method.name,
                    "returnType": method.return_type or "void",
                    "visibility": method.visibility,
                },
            )
    for relationship in diagram.relationships:
        ElementTree.SubElement(
            model,
            "packagedElement",
            {
                "xmi:type": f"uml:{relationship.relationship_type}",
                "xmi:id": relationship.id or f"{relationship.source_class_id}_{relationship.target_class_id}",
                "source": relationship.source_class_id,
                "target": relationship.target_class_id,
                "name": relationship.label or relationship.relationship_type,
            },
        )
    return ElementTree.tostring(root, encoding="unicode")


def import_xmi(content: str, name: str = "Diagrama importado") -> UmlDiagramModel:
    root = ElementTree.fromstring(content)
    classes: list[UmlClassModel] = []
    relationships: list[UmlRelationshipModel] = []
    for node in root.iter():
        node_type = node.attrib.get("{http://www.omg.org/XMI}type") or node.attrib.get("xmi:type")
        if node.tag.endswith("packagedElement") and node_type == "uml:Class":
            attributes = [
                UmlAttributeModel(
                    name=child.attrib.get("name", "atributo"),
                    data_type=child.attrib.get("type", "String"),
                    visibility=child.attrib.get("visibility", "private"),
                )
                for child in node
                if child.tag.endswith("ownedAttribute")
            ]
            methods = [
                UmlMethodModel(
                    name=child.attrib.get("name", "operacion"),
                    return_type=child.attrib.get("returnType"),
                    visibility=child.attrib.get("visibility", "public"),
                )
                for child in node
                if child.tag.endswith("ownedOperation")
            ]
            classes.append(
                UmlClassModel(
                    id=node.attrib.get("{http://www.omg.org/XMI}id") or node.attrib.get("xmi:id"),
                    name=node.attrib.get("name", "ClaseImportada"),
                    visibility=node.attrib.get("visibility", "public"),
                    attributes=attributes,
                    methods=methods,
                )
            )
        elif node.tag.endswith("packagedElement") and node_type and node_type != "uml:Class":
            relationships.append(
                UmlRelationshipModel(
                    id=node.attrib.get("{http://www.omg.org/XMI}id") or node.attrib.get("xmi:id"),
                    source_class_id=node.attrib.get("source", ""),
                    target_class_id=node.attrib.get("target", ""),
                    relationship_type=node_type.replace("uml:", "").lower(),
                    label=node.attrib.get("name"),
                )
            )
    return UmlDiagramModel(name=name, classes=classes, relationships=relationships)
