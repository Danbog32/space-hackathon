import type { Dataset, Annotation, CreateAnnotation, SearchResponse } from "@astro-zoom/proto";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UploadResponse {
  datasetId: string;
  status: string;
  message: string;
  statusUrl?: string;
  timestamp: string;
}

export interface ProcessingStatus {
  datasetId: string;
  status: "queued" | "processing" | "complete" | "error";
  progress: number;
  message: string;
  timestamp: string;
  result?: {
    width: number;
    height: number;
    levels: number;
    totalTiles: number;
  };
}

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

  async uploadImage(
    file: File,
    name: string,
    description?: string,
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", name);
    if (description) {
      formData.append("description", description);
    }

    // Use XMLHttpRequest for upload progress tracking
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = (e.loaded / e.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            reject(new Error("Failed to parse response"));
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.detail || "Upload failed"));
          } catch (e) {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        }
      });

      xhr.addEventListener("error", () => {
        reject(new Error("Network error during upload"));
      });

      xhr.open("POST", `${API_BASE}/uploads/upload`);
      xhr.send(formData);
    });
  },

  async getProcessingStatus(datasetId: string): Promise<ProcessingStatus> {
    const res = await fetch(`${API_BASE}/uploads/status/${datasetId}`);
    if (!res.ok) {
      if (res.status === 404) {
        throw new Error("Processing status not found");
      }
      throw new Error("Failed to fetch processing status");
    }
    return res.json();
  },

  async deleteDataset(datasetId: string): Promise<{ warnings?: string[] }> {
    const res = await fetch(`${API_BASE}/uploads/${datasetId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete dataset");
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return res.json();
    }
    return {};
  },
};
