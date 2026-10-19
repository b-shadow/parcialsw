typedef Json = Map<String, dynamic>;

DateTime parseDate(Object? value) =>
    DateTime.tryParse(value?.toString() ?? '')?.toLocal() ??
    DateTime.fromMillisecondsSinceEpoch(0);

List<Json> jsonList(Object? value) =>
    (value as List? ?? const <Object>[]).whereType<Json>().toList();
