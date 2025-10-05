import type {
  Dataset,
  Annotation,
  CreateAnnotation,
  Overlay,
  OverlayStatus,
  OverlayPosition,
  SearchResponse,
} from "@astro-zoom/proto";

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
  async getOverlays(datasetId: string): Promise<Overlay[]> {
    const res = await fetch(`${API_BASE}/overlays?datasetId=${encodeURIComponent(datasetId)}`);
    if (!res.ok) throw new Error("Failed to fetch overlays");
    return res.json();
  },

  async getOverlayStatus(overlayId: string): Promise<OverlayStatus> {
    const res = await fetch(`${API_BASE}/overlays/status/${overlayId}`);
    if (!res.ok) throw new Error("Failed to fetch overlay status");
    return res.json();
  },

  async uploadOverlay(options: {
    file: File;
    datasetId: string;
    name: string;
    opacity?: number;
    visible?: boolean;
    position?: Partial<OverlayPosition>;
    metadata?: Record<string, unknown>;
    onProgress?: (progress: number) => void;
  }): Promise<{ overlayId: string; status: string; message: string; statusUrl?: string }> {
    const { file, datasetId, name, opacity, visible, position, metadata, onProgress } = options;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("dataset_id", datasetId);
    formData.append("name", name);

    if (typeof opacity === "number") formData.append("opacity", opacity.toString());
    if (typeof visible === "boolean") formData.append("visible", String(visible));

    formData.append("position_x", (position?.x ?? 0).toString());
    formData.append("position_y", (position?.y ?? 0).toString());
    formData.append("width", (position?.width ?? 1).toString());
    formData.append("rotation", (position?.rotation ?? 0).toString());

    if (metadata) {
      formData.append("metadata", JSON.stringify(metadata));
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener("progress", (event) => {
        if (!onProgress || !event.lengthComputable) return;
        onProgress((event.loaded / event.total) * 100);
      });

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (error) {
            reject(new Error("Failed to parse overlay upload response"));
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            console.error("Overlay upload error:", xhr.status, error);
            reject(new Error(error.detail || "Overlay upload failed"));
          } catch (error) {
            console.error("Overlay upload failed:", xhr.status, xhr.responseText);
            reject(new Error(`Overlay upload failed with status ${xhr.status}: ${xhr.responseText || 'Unknown error'}`));
          }
        }
      });

      xhr.addEventListener("error", () => {
        reject(new Error("Network error during overlay upload"));
      });

      xhr.open("POST", `${API_BASE}/overlays`);
      xhr.send(formData);
    });
  },

  async updateOverlay(
    overlayId: string,
    update: {
      name?: string;
      opacity?: number;
      visible?: boolean;
      position?: OverlayPosition;
      metadata?: Record<string, unknown> | null;
    }
  ): Promise<Overlay> {
    const res = await fetch(`${API_BASE}/overlays/${overlayId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    });
    if (!res.ok) throw new Error("Failed to update overlay");
    return res.json();
  },

  async createOverlayFromDataset(options: {
    datasetId: string;
    sourceDatasetId: string;
    name?: string;
    opacity?: number;
    visible?: boolean;
    position?: Partial<OverlayPosition>;
    metadata?: Record<string, unknown>;
  }): Promise<Overlay> {
    const {
      datasetId,
      sourceDatasetId,
      name,
      opacity = 1,
      visible = true,
      position,
      metadata,
    } = options;

    const res = await fetch(`${API_BASE}/overlays/from-dataset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        datasetId,
        sourceDatasetId,
        name,
        opacity,
        visible,
        position: {
          x: position?.x ?? 0,
          y: position?.y ?? 0,
          width: position?.width ?? 1,
          rotation: position?.rotation ?? 0,
        },
        metadata,
      }),
    });

    if (!res.ok) {
      let message = "Failed to link overlay dataset";
      try {
        const error = await res.json();
        console.error("Overlay from dataset error:", res.status, error);
        if (error?.detail) {
          message = error.detail;
        }
      } catch (e) {
        console.error("Failed to parse error response:", res.status, e);
        message = `Failed to link overlay dataset (HTTP ${res.status})`;
      }
      throw new Error(message);
    }

    return res.json();
  },

  async deleteOverlay(overlayId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/overlays/${overlayId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete overlay");
  },

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

  async classifyRegion(datasetId: string, bbox: [number, number, number, number]): Promise<any> {
    const bboxStr = bbox.join(",");
    const res = await fetch(`${API_BASE}/classify?datasetId=${datasetId}&bbox=${bboxStr}`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to classify region");
    return res.json();
  },

  async detectObjects(
    query: string,
    datasetId: string,
    confidenceThreshold = 0.6,
    maxResults = 50,
    signal?: AbortSignal
  ): Promise<any> {
    const res = await fetch(
      `${API_BASE}/detect?q=${encodeURIComponent(
        query
      )}&datasetId=${datasetId}&confidence_threshold=${confidenceThreshold}&max_results=${maxResults}`,
      { signal }
    );
    if (!res.ok) throw new Error("Failed to detect objects");
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

  async deleteDataset(datasetId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/uploads/${datasetId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete dataset");
  },
};
