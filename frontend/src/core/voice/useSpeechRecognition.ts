import { useCallback, useEffect, useRef, useState } from "react";

// Web Speech API type declarations for browsers that support it
interface SpeechRecognitionResultItem {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionResultItem;
  [index: number]: SpeechRecognitionResultItem;
}

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message?: string;
}

interface BrowserSpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: ((this: BrowserSpeechRecognition, ev: Event) => void) | null;
  onend: ((this: BrowserSpeechRecognition, ev: Event) => void) | null;
  onerror: ((this: BrowserSpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;
  onresult: ((this: BrowserSpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition?: new () => BrowserSpeechRecognition;
    webkitSpeechRecognition?: new () => BrowserSpeechRecognition;
  }
}

export interface UseSpeechRecognitionOptions {
  lang?: string;
  onFinal?: (text: string) => void;
}

export interface UseSpeechRecognitionReturn {
  supported: boolean;
  listening: boolean;
  interim: string;
  start(): void;
  stop(): void;
  error: string | null;
}

export function useSpeechRecognition(options?: UseSpeechRecognitionOptions): UseSpeechRecognitionReturn {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const onFinalRef = useRef(options?.onFinal);
  onFinalRef.current = options?.onFinal;

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

      recognition.onresult = (event: SpeechRecognitionEvent) => {
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

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
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
    supported,
    listening,
    interim,
    start,
    stop,
    error,
  };
}
