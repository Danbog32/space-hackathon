"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Panel, Button } from "@astro-zoom/ui";
import { useViewerStore } from "@/store/viewerStore";
import { api } from "@/lib/api";

interface AnnotationsListProps {
  datasetId: string;
}

export function AnnotationsList({ datasetId }: AnnotationsListProps) {
  const annotations = useViewerStore((state) => state.annotations);
  const removeAnnotation = useViewerStore((state) => state.removeAnnotation);
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteAnnotation(id),
    onSuccess: (_, id) => {
      removeAnnotation(id);
      queryClient.invalidateQueries({ queryKey: ["annotations", datasetId] });
    },
  });

  return (
    <Panel title="Annotations" className="w-80 max-h-[calc(100vh-6rem)] overflow-y-auto">
      {annotations.length === 0 ? (
        <p className="text-sm text-gray-500">
          No annotations yet. Click on the image to create one.
        </p>
      ) : (
        <div className="space-y-2">
          {annotations.map((annotation) => (
            <div key={annotation.id} className="p-3 rounded bg-gray-800 border border-gray-700">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: annotation.color || "#ff0000" }}
                  />
                  <span className="text-sm font-medium">{annotation.label || "Untitled"}</span>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(annotation.id)}
                  className="text-xs text-red-400 hover:text-red-300"
                  disabled={deleteMutation.isPending}
                >
                  Delete
                </button>
              </div>

              {annotation.description && (
                <p className="text-xs text-gray-400 mb-2">{annotation.description}</p>
              )}

              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="px-2 py-0.5 rounded bg-gray-900">{annotation.type}</span>
                {annotation.userId && (
                  <span className="px-2 py-0.5 rounded bg-gray-900">{annotation.userId}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
