import { ChangeEvent, useRef, useState } from "react";
import {
  ArrowLeft,
  FileCode2,
  FileText,
  Image,
  LoaderCircle,
  Mic,
  Plus,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { useThemeStore } from "../../../core/theme/themeStore";
import { cn } from "../../../shared/utils/cn";
import { aiService } from "../../modelado_uml_inteligente/services/aiService";
import { umlService } from "../../modelado_uml_inteligente/services/umlService";
import { projectService } from "../services/projectService";

type AiSource = "text" | "voice" | "image";
type AiUmlResult = Awaited<ReturnType<typeof aiService.textToUml>>;

type BrowserSpeechRecognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: { results: ArrayLike<{ 0: { transcript: string } }> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
};

function fileToBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function fileToText(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

function validateImageResult(result: AiUmlResult) {
  const names = result.classes.map((item) => item.name.trim().toLocaleLowerCase());
  return (
    result.classes.length > 0 &&
    result.confidence >= 0.55 &&
    !result.classes.some((item) => !item.name.trim() || /^Clase\d+$/i.test(item.name)) &&
    new Set(names).size === names.length
  );
}

export function CreateProjectPage() {
  const navigate = useNavigate();
  const isDark = useThemeStore((state) => state.mode === "dark");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [prompt, setPrompt] = useState("");
  const [aiSource, setAiSource] = useState<AiSource>("text");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [xmiFile, setXmiFile] = useState<File | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState("");
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const xmiInputRef = useRef<HTMLInputElement | null>(null);

  const panelTone = isDark
    ? "border-slate-700 bg-[#0b1424] text-slate-100"
    : "border-blue-100 bg-white text-[#070b5f]";
  const fieldTone = isDark
    ? "border-slate-700 bg-[#08111f] text-white placeholder:text-slate-500"
    : "border-blue-200 bg-white text-[#070b5f] placeholder:text-blue-700/45";

  function hasAnyInput() {
    return Boolean(
      name.trim() ||
      description.trim() ||
      prompt.trim() ||
      imageFile ||
      xmiFile
    );
  }

  function projectData(allowCompletelyEmpty: boolean) {
    if (allowCompletelyEmpty && !hasAnyInput()) {
      return { name: "Proyecto sin titulo", description: undefined };
    }
    if (name.trim().length < 2 || !description.trim()) {
      throw new Error("Complete el nombre y la descripcion del proyecto.");
    }
    return { name: name.trim(), description: description.trim() };
  }

  function startVoiceCapture() {
    const browserWindow = window as Window & {
      SpeechRecognition?: new () => BrowserSpeechRecognition;
      webkitSpeechRecognition?: new () => BrowserSpeechRecognition;
    };
    const SpeechRecognition = browserWindow.SpeechRecognition ?? browserWindow.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMessage("El navegador no permite dictado. Puede escribir la descripcion del modelo.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "es-ES";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results).map((result) => result[0].transcript).join(" ");
      setPrompt((current) => [current.trim(), transcript.trim()].filter(Boolean).join(" "));
      setAiSource("voice");
      setMessage("Dictado transcrito. Revise el texto antes de crear el proyecto.");
    };
    recognition.onerror = () => {
      setMessage("No se pudo completar el dictado.");
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
    setIsListening(true);
    recognition.start();
  }

  async function buildAiResult() {
    if (aiSource === "image" && imageFile) {
      const result = await aiService.imageToUml({
        image_base64: await fileToBase64(imageFile),
        file_name: imageFile.name,
      });
      if (!validateImageResult(result)) {
        throw new Error(result.observations.join(" ") || "La imagen no pudo leerse con suficiente precision.");
      }
      return result;
    }
    if (!prompt.trim()) return null;
    if (prompt.trim().length < 3) throw new Error("Describa el modelo con mayor detalle.");
    return aiSource === "voice"
      ? aiService.voiceToUml({ transcript: prompt.trim() })
      : aiService.textToUml(prompt.trim());
  }

  async function initializeProject(data: { name: string; description?: string }) {
    const project = await projectService.create(data);
    const diagrams = await umlService.listDiagrams(project.id);
    const diagram = diagrams[0];
    if (!diagram) throw new Error("No se pudo inicializar el diagrama del proyecto.");
    return { project, diagram };
  }

  async function createProject() {
    if (isProcessing) return;
    setIsProcessing(true);
    setMessage("Preparando el proyecto...");
    try {
      if (xmiFile && !prompt.trim() && !imageFile) {
        projectData(false);
        throw new Error("El archivo esta listo. Use Importar para cargar el XMI.");
      }
      const data = projectData(true);
      const aiResult = await buildAiResult();
      const { project, diagram } = await initializeProject(data);
      if (aiResult) {
        await umlService.applyAiModificationToDiagram({
          diagramId: diagram.id,
          classes: [],
          relationships: [],
          result: aiResult,
        });
      }
      navigate(`/proyectos/${project.id}/uml/${diagram.id}`, { replace: true });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo crear el proyecto.");
    } finally {
      setIsProcessing(false);
    }
  }

  async function importProject() {
    if (isProcessing) return;
    setIsProcessing(true);
    setMessage("Importando el archivo XMI...");
    try {
      if (!xmiFile) throw new Error("Seleccione un archivo XML o XMI.");
      const data = projectData(false);
      const { project, diagram } = await initializeProject(data);
      await umlService.importXmiIntoDiagram(diagram.id, {
        project_id: project.id,
        name: data.name,
        file_name: xmiFile.name,
        content: await fileToText(xmiFile),
      });
      navigate(`/proyectos/${project.id}/uml/${diagram.id}`, { replace: true });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo importar el proyecto.");
    } finally {
      setIsProcessing(false);
    }
  }

  function handleImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setImageFile(file);
    if (file) {
      setAiSource("image");
      setMessage(`Imagen seleccionada: ${file.name}`);
    }
  }

  function clearImage() {
    setImageFile(null);
    setAiSource("text");
    if (imageInputRef.current) imageInputRef.current.value = "";
    setMessage("");
  }

  function handleXmi(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setXmiFile(file);
    setMessage(file ? `Archivo seleccionado: ${file.name}` : "");
  }

  function clearXmi() {
    setXmiFile(null);
    if (xmiInputRef.current) xmiInputRef.current.value = "";
    setMessage("");
  }

  return (
    <section className="mx-auto grid w-full max-w-6xl gap-6">
      <header>
        <Link className="mb-3 inline-flex items-center gap-2 text-sm font-semibold text-accent" to="/proyectos">
          <ArrowLeft size={16} />
          Volver a proyectos
        </Link>
        <h1 className="text-3xl font-black">Crear proyecto</h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Define los datos y elige si deseas iniciar vacío, con IA o importando un XMI.
        </p>
      </header>

      <div className={cn("overflow-hidden rounded-lg border shadow-sm", panelTone)}>
        <div className="grid gap-6 p-6 md:grid-cols-3">
          <div className="grid min-w-0 content-start gap-5 md:col-span-1">
            <div>
              <h2 className="text-xl font-black">Datos del proyecto</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">El nombre y la descripcion identifican el proyecto y su diagrama.</p>
            </div>
            <label className="grid gap-2 text-sm font-bold">
              Nombre del proyecto
              <span className={cn("flex h-12 items-center gap-3 rounded-md border px-3 focus-within:ring-2 focus-within:ring-teal-100", fieldTone)}>
                <FileText size={18} />
                <input className="min-w-0 flex-1 bg-transparent outline-none" placeholder="Ej. Sistema de ventas" value={name} onChange={(event) => setName(event.target.value)} />
              </span>
            </label>
            <label className="grid gap-2 text-sm font-bold">
              Descripcion
              <textarea className={cn("min-h-28 resize-y rounded-md border px-3 py-2 outline-none focus:ring-2 focus:ring-teal-100", fieldTone)} placeholder="Objetivo general del sistema" value={description} onChange={(event) => setDescription(event.target.value)} />
            </label>
          </div>

          <div className={cn("grid min-w-0 content-start gap-4 rounded-md border p-5 md:col-span-2", isDark ? "border-slate-700 bg-slate-900" : "border-blue-100 bg-slate-50/70")}>
            <div>
              <h2 className="flex items-center gap-2 text-xl font-black"><Sparkles size={20} /> Crear desde IA</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Describe el modelo, dicta una instruccion o carga una imagen.</p>
            </div>
            <textarea
              className={cn("min-h-32 resize-none rounded-md border px-3 py-2 outline-none focus:ring-2 focus:ring-teal-100", fieldTone)}
              maxLength={1000}
              placeholder="Ej. Sistema de ventas con clientes, productos, pedidos y pagos."
              value={prompt}
              onChange={(event) => {
                setPrompt(event.target.value);
                if (aiSource === "image") setAiSource("text");
              }}
            />
            <div className="grid grid-cols-3 gap-2">
              <button className={cn("h-10 rounded-md border text-sm font-bold", aiSource === "text" ? "border-teal-500 bg-teal-50 text-teal-800" : "border-slate-300")} onClick={() => setAiSource("text")} type="button"><FileText className="mr-1 inline" size={15} />Texto</button>
              <button className={cn("h-10 rounded-md border text-sm font-bold", aiSource === "voice" ? "border-teal-500 bg-teal-50 text-teal-800" : "border-slate-300")} disabled={isListening} onClick={startVoiceCapture} type="button"><Mic className="mr-1 inline" size={15} />{isListening ? "Oyendo" : "Voz"}</button>
              <button className={cn("h-10 rounded-md border text-sm font-bold", aiSource === "image" ? "border-teal-500 bg-teal-50 text-teal-800" : "border-slate-300")} onClick={() => imageInputRef.current?.click()} type="button"><Image className="mr-1 inline" size={15} />Imagen</button>
            </div>
            <input ref={imageInputRef} className="hidden" type="file" accept="image/*" onChange={handleImage} />
            {imageFile && (
              <div className="flex items-center gap-3 border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-950">
                <Image className="shrink-0 text-teal-700" size={18} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{imageFile.name}</p>
                  <p className="text-xs text-slate-500">{imageFile.type || "Imagen"}</p>
                </div>
                <button className="grid size-8 place-items-center rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" onClick={clearImage} title="Limpiar imagen" type="button"><X size={17} /></button>
              </div>
            )}

            <div className="mt-1 border-t border-slate-200 pt-4 dark:border-slate-700">
              <input ref={xmiInputRef} className="hidden" type="file" accept=".xml,.xmi,text/xml,application/xml" onChange={handleXmi} />
              {!xmiFile ? (
                <button className="flex h-11 w-full items-center justify-center gap-2 rounded-md border border-slate-300 text-sm font-bold hover:border-teal-500 hover:bg-teal-50 dark:border-slate-700 dark:hover:bg-slate-800" onClick={() => xmiInputRef.current?.click()} type="button">
                  <Upload size={17} />
                  Seleccionar archivo XMI
                </button>
              ) : (
                <div className="flex items-center gap-3 border border-teal-200 bg-teal-50 px-3 py-2 dark:border-teal-900 dark:bg-teal-950/30">
                  <FileCode2 className="shrink-0 text-teal-700 dark:text-teal-300" size={20} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold">{xmiFile.name}</p>
                    <p className="text-xs text-slate-500">{xmiFile.type || "Archivo XMI/XML"}</p>
                  </div>
                  <button className="grid size-8 place-items-center rounded-md text-slate-500 hover:bg-white dark:hover:bg-slate-800" onClick={clearXmi} title="Limpiar archivo XMI" type="button"><X size={17} /></button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3 border-t border-slate-200 px-6 py-4 md:flex-row md:items-center md:justify-between dark:border-slate-700">
          <p className={cn("min-h-5 text-sm", message ? "text-amber-700 dark:text-amber-300" : "text-slate-500")} role="status">{message}</p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <button className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-teal-700 px-6 text-sm font-bold text-white hover:bg-teal-800 disabled:cursor-wait disabled:opacity-60" disabled={isProcessing} onClick={() => void createProject()} type="button">
              {isProcessing ? <LoaderCircle className="animate-spin" size={18} /> : <Plus size={18} />}
              Crear proyecto
            </button>
            <button className="inline-flex h-12 items-center justify-center gap-2 rounded-md border border-teal-700 px-6 text-sm font-bold text-teal-800 hover:bg-teal-50 disabled:cursor-wait disabled:opacity-60 dark:text-teal-200 dark:hover:bg-teal-950/30" disabled={isProcessing} onClick={() => void importProject()} type="button">
              <Upload size={18} />
              Importar
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
