"use client";

import { useEffect, useRef } from "react";
import { useViewerStore } from "@/store/viewerStore";

// Dynamic import for OpenSeadragon to avoid SSR issues
let OpenSeadragon: any = null;
if (typeof window !== "undefined") {
  OpenSeadragon = require("openseadragon");
}

interface DeepZoomViewerProps {
  tileSource: string;
}

export function DeepZoomViewer({ tileSource }: DeepZoomViewerProps) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const osdRef = useRef<any>(null);
  const selectedSearchResult = useViewerStore((state) => state.selectedSearchResult);

  useEffect(() => {
    if (!viewerRef.current || osdRef.current || !OpenSeadragon) return;

    osdRef.current = OpenSeadragon({
      element: viewerRef.current,
      prefixUrl: "//openseadragon.github.io/openseadragon/images/",
      tileSources: tileSource,
      showNavigationControl: true,
      navigationControlAnchor: OpenSeadragon.ControlAnchor.BOTTOM_RIGHT,
      animationTime: 0.5,
      blendTime: 0.1,
      constrainDuringPan: true,
      maxZoomPixelRatio: 2,
      minZoomLevel: 0.5,
      visibilityRatio: 1,
      zoomPerScroll: 2,
      timeout: 120000,
    });

    // Keyboard shortcuts
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!osdRef.current) return;
      const viewer = osdRef.current;

      switch (e.key.toLowerCase()) {
        case "f":
          viewer.viewport.goHome();
          break;
        case "g":
          useViewerStore.getState().toggleGrid();
          break;
      }
    };

    window.addEventListener("keypress", handleKeyPress);

    return () => {
      window.removeEventListener("keypress", handleKeyPress);
      if (osdRef.current) {
        osdRef.current.destroy();
        osdRef.current = null;
      }
    };
  }, [tileSource]);

  // Fly to search result when selected
  useEffect(() => {
    if (!osdRef.current || !selectedSearchResult) return;

    const viewer = osdRef.current;
    const bbox = selectedSearchResult.bbox;

    // Convert pixel coordinates to viewport coordinates
    const viewportRect = viewer.viewport.imageToViewportRectangle(
      bbox.x,
      bbox.y,
      bbox.width,
      bbox.height
    );

    viewer.viewport.fitBounds(viewportRect, true);
  }, [selectedSearchResult]);

  return <div ref={viewerRef} className="h-full w-full openseadragon-container" />;
}
