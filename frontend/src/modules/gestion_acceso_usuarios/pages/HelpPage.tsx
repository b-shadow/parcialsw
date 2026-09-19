import { BookOpen, CheckCircle2 } from "lucide-react";

import { Panel } from "../../../shared/components/Panel";

const steps = [
  "Crear o seleccionar un proyecto.",
  "Abrir el entorno UML del proyecto.",
  "Crear clases, atributos, metodos y relaciones.",
  "Validar el diagrama antes de transformarlo.",
  "Generar backend Spring Boot y frontend Flutter desde el modelo."
];

export function HelpPage() {
  return (
    <section className="grid gap-5">
      <div className="flex items-center gap-3">
        <BookOpen className="text-accent" aria-hidden="true" />
        <h1 className="text-2xl font-semibold">Manual guiado</h1>
      </div>
      <Panel className="p-5">
        <div className="grid gap-4">
          {steps.map((step) => (
            <div className="flex items-start gap-3" key={step}>
              <CheckCircle2 className="mt-0.5 text-accent" size={18} aria-hidden="true" />
              <p className="text-sm text-slate-700">{step}</p>
            </div>
          ))}
        </div>
      </Panel>
    </section>
  );
}
