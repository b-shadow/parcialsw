import type { UmlElementType } from "../types/uml";

export interface ElementTypeSelectProps {
  value: UmlElementType | string;
  disabled?: boolean;
  onChange: (value: UmlElementType) => void;
}

const ELEMENT_TYPE_OPTIONS: Array<{ value: UmlElementType; label: string }> = [
  { value: "class", label: "Clase" },
  { value: "interface", label: "Interfaz" },
  { value: "enum", label: "Enum" },
  { value: "abstract_class", label: "Clase abstracta" },
];

export function ElementTypeSelect({ value, disabled = false, onChange }: ElementTypeSelectProps) {
  const normalizedValue = (value as UmlElementType) || "class";

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="uml-element-type-select" className="text-xs font-semibold text-slate-600 dark:text-slate-300">
        Tipo de elemento:
      </label>
      <select
        id="uml-element-type-select"
        aria-label="Tipo de elemento"
        className="h-8 rounded-md border border-slate-300 bg-white px-2 text-xs font-medium text-slate-800 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
        disabled={disabled}
        value={normalizedValue}
        onChange={(e) => onChange(e.target.value as UmlElementType)}
      >
        {ELEMENT_TYPE_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
