import { useCallback, useEffect, useRef, useState } from "react";

// Tipos para la API de reconocimiento de voz del navegador.
interface ElementoResultadoVoz {
  transcript: string;
  confidence: number;
}

interface ListaResultadosVoz {
  length: number;
  item(index: number): ResultadoVoz;
  [index: number]: ResultadoVoz;
}

interface ResultadoVoz {
  isFinal: boolean;
  length: number;
  item(index: number): ElementoResultadoVoz;
  [index: number]: ElementoResultadoVoz;
}

interface EventoResultadoVoz {
  resultIndex: number;
  results: ListaResultadosVoz;
}

interface EventoErrorVoz {
  error: string;
  message?: string;
}

interface ReconocimientoVozNavegador extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: ((this: ReconocimientoVozNavegador, ev: Event) => void) | null;
  onend: ((this: ReconocimientoVozNavegador, ev: Event) => void) | null;
  onerror: ((this: ReconocimientoVozNavegador, ev: EventoErrorVoz) => void) | null;
  onresult: ((this: ReconocimientoVozNavegador, ev: EventoResultadoVoz) => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition?: new () => ReconocimientoVozNavegador;
    webkitSpeechRecognition?: new () => ReconocimientoVozNavegador;
  }
}

export interface OpcionesReconocimientoVoz {
  lang?: string;
  alFinalizar?: (text: string) => void;
}

export interface ResultadoReconocimientoVoz {
  disponible: boolean;
  escuchando: boolean;
  transcripcionParcial: string;
  iniciar(): void;
  detener(): void;
  error: string | null;
}

export function useReconocimientoVoz(options?: OpcionesReconocimientoVoz): ResultadoReconocimientoVoz {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<ReconocimientoVozNavegador | null>(null);
  const onFinalRef = useRef(options?.alFinalizar);
  onFinalRef.current = options?.alFinalizar;

  const supported = typeof window !== "undefined" && Boolean(
    window.SpeechRecognition || window.webkitSpeechRecognition
  );

  const stop = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Recognition might already be stopped
      }
      recognitionRef.current = null;
    }
    setListening(false);
    setInterim("");
  }, []);

  const start = useCallback(() => {
    if (!supported) return;

    // If already running, stop previous
    if (recognitionRef.current) {
      stop();
    }

    setError(null);
    setInterim("");

    try {
      const SpeechRecognitionConstructor = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognitionConstructor) return;

      const recognition = new SpeechRecognitionConstructor();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = options?.lang ?? "es-ES";

      recognition.onstart = () => {
        setListening(true);
        setError(null);
      };

      recognition.onresult = (event: EventoResultadoVoz) => {
        let finalChunk = "";
        let interimChunk = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i];
          const transcript = res[0]?.transcript ?? "";
          if (res.isFinal) {
            finalChunk += transcript;
          } else {
            interimChunk += transcript;
          }
        }

        setInterim(interimChunk);

        if (finalChunk.trim()) {
          onFinalRef.current?.(finalChunk.trim());
        }
      };

      recognition.onerror = (event: EventoErrorVoz) => {
        if (event.error === "not-allowed") {
          setError("Permite el micrófono para dictar");
        } else if (event.error === "no-speech") {
          setError("No se detectó voz");
        } else {
          setError(`Error de micrófono: ${event.error}`);
        }
        setListening(false);
      };

      recognition.onend = () => {
        setListening(false);
        setInterim("");
        recognitionRef.current = null;
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      setError("No se pudo iniciar el micrófono");
      setListening(false);
    }
  }, [options?.lang, stop, supported]);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
        recognitionRef.current = null;
      }
    };
  }, []);

  return {
    disponible: supported,
    escuchando: listening,
    transcripcionParcial: interim,
    iniciar: start,
    detener: stop,
    error,
  };
}
