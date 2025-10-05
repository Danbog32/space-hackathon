"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useViewerStore } from "@/store/viewerStore";
import { DeepZoomViewer } from "./DeepZoomViewer";
import { CompareSwipe } from "./CompareSwipe";
import { Annotator } from "./Annotator";
import { ViewerToolbar } from "./ViewerToolbar";
import { ObjectDetector } from "./ObjectDetector";
import { AnnotationsList } from "./AnnotationsList";
import { TimeBar } from "./TimeBar";
import { OverlayManager } from "./OverlayManager";

interface ViewerContainerProps {
  datasetId: string;
}

export function ViewerContainer({ datasetId }: ViewerContainerProps) {
  const mode = useViewerStore((state) => state.mode);
  const kioskMode = useViewerStore((state) => state.kioskMode);
  const setAnnotations = useViewerStore((state) => state.setAnnotations);
  const setOverlays = useViewerStore((state) => state.setOverlays);
  const [aiPanelsVisible, setAiPanelsVisible] = useState(true);

  const {
    data: dataset,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["dataset", datasetId],
    queryFn: () => api.getDataset(datasetId),
  });

  const { data: annotations } = useQuery({
    queryKey: ["annotations", datasetId],
    queryFn: () => api.getAnnotations(datasetId),
  });

  const { data: overlays } = useQuery({
    queryKey: ["overlays", datasetId],
    queryFn: () => api.getOverlays(datasetId),
  });

  useEffect(() => {
    if (annotations) {
      setAnnotations(annotations);
    }
  }, [annotations, setAnnotations]);

  useEffect(() => {
    if (overlays) {
      setOverlays(overlays);
    }
  }, [overlays, setOverlays]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-black">
        <div className="text-center">
          <div className="mb-4 text-6xl">🌌</div>
          <p className="text-xl text-gray-400">Loading dataset...</p>
        </div>
      </div>
    );
  }

  if (error || !dataset) {
    return (
      <div className="flex h-screen items-center justify-center bg-black">
        <div className="text-center">
          <div className="mb-4 text-6xl">⚠️</div>
          <p className="text-xl text-red-400">Failed to load dataset</p>
          <p className="mt-2 text-sm text-gray-500">{(error as Error)?.message}</p>
        </div>
      </div>
    );
  }

  const tileSource = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${dataset.tileUrl}/info.dzi`;

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      {!kioskMode && <ViewerToolbar dataset={dataset} />}

      {mode === "explore" && <DeepZoomViewer tileSource={tileSource} />}
      {mode === "compare" && <CompareSwipe tileSource={tileSource} />}
      {mode === "annotate" && <Annotator tileSource={tileSource} datasetId={datasetId} />}
      {mode === "time" && (
        <>
          <DeepZoomViewer tileSource={tileSource} />
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2">
            <TimeBar
              items={[
                { id: "2023-01", label: "January 2023", timestamp: "2023-01-01" },
                { id: "2023-06", label: "June 2023", timestamp: "2023-06-01" },
                { id: "2024-01", label: "January 2024", timestamp: "2024-01-01" },
              ]}
              selected="2024-01"
              onSelect={(id) => console.log("Selected:", id)}
            />
          </div>
        </>
      )}

      {!kioskMode && (
        <>
          {/* Toggle Button for AI Panels */}
          <button
            onClick={() => setAiPanelsVisible(!aiPanelsVisible)}
            className="absolute left-4 top-20 z-30 bg-gray-900/90 hover:bg-gray-800/90 text-white px-3 py-2 rounded-lg shadow-lg border border-gray-700 transition-all flex items-center gap-2"
            title={aiPanelsVisible ? "Hide AI Panels" : "Show AI Panels"}
          >
            {aiPanelsVisible ? "◀ Hide AI" : "▶ Show AI"}
          </button>

          {aiPanelsVisible && (
            <div className="absolute left-4 top-32 z-20 space-y-4">
              <ObjectDetector datasetId={datasetId} />
            </div>
          )}

          {mode === "annotate" && (
            <div className="absolute right-4 top-20 z-20">
              <AnnotationsList datasetId={datasetId} />
            </div>
          )}

          <div className="absolute right-4 bottom-8 z-20 w-80 max-w-full">
            <OverlayManager datasetId={datasetId} />
          </div>
        </>
      )}
    </div>
  );
}
