import { create } from "zustand";

import type { DetalleClaseUML, RelacionUML, ValidacionUML } from "../types/uml";

type UmlState = {
  classes: DetalleClaseUML[];
  relationships: RelacionUML[];
  validation: ValidacionUML | null;
  selectedClassId: string | null;
  setClasses: (classes: DetalleClaseUML[]) => void;
  addClass: (umlClass: DetalleClaseUML) => void;
  updateClass: (umlClass: DetalleClaseUML) => void;
  removeClass: (classId: string) => void;
  setRelationships: (relationships: RelacionUML[]) => void;
  addRelationship: (relationship: RelacionUML) => void;
  updateRelationship: (relationship: RelacionUML) => void;
  removeRelationship: (relationshipId: string) => void;
  setValidation: (validation: ValidacionUML | null) => void;
  setSelectedClassId: (classId: string | null) => void;
};

export const useAlmacenUML = create<UmlState>((set) => ({
  classes: [],
  relationships: [],
  validation: null,
  selectedClassId: null,
  setClasses: (classes) => set({ classes }),
  addClass: (umlClass) => set((state) => ({ classes: [...state.classes, umlClass] })),
  updateClass: (umlClass) =>
    set((state) => ({ classes: state.classes.map((item) => (item.id === umlClass.id ? umlClass : item)) })),
  removeClass: (classId) =>
    set((state) => ({
      classes: state.classes.filter((item) => item.id !== classId),
      relationships: state.relationships.filter(
        (item) =>
          item.source_class_id !== classId &&
          item.target_class_id !== classId &&
          item.metadata_json?.association_class_id !== classId
      )
    })),
  setRelationships: (relationships) => set({ relationships }),
  addRelationship: (relationship) => set((state) => ({ relationships: [...state.relationships, relationship] })),
  updateRelationship: (relationship) =>
    set((state) => ({
      relationships: state.relationships.map((item) => (item.id === relationship.id ? relationship : item))
    })),
  removeRelationship: (relationshipId) =>
    set((state) => ({ relationships: state.relationships.filter((item) => item.id !== relationshipId) })),
  setValidation: (validation) => set({ validation }),
  setSelectedClassId: (classId) => set({ selectedClassId: classId })
}));
