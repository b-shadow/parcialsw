import { useEffect, useRef, useState } from "react";
import { ArrowDown, ArrowUp, Check, Plus, Save, Sparkles, Trash2, X } from "lucide-react";

import { phase1Service } from "../../../core/api/phase1Service";
import { ProjectSocketClient } from "../../../core/websocket/projectSocket";
import { Button } from "../../../shared/components/Button";
import { cn } from "../../../shared/utils/cn";
import { umlService } from "../services/umlService";
import type { MethodReadiness, MethodRule, MethodSpecification, MethodSpecificationProposal, UmlClassDetail, UmlMethod } from "../types/uml";

type Props = {
  projectId: string;
  diagramId: string;
  umlClass: UmlClassDetail;
  classes: UmlClassDetail[];
  method: UmlMethod;
  dark: boolean;
  onClose: () => void;
  onMethodChange: (method: UmlMethod) => void;
};

type Draft = Omit<MethodSpecification, "id" | "method_id" | "revision" | "created_at" | "updated_at">;
type Tab = "signature" | "behavior" | "backend" | "flutter" | "validation";

const emptyDraft: Draft = {
  description: "",
  operation_kind: "custom",
  exposure: "internal",
  preconditions: [],
  postconditions: [],
  business_rules: [],
  validations: [],
  side_effects: [],
  required_permissions: [],
  related_entities: [],
  backend_contract: null,
  frontend_contract: null,
  schema_version: 1
};

const inputClass = "h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white";

