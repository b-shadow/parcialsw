import 'common.dart';

class DiagramSummary {
  final String id;
  final String projectId;
  final String name;
  final String type;
  final int classCount;
  final int relationshipCount;
  final DateTime updatedAt;

  const DiagramSummary({
    required this.id,
    required this.projectId,
    required this.name,
    required this.type,
    required this.classCount,
    required this.relationshipCount,
    required this.updatedAt,
  });

  factory DiagramSummary.fromJson(Json json) => DiagramSummary(
    id: json['id'].toString(),
    projectId: json['project_id'].toString(),
    name: json['name']?.toString() ?? 'Diagrama',
    type: json['diagram_type']?.toString() ?? 'class',
    classCount: json['class_count'] as int? ?? 0,
    relationshipCount: json['relationship_count'] as int? ?? 0,
    updatedAt: parseDate(json['updated_at']),
  );
}

class UmlAttribute {
  final String name;
  final String dataType;
  final String visibility;
  final String? multiplicity;

  const UmlAttribute(
    this.name,
    this.dataType,
    this.visibility,
    this.multiplicity,
  );

  factory UmlAttribute.fromJson(Json json) => UmlAttribute(
    json['name'].toString(),
    json['data_type'].toString(),
    json['visibility']?.toString() ?? 'private',
    json['multiplicity']?.toString(),
  );

  Json toJson() => {
    'name': name,
    'data_type': dataType,
    'visibility': visibility,
    'multiplicity': multiplicity,
  };
}

class UmlMethod {
  final String name;
  final String? returnType;
  final String visibility;

  const UmlMethod(this.name, this.returnType, this.visibility);

  factory UmlMethod.fromJson(Json json) => UmlMethod(
    json['name'].toString(),
    json['return_type']?.toString(),
    json['visibility']?.toString() ?? 'public',
  );

  Json toJson() => {
    'name': name,
    'return_type': returnType,
    'visibility': visibility,
  };
}

class UmlClassNode {
  final String id;
  final String name;
  final String? stereotype;
  final double x;
  final double y;
  final double width;
  final double height;
  final List<UmlAttribute> attributes;
  final List<UmlMethod> methods;

  const UmlClassNode({
    required this.id,
    required this.name,
    this.stereotype,
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    required this.attributes,
    required this.methods,
  });

  factory UmlClassNode.fromJson(Json json) {
    final visual = json['visual'] as Json?;
    final attributes = jsonList(
      json['attributes'],
    ).map(UmlAttribute.fromJson).toList();
    final methods = jsonList(json['methods']).map(UmlMethod.fromJson).toList();
    final estimatedHeight = 68.0 + (attributes.length + methods.length) * 22.0;
    return UmlClassNode(
      id: json['id'].toString(),
      name: json['name']?.toString() ?? 'Clase',
      stereotype: json['stereotype']?.toString(),
      x: (visual?['position_x'] as num?)?.toDouble() ?? 20,
      y: (visual?['position_y'] as num?)?.toDouble() ?? 20,
      width: (visual?['width'] as num?)?.toDouble() ?? 230,
      height:
          (visual?['height'] as num?)?.toDouble() ??
          estimatedHeight.clamp(120, 320).toDouble(),
      attributes: attributes,
      methods: methods,
    );
  }

  Json toJson() => {
    'id': id,
    'name': name,
    'stereotype': stereotype,
    'attributes': attributes.map((item) => item.toJson()).toList(),
    'methods': methods.map((item) => item.toJson()).toList(),
    'visual': {
      'position_x': x,
      'position_y': y,
      'width': width,
      'height': height,
    },
  };
}

class UmlRelationship {
  final String id;
  final String sourceId;
  final String targetId;
  final String type;
  final String? sourceCardinality;
  final String? targetCardinality;
  final String? label;

  const UmlRelationship({
    required this.id,
    required this.sourceId,
    required this.targetId,
    required this.type,
    this.sourceCardinality,
    this.targetCardinality,
    this.label,
  });

  factory UmlRelationship.fromJson(Json json) => UmlRelationship(
    id: json['id'].toString(),
    sourceId: json['source_class_id'].toString(),
    targetId: json['target_class_id'].toString(),
    type: json['relationship_type']?.toString() ?? 'association',
    sourceCardinality: json['source_cardinality']?.toString(),
    targetCardinality: json['target_cardinality']?.toString(),
    label: json['label']?.toString(),
  );

  Json toJson() => {
    'id': id,
    'source_class_id': sourceId,
    'target_class_id': targetId,
    'relationship_type': type,
    'source_cardinality': sourceCardinality,
    'target_cardinality': targetCardinality,
    'label': label,
  };
}

class DiagramDetail {
  final String id;
  final String name;
  final int logicalVersion;
  final bool canEdit;
  final List<UmlClassNode> classes;
  final List<UmlRelationship> relationships;

  const DiagramDetail({
    required this.id,
    required this.name,
    required this.logicalVersion,
    required this.canEdit,
    required this.classes,
    required this.relationships,
  });

  factory DiagramDetail.fromJson(Json json) {
    final diagram = json['diagram'] as Json;
    return DiagramDetail(
      id: diagram['id'].toString(),
      name: diagram['name']?.toString() ?? 'Diagrama',
      logicalVersion: json['logical_version'] as int? ?? 0,
      canEdit: json['can_edit'] == true,
      classes: jsonList(json['classes']).map(UmlClassNode.fromJson).toList(),
      relationships: jsonList(
        json['relationships'],
      ).map(UmlRelationship.fromJson).toList(),
    );
  }

  Json toJson() => {
    'diagram': {'id': id, 'name': name},
    'logical_version': logicalVersion,
    'can_edit': false,
    'classes': classes.map((item) => item.toJson()).toList(),
    'relationships': relationships.map((item) => item.toJson()).toList(),
  };
}
