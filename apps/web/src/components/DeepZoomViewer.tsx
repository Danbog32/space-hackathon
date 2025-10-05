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
  const overlaysRef = useRef<any[]>([]);
  const selectedSearchResult = useViewerStore((state) => state.selectedSearchResult);
  const searchResults = useViewerStore((state) => state.searchResults);
  const boundingBoxOpacity = useViewerStore((state) => state.boundingBoxOpacity) || 0.4;

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

  // Draw bounding boxes for search results
  useEffect(() => {
    if (!osdRef.current || !searchResults) return;

    const viewer = osdRef.current;
    
    // Clear existing overlays
    overlaysRef.current.forEach((overlay) => {
      try {
        viewer.removeOverlay(overlay);
      } catch (e) {
        console.warn("Failed to remove overlay:", e);
      }
    });
    overlaysRef.current = [];

    // Wait for the viewer to be fully loaded
    if (!viewer.isOpen()) {
      console.log("⏳ Viewer not open yet, waiting...");
      return;
    }

    // Get actual image dimensions
    const tiledImage = viewer.world.getItemAt(0);
    if (!tiledImage) {
      console.log("⏳ No tiled image loaded yet");
      return;
    }

    const contentSize = tiledImage.getContentSize();
    const actualImageWidth = contentSize.x;
    const actualImageHeight = contentSize.y;

    console.log(`🖼️ Image dimensions: ${actualImageWidth} × ${actualImageHeight}`);
    console.log(`📦 Drawing ${searchResults.length} bounding boxes...`);

    let validBoxes = 0;
    let filteredBoxes = 0;

    searchResults.forEach((result, idx) => {
      const bboxData = result.bbox;
      
      // Ensure bbox is in the correct format
      const bboxX = typeof bboxData.x === 'number' ? bboxData.x : 0;
      const bboxY = typeof bboxData.y === 'number' ? bboxData.y : 0;
      const bboxWidth = typeof bboxData.width === 'number' ? bboxData.width : 0;
      const bboxHeight = typeof bboxData.height === 'number' ? bboxData.height : 0;

      // STRICT validation: box must be ENTIRELY within image bounds
      const isOutOfBounds = 
        bboxX < 0 || 
        bboxY < 0 || 
        bboxX >= actualImageWidth || 
        bboxY >= actualImageHeight ||
        bboxX + bboxWidth > actualImageWidth || 
        bboxY + bboxHeight > actualImageHeight ||
        bboxWidth <= 0 ||
        bboxHeight <= 0;

      if (isOutOfBounds) {
        console.log(
          `❌ Detection ${idx + 1} OUT OF BOUNDS - Filtered:`,
          `[${bboxX}, ${bboxY}, ${bboxWidth}, ${bboxHeight}]`,
          `Image: [0, 0, ${actualImageWidth}, ${actualImageHeight}]`
        );
        filteredBoxes++;
        return; // Skip this box
      }

      // Convert pixel coordinates to normalized viewport coordinates (0-1)
      const viewportRect = viewer.viewport.imageToViewportRectangle(
        bboxX,
        bboxY,
        bboxWidth,
        bboxHeight
      );

      // Create overlay element
      const overlayDiv = document.createElement("div");
      overlayDiv.style.border = "2px solid red";
      overlayDiv.style.background = `rgba(255, 0, 0, ${boundingBoxOpacity})`;
      overlayDiv.style.pointerEvents = "none";
      overlayDiv.style.boxSizing = "border-box";

      // Add label
      const label = document.createElement("div");
      label.textContent = `${idx + 1}`;
      label.style.position = "absolute";
      label.style.top = "2px";
      label.style.left = "2px";
      label.style.background = "rgba(255, 0, 0, 0.9)";
      label.style.color = "white";
      label.style.padding = "2px 6px";
      label.style.fontSize = "12px";
      label.style.fontWeight = "bold";
      label.style.borderRadius = "3px";
      overlayDiv.appendChild(label);

      viewer.addOverlay({
        element: overlayDiv,
        location: new OpenSeadragon.Rect(
          viewportRect.x,
          viewportRect.y,
          viewportRect.width,
          viewportRect.height
        ),
      });

      overlaysRef.current.push(overlayDiv);
      validBoxes++;

      console.log(
        `✅ Detection ${idx + 1} VALID:`,
        `Pixel [${bboxX}, ${bboxY}, ${bboxWidth}, ${bboxHeight}]`,
        `→ Viewport [${viewportRect.x.toFixed(4)}, ${viewportRect.y.toFixed(4)}, ${viewportRect.width.toFixed(4)}, ${viewportRect.height.toFixed(4)}]`
      );
    });

    console.log(`📊 Summary: ${validBoxes} boxes shown, ${filteredBoxes} filtered out`);
  }, [searchResults, boundingBoxOpacity]);

  // Fly to search result when selected
  useEffect(() => {
    if (!osdRef.current || !selectedSearchResult) return;

    const viewer = osdRef.current;
    const bbox = selectedSearchResult.bbox;

    // Wait for the viewer to be fully loaded
    if (!viewer.isOpen()) {
      console.log("⏳ Viewer not open yet for fly-to");
      return;
    }

    // Get actual image dimensions for validation
    const tiledImage = viewer.world.getItemAt(0);
    if (!tiledImage) {
      console.log("⏳ No tiled image loaded yet for fly-to");
      return;
    }

    const contentSize = tiledImage.getContentSize();
    const actualImageWidth = contentSize.x;
    const actualImageHeight = contentSize.y;

    // Validate that the bbox is within bounds before flying to it
    const bboxX = typeof bbox.x === 'number' ? bbox.x : 0;
    const bboxY = typeof bbox.y === 'number' ? bbox.y : 0;
    const bboxWidth = typeof bbox.width === 'number' ? bbox.width : 0;
    const bboxHeight = typeof bbox.height === 'number' ? bbox.height : 0;

    const isOutOfBounds = 
      bboxX < 0 || 
      bboxY < 0 || 
      bboxX >= actualImageWidth || 
      bboxY >= actualImageHeight ||
      bboxX + bboxWidth > actualImageWidth || 
      bboxY + bboxHeight > actualImageHeight ||
      bboxWidth <= 0 ||
      bboxHeight <= 0;

    if (isOutOfBounds) {
      console.error("🚫 Cannot fly to out-of-bounds detection:", bbox);
      return;
    }

    // Convert pixel coordinates to viewport coordinates
    const viewportRect = viewer.viewport.imageToViewportRectangle(
      bboxX,
      bboxY,
      bboxWidth,
      bboxHeight
    );

    console.log("✈️ Flying to detection:", viewportRect);
    viewer.viewport.fitBounds(viewportRect, true);
  }, [selectedSearchResult]);

  return <div ref={viewerRef} className="h-full w-full openseadragon-container" />;
}
