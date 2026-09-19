import { FormEvent, useState } from "react";
import { BrainCircuit, Code2, Database, Download, Smartphone } from "lucide-react";

import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { generationService } from "../services/generationService";
import type { GeneratedBackend, GeneratedFrontend, Transformation } from "../types/generation";

export function GenerationPage() {
  const [diagramId, setDiagramId] = useState("");
  const [name, setName] = useState("AplicacionGenerada");
  const [transformation, setTransformation] = useState<Transformation | null>(null);
  const [backend, setBackend] = useState<GeneratedBackend | null>(null);
  const [frontend, setFrontend] = useState<GeneratedFrontend | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleTransform(event: FormEvent) {
    event.preventDefault();
    if (!diagramId.trim()) {
      setError("Debe seleccionar un diagrama.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const created = await generationService.transform({ diagram_id: diagramId.trim(), target_platform: "full_stack" });
      setTransformation(created);
    } catch {
      setError("No se pudo transformar el modelo UML.");
    } finally {
      setLoading(false);
    }
  }

  async function generateBackend() {
    if (!transformation) {
      return;
    }
    setBackend(
      await generationService.springBoot({
        transformation_id: transformation.id,
        name: `${name}Backend`,
        version_label: "v1"
      })
    );
  }

  async function generateFrontend() {
    if (!transformation) {
      return;
    }
    setFrontend(
      await generationService.flutter({
        transformation_id: transformation.id,
        name: `${name}Mobile`,
        version_label: "v1",
        backend_id: backend?.id
      })
    );
  }

  async function downloadBackend() {
    if (!backend) {
      return;
    }
    const blob = await generationService.downloadSpringBoot(backend.id);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${backend.name}.zip`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function downloadFrontend() {
    if (!frontend) {
      return;
    }
    const blob = await generationService.downloadFlutter(frontend.id);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${frontend.name}.zip`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Transformacion y generacion</h1>
        <p className="mt-1 text-sm text-slate-600">Ejecucion de pipeline UML hacia Spring Boot y Flutter.</p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[360px_1fr]">
        <Panel className="p-5">
          <form className="grid gap-4" onSubmit={handleTransform}>
            <Input label="ID del diagrama UML" value={diagramId} onChange={(event) => setDiagramId(event.target.value)} />
            <Input label="Nombre base" value={name} onChange={(event) => setName(event.target.value)} />
            {error && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
            <Button disabled={loading} icon={<BrainCircuit size={18} aria-hidden="true" />} type="submit">
              {loading ? "Transformando" : "Transformar UML"}
            </Button>
          </form>
        </Panel>

        <div className="grid gap-4 md:grid-cols-3">
          <Panel className="p-5">
            <Database className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Modelo intermedio</h2>
            <p className="mt-2 text-sm text-slate-600">{transformation?.id ?? "Sin transformacion activa"}</p>
            <div className="mt-4">
              <StatusBadge tone={transformation ? "success" : "neutral"}>{transformation?.status ?? "pendiente"}</StatusBadge>
            </div>
          </Panel>
          <Panel className="p-5">
            <Code2 className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Spring Boot</h2>
            <p className="mt-2 text-sm text-slate-600">{backend?.name ?? "Backend no generado"}</p>
            {backend && (
              <p className="mt-2 text-xs text-slate-500">
                {backend.manifest.file_count ?? 0} archivos, {backend.manifest.entity_count ?? 0} entidades
              </p>
            )}
            <Button className="mt-4" disabled={!transformation} onClick={generateBackend} variant="secondary">
              Generar
            </Button>
            <Button
              className="mt-2 w-full"
              disabled={!backend}
              icon={<Download size={18} aria-hidden="true" />}
              onClick={downloadBackend}
              variant="ghost"
            >
              Descargar ZIP
            </Button>
          </Panel>
          <Panel className="p-5">
            <Smartphone className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Flutter</h2>
            <p className="mt-2 text-sm text-slate-600">{frontend?.name ?? "Frontend movil no generado"}</p>
            {frontend && (
              <p className="mt-2 text-xs text-slate-500">
                {frontend.manifest.file_count ?? 0} archivos, {frontend.manifest.entity_count ?? 0} entidades
              </p>
            )}
            <Button className="mt-4" disabled={!transformation} onClick={generateFrontend} variant="secondary">
              Generar
            </Button>
            <Button
              className="mt-2 w-full"
              disabled={!frontend}
              icon={<Download size={18} aria-hidden="true" />}
              onClick={downloadFrontend}
              variant="ghost"
            >
              Descargar ZIP
            </Button>
          </Panel>
        </div>
      </div>
    </section>
  );
}
