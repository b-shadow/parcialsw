import { create } from "zustand";

import type { DetalleClaseUML, RelacionUML, ValidacionUML } from "../types/uml";

type UmlState = {
  classes: DetalleClaseUML[];
  relationships: RelacionUML[];
  validation: ValidacionUML | null;
  selectedClassId: string | null;
  establecerClases: (classes: DetalleClaseUML[]) => void;
  agregarClase: (umlClass: DetalleClaseUML) => void;
  actualizarClase: (umlClass: DetalleClaseUML) => void;
  quitarClase: (classId: string) => void;
  establecerRelaciones: (relationships: RelacionUML[]) => void;
  agregarRelacion: (relationship: RelacionUML) => void;
  actualizarRelacion: (relationship: RelacionUML) => void;
  quitarRelacion: (relationshipId: string) => void;
  establecerValidacion: (validation: ValidacionUML | null) => void;
  establecerIdClaseSeleccionada: (classId: string | null) => void;
};

export const useAlmacenUML = create<UmlState>((set) => ({
  classes: [],
  relationships: [],
  validation: null,
  selectedClassId: null,
  establecerClases: (classes) => set({ classes }),
  agregarClase: (umlClass) => set((state) => ({ classes: [...state.classes, umlClass] })),
  actualizarClase: (umlClass) =>
    set((state) => ({ classes: state.classes.map((item) => (item.id === umlClass.id ? umlClass : item)) })),
  quitarClase: (classId) =>
    set((state) => ({
      classes: state.classes.filter((item) => item.id !== classId),
      relationships: state.relationships.filter(
        (item) =>
          item.source_class_id !== classId &&
          item.target_class_id !== classId &&
          item.metadata_json?.association_class_id !== classId
      )
    })),
  establecerRelaciones: (relationships) => set({ relationships }),
  agregarRelacion: (relationship) => set((state) => ({ relationships: [...state.relationships, relationship] })),
  actualizarRelacion: (relationship) =>
    set((state) => ({
      relationships: state.relationships.map((item) => (item.id === relationship.id ? relationship : item))
    })),
  quitarRelacion: (relationshipId) =>
    set((state) => ({ relationships: state.relationships.filter((item) => item.id !== relationshipId) })),
  establecerValidacion: (validation) => set({ validation }),
  establecerIdClaseSeleccionada: (classId) => set({ selectedClassId: classId })
}));
