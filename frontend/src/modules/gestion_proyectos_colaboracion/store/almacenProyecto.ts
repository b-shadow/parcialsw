import { create } from "zustand";

import type { Proyecto } from "../types/proyecto";

type ProjectState = {
  activeProject: Proyecto | null;
  setActiveProject: (project: Proyecto | null) => void;
};

export const useAlmacenProyecto = create<ProjectState>((set) => ({
  activeProject: null,
  setActiveProject: (project) => set({ activeProject: project })
}));
