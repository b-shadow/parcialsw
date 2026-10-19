import re

JAVA_RESERVED = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new", "package",
    "private", "protected", "public", "return", "short", "static", "strictfp",
    "super", "switch", "synchronized", "this", "throw", "throws", "transient",
    "try", "void", "volatile", "while",
}
DART_RESERVED = {
    "abstract", "as", "assert", "async", "await", "break", "case", "catch",
    "class", "const", "continue", "covariant", "default", "deferred", "do",
    "dynamic", "else", "enum", "export", "extends", "extension", "external",
    "factory", "false", "final", "finally", "for", "function", "get", "hide",
    "if", "implements", "import", "in", "interface", "is", "late", "library",
    "mixin", "new", "null", "on", "operator", "part", "required", "rethrow",
    "return", "set", "show", "static", "super", "switch", "sync", "this",
    "throw", "true", "try", "typedef", "var", "void", "while", "with", "yield",
}


def words(value: str) -> list[str]:
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return [item for item in re.split(r"[^A-Za-z0-9]+", expanded) if item]


def pascal(value: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in words(value))


def camel(value: str) -> str:
    result = pascal(value)
    return result[:1].lower() + result[1:]


def snake(value: str) -> str:
    return "_".join(item.casefold() for item in words(value))


def kebab(value: str) -> str:
    return "-".join(item.casefold() for item in words(value))


def safe_route(path: str) -> str:
    value = "/" + path.strip().strip("/")
    return value if value != "/" else "/"


def is_reserved(name: str) -> bool:
    normalized = name.casefold()
    return normalized in JAVA_RESERVED or normalized in DART_RESERVED
