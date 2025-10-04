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
  const showSnippets = useViewerStore((state) => state.showSnippets);
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
          {annotations.map((annotation) => {
            // Debug: Log annotation metadata
            if (annotation.metadata) {
              console.log('Annotation', annotation.id, 'metadata:', annotation.metadata);
              console.log('Has snippet_preview:', !!annotation.metadata.snippet_preview);
            }
            return (
            <div key={annotation.id} className="p-3 rounded bg-gray-800 border border-gray-700">
              {/* Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded flex-shrink-0"
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

              {/* Description */}
              {annotation.description && (
                <p className="text-xs text-gray-400 mb-2">{annotation.description}</p>
              )}

              {/* Tags Row */}
              <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                <span className="px-2 py-0.5 rounded bg-gray-900">{annotation.type}</span>
                {annotation.metadata?.confidence && (
                  <span className="px-2 py-0.5 rounded bg-green-900/30 text-green-400">
                    {(annotation.metadata.confidence as number * 100).toFixed(0)}%
                  </span>
                )}
                {annotation.userId && (
                  <span className="px-2 py-0.5 rounded bg-gray-900">{annotation.userId}</span>
                )}
              </div>

              {/* Thumbnail Preview - BELOW tags - Only shown when toggle is ON */}
              {showSnippets && (
                annotation.metadata?.snippet_preview ? (
                  <div className="mt-2">
                    <img 
                      src={annotation.metadata.snippet_preview as string}
                      alt={annotation.label || "Annotation"}
                      className="w-full max-w-[200px] rounded border border-gray-600"
                      title={`${annotation.label} (${annotation.metadata.snippet_size})`}
                    />
                    {annotation.metadata.snippet_size && (
                      <p className="text-xs text-gray-500 mt-1">
                        Size: {annotation.metadata.snippet_size as string}
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="mt-2 text-xs text-gray-500 italic">
                    No snippet preview available
                  </div>
                )
              )}
            </div>
            );
          })}
        </div>
      )}
    </Panel>
  );
}