export function MethodSpecificationEditor({ projectId, diagramId, umlClass, classes, method, dark, onClose, onMethodChange }: Props) {
  const [tab, setTab] = useState<Tab>("signature");
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [revision, setRevision] = useState<number | null>(null);
  const [readiness, setReadiness] = useState<MethodReadiness | null>(null);
  const [dirty, setDirty] = useState(false);
  const [remoteConflict, setRemoteConflict] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refineText, setRefineText] = useState("");
  const [proposal, setProposal] = useState<MethodSpecificationProposal | null>(null);
  const [selectedProposalFields, setSelectedProposalFields] = useState<string[]>([]);
  const [parameterDraft, setParameterDraft] = useState({ name: "", data_type: "String", default_value: "" });
  const dirtyRef = useRef(false);

  useEffect(() => {
    dirtyRef.current = dirty;
  }, [dirty]);

  const load = async () => {
    const envelope = await umlService.methodSpecification(method.id);
    setRevision(envelope.specification?.revision ?? null);
    setDraft(envelope.specification ? specificationDraft(envelope.specification) : emptyDraft);
    setReadiness(envelope.readiness);
    setDirty(false);
    setRemoteConflict(false);
  };

  useEffect(() => {
    void load().catch(() => setError("No se pudo cargar la especificacion."));
  }, [method.id]);

  useEffect(() => {
    const client = new ProjectSocketClient({
      projectId,
      getProjectSequence: () => 0,
      getConversationSequence: () => 0,
      onStatus: () => undefined,
      onEvent: (event) => {
        if (!("protocol_version" in event) || event.protocol_version !== 2) return;
        if (!event.type.startsWith("METHOD_SPECIFICATION_")) return;
        if (event.payload.method_id !== method.id) return;
        if (dirtyRef.current) setRemoteConflict(true);
        else void load();
      }
    });
    client.connect();
    client.setActiveDiagram(diagramId);
    return () => client.close();
  }, [diagramId, method.id, projectId]);

  const updateDraft = (patch: Partial<Draft>) => {
    setDraft((current) => ({ ...current, ...patch }));
    setDirty(true);
  };

  const save = async (): Promise<boolean> => {
    setBusy(true);
    setError(null);
    try {
      const saved = await umlService.saveMethodSpecification(method.id, draft, revision);
      setRevision(saved.revision);
      setDraft(specificationDraft(saved));
      setReadiness(await umlService.validateMethodSpecification(method.id));
      setDirty(false);
      setRemoteConflict(false);
      return true;
    } catch (reason) {
      const status = (reason as { response?: { status?: number } }).response?.status;
      if (status === 409) setRemoteConflict(true);
      setError(status === 409 ? "Otra persona guardo una revision nueva. Compara o recarga antes de continuar." : "No se pudo guardar el borrador.");
      return false;
    } finally {
      setBusy(false);
    }
  };

  const validateStrict = async () => {
    setBusy(true);
    try {
      if (dirty && !(await save())) return;
      setReadiness(await umlService.validateMethodSpecification(method.id, true));
      setTab("validation");
    } finally {
      setBusy(false);
    }
  };

  const refine = async () => {
    if (!refineText.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await umlService.refineMethodSpecification(method.id, refineText, revision ?? 0);
      setProposal(result);
      setSelectedProposalFields(result.changed_fields);
    } catch {
      setError("No se pudo preparar la propuesta. Verifica la revision y las referencias.");
    } finally {
      setBusy(false);
    }
  };

  const applyProposal = async () => {
    if (!proposal) return;
    setBusy(true);
    try {
      await phase1Service.confirmAiAction(projectId, proposal.action_id);
      setProposal(null);
      setRefineText("");
      await load();
    } catch {
      setError("La propuesta ya no puede aplicarse. Conservamos el texto para reintentar.");
    } finally {
      setBusy(false);
    }
  };

  const acceptSelectedProposalFields = async () => {
    if (!proposal || selectedProposalFields.length === 0) return;
    const next = { ...draft } as Draft;
    const writable = next as unknown as Record<string, unknown>;
    const proposed = proposal.patch as unknown as Record<string, unknown>;
    for (const field of selectedProposalFields) {
      if (field in writable && field in proposed) writable[field] = proposed[field];
    }
    try {
      await phase1Service.rejectAiAction(projectId, proposal.action_id);
      setDraft(next);
      setDirty(true);
      setProposal(null);
      setSelectedProposalFields([]);
    } catch {
      setError("No se pudo cerrar la propuesta. Se conserva para evitar una aplicacion duplicada.");
    }
  };

  const rejectProposal = async () => {
    if (!proposal) return;
    try {
      await phase1Service.rejectAiAction(projectId, proposal.action_id);
      setProposal(null);
      setSelectedProposalFields([]);
    } catch {
      setError("No se pudo rechazar la propuesta.");
    }
  };

  const saveSignature = async () => {
    setBusy(true);
    try {
      const updated = await umlService.updateMethod(method.id, {
        name: method.name,
        visibility: method.visibility,
        return_type: method.return_type,
        order_index: method.order_index
      });
      onMethodChange(updated);
    } finally {
      setBusy(false);
    }
  };

  const addParameter = async () => {
    if (!parameterDraft.name.trim()) return;
    const created = await umlService.addParameter(method.id, {
      ...parameterDraft,
      default_value: parameterDraft.default_value || null,
      order_index: method.parameters.length
    });
    onMethodChange({ ...method, parameters: [...method.parameters, created] });
    setParameterDraft({ name: "", data_type: "String", default_value: "" });
  };

  const mutateParameter = async (parameter: UmlMethod["parameters"][number], patch: Partial<UmlMethod["parameters"][number]>) => {
    const updated = await umlService.updateParameter(parameter.id, patch);
    onMethodChange({ ...method, parameters: method.parameters.map((item) => item.id === updated.id ? updated : item) });
  };

  const removeParameter = async (parameterId: string) => {
    await umlService.deleteParameter(parameterId);
    onMethodChange({ ...method, parameters: method.parameters.filter((item) => item.id !== parameterId) });
  };

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "signature", label: "Firma" }, { id: "behavior", label: "Comportamiento" },
    { id: "backend", label: "Backend" }, { id: "flutter", label: "Flutter" },
    { id: "validation", label: "Validacion" }
  ];

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/50 p-3" role="dialog" aria-modal="true" aria-label="Especificacion funcional del metodo">
      <div className={cn("flex h-[min(850px,calc(100vh-24px))] w-full max-w-6xl flex-col overflow-hidden rounded-lg border shadow-2xl", dark ? "border-slate-700 bg-slate-950 text-slate-100" : "border-slate-200 bg-white text-slate-950")}>
        <header className={cn("flex shrink-0 items-center justify-between border-b px-5 py-4", dark ? "border-slate-700" : "border-slate-200")}>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase text-teal-600">{umlClass.name}</p>
            <h2 className="truncate text-lg font-bold">{method.name}({method.parameters.map((item) => item.name).join(", ")}): {method.return_type ?? "void"}</h2>
            <p className="text-xs text-slate-500">Estado: {readiness?.status ?? "cargando"} | Revision {revision ?? 0}</p>
          </div>
          <button className="flex h-9 w-9 items-center justify-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800" onClick={onClose} title="Cerrar"><X size={19} /></button>
        </header>

        {remoteConflict && <div className="flex items-center justify-between gap-3 border-b border-amber-300 bg-amber-50 px-5 py-2 text-sm text-amber-900"><span>Existe una revision remota. Tu borrador no fue sobrescrito.</span><button className="font-bold underline" onClick={() => void load()}>Descartar local y recargar</button></div>}
        {error && <p className="border-b border-red-200 bg-red-50 px-5 py-2 text-sm text-red-700">{error}</p>}

        <nav className={cn("flex shrink-0 overflow-x-auto border-b px-4", dark ? "border-slate-700" : "border-slate-200")}>
          {tabs.map((item) => <button key={item.id} className={cn("h-11 whitespace-nowrap border-b-2 px-4 text-sm font-semibold", tab === item.id ? "border-teal-600 text-teal-600" : "border-transparent text-slate-500")} onClick={() => setTab(item.id)}>{item.label}</button>)}
        </nav>

        <main className="flex-1 overflow-y-auto p-5">
          {tab === "signature" && <SignatureTab method={method} inputClass={inputClass} onMethodChange={onMethodChange} onSave={() => void saveSignature()} parameterDraft={parameterDraft} setParameterDraft={setParameterDraft} onAdd={() => void addParameter()} onMutate={mutateParameter} onRemove={removeParameter} />}
          {tab === "behavior" && <BehaviorTab draft={draft} classes={classes} updateDraft={updateDraft} inputClass={inputClass} />}
          {tab === "backend" && <BackendTab draft={draft} updateDraft={updateDraft} inputClass={inputClass} />}
          {tab === "flutter" && <FlutterTab draft={draft} method={method} classes={classes} updateDraft={updateDraft} inputClass={inputClass} />}
          {tab === "validation" && <ValidationTab readiness={readiness} />}

          <section className={cn("mt-6 border-t pt-5", dark ? "border-slate-700" : "border-slate-200")}>
            <h3 className="flex items-center gap-2 text-sm font-bold"><Sparkles size={16} />Refinar este metodo con IA</h3>
            <div className="mt-2 flex gap-2">
              <textarea className="min-h-20 flex-1 resize-y rounded-md border border-slate-300 bg-transparent p-3 text-sm dark:border-slate-700" value={refineText} onChange={(event) => setRefineText(event.target.value)} placeholder="Describe que debe hacer, sus reglas y como lo usa el usuario..." />
              <Button disabled={busy || !refineText.trim()} icon={<Sparkles size={16} />} onClick={() => void refine()}>Proponer</Button>
            </div>
            {proposal && <div className="mt-3 border-l-2 border-teal-500 bg-teal-50 p-3 text-sm text-slate-900 dark:bg-teal-950/30 dark:text-slate-100"><p className="font-bold">{proposal.summary}</p><div className="mt-2 flex flex-wrap gap-x-4 gap-y-2">{proposal.changed_fields.map((field) => <label className="flex items-center gap-1" key={field}><input type="checkbox" checked={selectedProposalFields.includes(field)} onChange={(event) => setSelectedProposalFields((current) => event.target.checked ? [...current, field] : current.filter((item) => item !== field))} />{field}</label>)}</div>{proposal.unresolved_references.map((item) => <p className="mt-1 text-amber-700" key={item}>{item}</p>)}<div className="mt-3 flex flex-wrap gap-2"><Button icon={<Check size={15} />} onClick={() => void applyProposal()}>Confirmar todo</Button><Button variant="secondary" disabled={selectedProposalFields.length === 0} onClick={() => void acceptSelectedProposalFields()}>Incorporar seleccion al borrador</Button><Button variant="secondary" onClick={() => void rejectProposal()}>Rechazar</Button></div></div>}
          </section>
        </main>

        <footer className={cn("flex shrink-0 items-center justify-between gap-3 border-t px-5 py-3", dark ? "border-slate-700" : "border-slate-200")}>
          <Button variant="secondary" onClick={() => void validateStrict()}>Validar para generar</Button>
          <div className="flex gap-2"><Button variant="secondary" onClick={onClose}>Cerrar</Button><Button disabled={busy || !dirty || remoteConflict} icon={<Save size={16} />} onClick={() => void save()}>Guardar borrador</Button></div>
        </footer>
      </div>
    </div>
  );
}

