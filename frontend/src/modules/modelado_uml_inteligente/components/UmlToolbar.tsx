import { CheckCircle2, Download, Image, Upload } from "lucide-react";

import { Button } from "../../../shared/components/Button";

type UmlToolbarProps = {
  onAddClass: () => void;
  onValidate: () => void;
  onExport: () => void;
  onImport: () => void;
  onImage: () => void;
};

export function UmlToolbar({ onAddClass, onValidate, onExport, onImport, onImage }: UmlToolbarProps) {
  void onAddClass;

  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-950">
      <Button icon={<CheckCircle2 size={18} aria-hidden="true" />} onClick={onValidate} variant="secondary">
        Validar
      </Button>
      <Button icon={<Upload size={18} aria-hidden="true" />} onClick={onImport} variant="secondary">
        Importar XML
      </Button>
      <Button icon={<Download size={18} aria-hidden="true" />} onClick={onExport} variant="secondary">
        Exportar XML
      </Button>
      <Button icon={<Image size={18} aria-hidden="true" />} onClick={onImage} variant="ghost">
        Imagen a UML
      </Button>
    </div>
  );
}
