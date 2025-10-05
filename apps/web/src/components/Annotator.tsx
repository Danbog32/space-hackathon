"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useViewerStore } from "@/store/viewerStore";

// Dynamic import for OpenSeadragon to avoid SSR issues
let OpenSeadragon: any = null;
if (typeof window !== "undefined") {
  OpenSeadragon = require("openseadragon");
}
import { api } from "@/lib/api";
import type { CreateAnnotation } from "@astro-zoom/proto";
import { useMutation } from "@tanstack/react-query";

interface AnnotatorProps {
  tileSource: string;
  datasetId: string;
}

type AnnotationType = "point" | "rect" | "polygon";
type InteractionMode = "navigate" | AnnotationType;

export function Annotator({ tileSource, datasetId }: AnnotatorProps) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const osdRef = useRef<any>(null);
  const [interactionMode, setInteractionMode] = useState<InteractionMode>("navigate");
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [classification, setClassification] = useState<any>(null);
  const [showClassification, setShowClassification] = useState(false);
  const [currentAnnotationId, setCurrentAnnotationId] = useState<string | null>(null);
  const annotations = useViewerStore((state) => state.annotations);
  const addAnnotation = useViewerStore((state) => state.addAnnotation);
  const updateAnnotation = useViewerStore((state) => state.updateAnnotation);

  // Classification mutation
  const classifyMutation = useMutation({
    mutationFn: (bbox: [number, number, number, number]) => api.classifyRegion(datasetId, bbox),
    onSuccess: async (data) => {
      console.log("🎉 Raw classification response:", data);
      console.log("🎉 All keys in response:", Object.keys(data));

      setClassification(data);
      setShowClassification(true);

      // Update the annotation label with the classification result
      if (currentAnnotationId && data.primary_classification) {
        try {
          // Debug: Log what we're sending
          console.log("🔍 Classification data received:", {
            has_snippet_preview: !!data.snippet_preview,
            snippet_preview_length: data.snippet_preview?.length || 0,
            snippet_size: data.snippet_size,
            confidence: data.confidence,
            model: data.model,
          });

          const metadata = {
            snippet_preview: data.snippet_preview,
            snippet_size: data.snippet_size,
            confidence: data.confidence,
            model: data.model,
          };

          console.log("📤 Sending update with metadata:", {
            ...metadata,
            snippet_preview: metadata.snippet_preview
              ? `[${metadata.snippet_preview.substring(0, 50)}...]`
              : "MISSING",
          });

          const updatedAnnotation = await api.updateAnnotation(currentAnnotationId, {
            label: data.primary_classification,
            description: `AI Classified: ${(data.confidence * 100).toFixed(1)}% confidence`,
            metadata,
          });

          console.log("✅ Update response:", {
            has_metadata: !!updatedAnnotation.metadata,
            metadata_keys: updatedAnnotation.metadata
              ? Object.keys(updatedAnnotation.metadata)
              : [],
          });

          updateAnnotation(currentAnnotationId, updatedAnnotation);
        } catch (error) {
          console.error("Failed to update annotation label:", error);
        }
      }

      // Auto-hide after 5 seconds
      setTimeout(() => setShowClassification(false), 5000);
    },
  });

  useEffect(() => {
    if (!viewerRef.current || osdRef.current || !OpenSeadragon) return;

    osdRef.current = OpenSeadragon({
      element: viewerRef.current,
      prefixUrl: "//openseadragon.github.io/openseadragon/images/",
      tileSources: tileSource,
      showNavigationControl: true,
      navigationControlAnchor: OpenSeadragon.ControlAnchor.BOTTOM_RIGHT,
    });

    return () => {
      if (osdRef.current) {
        osdRef.current.destroy();
        osdRef.current = null;
      }
    };
  }, [tileSource]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !osdRef.current) return;

    const viewer = osdRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Resize canvas to match viewer
    const resize = () => {
      const container = viewer.container;
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    };

    resize();
    window.addEventListener("resize", resize);

    // Draw annotations
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      annotations.forEach((annotation) => {
        const geom = annotation.geometry as any;

        if (annotation.type === "rect") {
          const viewportRect = viewer.viewport.imageToViewportRectangle(
            geom.x,
            geom.y,
            geom.width,
            geom.height
          );
          const pixelRect = viewer.viewport.viewportToViewerElementRectangle(viewportRect);

          ctx.strokeStyle = annotation.color || "#ff0000";
          ctx.lineWidth = 2;
          ctx.strokeRect(pixelRect.x, pixelRect.y, pixelRect.width, pixelRect.height);

          if (annotation.label) {
            ctx.fillStyle = annotation.color || "#ff0000";
            ctx.font = "12px sans-serif";
            ctx.fillText(annotation.label, pixelRect.x, pixelRect.y - 5);
          }
        } else if (annotation.type === "point") {
          const viewportPoint = viewer.viewport.imageToViewportCoordinates(geom.x, geom.y);
          const pixelPoint = viewer.viewport.viewportToViewerElementCoordinates(viewportPoint);

          ctx.fillStyle = annotation.color || "#ff0000";
          ctx.beginPath();
          ctx.arc(pixelPoint.x, pixelPoint.y, 5, 0, 2 * Math.PI);
          ctx.fill();

          if (annotation.label) {
            ctx.fillStyle = annotation.color || "#ff0000";
            ctx.font = "12px sans-serif";
            ctx.fillText(annotation.label, pixelPoint.x + 10, pixelPoint.y);
          }
        }
      });

      requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener("resize", resize);
    };
  }, [annotations]);

  useEffect(() => {
    if (interactionMode !== "rect") {
      setIsDrawing(false);
      setStartPoint(null);
    }
  }, [interactionMode]);

  const handleAnnotationClick = useCallback(
    async (imagePoint: { x: number; y: number }) => {
      if (interactionMode === "navigate") {
        return;
      }

      if (interactionMode === "point") {
        const annotationData: CreateAnnotation = {
          datasetId,
          type: "point",
          geometry: { x: imagePoint.x, y: imagePoint.y },
          label: "Point",
          color: "#00ff00",
        };

        try {
          const created = await api.createAnnotation(annotationData);
          addAnnotation(created);
        } catch (error) {
          console.error("Failed to create annotation:", error);
        }
      } else if (interactionMode === "rect") {
        if (!isDrawing) {
          setIsDrawing(true);
          setStartPoint({ x: imagePoint.x, y: imagePoint.y });
        } else if (startPoint) {
          const width = Math.abs(imagePoint.x - startPoint.x);
          const height = Math.abs(imagePoint.y - startPoint.y);
          const x = Math.min(imagePoint.x, startPoint.x);
          const y = Math.min(imagePoint.y, startPoint.y);

          const annotationData: CreateAnnotation = {
            datasetId,
            type: "rect",
            geometry: { x, y, width, height },
            label: "Classifying...",
            color: "#ff0000",
          };

          try {
            const created = await api.createAnnotation(annotationData);
            addAnnotation(created);

            // Store the annotation ID so we can update it with the classification
            setCurrentAnnotationId(created.id);

            // Automatically classify the region
            classifyMutation.mutate([
              Math.round(x),
              Math.round(y),
              Math.round(width),
              Math.round(height),
            ]);
          } catch (error) {
            console.error("Failed to create annotation:", error);
          }

          setIsDrawing(false);
          setStartPoint(null);
        }
      }
    },
    [addAnnotation, interactionMode, classifyMutation, datasetId, isDrawing, startPoint]
  );

  useEffect(() => {
    if (!osdRef.current || !handleAnnotationClick) return;

    const viewer = osdRef.current;

    const handleCanvasClick = (event: any) => {
      if (!event?.position) return;

      const button = event.originalEvent?.button;
      if (typeof button === "number" && button !== 0) {
        return;
      }

      const viewportPoint = viewer.viewport.pointFromPixel(event.position);
      const imagePoint = viewer.viewport.viewportToImageCoordinates(viewportPoint);

      handleAnnotationClick(imagePoint);
    };

    viewer.addHandler("canvas-click", handleCanvasClick);

    return () => {
      viewer.removeHandler("canvas-click", handleCanvasClick);
    };
  }, [handleAnnotationClick]);

  useEffect(() => {
    const viewer = osdRef.current;
    if (!viewer) return;

    const isNavigating = interactionMode === "navigate";

    if (typeof viewer.setMouseNavEnabled === "function") {
      viewer.setMouseNavEnabled(true);
    }

    if (viewer.gestureSettingsMouse) {
      viewer.gestureSettingsMouse.clickToZoom = isNavigating;
      viewer.gestureSettingsMouse.dblClickToZoom = isNavigating;
      viewer.gestureSettingsMouse.dragToPan = isNavigating;
      viewer.gestureSettingsMouse.scrollToZoom = isNavigating;
    }

    if (viewer.gestureSettingsTouch) {
      viewer.gestureSettingsTouch.pinchToZoom = isNavigating;
      viewer.gestureSettingsTouch.dragToPan = isNavigating;
    }
  }, [interactionMode]);

  return (
    <div className="relative h-full w-full">
      <div
        ref={viewerRef}
        className={`h-full w-full openseadragon-container ${
          interactionMode === "navigate" ? "cursor-grab" : "cursor-crosshair"
        }`}
      />
      <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none" />
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 bg-gray-900/90 p-2 rounded-lg backdrop-blur-sm">
        <button
          onClick={() => setInteractionMode("navigate")}
          className={`px-4 py-2 rounded ${
            interactionMode === "navigate" ? "bg-blue-600" : "bg-gray-700"
          }`}
        >
          Pan / Zoom
        </button>
        <button
          onClick={() => setInteractionMode("point")}
          className={`px-4 py-2 rounded ${
            interactionMode === "point" ? "bg-blue-600" : "bg-gray-700"
          }`}
        >
          Point
        </button>
        <button
          onClick={() => setInteractionMode("rect")}
          className={`px-4 py-2 rounded ${
            interactionMode === "rect" ? "bg-blue-600" : "bg-gray-700"
          }`}
        >
          Rectangle + AI Classify
        </button>
      </div>

      {/* Classification result popup */}
      {showClassification && classification && (
        <div className="absolute bottom-4 left-2 bg-gray-900/95 p-4 rounded-lg backdrop-blur-sm border border-green-500/50 max-w-md">
          <div className="flex items-start justify-between mb-3">
            <h4 className="text-sm font-semibold text-green-400">🔬 AI Classification</h4>
            <button
              onClick={() => setShowClassification(false)}
              className="text-gray-400 hover:text-white text-xs"
            >
              ✕
            </button>
          </div>

          {/* High-quality snippet preview */}
          {classification.snippet_preview && (
            <div className="mb-3">
              <div className="text-xs text-gray-400 mb-1">
                What CLIP analyzed ({classification.snippet_size}):
              </div>
              <img
                src={classification.snippet_preview}
                alt="Analyzed region"
                className="w-full rounded border border-gray-700"
              />
              {classification.source_info && (
                <div className="text-xs text-gray-500 mt-1">
                  Source: {classification.source_info}
                </div>
              )}
            </div>
          )}

          <div className="space-y-2">
            <div className="text-sm">
              <span className="text-gray-400">Detected: </span>
              <span className="text-white font-medium">
                {classification.primary_classification}
              </span>
            </div>
            <div className="text-sm">
              <span className="text-gray-400">Confidence: </span>
              <span className="text-green-400 font-medium">
                {(classification.confidence * 100).toFixed(1)}%
              </span>
            </div>
            {classification.model && (
              <div className="text-xs text-gray-500">Model: {classification.model}</div>
            )}
            {classification.all_classifications &&
              classification.all_classifications.length > 1 && (
                <div className="text-xs text-gray-400 mt-2 pt-2 border-t border-gray-700">
                  <div>Other possibilities:</div>
                  {classification.all_classifications.slice(1, 4).map((cls: any, idx: number) => (
                    <div key={idx} className="flex justify-between mt-1">
                      <span>{cls.type}</span>
                      <span>{(cls.confidence * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
          </div>
        </div>
      )}
    </div>
  );
}