type ParameterDraft = { name: string; data_type: string; default_value: string };

type SignatureTabProps = {
  method: UmlMethod;
  inputClass: string;
  onMethodChange: (method: UmlMethod) => void;
  onSave: () => void;
  parameterDraft: ParameterDraft;
  setParameterDraft: (draft: ParameterDraft) => void;
  onAdd: () => void;
  onMutate: (
    parameter: UmlMethod["parameters"][number],
    patch: Partial<UmlMethod["parameters"][number]>
  ) => Promise<void>;
  onRemove: (parameterId: string) => Promise<void>;
};

function SignatureTab({ method, inputClass, onMethodChange, onSave, parameterDraft, setParameterDraft, onAdd, onMutate, onRemove }: SignatureTabProps) {
  const move = (index: number, direction: -1 | 1) => {
    const other = index + direction;
    if (other < 0 || other >= method.parameters.length) return;
    void onMutate(method.parameters[index], { order_index: other });
    void onMutate(method.parameters[other], { order_index: index });
  };
  return <section><h3 className="text-base font-bold">Firma UML</h3><div className="mt-3 grid gap-3 md:grid-cols-3"><label className="text-sm">Nombre<input className={inputClass} value={method.name} onChange={(e) => onMethodChange({ ...method, name: e.target.value })} /></label><label className="text-sm">Visibilidad<select className={inputClass} value={method.visibility} onChange={(e) => onMethodChange({ ...method, visibility: e.target.value })}><option value="public">Publico</option><option value="private">Privado</option><option value="protected">Protegido</option></select></label><label className="text-sm">Retorno<input className={inputClass} value={method.return_type ?? ""} onChange={(e) => onMethodChange({ ...method, return_type: e.target.value })} /></label></div><div className="mt-3"><Button icon={<Save size={15} />} onClick={onSave}>Guardar firma</Button></div><h3 className="mt-6 text-sm font-bold">Parametros ordenados</h3><div className="mt-2 grid gap-2">{[...method.parameters].sort((a, b) => a.order_index - b.order_index).map((item, index) => <div className="grid gap-2 md:grid-cols-[1fr_1fr_1fr_auto]" key={item.id}><input className={inputClass} value={item.name} onChange={(e) => onMethodChange({ ...method, parameters: method.parameters.map((p) => p.id === item.id ? { ...p, name: e.target.value } : p) })} onBlur={() => void onMutate(item, { name: item.name })} /><input className={inputClass} value={item.data_type} onChange={(e) => onMethodChange({ ...method, parameters: method.parameters.map((p) => p.id === item.id ? { ...p, data_type: e.target.value } : p) })} onBlur={() => void onMutate(item, { data_type: item.data_type })} /><input className={inputClass} placeholder="Valor por defecto" value={item.default_value ?? ""} onChange={(e) => onMethodChange({ ...method, parameters: method.parameters.map((p) => p.id === item.id ? { ...p, default_value: e.target.value } : p) })} onBlur={() => void onMutate(item, { default_value: item.default_value })} /><div className="flex gap-1"><button title="Subir" onClick={() => move(index, -1)}><ArrowUp size={17} /></button><button title="Bajar" onClick={() => move(index, 1)}><ArrowDown size={17} /></button><button title="Eliminar parametro" onClick={() => void onRemove(item.id)}><Trash2 size={17} /></button></div></div>)}</div><div className="mt-3 grid gap-2 md:grid-cols-[1fr_1fr_1fr_auto]"><input className={inputClass} placeholder="Nombre" value={parameterDraft.name} onChange={(e) => setParameterDraft({ ...parameterDraft, name: e.target.value })} /><input className={inputClass} placeholder="Tipo" value={parameterDraft.data_type} onChange={(e) => setParameterDraft({ ...parameterDraft, data_type: e.target.value })} /><input className={inputClass} placeholder="Valor por defecto" value={parameterDraft.default_value} onChange={(e) => setParameterDraft({ ...parameterDraft, default_value: e.target.value })} /><Button icon={<Plus size={15} />} onClick={onAdd}>Agregar</Button></div></section>;
}

