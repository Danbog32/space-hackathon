"use client";

import { useEffect, useRef, useState } from "react";
import { useViewerStore } from "@/store/viewerStore";

interface DeepZoomViewerProps {
  tileSource: string;
}

export function DeepZoomViewer({ tileSource }: DeepZoomViewerProps) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const osdRef = useRef<any>(null);
  const selectedSearchResult = useViewerStore((state) => state.selectedSearchResult);
  const [isClient, setIsClient] = useState(false);

  // Ensure we're on the client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!isClient || !viewerRef.current || osdRef.current) return;

    // Dynamically import OpenSeadragon only on client side
    import("openseadragon").then((OpenSeadragon) => {
      osdRef.current = OpenSeadragon.default({
        element: viewerRef.current,
        prefixUrl: "//openseadragon.github.io/openseadragon/images/",
        tileSources: tileSource,
        showNavigationControl: true,
        navigationControlAnchor: OpenSeadragon.default.ControlAnchor.BOTTOM_RIGHT,
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

      // Add error handling
      osdRef.current.addHandler("open-failed", (event: any) => {
        console.error("OpenSeadragon failed to open:", event);
      });

      osdRef.current.addHandler("tile-load-failed", (event: any) => {
        console.error("Tile load failed:", event);
      });

      return () => {
        window.removeEventListener("keypress", handleKeyPress);
        if (osdRef.current) {
          osdRef.current.destroy();
          osdRef.current = null;
        }
      };
    }).catch((error) => {
      console.error("Failed to load OpenSeadragon:", error);
    });
  }, [tileSource, isClient]);

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

  // Show loading state while OpenSeadragon loads
  if (!isClient) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-black">
        <div className="text-center">
          <div className="mb-4 text-6xl">🌌</div>
          <p className="text-xl text-gray-400">Loading viewer...</p>
        </div>
      </div>
    );
  }

  return <div ref={viewerRef} className="h-full w-full openseadragon-container" />;
}
