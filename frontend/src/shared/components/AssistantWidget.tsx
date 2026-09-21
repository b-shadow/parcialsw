import { FormEvent, useMemo, useState } from "react";
import { Bot, HelpCircle, Maximize2, MessageCircle, Minimize2, Send, X } from "lucide-react";

import { useThemeStore } from "../../core/theme/themeStore";
import { cn } from "../utils/cn";

type AssistantMessage = {
  role: "assistant" | "user";
  text: string;
};

type HelpTopic = {
  title: string;
  keywords: string[];
  answer: string;
};

const topics: HelpTopic[] = [
  {
    title: "Generar UML desde imagen",
    keywords: ["foto", "imagen", "image", "uml", "diagrama", "camara", "dibujo", "papel"],
    answer:
      "Para generar un diagrama desde una foto: entra a Proyectos, abre un proyecto, ve a Colaborativo, crea o abre un diagrama UML y usa el boton Imagen a UML. Selecciona la foto y el sistema detectara clases, atributos, metodos y relaciones cuando el patron sea reconocido."
  },
  {
    title: "Generar UML por texto",
    keywords: ["texto", "prompt", "escrito", "ia local", "crear diagrama", "generar diagrama"],
    answer:
      "Para generar por texto: abre un diagrama en Colaborativo, escribe la descripcion en el panel IA local preparada y pulsa Texto. Puedes describir clases, atributos, metodos, relaciones y multiplicidades. Si quieres una clase asociativa, indica que una clase se usa como clase asociativa de una relacion."
  },
  {
    title: "Generar UML por voz",
    keywords: ["voz", "microfono", "hablar", "dictar", "audio"],
    answer:
      "Para generar por voz: abre el editor UML y usa el boton Voz en el panel IA local preparada. Dicta la misma instruccion que escribirias en texto, por ejemplo: crea Estudiante, Curso e Inscripcion como clase asociativa con multiplicidad muchos a muchos."
  },
  {
    title: "Importar o exportar Enterprise Architect",
    keywords: ["enterprise", "architect", "ea", "xml", "xmi", "importar", "exportar"],
    answer:
      "En el editor UML usa Importar XML para cargar archivos XML/XMI de Enterprise Architect. Para llevar el modelo de vuelta a Enterprise Architect usa Exportar XML; el exportador conserva clases, atributos, metodos, relaciones, multiplicidades y association class cuando el modelo contiene esos datos."
  },
  {
    title: "Editar multiplicidad",
    keywords: ["multiplicity", "multiplicidad", "relacion", "linea", "cardinalidad", "1", "0..*", "*"],
    answer:
      "Para editar multiplicidad, haz clic sobre una linea de relacion en el editor UML. Se abre el modal de propiedades de relacion, donde puedes elegir multiplicidad de origen y destino: 1, 0..1, 1..*, 0..*, * u otros valores soportados."
  },
  {
    title: "Generar backend y frontend",
    keywords: ["backend", "frontend", "spring", "flutter", "generacion", "codigo", "descargar zip"],
    answer:
      "Para generar software entra a Generacion. Primero selecciona proyecto, luego diagrama. Transforma el UML a modelo intermedio, genera backend Spring Boot y despues se habilita Flutter. Cada salida puede descargarse como ZIP."
  },
  {
    title: "Base de datos del backend generado",
    keywords: ["postgres", "postgresql", "pgadmin", "base de datos", "docker", "sql"],
    answer:
      "El backend generado incluye configuracion para PostgreSQL y scripts de base de datos. Puedes levantar PostgreSQL con Docker o usar una instancia existente/pgAdmin. Revisa el README y database/init.sql dentro del backend generado."
  },
  {
    title: "Guardar versiones",
    keywords: ["version", "versiones", "historial", "snapshot", "guardar version"],
    answer:
      "El sistema tiene guardado manual de versiones del proyecto desde el espacio colaborativo. Guarda snapshots del estado del proyecto; el versionado automatico por cada cambio de diagrama todavia no es el modo principal."
  },
  {
    title: "Validar UML",
    keywords: ["validar", "validacion", "errores", "advertencias", "recomendaciones"],
    answer:
      "En el editor UML usa Validar para revisar errores, advertencias y recomendaciones del diagrama. La validacion ayuda antes de exportar a Enterprise Architect o generar codigo."
  },
  {
    title: "Flujo recomendado",
    keywords: ["como empiezo", "flujo", "pasos", "usar sistema", "guia", "ayuda"],
    answer:
      "Flujo recomendado: 1. Crea un proyecto. 2. Abre Colaborativo. 3. Crea o importa/genera un diagrama UML. 4. Ajusta clases y relaciones. 5. Valida. 6. Exporta XML o ve a Generacion para producir backend y frontend."
  }
];

const initialMessages: AssistantMessage[] = [
  {
    role: "assistant",
    text: "Hola. Soy el asistente del sistema. Puedes preguntarme donde generar UML desde fotos, como exportar a Enterprise Architect, como generar backend/frontend o como editar multiplicidades."
  }
];