function RuleList({ title, values, onChange }: { title: string; values: MethodRule[]; onChange: (value: MethodRule[]) => void }) {
  const add = () => onChange([...values, { code: `regla_${values.length + 1}`, description: "", severity: "error" }]);
  return <div><div className="flex items-center justify-between"><h4 className="text-sm font-bold">{title}</h4><button className="flex h-8 items-center gap-1 text-xs font-bold text-teal-600" onClick={add}><Plus size={14} />Agregar</button></div><div className="mt-2 grid gap-2">{values.map((item, index) => <div className="grid gap-2 md:grid-cols-[180px_1fr_110px_auto]" key={`${item.code}-${index}`}><input className={inputClass} value={item.code} onChange={(e) => onChange(values.map((value, i) => i === index ? { ...value, code: e.target.value } : value))} /><input className={inputClass} value={item.description} onChange={(e) => onChange(values.map((value, i) => i === index ? { ...value, description: e.target.value } : value))} /><select className={inputClass} value={item.severity} onChange={(e) => onChange(values.map((value, i) => i === index ? { ...value, severity: e.target.value as MethodRule["severity"] } : value))}><option value="error">Error</option><option value="warning">Advertencia</option><option value="info">Info</option></select><button title="Quitar" onClick={() => onChange(values.filter((_, i) => i !== index))}><Trash2 size={17} /></button></div>)}</div></div>;
}

