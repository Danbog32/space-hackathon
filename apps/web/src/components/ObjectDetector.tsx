"use client";

import { useState, useRef } from "react";
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
  const boundingBoxOpacity = useViewerStore((state) => state.boundingBoxOpacity);
  const setBoundingBoxOpacity = useViewerStore((state) => state.setBoundingBoxOpacity);
  const [detections, setDetections] = useState<any[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [progress, setProgress] = useState(0);

  const detectMutation = useMutation({
    mutationFn: async (q: string) => {
      // Create new abort controller for this request
      abortControllerRef.current = new AbortController();
      setProgress(0);
      
      // Simulate progress - much slower to match actual AI processing (~750 proposals)
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return 90; // Stop at 90% until complete
          // Slow progress: +1% every 1.5 seconds (takes ~2 minutes to reach 90%)
          return prev + 1;
        });
      }, 1500);
      
      try {
        const result = await api.detectObjects(q, datasetId, confidenceThreshold, 500, abortControllerRef.current.signal);
        clearInterval(progressInterval);
        setProgress(100);
        return result;
      } catch (error) {
        clearInterval(progressInterval);
        setProgress(0);
        throw error;
      }
    },
    onSuccess: (data) => {
      // Convert detections to search results format for viewer display
      const results = data.detections.map((detection: any, idx: number) => {
        // Normalize bbox format: ensure it's {x, y, width, height}
        let normalizedBbox;
        if (Array.isArray(detection.bbox)) {
          // If bbox is array [x, y, w, h], convert to object
          normalizedBbox = {
            x: detection.bbox[0],
            y: detection.bbox[1],
            width: detection.bbox[2],
            height: detection.bbox[3],
          };
        } else {
          // Already an object
          normalizedBbox = detection.bbox;
        }
        
        return {
          ...detection,
          bbox: normalizedBbox,
          rank: idx + 1,
          score: detection.confidence,
        };
      });
      setDetections(results);
      setSearchResults(results);
      setIsOpen(true);
      abortControllerRef.current = null;
    },
    onError: () => {
      abortControllerRef.current = null;
    },
  });

  const handleDetect = (e: React.FormEvent) => {
    e.preventDefault();
    if (objectType.trim()) {
      detectMutation.mutate(objectType);
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setProgress(0);
  };

  const handleClearAll = () => {
    setDetections([]);
    setSearchResults([]);
    selectSearchResult(null);
    setIsOpen(false);
    setProgress(0);
  };

  const commonObjects = [
    // Space objects
    "galaxy", "star", "nebula", "star cluster", "planet", "crater", "solar flare", "comet", "asteroid",
    // Animals
    "dog", "cat", "bird", "horse", "elephant", "bear", "deer",
    // Landmarks & structures
    "building", "house", "tower", "bridge", "monument", "temple", "castle",
    // Infrastructure
    "road", "highway", "river", "lake", "mountain", "forest", "beach",
    // Vehicles
    "car", "truck", "airplane", "ship", "train"
  ];

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

          <div>
            <label className="text-xs text-gray-400 block mb-1">
              Bounding Box Opacity: {(boundingBoxOpacity * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={boundingBoxOpacity}
              onChange={(e) => setBoundingBoxOpacity(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="flex gap-2 items-center">
            {detectMutation.isPending ? (
              <>
                {/* Circular Progress Indicator */}
                <div className="relative w-12 h-12 flex-shrink-0">
                  <svg className="w-full h-full transform -rotate-90">
                    {/* Background circle */}
                    <circle
                      cx="24"
                      cy="24"
                      r="20"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                      className="text-gray-700"
                    />
                    {/* Progress circle */}
                    <circle
                      cx="24"
                      cy="24"
                      r="20"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                      strokeDasharray={`${2 * Math.PI * 20}`}
                      strokeDashoffset={`${2 * Math.PI * 20 * (1 - progress / 100)}`}
                      className="text-green-500 transition-all duration-300"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-semibold text-green-400">
                      {Math.round(progress)}%
                    </span>
                  </div>
                </div>
                <Button
                  type="button"
                  onClick={handleStop}
                  className="flex-1 bg-red-600 hover:bg-red-700"
                >
                  ⏹ Stop
                </Button>
              </>
            ) : (
              <Button type="submit" className="flex-1" disabled={detectMutation.isPending}>
                Detect Objects
              </Button>
            )}
            
            {detections.length > 0 && !detectMutation.isPending && (
              <Button
                type="button"
                onClick={handleClearAll}
                className="bg-gray-700 hover:bg-gray-600"
                title="Clear all detected bounding boxes"
              >
                🗑️ Clear
              </Button>
            )}
          </div>
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
            {detectMutation.error?.message === "canceled" || detectMutation.error?.message.includes("abort")
              ? "Detection stopped by user."
              : "Detection failed. Make sure AI service is running."}
          </div>
        )}

        {detections.length > 0 && !detectMutation.isPending && (
          <div className="mt-3 text-xs text-green-400 flex items-center gap-2">
            ✅ Found {detections.length} detection{detections.length !== 1 ? 's' : ''}
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
                    {detection.bbox.x.toFixed(0)}, {detection.bbox.y.toFixed(0)} •{" "}
                    {detection.bbox.width.toFixed(0)} × {detection.bbox.height.toFixed(0)}
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

