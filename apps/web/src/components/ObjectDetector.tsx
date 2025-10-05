"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Panel, Input, Button } from "@astro-zoom/ui";
import { api } from "@/lib/api";
import { useViewerStore } from "@/store/viewerStore";

interface ObjectDetectorProps {
  datasetId: string;
}

export function ObjectDetector({ datasetId }: ObjectDetectorProps) {
  const [objectType, setObjectType] = useState("");
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.6);
  const [isOpen, setIsOpen] = useState(false);
  const setSearchResults = useViewerStore((state) => state.setSearchResults);
  const selectSearchResult = useViewerStore((state) => state.selectSearchResult);
  const [detections, setDetections] = useState<any[]>([]);

  const detectMutation = useMutation({
    mutationFn: (q: string) => api.detectObjects(q, datasetId, confidenceThreshold, 50),
    onSuccess: (data) => {
      // Convert detections to search results format for viewer display
      const results = data.detections.map((detection: any, idx: number) => ({
        ...detection,
        rank: idx + 1,
        score: detection.confidence,
      }));
      setDetections(data.detections);
      setSearchResults(results);
      setIsOpen(true);
    },
  });

  const handleDetect = (e: React.FormEvent) => {
    e.preventDefault();
    if (objectType.trim()) {
      detectMutation.mutate(objectType);
    }
  };

  const commonObjects = ["galaxy", "star", "nebula", "star cluster", "planet", "moon crater"];

  return (
    <div className="w-80">
      <Panel className="p-4">
        <form onSubmit={handleDetect} className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold mb-2">🎯 Object Detection</h3>
            <p className="text-xs text-gray-400 mb-3">
              Find ALL instances of a specific object type
            </p>
            <Input
              placeholder="e.g., galaxy, star, nebula"
              value={objectType}
              onChange={(e) => setObjectType(e.target.value)}
            />
          </div>

          <div>
            <label className="text-xs text-gray-400 block mb-1">
              Confidence Threshold: {(confidenceThreshold * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <Button type="submit" className="w-full" disabled={detectMutation.isPending}>
            {detectMutation.isPending ? "Detecting..." : "Detect Objects"}
          </Button>
        </form>

        {/* Quick selection buttons */}
        <div className="mt-3">
          <p className="text-xs text-gray-400 mb-2">Quick select:</p>
          <div className="flex flex-wrap gap-1">
            {commonObjects.map((obj) => (
              <button
                key={obj}
                onClick={() => setObjectType(obj)}
                className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
              >
                {obj}
              </button>
            ))}
          </div>
        </div>

        {detectMutation.isError && (
          <div className="mt-3 text-xs text-red-400">
            Detection failed. Make sure AI service is running.
          </div>
        )}

        {isOpen && detections.length > 0 && (
          <div className="mt-4 max-h-64 overflow-y-auto">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold">
                Found {detections.length} {objectType}(s)
              </h4>
              <button
                onClick={() => setIsOpen(false)}
                className="text-xs text-gray-400 hover:text-white"
              >
                Hide
              </button>
            </div>
            <div className="space-y-2">
              {detections.map((detection, idx) => (
                <button
                  key={idx}
                  onClick={() => selectSearchResult(detection)}
                  className="w-full text-left p-2 rounded bg-gray-800 hover:bg-gray-700 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <span className="text-xs text-gray-400">Detection {idx + 1}</span>
                    <span className="text-xs text-green-400">
                      {(detection.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {detection.bbox[0].toFixed(0)}, {detection.bbox[1].toFixed(0)} •{" "}
                    {detection.bbox[2].toFixed(0)} × {detection.bbox[3].toFixed(0)}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}