function BehaviorTab({ draft, classes, updateDraft, inputClass: fieldClass }: { draft: Draft; classes: UmlClassDetail[]; updateDraft: (patch: Partial<Draft>) => void; inputClass: string }) {
  const addSideEffect = () => updateDraft({
    side_effects: [...draft.side_effects, { code: `efecto_${draft.side_effects.length + 1}`, kind: "data_change", description: "", target_entity_id: null, target_entity_name: null }]
  });
  const addRelatedEntity = () => updateDraft({
    related_entities: [...draft.related_entities, { class_id: null, class_name: "", relation: "reads", required: false, source_parameter_id: null }]
  });
  return (
    <section className="grid gap-5">
      <label className="text-sm">Descripcion funcional<textarea className="mt-1 min-h-24 w-full resize-y rounded-md border border-slate-300 bg-transparent p-3 dark:border-slate-700" value={draft.description ?? ""} onChange={(e) => updateDraft({ description: e.target.value })} /></label>
      <div className="grid gap-3 md:grid-cols-2">
        <label className="text-sm">Tipo de operacion<select className={fieldClass} value={draft.operation_kind} onChange={(e) => updateDraft({ operation_kind: e.target.value as Draft["operation_kind"] })}>{["custom", "create", "read", "search", "update", "delete", "calculate", "business_action"].map((item) => <option key={item}>{item}</option>)}</select></label>
        <label className="text-sm">Exposicion<select className={fieldClass} value={draft.exposure} onChange={(e) => updateDraft({ exposure: e.target.value as Draft["exposure"] })}><option value="internal">Interno</option><option value="api">API</option><option value="user_action">Accion de usuario</option></select></label>
      </div>
      <RuleList title="Precondiciones" values={draft.preconditions} onChange={(preconditions) => updateDraft({ preconditions })} />
      <RuleList title="Postcondiciones" values={draft.postconditions} onChange={(postconditions) => updateDraft({ postconditions })} />
      <RuleList title="Reglas de negocio" values={draft.business_rules} onChange={(business_rules) => updateDraft({ business_rules })} />
      <RuleList title="Validaciones" values={draft.validations} onChange={(validations) => updateDraft({ validations })} />
      <div>
        <div className="flex items-center justify-between"><h4 className="text-sm font-bold">Efectos laterales</h4><button className="flex items-center gap-1 text-xs font-bold text-teal-600" onClick={addSideEffect}><Plus size={14} />Agregar</button></div>
        <div className="mt-2 grid gap-2">{draft.side_effects.map((effect, index) => <div className="grid gap-2 md:grid-cols-[160px_170px_1fr_auto]" key={`${effect.code}-${index}`}><input className={fieldClass} value={effect.code} onChange={(e) => updateDraft({ side_effects: draft.side_effects.map((item, i) => i === index ? { ...item, code: e.target.value } : item) })} /><select className={fieldClass} value={effect.kind} onChange={(e) => updateDraft({ side_effects: draft.side_effects.map((item, i) => i === index ? { ...item, kind: e.target.value as typeof item.kind } : item) })}>{["data_change", "status_change", "notification", "audit_event", "refresh_required"].map((kind) => <option key={kind}>{kind}</option>)}</select><input className={fieldClass} placeholder="Descripcion observable" value={effect.description} onChange={(e) => updateDraft({ side_effects: draft.side_effects.map((item, i) => i === index ? { ...item, description: e.target.value } : item) })} /><button title="Quitar" onClick={() => updateDraft({ side_effects: draft.side_effects.filter((_, i) => i !== index) })}><Trash2 size={17} /></button></div>)}</div>
      </div>
      <div>
        <div className="flex items-center justify-between"><h4 className="text-sm font-bold">Entidades relacionadas</h4><button className="flex items-center gap-1 text-xs font-bold text-teal-600" onClick={addRelatedEntity}><Plus size={14} />Agregar</button></div>
        <div className="mt-2 grid gap-2">{draft.related_entities.map((entity, index) => <div className="grid gap-2 md:grid-cols-[1fr_180px_120px_auto]" key={`${entity.class_id}-${index}`}><select className={fieldClass} value={entity.class_id ?? ""} onChange={(e) => { const selected = classes.find((item) => item.id === e.target.value); updateDraft({ related_entities: draft.related_entities.map((item, i) => i === index ? { ...item, class_id: selected?.id ?? null, class_name: selected?.name ?? "" } : item) }); }}><option value="">Seleccionar clase</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select className={fieldClass} value={entity.relation} onChange={(e) => updateDraft({ related_entities: draft.related_entities.map((item, i) => i === index ? { ...item, relation: e.target.value as typeof item.relation } : item) })}>{["owner", "input_reference", "output", "reads", "creates", "updates", "deletes", "refresh_target"].map((relation) => <option key={relation}>{relation}</option>)}</select><label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={entity.required} onChange={(e) => updateDraft({ related_entities: draft.related_entities.map((item, i) => i === index ? { ...item, required: e.target.checked } : item) })} />Obligatoria</label><button title="Quitar" onClick={() => updateDraft({ related_entities: draft.related_entities.filter((_, i) => i !== index) })}><Trash2 size={17} /></button></div>)}</div>
      </div>
      <label className="text-sm">Permisos (uno por linea, recurso.accion)<textarea className="mt-1 min-h-20 w-full rounded-md border border-slate-300 bg-transparent p-3 dark:border-slate-700" value={draft.required_permissions.map((item) => item.code).join("\n")} onChange={(e) => updateDraft({ required_permissions: e.target.value.split("\n").map((code) => code.trim()).filter(Boolean).map((code) => ({ code })) })} /></label>
    </section>
  );
}

