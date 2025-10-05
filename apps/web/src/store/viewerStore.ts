import { create } from "zustand";
import type { Annotation, SearchResult } from "@astro-zoom/proto";

type ViewMode = "explore" | "compare" | "annotate" | "time";

interface ViewerState {
  mode: ViewMode;
  setMode: (mode: ViewMode) => void;

  annotations: Annotation[];
  setAnnotations: (annotations: Annotation[]) => void;
  addAnnotation: (annotation: Annotation) => void;
  updateAnnotation: (id: string, data: Partial<Annotation>) => void;
  removeAnnotation: (id: string) => void;

  searchResults: SearchResult[];
  setSearchResults: (results: SearchResult[]) => void;
  selectedSearchResult: SearchResult | null;
  selectSearchResult: (result: SearchResult | null) => void;

  kioskMode: boolean;
  toggleKioskMode: () => void;

  gridVisible: boolean;
  toggleGrid: () => void;

  showSnippets: boolean;
  toggleShowSnippets: () => void;

  boundingBoxOpacity: number;
  setBoundingBoxOpacity: (opacity: number) => void;
}

export const useViewerStore = create<ViewerState>((set) => ({
  mode: "explore",
  setMode: (mode) => set({ mode }),

  annotations: [],
  setAnnotations: (annotations) => set({ annotations }),
  addAnnotation: (annotation) =>
    set((state) => ({ annotations: [...state.annotations, annotation] })),
  updateAnnotation: (id, data) =>
    set((state) => ({
      annotations: state.annotations.map((a) => (a.id === id ? { ...a, ...data } : a)),
    })),
  removeAnnotation: (id) =>
    set((state) => ({
      annotations: state.annotations.filter((a) => a.id !== id),
    })),

  searchResults: [],
  setSearchResults: (results) => set({ searchResults: results }),
  selectedSearchResult: null,
  selectSearchResult: (result) => set({ selectedSearchResult: result }),

  kioskMode: false,
  toggleKioskMode: () => set((state) => ({ kioskMode: !state.kioskMode })),

  gridVisible: false,
  toggleGrid: () => set((state) => ({ gridVisible: !state.gridVisible })),

  showSnippets: true,
  toggleShowSnippets: () => set((state) => ({ showSnippets: !state.showSnippets })),

  boundingBoxOpacity: 0.4,
  setBoundingBoxOpacity: (opacity) => set({ boundingBoxOpacity: opacity }),
}));
