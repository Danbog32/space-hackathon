import type { Dataset, Annotation, CreateAnnotation, SearchResponse } from "@astro-zoom/proto";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
  async getDatasets(): Promise<Dataset[]> {
    const res = await fetch(`${API_BASE}/datasets`);
    if (!res.ok) throw new Error("Failed to fetch datasets");
    return res.json();
  },

  async getDataset(id: string): Promise<Dataset> {
    const res = await fetch(`${API_BASE}/datasets/${id}`);
    if (!res.ok) throw new Error("Failed to fetch dataset");
    return res.json();
  },

  async getAnnotations(datasetId: string): Promise<Annotation[]> {
    const res = await fetch(`${API_BASE}/annotations?datasetId=${datasetId}`);
    if (!res.ok) throw new Error("Failed to fetch annotations");
    return res.json();
  },

  async createAnnotation(data: CreateAnnotation): Promise<Annotation> {
    const res = await fetch(`${API_BASE}/annotations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create annotation");
    return res.json();
  },

  async updateAnnotation(id: string, data: Partial<Annotation>): Promise<Annotation> {
    const res = await fetch(`${API_BASE}/annotations/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update annotation");
    return res.json();
  },

  async deleteAnnotation(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/annotations/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete annotation");
  },

  async search(query: string, datasetId: string, topK = 20): Promise<SearchResponse> {
    const res = await fetch(
      `${API_BASE}/search?q=${encodeURIComponent(query)}&datasetId=${datasetId}&topK=${topK}`
    );
    if (!res.ok) throw new Error("Failed to search");
    return res.json();
  },
};
