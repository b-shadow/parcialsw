import { create } from "zustand";

import type { AccionIA, MensajeIA, RecomendacionIA, PresenciaProyecto } from "../../../core/contracts/phase1";
import type { EstadoSocketProyecto } from "../../../core/websocket/socketProyecto";

type ProjectAiState = {
  projectId: string | null;
  conversationId: string | null;
  messages: MensajeIA[];
  actions: AccionIA[];
  recommendations: RecomendacionIA[];
  presence: PresenciaProyecto[];
  projectSequence: number;
  conversationSequence: number;
  socketStatus: EstadoSocketProyecto;
  processing: boolean;
  hasMoreBefore: boolean;
  initialize: (projectId: string, conversationId?: string) => void;
  establecerHistorial: (messages: MensajeIA[], hasMoreBefore: boolean) => void;
  prependHistory: (messages: MensajeIA[], hasMoreBefore: boolean) => void;
  upsertMessage: (message: MensajeIA) => void;
  establecerAcciones: (actions: AccionIA[]) => void;
  upsertAction: (action: AccionIA) => void;
  establecerRecomendaciones: (items: RecomendacionIA[]) => void;
  upsertRecommendation: (item: RecomendacionIA) => void;
  establecerPresencia: (presence: PresenciaProyecto[]) => void;
  upsertPresence: (member: PresenciaProyecto) => void;
  quitarPresencia: (userId: string) => void;
  establecerSecuencias: (projectSequence?: number, conversationSequence?: number) => void;
  establecerEstadoSocket: (status: EstadoSocketProyecto) => void;
  establecerProcesamiento: (processing: boolean) => void;
};

function sortedUnique<T extends { id: string }>(current: T[], incoming: T[], compare: (a: T, b: T) => number) {
  const byId = new Map(current.map((item) => [item.id, item]));
  incoming.forEach((item) => byId.set(item.id, item));
  return [...byId.values()].sort(compare);
}

export function ultimaSecuenciaContinuaMensajes(messages: MensajeIA[]): number {
  const sequences = [...new Set(messages.map((item) => item.sequence_number))].sort((a, b) => a - b);
  if (!sequences.length) return 0;
  let last = sequences[0];
  for (const sequence of sequences.slice(1)) {
    if (sequence !== last + 1) break;
    last = sequence;
  }
  return last;
}

export const useAlmacenIAProyecto = create<ProjectAiState>((set) => ({
  projectId: null,
  conversationId: null,
  messages: [],
  actions: [],
  recommendations: [],
  presence: [],
  projectSequence: 0,
  conversationSequence: 0,
  socketStatus: "disconnected",
  processing: false,
  hasMoreBefore: false,
  initialize: (projectId, conversationId = "legacy") => set((state) =>
    state.projectId === projectId && state.conversationId === conversationId ? state : {
    projectId,
    conversationId,
    messages: [],
    actions: [],
    recommendations: [],
    presence: [],
    projectSequence: 0,
    conversationSequence: 0,
    socketStatus: "disconnected",
    processing: false,
    hasMoreBefore: false
  }),
  establecerHistorial: (messages, hasMoreBefore) => set((state) => {
    const merged = sortedUnique(state.messages, messages, (a, b) => a.sequence_number - b.sequence_number);
    return {
      messages: merged,
      hasMoreBefore,
      conversationSequence: ultimaSecuenciaContinuaMensajes(merged)
    };
  }),
  prependHistory: (messages, hasMoreBefore) => set((state) => ({
    messages: sortedUnique(state.messages, messages, (a, b) => a.sequence_number - b.sequence_number),
    hasMoreBefore
  })),
  upsertMessage: (message) => set((state) => ({
    messages: sortedUnique(state.messages, [message], (a, b) => a.sequence_number - b.sequence_number),
    conversationSequence: ultimaSecuenciaContinuaMensajes(
      sortedUnique(state.messages, [message], (a, b) => a.sequence_number - b.sequence_number)
    )
  })),
  establecerAcciones: (actions) => set({ actions }),
  upsertAction: (action) => set((state) => ({
    actions: sortedUnique(state.actions, [action], (a, b) => b.created_at.localeCompare(a.created_at))
  })),
  establecerRecomendaciones: (recommendations) => set({ recommendations }),
  upsertRecommendation: (item) => set((state) => ({
    recommendations: sortedUnique(
      state.recommendations,
      [item],
      (a, b) => b.created_at.localeCompare(a.created_at)
    )
  })),
  establecerPresencia: (presence) => set({
    presence: [...new Map(presence.map((member) => [member.user_id, member])).values()]
      .sort((a, b) => a.display_name.localeCompare(b.display_name))
  }),
  upsertPresence: (member) => set((state) => ({
    presence: [
      ...state.presence.filter((current) => current.user_id !== member.user_id),
      member
    ].sort((a, b) => a.display_name.localeCompare(b.display_name))
  })),
  quitarPresencia: (userId) => set((state) => ({
    presence: state.presence.filter((member) => member.user_id !== userId)
  })),
  establecerSecuencias: (projectSequence, conversationSequence) => set((state) => ({
    projectSequence: Math.max(state.projectSequence, projectSequence ?? 0),
    conversationSequence: Math.max(state.conversationSequence, conversationSequence ?? 0)
  })),
  establecerEstadoSocket: (socketStatus) => set({ socketStatus }),
  establecerProcesamiento: (processing) => set({ processing })
}));
