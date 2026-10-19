import type { ReactNode } from "react";
import { CheckCircle2, Download, Upload } from "lucide-react";

import { Button } from "../../../shared/components/Button";

type UmlToolbarProps = {
  onAddClass: () => void;
  onValidate: () => void;
  onExport: () => void;
  onImport: () => void;
  rightContent?: ReactNode;
};

export function UmlToolbar({ onAddClass, onValidate, onExport, onImport, rightContent }: UmlToolbarProps) {
  void onAddClass;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-950">
      <div className="flex flex-wrap items-center gap-2">
        <Button className="h-9 px-3" icon={<CheckCircle2 size={16} aria-hidden="true" />} onClick={onValidate} variant="secondary">
          Validar
        </Button>
        <Button className="h-9 px-3" icon={<Upload size={16} aria-hidden="true" />} onClick={onImport} variant="secondary">
          Importar XML
        </Button>
        <Button className="h-9 px-3" icon={<Download size={16} aria-hidden="true" />} onClick={onExport} variant="secondary">
          Exportar XML
        </Button>
      </div>
      {rightContent}
    </div>
  );
}
