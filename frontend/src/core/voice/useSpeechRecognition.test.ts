/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-this-alias */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useSpeechRecognition } from "./useSpeechRecognition";

describe("useSpeechRecognition (V1.8)", () => {
  const originalSpeechRecognition = window.SpeechRecognition;
  const originalWebkitSpeechRecognition = window.webkitSpeechRecognition;

  beforeEach(() => {
    delete (window as Partial<Window>).SpeechRecognition;
    delete (window as Partial<Window>).webkitSpeechRecognition;
  });

  afterEach(() => {
    window.SpeechRecognition = originalSpeechRecognition;
    window.webkitSpeechRecognition = originalWebkitSpeechRecognition;
  });

  it("Sin SpeechRecognition en window -> supported false", () => {
    const { result } = renderHook(() => useSpeechRecognition());
    expect(result.current.supported).toBe(false);
    expect(result.current.listening).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("Resultado parcial -> actualiza interim", () => {
    let mockInstance: any = null;

    class MockSpeechRecognition {
      continuous = false;
      interimResults = true;
      lang = "es-ES";
      onstart: (() => void) | null = null;
      onresult: ((ev: any) => void) | null = null;
      onerror: ((ev: any) => void) | null = null;
      onend: (() => void) | null = null;

      start() {
        mockInstance = this;
        this.onstart?.();
      }
      stop() {
        this.onend?.();
      }
      abort() {
        this.onend?.();
      }
    }

    window.SpeechRecognition = MockSpeechRecognition as any;

    const { result } = renderHook(() => useSpeechRecognition());
    expect(result.current.supported).toBe(true);

    act(() => {
      result.current.start();
    });

    expect(result.current.listening).toBe(true);

    act(() => {
      mockInstance.onresult({
        resultIndex: 0,
        results: [
          {
            isFinal: false,
            0: { transcript: "crea una clase", confidence: 0.9 },
            length: 1,
          },
        ],
      });
    });

    expect(result.current.interim).toBe("crea una clase");
  });

  it("Evento de resultado final -> llama onFinal con el texto", () => {
    let mockInstance: any = null;
    const onFinal = vi.fn();

    class MockSpeechRecognition {
      continuous = false;
      interimResults = true;
      lang = "es-ES";
      onstart: (() => void) | null = null;
      onresult: ((ev: any) => void) | null = null;
      onerror: ((ev: any) => void) | null = null;
      onend: (() => void) | null = null;

      start() {
        mockInstance = this;
        this.onstart?.();
      }
      stop() {
        this.onend?.();
      }
      abort() {
        this.onend?.();
      }
    }

    window.SpeechRecognition = MockSpeechRecognition as any;

    const { result } = renderHook(() => useSpeechRecognition({ onFinal }));

    act(() => {
      result.current.start();
    });

    act(() => {
      mockInstance.onresult({
        resultIndex: 0,
        results: [
          {
            isFinal: true,
            0: { transcript: "crea una clase Factura", confidence: 0.95 },
            length: 1,
          },
        ],
      });
    });

    expect(onFinal).toHaveBeenCalledWith("crea una clase Factura");
  });

  it("Error 'not-allowed' -> error = 'Permite el micrófono para dictar'", () => {
    let mockInstance: any = null;

    class MockSpeechRecognition {
      onstart: (() => void) | null = null;
      onresult: ((ev: any) => void) | null = null;
      onerror: ((ev: any) => void) | null = null;
      onend: (() => void) | null = null;

      start() {
        mockInstance = this;
        this.onstart?.();
      }
      stop() {
        this.onend?.();
      }
      abort() {
        this.onend?.();
      }
    }

    window.SpeechRecognition = MockSpeechRecognition as any;

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.start();
    });

    act(() => {
      mockInstance.onerror({ error: "not-allowed" });
    });

    expect(result.current.error).toBe("Permite el micrófono para dictar");
    expect(result.current.listening).toBe(false);
  });
});
