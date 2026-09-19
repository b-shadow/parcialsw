import { Activity, BarChart3, FolderKanban, Users } from "lucide-react";

import { Panel } from "../../../shared/components/Panel";

const metrics = [
  { label: "Proyectos activos", value: "12", icon: FolderKanban },
  { label: "Diagramas UML", value: "34", icon: BarChart3 },
  { label: "Colaboradores", value: "18", icon: Users },
  { label: "Eventos auditados", value: "126", icon: Activity }
];

export function ReportsPage() {
  return (
    <section className="grid gap-5">
      <h1 className="text-2xl font-semibold">Reportes</h1>
      <div className="grid gap-4 md:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Panel key={metric.label} className="p-4">
              <Icon className="text-accent" size={22} aria-hidden="true" />
              <p className="mt-4 text-2xl font-semibold">{metric.value}</p>
              <p className="text-sm text-slate-500">{metric.label}</p>
            </Panel>
          );
        })}
      </div>
      <Panel className="p-5">
        <h2 className="text-lg font-semibold">Actividad reciente</h2>
        <div className="mt-4 grid gap-3 text-sm text-slate-600">
          <p>Modelos validados: consistencia estructural, nombres y relaciones.</p>
          <p>Generaciones ejecutadas: backend Spring Boot y frontend Flutter.</p>
          <p>Colaboracion: eventos UML sincronizados por proyecto.</p>
        </div>
      </Panel>
    </section>
  );
}
