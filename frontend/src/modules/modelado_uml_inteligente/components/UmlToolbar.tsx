import { CheckCircle2, Download, Image, Plus, Upload } from "lucide-react";

import { Button } from "../../../shared/components/Button";

type UmlToolbarProps = {
  onAddClass: () => void;
  onValidate: () => void;
  onExport: () => void;
};

export function UmlToolbar({ onAddClass, onValidate, onExport }: UmlToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 bg-white p-3">
      <Button icon={<Plus size={18} aria-hidden="true" />} onClick={onAddClass}>
        Clase
      </Button>
      <Button icon={<CheckCircle2 size={18} aria-hidden="true" />} onClick={onValidate} variant="secondary">
        Validar
      </Button>
      <Button icon={<Upload size={18} aria-hidden="true" />} variant="secondary">
        Importar XMI
      </Button>
      <Button icon={<Download size={18} aria-hidden="true" />} onClick={onExport} variant="secondary">
        Exportar XMI
      </Button>
      <Button icon={<Image size={18} aria-hidden="true" />} variant="ghost">
        Imagen a UML
      </Button>
    </div>
  );
}