function BackendTab({ draft, updateDraft, inputClass: fieldClass }: { draft: Draft; updateDraft: (patch: Partial<Draft>) => void; inputClass: string }) {
  const contract = draft.backend_contract;
  if (!contract) return <section><p className="text-sm text-slate-500">Este metodo no tiene contrato backend.</p><Button className="mt-3" onClick={() => updateDraft({ backend_contract: { http_method: "POST", path: `/${draft.operation_kind}`, request_dto: null, response_dto: null, transactional: false, authorization: [], error_codes: [], status_codes: { success: 200, validation_error: 400, not_found: 404, conflict: 409 } } })}>Definir contrato</Button></section>;
  const set = (patch: Partial<NonNullable<Draft["backend_contract"]>>) => updateDraft({ backend_contract: { ...contract, ...patch } });
  const status = (key: keyof typeof contract.status_codes, value: string) => set({ status_codes: { ...contract.status_codes, [key]: Number(value) } });
  return <section className="grid gap-4"><div className="grid gap-3 md:grid-cols-[160px_1fr]"><label className="text-sm">Metodo HTTP<select className={fieldClass} value={contract.http_method} onChange={(e) => set({ http_method: e.target.value as typeof contract.http_method })}>{["GET", "POST", "PUT", "PATCH", "DELETE"].map((item) => <option key={item}>{item}</option>)}</select></label><label className="text-sm">Ruta<input className={fieldClass} value={contract.path} onChange={(e) => set({ path: e.target.value })} /></label></div><div className="grid gap-3 md:grid-cols-2"><label className="text-sm">DTO entrada<input className={fieldClass} value={contract.request_dto ?? ""} onChange={(e) => set({ request_dto: e.target.value || null })} /></label><label className="text-sm">DTO respuesta<input className={fieldClass} value={contract.response_dto ?? ""} onChange={(e) => set({ response_dto: e.target.value || null })} /></label></div><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{(["success", "validation_error", "not_found", "conflict"] as const).map((key) => <label className="text-sm" key={key}>{key}<input className={fieldClass} type="number" min={100} max={599} value={contract.status_codes[key]} onChange={(e) => status(key, e.target.value)} /></label>)}</div><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={contract.transactional} onChange={(e) => set({ transactional: e.target.checked })} />Transaccional</label><label className="text-sm">Autorizaciones separadas por coma<input className={fieldClass} value={contract.authorization.join(", ")} onChange={(e) => set({ authorization: e.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} /></label><label className="text-sm">Codigos de error separados por coma<input className={fieldClass} value={contract.error_codes.join(", ")} onChange={(e) => set({ error_codes: e.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} /></label><button className="w-fit text-sm font-bold text-red-600" onClick={() => updateDraft({ backend_contract: null })}>Limpiar contrato backend</button></section>;
}

function FlutterTab({ draft, method, classes, updateDraft, inputClass: fieldClass }: { draft: Draft; method: UmlMethod; classes: UmlClassDetail[]; updateDraft: (patch: Partial<Draft>) => void; inputClass: string }) {
  const contract = draft.frontend_contract;
  if (!contract) return <section><p className="text-sm text-slate-500">Este metodo no tiene representacion Flutter.</p><Button className="mt-3" onClick={() => updateDraft({ frontend_contract: { interaction: "form", label: method.name, placement: null, confirmation_required: draft.operation_kind === "delete", refresh_targets: [], success_message: null, fields: method.parameters.map((item) => ({ parameter_id: item.id, parameter: item.name, control: controlFor(item.data_type), source_entity_id: null, source_entity: null, display_fields: [], hidden: false })) } })}>Definir interaccion</Button></section>;
  const set = (patch: Partial<NonNullable<Draft["frontend_contract"]>>) => updateDraft({ frontend_contract: { ...contract, ...patch } });
  return <section className="grid gap-4"><div className="grid gap-3 md:grid-cols-2"><label className="text-sm">Interaccion<select className={fieldClass} value={contract.interaction} onChange={(e) => set({ interaction: e.target.value as typeof contract.interaction })}>{["form", "button", "menu_action", "background", "filter"].map((item) => <option key={item}>{item}</option>)}</select></label><label className="text-sm">Etiqueta<input className={fieldClass} value={contract.label} onChange={(e) => set({ label: e.target.value })} /></label><label className="text-sm">Ubicacion<input className={fieldClass} placeholder="detalle, formulario, menu..." value={contract.placement ?? ""} onChange={(e) => set({ placement: e.target.value || null })} /></label><label className="text-sm">Mensaje de exito<input className={fieldClass} value={contract.success_message ?? ""} onChange={(e) => set({ success_message: e.target.value || null })} /></label></div><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={contract.confirmation_required} onChange={(e) => set({ confirmation_required: e.target.checked })} />Pedir confirmacion</label><label className="text-sm">Vistas a refrescar<select className={fieldClass} multiple value={contract.refresh_targets} onChange={(e) => set({ refresh_targets: Array.from(e.target.selectedOptions, (option) => option.value) })}>{classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><h4 className="text-sm font-bold">Parametros y controles</h4>{contract.fields.map((item, index) => { const source = classes.find((value) => value.id === item.source_entity_id); return <div className="grid gap-2 rounded-md border border-slate-200 p-2 dark:border-slate-700 md:grid-cols-2" key={item.parameter_id ?? item.parameter}><input className={fieldClass} value={item.parameter} disabled /><select className={fieldClass} value={item.control} onChange={(e) => set({ fields: contract.fields.map((value, i) => i === index ? { ...value, control: e.target.value } : value) })}>{["text_input", "multiline_text", "number_input", "decimal_input", "switch", "date_picker", "date_time_picker", "single_select", "entity_selector", "multi_select"].map((control) => <option key={control}>{control}</option>)}</select><select className={fieldClass} value={item.source_entity_id ?? ""} onChange={(e) => { const selected = classes.find((value) => value.id === e.target.value); set({ fields: contract.fields.map((value, i) => i === index ? { ...value, source_entity_id: selected?.id ?? null, source_entity: selected?.name ?? null, display_fields: [] } : value) }); }}><option value="">Sin entidad origen</option>{classes.map((value) => <option key={value.id} value={value.id}>{value.name}</option>)}</select><select className={fieldClass} multiple value={item.display_fields} disabled={!source} onChange={(e) => set({ fields: contract.fields.map((value, i) => i === index ? { ...value, display_fields: Array.from(e.target.selectedOptions, (option) => option.value) } : value) })}>{source?.attributes.map((attribute) => <option key={attribute.id} value={attribute.name}>{attribute.name}</option>)}</select><label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={item.hidden} onChange={(e) => set({ fields: contract.fields.map((value, i) => i === index ? { ...value, hidden: e.target.checked } : value) })} />Oculto</label></div>; })}<button className="w-fit text-sm font-bold text-red-600" onClick={() => updateDraft({ frontend_contract: null })}>Limpiar contrato Flutter</button></section>;
}

function ValidationTab({ readiness }: { readiness: MethodReadiness | null }) {
  if (!readiness) return <p className="text-sm text-slate-500">Ejecuta la validacion para generar.</p>;
  return <section><h3 className="text-base font-bold">{readiness.ready_for_generation ? "Listo para generar" : "Requiere revision"}</h3><div className="mt-3 grid gap-2">{[...readiness.errors, ...readiness.warnings].map((item) => <div className={cn("border-l-2 px-3 py-2 text-sm", item.severity === "error" ? "border-red-500 bg-red-50 text-red-900 dark:bg-red-950/30 dark:text-red-100" : "border-amber-500 bg-amber-50 text-amber-900 dark:bg-amber-950/30 dark:text-amber-100")} key={`${item.code}-${item.path}`}><p className="font-bold">{item.message}</p><p className="text-xs opacity-75">{item.path}{item.suggestion ? ` | ${item.suggestion}` : ""}</p></div>)}</div></section>;
}

function specificationDraft(specification: MethodSpecification): Draft {
  return {
    description: specification.description,
    operation_kind: specification.operation_kind,
    exposure: specification.exposure,
    preconditions: specification.preconditions,
    postconditions: specification.postconditions,
    business_rules: specification.business_rules,
    validations: specification.validations,
    side_effects: specification.side_effects,
    required_permissions: specification.required_permissions,
    related_entities: specification.related_entities,
    backend_contract: specification.backend_contract,
    frontend_contract: specification.frontend_contract,
    schema_version: specification.schema_version
  };
}

function controlFor(dataType: string) {
  const type = dataType.toLowerCase();
  if (["int", "integer", "long"].includes(type)) return "number_input";
  if (["double", "float", "decimal", "bigdecimal"].includes(type)) return "decimal_input";
  if (["boolean", "bool"].includes(type)) return "switch";
  if (["date", "localdate"].includes(type)) return "date_picker";
  if (["datetime", "localdatetime"].includes(type)) return "date_time_picker";
  return "text_input";
}
