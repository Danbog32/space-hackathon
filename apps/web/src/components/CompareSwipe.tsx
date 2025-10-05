"use client";

import { useEffect, useRef, useState } from "react";

// Dynamic import for OpenSeadragon to avoid SSR issues
let OpenSeadragon: any = null;
if (typeof window !== "undefined") {
  OpenSeadragon = require("openseadragon");
}

interface CompareSwipeProps {
  tileSource: string;
  tileSourceB?: string;
}

export function CompareSwipe({ tileSource, tileSourceB }: CompareSwipeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerARef = useRef<HTMLDivElement>(null);
  const viewerBRef = useRef<HTMLDivElement>(null);
  const osdARef = useRef<any>(null);
  const osdBRef = useRef<any>(null);
  const [dividerPosition, setDividerPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (!viewerARef.current || !viewerBRef.current || !OpenSeadragon) return;

    // Create both viewers
    osdARef.current = OpenSeadragon({
      element: viewerARef.current,
      prefixUrl: "//openseadragon.github.io/openseadragon/images/",
      tileSources: tileSource,
      showNavigationControl: false,
      animationTime: 0.5,
    });

    osdBRef.current = OpenSeadragon({
      element: viewerBRef.current,
      prefixUrl: "//openseadragon.github.io/openseadragon/images/",
      tileSources: tileSourceB || tileSource,
      showNavigationControl: false,
      animationTime: 0.5,
    });

    // Sync zoom and pan between viewers while avoiding recursive updates
    const panSyncing = new WeakMap<OpenSeadragon.Viewer, boolean>();
    const zoomSyncing = new WeakMap<OpenSeadragon.Viewer, boolean>();

    panSyncing.set(osdARef.current, false);
    panSyncing.set(osdBRef.current, false);
    zoomSyncing.set(osdARef.current, false);
    zoomSyncing.set(osdBRef.current, false);

    const syncViewports = (
      sourceViewer: OpenSeadragon.Viewer,
      targetViewer: OpenSeadragon.Viewer
    ) => {
      const handleZoom = () => {
        if (!sourceViewer.viewport || !targetViewer.viewport) return;
        if (zoomSyncing.get(targetViewer)) return;

        zoomSyncing.set(targetViewer, true);
        try {
          const zoom = sourceViewer.viewport.getZoom();
          const refPoint = sourceViewer.viewport.getCenter();
          targetViewer.viewport.zoomTo(zoom, refPoint, true);
        } finally {
          zoomSyncing.set(targetViewer, false);
        }
      };

      const handlePan = () => {
        if (!sourceViewer.viewport || !targetViewer.viewport) return;
        if (panSyncing.get(targetViewer)) return;

        panSyncing.set(targetViewer, true);
        try {
          const center = sourceViewer.viewport.getCenter();
          targetViewer.viewport.panTo(center, true);
        } finally {
          panSyncing.set(targetViewer, false);
        }
      };

      sourceViewer.addHandler("zoom", handleZoom);
      sourceViewer.addHandler("pan", handlePan);

      return () => {
        sourceViewer.removeHandler("zoom", handleZoom);
        sourceViewer.removeHandler("pan", handlePan);
      };
    };

    const cleanupA = syncViewports(osdARef.current, osdBRef.current);
    const cleanupB = syncViewports(osdBRef.current, osdARef.current);

    return () => {
      cleanupA?.();
      cleanupB?.();
      osdARef.current?.destroy();
      osdBRef.current?.destroy();
      osdARef.current = null;
      osdBRef.current = null;
    };
  }, [tileSource, tileSourceB]);

  const handleMouseDown = () => setIsDragging(true);
  const handleMouseUp = () => setIsDragging(false);
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = (x / rect.width) * 100;
    setDividerPosition(Math.max(0, Math.min(100, percentage)));
  };

  return (
    <div
      ref={containerRef}
      className="relative h-full w-full"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div ref={viewerARef} className="absolute inset-0 openseadragon-container" />
      <div
        ref={viewerBRef}
        className="absolute inset-0 openseadragon-container"
        style={{ clipPath: `inset(0 0 0 ${dividerPosition}%)` }}
      />
      <div
        className="absolute top-0 bottom-0 w-1 bg-white cursor-ew-resize z-10"
        style={{ left: `${dividerPosition}%` }}
        onMouseDown={handleMouseDown}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg">
          <svg className="w-5 h-5 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 9l4-4 4 4m0 6l-4 4-4-4"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
