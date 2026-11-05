import 'common.dart';

class ResumenDiagrama {
  final String id;
  final String projectId;
  final String name;
  final String type;
  final int classCount;
  final int relationshipCount;
  final DateTime updatedAt;

  const ResumenDiagrama({
    required this.id,
    required this.projectId,
    required this.name,
    required this.type,
    required this.classCount,
    required this.relationshipCount,
    required this.updatedAt,
  });

  factory ResumenDiagrama.fromJson(Json json) => ResumenDiagrama(
    id: json['id'].toString(),
    projectId: json['project_id'].toString(),
    name: json['name']?.toString() ?? 'Diagrama',
    type: json['diagram_type']?.toString() ?? 'class',
    classCount: json['class_count'] as int? ?? 0,
    relationshipCount: json['relationship_count'] as int? ?? 0,
    updatedAt: parseDate(json['updated_at']),
  );
}

class AtributoUML {
  final String name;
  final String dataType;
  final String visibility;
  final String? multiplicity;

  const AtributoUML(
    this.name,
    this.dataType,
    this.visibility,
    this.multiplicity,
  );

  factory AtributoUML.fromJson(Json json) => AtributoUML(
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

class MetodoUML {
  final String name;
  final String? returnType;
  final String visibility;
  final List<ParametroUML> parameters;

  const MetodoUML(
    this.name,
    this.returnType,
    this.visibility, [
    this.parameters = const [],
  ]);

  factory MetodoUML.fromJson(Json json) => MetodoUML(
    json['name'].toString(),
    json['return_type']?.toString(),
    json['visibility']?.toString() ?? 'public',
    jsonList(json['parameters']).map(ParametroUML.fromJson).toList(),
  );

  Json toJson() => {
    'name': name,
    'return_type': returnType,
    'visibility': visibility,
    'parameters': parameters.map((item) => item.toJson()).toList(),
  };

  String get firma =>
      '$name(${parameters.map((item) => '${item.name}: ${item.dataType}').join(', ')}): ${returnType ?? 'void'}';
}

class ParametroUML {
  final String name;
  final String dataType;
  const ParametroUML(this.name, this.dataType);

  factory ParametroUML.fromJson(Json json) =>
      ParametroUML(json['name'].toString(), json['data_type'].toString());

  Json toJson() => {'name': name, 'data_type': dataType};
}

class NodoClaseUML {
  final String id;
  final String name;
  final String? stereotype;
  final String elementType;
  final double x;
  final double y;
  final double width;
  final double height;
  final List<AtributoUML> attributes;
  final List<MetodoUML> methods;

  const NodoClaseUML({
    required this.id,
    required this.name,
    this.stereotype,
    this.elementType = 'class',
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    required this.attributes,
    required this.methods,
  });

  factory NodoClaseUML.fromJson(Json json) {
    final visual = json['visual'] as Json?;
    final attributes = jsonList(
      json['attributes'],
    ).map(AtributoUML.fromJson).toList();
    final methods = jsonList(json['methods']).map(MetodoUML.fromJson).toList();
    final estimatedHeight = 66.0 + (attributes.length + methods.length) * 18.0;
    return NodoClaseUML(
      id: json['id'].toString(),
      name: json['name']?.toString() ?? 'Clase',
      stereotype: json['stereotype']?.toString(),
      elementType: json['element_type']?.toString() ?? 'class',
      x:
          (visual?['position_x'] as num? ?? visual?['x'] as num?)?.toDouble() ??
          20,
      y:
          (visual?['position_y'] as num? ?? visual?['y'] as num?)?.toDouble() ??
          20,
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
    'element_type': elementType,
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

class RelacionUML {
  final String id;
  final String sourceId;
  final String targetId;
  final String type;
  final String? sourceCardinality;
  final String? targetCardinality;
  final String? label;

  const RelacionUML({
    required this.id,
    required this.sourceId,
    required this.targetId,
    required this.type,
    this.sourceCardinality,
    this.targetCardinality,
    this.label,
  });

  factory RelacionUML.fromJson(Json json) => RelacionUML(
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

class DetalleDiagrama {
  final String id;
  final String name;
  final int logicalVersion;
  final bool canEdit;
  final List<NodoClaseUML> classes;
  final List<RelacionUML> relationships;

  const DetalleDiagrama({
    required this.id,
    required this.name,
    required this.logicalVersion,
    required this.canEdit,
    required this.classes,
    required this.relationships,
  });

  factory DetalleDiagrama.fromJson(Json json) {
    final diagram = json['diagram'] as Json;
    return DetalleDiagrama(
      id: diagram['id'].toString(),
      name: diagram['name']?.toString() ?? 'Diagrama',
      logicalVersion: json['logical_version'] as int? ?? 0,
      canEdit: json['can_edit'] == true,
      classes: jsonList(json['classes']).map(NodoClaseUML.fromJson).toList(),
      relationships: jsonList(
        json['relationships'],
      ).map(RelacionUML.fromJson).toList(),
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
