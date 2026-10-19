import { create } from "zustand";

import type { AiAction, AiMessage, AiRecommendation, ProjectPresence } from "../../../core/contracts/phase1";
import type { ProjectSocketStatus } from "../../../core/websocket/projectSocket";

type ProjectAiState = {
  projectId: string | null;
  conversationId: string | null;
  messages: AiMessage[];
  actions: AiAction[];
  recommendations: AiRecommendation[];
  presence: ProjectPresence[];
  projectSequence: number;
  conversationSequence: number;
  socketStatus: ProjectSocketStatus;
  processing: boolean;
  hasMoreBefore: boolean;
  initialize: (projectId: string, conversationId?: string) => void;
  setHistory: (messages: AiMessage[], hasMoreBefore: boolean) => void;
  prependHistory: (messages: AiMessage[], hasMoreBefore: boolean) => void;
  upsertMessage: (message: AiMessage) => void;
  setActions: (actions: AiAction[]) => void;
  upsertAction: (action: AiAction) => void;
  setRecommendations: (items: AiRecommendation[]) => void;
  upsertRecommendation: (item: AiRecommendation) => void;
  setPresence: (presence: ProjectPresence[]) => void;
  upsertPresence: (member: ProjectPresence) => void;
  removePresence: (userId: string) => void;
  setSequences: (projectSequence?: number, conversationSequence?: number) => void;
  setSocketStatus: (status: ProjectSocketStatus) => void;
  setProcessing: (processing: boolean) => void;
};

function sortedUnique<T extends { id: string }>(current: T[], incoming: T[], compare: (a: T, b: T) => number) {
  const byId = new Map(current.map((item) => [item.id, item]));
  incoming.forEach((item) => byId.set(item.id, item));
  return [...byId.values()].sort(compare);
}

export const useProjectAiStore = create<ProjectAiState>((set) => ({
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
  setHistory: (messages, hasMoreBefore) => set({
    messages: sortedUnique([], messages, (a, b) => a.sequence_number - b.sequence_number),
    hasMoreBefore,
    conversationSequence: Math.max(0, ...messages.map((item) => item.sequence_number))
  }),
  prependHistory: (messages, hasMoreBefore) => set((state) => ({
    messages: sortedUnique(state.messages, messages, (a, b) => a.sequence_number - b.sequence_number),
    hasMoreBefore
  })),
  upsertMessage: (message) => set((state) => ({
    messages: sortedUnique(state.messages, [message], (a, b) => a.sequence_number - b.sequence_number),
    conversationSequence: Math.max(state.conversationSequence, message.sequence_number)
  })),
  setActions: (actions) => set({ actions }),
  upsertAction: (action) => set((state) => ({
    actions: sortedUnique(state.actions, [action], (a, b) => b.created_at.localeCompare(a.created_at))
  })),
  setRecommendations: (recommendations) => set({ recommendations }),
  upsertRecommendation: (item) => set((state) => ({
    recommendations: sortedUnique(
      state.recommendations,
      [item],
      (a, b) => b.created_at.localeCompare(a.created_at)
    )
  })),
  setPresence: (presence) => set({
    presence: [...new Map(presence.map((member) => [member.user_id, member])).values()]
      .sort((a, b) => a.display_name.localeCompare(b.display_name))
  }),
  upsertPresence: (member) => set((state) => ({
    presence: [
      ...state.presence.filter((current) => current.user_id !== member.user_id),
      member
    ].sort((a, b) => a.display_name.localeCompare(b.display_name))
  })),
  removePresence: (userId) => set((state) => ({
    presence: state.presence.filter((member) => member.user_id !== userId)
  })),
  setSequences: (projectSequence, conversationSequence) => set((state) => ({
    projectSequence: Math.max(state.projectSequence, projectSequence ?? 0),
    conversationSequence: Math.max(state.conversationSequence, conversationSequence ?? 0)
  })),
  setSocketStatus: (socketStatus) => set({ socketStatus }),
  setProcessing: (processing) => set({ processing })
}));
