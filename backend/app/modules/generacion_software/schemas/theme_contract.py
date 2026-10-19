from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

HEX_PATTERN = r"^#[0-9A-Fa-f]{6}$"
SUPPORTED_FONTS = {"system": "system"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ThemePalette(StrictModel):
    primary: str = Field(pattern=HEX_PATTERN)
    on_primary: str = Field(pattern=HEX_PATTERN)
    secondary: str = Field(pattern=HEX_PATTERN)
    on_secondary: str = Field(pattern=HEX_PATTERN)
    background: str = Field(pattern=HEX_PATTERN)
    on_background: str = Field(pattern=HEX_PATTERN)
    surface: str = Field(pattern=HEX_PATTERN)
    on_surface: str = Field(pattern=HEX_PATTERN)
    error: str = Field(pattern=HEX_PATTERN)
    on_error: str = Field(pattern=HEX_PATTERN)
    outline: str = Field(pattern=HEX_PATTERN)

    @field_validator("*", mode="after")
    @classmethod
    def uppercase_hex(cls, value: str) -> str:
        return value.upper()


class ThemeTypography(StrictModel):
    font_family: Literal["system"] = "system"
    heading_font_family: Literal["system"] = "system"
    scale: Literal["compact", "normal", "large"] = "normal"
    weight: Literal["regular", "medium"] = "regular"


class ThemeShape(StrictModel):
    button_radius: int = Field(default=8, ge=0, le=24)
    input_radius: int = Field(default=8, ge=0, le=24)
    card_radius: int = Field(default=8, ge=0, le=24)
    dialog_radius: int = Field(default=8, ge=0, le=24)


class ThemeComponents(StrictModel):
    button_style: Literal["filled", "outline", "tonal"] = "filled"
    input_style: Literal["outline", "filled"] = "outline"
    card_style: Literal["flat", "outlined", "elevated"] = "outlined"
    navigation_style: Literal["bottom_bar", "navigation_drawer", "automatic"] = "automatic"
    density: Literal["compact", "normal", "comfortable"] = "normal"
    show_field_labels: bool = True


class FlutterThemeConfigV2(StrictModel):
    schema_version: Literal[2] = 2
    mode: Literal["light", "dark", "system"] = "system"
    light: ThemePalette
    dark: ThemePalette
    typography: ThemeTypography = Field(default_factory=ThemeTypography)
    shape: ThemeShape = Field(default_factory=ThemeShape)
    components: ThemeComponents = Field(default_factory=ThemeComponents)


class ThemeDiagnostic(StrictModel):
    code: str
    severity: Literal["warning", "error"]
    path: str
    message: str
    suggestion: str | None = None
    actual: float | None = None
    required: float | None = None


DEFAULT_THEME_V2 = FlutterThemeConfigV2(
    light=ThemePalette(
        primary="#0F766E", on_primary="#FFFFFF", secondary="#2563EB",
        on_secondary="#FFFFFF", background="#F8FAFC", on_background="#0F172A",
        surface="#FFFFFF", on_surface="#0F172A", error="#B91C1C",
        on_error="#FFFFFF", outline="#64748B",
    ),
    dark=ThemePalette(
        primary="#5EEAD4", on_primary="#042F2E", secondary="#93C5FD",
        on_secondary="#172554", background="#020617", on_background="#E2E8F0",
        surface="#0F172A", on_surface="#E2E8F0", error="#FCA5A5",
        on_error="#450A0A", outline="#94A3B8",
    ),
)


def _hex(value: Any, fallback: str, path: str, normalized: list[str]) -> str:
    text = str(value or "").strip().upper()
    if len(text) == 7 and text.startswith("#"):
        try:
            int(text[1:], 16)
            if text != value:
                normalized.append(path)
            return text
        except ValueError:
            pass
    normalized.append(path)
    return fallback


def adapt_theme_v1_to_v2(raw: dict[str, Any]) -> dict[str, Any]:
    defaults = DEFAULT_THEME_V2.model_dump(mode="json")
    light = defaults["light"]
    light["primary"] = str(raw.get("primary_color") or light["primary"])
    light["secondary"] = str(raw.get("secondary_color") or light["secondary"])
    light["background"] = str(raw.get("background_color") or light["background"])
    light["surface"] = str(raw.get("surface_color") or light["surface"])
    for token in ("primary", "secondary", "background", "surface"):
        color = str(light[token]).upper()
        if len(color) == 7 and color.startswith("#"):
            light[f"on_{token}"] = _best_on_color(color)
    radius = raw.get("border_radius", 8)
    return {
        **defaults,
        "typography": {
            **defaults["typography"],
            # Legacy family names cannot be promoted to v2 unless their files and
            # licenses are bundled in both the preview and generated application.
            "font_family": "system",
            "heading_font_family": "system",
        },
        "shape": {key: radius for key in defaults["shape"]},
        "components": {
            **defaults["components"],
            "button_style": raw.get("button_style", "filled"),
            "density": raw.get("density", "normal"),
        },
    }


def _best_on_color(background: str) -> str:
    return "#000000" if contrast_ratio(background, "#000000") >= contrast_ratio(background, "#FFFFFF") else "#FFFFFF"


def _channel(value: int) -> float:
    ratio = value / 255
    return ratio / 12.92 if ratio <= 0.04045 else ((ratio + 0.055) / 1.055) ** 2.4


def contrast_ratio(first: str, second: str) -> float:
    def luminance(color: str) -> float:
        values = [int(color[index:index + 2], 16) for index in (1, 3, 5)]
        red, green, blue = (_channel(item) for item in values)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue
    one, two = luminance(first), luminance(second)
    return round((max(one, two) + 0.05) / (min(one, two) + 0.05), 2)


def validate_theme_contrast(theme: FlutterThemeConfigV2) -> list[ThemeDiagnostic]:
    diagnostics: list[ThemeDiagnostic] = []
    pairs = (("primary", "on_primary"), ("secondary", "on_secondary"),
             ("background", "on_background"), ("surface", "on_surface"),
             ("error", "on_error"))
    for mode in ("light", "dark"):
        palette = getattr(theme, mode)
        for background, foreground in pairs:
            ratio = contrast_ratio(getattr(palette, background), getattr(palette, foreground))
            if ratio < 4.5:
                diagnostics.append(ThemeDiagnostic(
                    code="theme_contrast_insufficient", severity="error",
                    path=f"{mode}.{background}/{foreground}", actual=ratio, required=4.5,
                    message=f"El contraste {ratio}:1 no alcanza 4.5:1.",
                    suggestion="Aclare u oscurezca el color de texto hasta alcanzar 4.5:1.",
                ))
        outline_ratio = contrast_ratio(palette.outline, palette.surface)
        if outline_ratio < 3:
            diagnostics.append(ThemeDiagnostic(
                code="theme_outline_contrast_insufficient", severity="error",
                path=f"{mode}.outline/surface", actual=outline_ratio, required=3,
                message=f"El borde tiene contraste {outline_ratio}:1; requiere 3:1.",
                suggestion="Use un color de borde con mayor contraste respecto a la superficie.",
            ))
    return diagnostics


def normalize_theme(raw: dict[str, Any] | None) -> tuple[FlutterThemeConfigV2, list[ThemeDiagnostic], list[str]]:
    normalized_fields: list[str] = []
    source = dict(raw or {})
    if source.get("schema_version", 1) == 1:
        source = adapt_theme_v1_to_v2(source)
        normalized_fields.append("schema_version")
    defaults = DEFAULT_THEME_V2.model_dump(mode="json")
    for mode in ("light", "dark"):
        palette = source.setdefault(mode, {})
        for key, fallback in defaults[mode].items():
            palette[key] = _hex(palette.get(key), fallback, f"{mode}.{key}", normalized_fields)
    theme = FlutterThemeConfigV2.model_validate(source)
    return theme, validate_theme_contrast(theme), sorted(set(normalized_fields))


SYSTEM_THEME_PRESETS: tuple[dict[str, Any], ...] = (
    {"id": "professional-light", "name": "Profesional claro", "description": "Tema sobrio y accesible.", "config": DEFAULT_THEME_V2.model_dump(mode="json")},
    {"id": "professional-dark", "name": "Profesional oscuro", "description": "Tema oscuro de alto contraste.", "config": DEFAULT_THEME_V2.model_copy(update={"mode": "dark"}).model_dump(mode="json")},
    {"id": "academic", "name": "Academico", "description": "Azul institucional con densidad comoda.", "config": DEFAULT_THEME_V2.model_copy(update={"components": ThemeComponents(density="comfortable", button_style="outline")}).model_dump(mode="json")},
)
