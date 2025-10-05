import { create } from "zustand";
import type { Annotation, Overlay, SearchResult } from "@astro-zoom/proto";

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

  overlays: Overlay[];
  setOverlays: (overlays: Overlay[]) => void;
  upsertOverlay: (overlay: Overlay) => void;
  removeOverlay: (overlayId: string) => void;
  activeOverlayId: string | null;
  setActiveOverlayId: (overlayId: string | null) => void;
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

  overlays: [],
  setOverlays: (overlays) => set({ overlays }),
  upsertOverlay: (overlay) =>
    set((state) => {
      const existingIndex = state.overlays.findIndex((item) => item.id === overlay.id);
      if (existingIndex === -1) {
        return { overlays: [...state.overlays, overlay] };
      }
      const updated = [...state.overlays];
      updated.splice(existingIndex, 1, overlay);
      return { overlays: updated };
    }),
  removeOverlay: (overlayId) =>
    set((state) => ({ overlays: state.overlays.filter((overlay) => overlay.id !== overlayId) })),
  activeOverlayId: null,
  setActiveOverlayId: (overlayId) => set({ activeOverlayId: overlayId }),
}));