function normalizeQuestion(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function answerQuestion(question: string) {
  const normalized = normalizeQuestion(question);
  const scored = topics
    .map((topic) => ({
      topic,
      score: topic.keywords.reduce((total, keyword) => {
        return total + (normalized.includes(normalizeQuestion(keyword)) ? 1 : 0);
      }, 0)
    }))
    .sort((first, second) => second.score - first.score);
  const best = scored[0];
  if (best && best.score > 0) {
    return best.topic.answer;
  }
  return "No tengo una respuesta exacta para esa consulta todavia. Prueba preguntando por imagen a UML, texto, voz, exportar XML, multiplicidad, generacion Spring Boot/Flutter, PostgreSQL o versiones.";
}

const quickQuestions = [
  "Donde genero diagramas mediante fotos?",
  "Como exporto a Enterprise Architect?",
  "Como genero backend y frontend?",
  "Como edito multiplicidad?"
];

export function AssistantWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<AssistantMessage[]>(initialMessages);
  const isDark = useThemeStore((state) => state.mode === "dark");
  const panelSize = isExpanded ? "h-[640px] w-[520px]" : "h-[520px] w-[380px]";
  const suggestedQuestions = useMemo(() => quickQuestions, []);

  function ask(nextQuestion: string) {
    const trimmed = nextQuestion.trim();
    if (!trimmed) {
      return;
    }
    setMessages((current) => [
      ...current,
      { role: "user", text: trimmed },
      { role: "assistant", text: answerQuestion(trimmed) }
    ]);
    setQuestion("");
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    ask(question);
  }

  return (
    <div className="fixed bottom-5 right-5 z-[70]">
      {isOpen ? (
        <section
          className={cn(
            "flex max-h-[calc(100vh-2.5rem)] flex-col overflow-hidden rounded-lg border shadow-2xl transition-all",
            panelSize,
            isDark ? "border-slate-700 bg-slate-950 text-slate-100" : "border-slate-200 bg-white text-slate-950"
          )}
        >
          <header className={cn("flex items-center justify-between border-b px-4 py-3", isDark ? "border-slate-800" : "border-slate-200")}>
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-white">
                <Bot size={18} aria-hidden="true" />
              </span>
              <div>
                <h2 className="text-sm font-bold">Asistente CASE</h2>
                <p className={cn("text-xs", isDark ? "text-slate-400" : "text-slate-500")}>Manual inteligente</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                className={cn("rounded-md p-2 transition", isDark ? "hover:bg-slate-800" : "hover:bg-slate-100")}
                onClick={() => setIsExpanded((current) => !current)}
                title={isExpanded ? "Reducir asistente" : "Ampliar asistente"}
                type="button"
              >
                {isExpanded ? <Minimize2 size={16} aria-hidden="true" /> : <Maximize2 size={16} aria-hidden="true" />}
              </button>
              <button
                className={cn("rounded-md p-2 transition", isDark ? "hover:bg-slate-800" : "hover:bg-slate-100")}
                onClick={() => setIsOpen(false)}
                title="Cerrar asistente"
                type="button"
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-auto px-4 py-3">
            <div className="grid gap-3">
              {messages.map((message, index) => (
                <div
                  className={cn(
                    "max-w-[88%] rounded-lg px-3 py-2 text-sm leading-5",
                    message.role === "assistant"
                      ? isDark
                        ? "bg-slate-900 text-slate-100"
                        : "bg-slate-100 text-slate-800"
                      : "ml-auto bg-accent text-white"
                  )}
                  key={`${message.role}-${index}-${message.text.slice(0, 16)}`}
                >
                  {message.text}
                </div>
              ))}
            </div>
          </div>

          <div className={cn("border-t p-3", isDark ? "border-slate-800" : "border-slate-200")}>
            <div className="mb-3 flex flex-wrap gap-2">
              {suggestedQuestions.map((item) => (
                <button
                  className={cn(
                    "rounded-md border px-2.5 py-1.5 text-xs font-medium transition",
                    isDark ? "border-slate-700 text-slate-200 hover:bg-slate-800" : "border-slate-200 text-slate-700 hover:bg-slate-50"
                  )}
                  key={item}
                  onClick={() => ask(item)}
                  type="button"
                >
                  {item}
                </button>
              ))}
            </div>
            <form className="flex gap-2" onSubmit={handleSubmit}>
              <input
                className={cn(
                  "h-10 min-w-0 flex-1 rounded-md border px-3 text-sm outline-none transition focus:border-accent focus:ring-2",
                  isDark
                    ? "border-slate-700 bg-slate-900 text-slate-100 placeholder:text-slate-500 focus:ring-teal-900/50"
                    : "border-slate-300 bg-white text-slate-950 placeholder:text-slate-400 focus:ring-teal-100"
                )}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Pregunta sobre el sistema..."
                value={question}
              />
              <button
                className="flex h-10 w-10 items-center justify-center rounded-md bg-accent text-white transition hover:bg-teal-800"
                title="Enviar pregunta"
                type="submit"
              >
                <Send size={16} aria-hidden="true" />
              </button>
            </form>
          </div>
        </section>
      ) : (
        <button
          className="flex h-14 w-14 items-center justify-center rounded-full bg-accent text-white shadow-2xl shadow-teal-950/25 transition hover:bg-teal-800"
          onClick={() => setIsOpen(true)}
          title="Abrir asistente inteligente"
          type="button"
        >
          <MessageCircle size={24} aria-hidden="true" />
          <span className="sr-only">Abrir asistente inteligente</span>
        </button>
      )}
      {!isOpen && (
        <div
          className={cn(
            "pointer-events-none absolute bottom-16 right-0 hidden w-52 rounded-md border px-3 py-2 text-xs shadow-lg sm:block",
            isDark ? "border-slate-700 bg-slate-950 text-slate-200" : "border-slate-200 bg-white text-slate-700"
          )}
        >
          <span className="inline-flex items-center gap-2">
            <HelpCircle size={14} aria-hidden="true" />
            Preguntame como usar el sistema.
          </span>
        </div>
      )}
    </div>
  );
}
