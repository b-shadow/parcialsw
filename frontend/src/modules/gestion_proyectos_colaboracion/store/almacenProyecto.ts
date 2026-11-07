import { create } from "zustand";

import type { Proyecto } from "../types/proyecto";

type ProjectState = {
  activeProject: Proyecto | null;
  establecerProyectoActivo: (project: Proyecto | null) => void;
};

export const useAlmacenProyecto = create<ProjectState>((set) => ({
  activeProject: null,
  establecerProyectoActivo: (project) => set({ activeProject: project })
}));
