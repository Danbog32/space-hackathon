"use client";

import { useEffect, useRef, useState } from "react";
import OpenSeadragon from "openseadragon";
import { useViewerStore } from "@/store/viewerStore";
import { api } from "@/lib/api";
import type { CreateAnnotation } from "@astro-zoom/proto";
import { useMutation } from "@tanstack/react-query";

interface AnnotatorProps {
  tileSource: string;
  datasetId: string;
}

type AnnotationType = "point" | "rect" | "polygon";

export function Annotator({ tileSource, datasetId }: AnnotatorProps) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const osdRef = useRef<OpenSeadragon.Viewer | null>(null);
  const [annotationType, setAnnotationType] = useState<AnnotationType>("rect");
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [classification, setClassification] = useState<any>(null);
  const [showClassification, setShowClassification] = useState(false);
  const annotations = useViewerStore((state) => state.annotations);
  const addAnnotation = useViewerStore((state) => state.addAnnotation);

  // Classification mutation
  const classifyMutation = useMutation({
    mutationFn: (bbox: [number, number, number, number]) => 
      api.classifyRegion(datasetId, bbox),
    onSuccess: (data) => {
      setClassification(data);
      setShowClassification(true);
      // Auto-hide after 5 seconds
      setTimeout(() => setShowClassification(false), 5000);
    },
  });

  useEffect(() => {
    if (!viewerRef.current || osdRef.current) return;

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

  const handleCanvasClick = async (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!osdRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const viewer = osdRef.current;
    const viewportPoint = viewer.viewport.viewerElementToViewportCoordinates(
      new OpenSeadragon.Point(x, y)
    );
    const imagePoint = viewer.viewport.viewportToImageCoordinates(viewportPoint);

    if (annotationType === "point") {
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
    } else if (annotationType === "rect") {
      if (!isDrawing) {
        setIsDrawing(true);
        setStartPoint({ x: imagePoint.x, y: imagePoint.y });
      } else {
        if (startPoint) {
          const width = Math.abs(imagePoint.x - startPoint.x);
          const height = Math.abs(imagePoint.y - startPoint.y);
          const x = Math.min(imagePoint.x, startPoint.x);
          const y = Math.min(imagePoint.y, startPoint.y);

          const annotationData: CreateAnnotation = {
            datasetId,
            type: "rect",
            geometry: { x, y, width, height },
            label: "Rectangle",
            color: "#ff0000",
          };

          try {
            const created = await api.createAnnotation(annotationData);
            addAnnotation(created);

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
    }
  };

  return (
    <div className="relative h-full w-full">
      <div ref={viewerRef} className="h-full w-full openseadragon-container" />
      <canvas
        ref={canvasRef}
        className="absolute inset-0 pointer-events-auto cursor-crosshair"
        onClick={handleCanvasClick}
      />
      <div className="absolute top-4 left-1/2 -translate-x-1/2 flex gap-2 bg-gray-900/90 p-2 rounded-lg backdrop-blur-sm">
        <button
          onClick={() => setAnnotationType("point")}
          className={`px-4 py-2 rounded ${annotationType === "point" ? "bg-blue-600" : "bg-gray-700"}`}
        >
          Point
        </button>
        <button
          onClick={() => setAnnotationType("rect")}
          className={`px-4 py-2 rounded ${annotationType === "rect" ? "bg-blue-600" : "bg-gray-700"}`}
        >
          Rectangle + AI Classify
        </button>
      </div>

      {/* Classification result popup */}
      {showClassification && classification && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-gray-900/95 p-4 rounded-lg backdrop-blur-sm border border-green-500/50 max-w-sm">
          <div className="flex items-start justify-between mb-2">
            <h4 className="text-sm font-semibold text-green-400">🔬 AI Classification</h4>
            <button
              onClick={() => setShowClassification(false)}
              className="text-gray-400 hover:text-white text-xs"
            >
              ✕
            </button>
          </div>
          <div className="space-y-2">
            <div className="text-sm">
              <span className="text-gray-400">Detected: </span>
              <span className="text-white font-medium">{classification.primary_classification}</span>
            </div>
            <div className="text-sm">
              <span className="text-gray-400">Confidence: </span>
              <span className="text-green-400 font-medium">
                {(classification.confidence * 100).toFixed(1)}%
              </span>
            </div>
            {classification.all_classifications && classification.all_classifications.length > 1 && (
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
