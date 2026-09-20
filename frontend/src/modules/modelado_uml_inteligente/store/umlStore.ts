import { create } from "zustand";

import type { UmlClassDetail, UmlRelationship, UmlValidation } from "../types/uml";

type UmlState = {
  classes: UmlClassDetail[];
  relationships: UmlRelationship[];
  validation: UmlValidation | null;
  selectedClassId: string | null;
  setClasses: (classes: UmlClassDetail[]) => void;
  addClass: (umlClass: UmlClassDetail) => void;
  updateClass: (umlClass: UmlClassDetail) => void;
  removeClass: (classId: string) => void;
  setRelationships: (relationships: UmlRelationship[]) => void;
  addRelationship: (relationship: UmlRelationship) => void;
  updateRelationship: (relationship: UmlRelationship) => void;
  removeRelationship: (relationshipId: string) => void;
  setValidation: (validation: UmlValidation | null) => void;
  setSelectedClassId: (classId: string | null) => void;
};

export const useUmlStore = create<UmlState>((set) => ({
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
