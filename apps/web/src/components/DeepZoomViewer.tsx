"use client";

import { useEffect, useMemo, useRef } from "react";
import { api } from "@/lib/api";

import { useViewerStore } from "@/store/viewerStore";
import type { Overlay } from "@astro-zoom/proto";
type OpenSeadragonModule = typeof import("openseadragon");
type Viewer = InstanceType<OpenSeadragonModule["Viewer"]>;
type TiledImage = InstanceType<OpenSeadragonModule["TiledImage"]>;
type Point = InstanceType<OpenSeadragonModule["Point"]>;

type HandlerAugmentation = {
  preventDefaultAction?: boolean;
  stopHandlers?: boolean;
};

type CanvasPressEvent = import("openseadragon").CanvasPressEvent & HandlerAugmentation;
type CanvasDragEvent = import("openseadragon").CanvasDragEvent & HandlerAugmentation;
type CanvasReleaseEvent = import("openseadragon").CanvasReleaseEvent & HandlerAugmentation;


let cachedOpenSeadragon: OpenSeadragonModule | null = null;

const getOpenSeadragon = (): OpenSeadragonModule | null => {
  if (typeof window === "undefined") {
    return null;
  }

  if (!cachedOpenSeadragon) {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    cachedOpenSeadragon = require("openseadragon") as OpenSeadragonModule;
  }

  return cachedOpenSeadragon;
};

interface DeepZoomViewerProps {
  tileSource: string;
}

export function DeepZoomViewer({ tileSource }: DeepZoomViewerProps) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const osdRef = useRef<Viewer | null>(null);
  const overlayItemsRef = useRef<Map<string, TiledImage>>(new Map());
  const overlaysRef = useRef<Overlay[]>([]);
  const lastDraggedOverlayRef = useRef<Overlay | null>(null);
  const dragOffsetRef = useRef<Point | null>(null);
  const isDraggingOverlayRef = useRef(false);
  const searchOverlaysRef = useRef<any[]>([]);
  const selectedSearchResult = useViewerStore((state) => state.selectedSearchResult);
  const overlays = useViewerStore((state) => state.overlays);
  const upsertOverlay = useViewerStore((state) => state.upsertOverlay);
  const activeOverlayId = useViewerStore((state) => state.activeOverlayId);
  const overlayMoveEnabled = useViewerStore((state) => state.overlayMoveEnabled);
  const searchResults = useViewerStore((state) => state.searchResults);
  const boundingBoxOpacity = useViewerStore((state) => state.boundingBoxOpacity) || 0.4;

  useEffect(() => {
    const osd = getOpenSeadragon();
    if (!viewerRef.current || osdRef.current || !osd) return;

    osdRef.current = osd({
      element: viewerRef.current,
      prefixUrl: "//openseadragon.github.io/openseadragon/images/",
      tileSources: tileSource,
      showNavigationControl: true,
      navigationControlAnchor: osd.ControlAnchor.BOTTOM_RIGHT,
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
        overlayItemsRef.current.clear();
        searchOverlaysRef.current = [];
      }
    };
  }, [tileSource]);

  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000", []);

  useEffect(() => {
    overlaysRef.current = overlays;
  }, [overlays]);

  // Handle overlay management (tiled images)
  useEffect(() => {
    const viewer = osdRef.current;
    const osd = getOpenSeadragon();
    if (!viewer || !osd) return;

    const overlayItems = overlayItemsRef.current;
    const knownIds = new Set(overlays.map((overlay) => overlay.id));

    overlayItems.forEach((item, overlayId) => {
      if (!knownIds.has(overlayId)) {
        viewer.world.removeItem(item);
        overlayItems.delete(overlayId);
      }
    });

    overlays.forEach((overlay) => {
      const target = overlayItems.get(overlay.id);
      const tileSourceUrl = `${apiBase}${overlay.tileUrl}/info.dzi`;
      if (!target) {
        viewer.addTiledImage({
          tileSource: tileSourceUrl,
          x: overlay.position.x,
          y: overlay.position.y,
          width: overlay.position.width,
          success: (event: Event) => {
            const { item } = event as unknown as { item: TiledImage };
            overlayItems.set(overlay.id, item);
            item.setOpacity(overlay.visible ? overlay.opacity : 0);
            if (typeof item.setRotation === "function") {
              item.setRotation(overlay.position.rotation ?? 0);
            }
          },
          error: (event) => {
            console.error("Failed to add overlay", overlay.id, event);
          },
        });
      } else {
        target.setOpacity(overlay.visible ? overlay.opacity : 0);
        target.setWidth(overlay.position.width);
        target.setPosition(new osd.Point(overlay.position.x, overlay.position.y));
        if (typeof target.setRotation === "function") {
          target.setRotation(overlay.position.rotation ?? 0);
        }
      }
    });
  }, [apiBase, overlays]);

  // Handle overlay dragging
  useEffect(() => {
    const viewer = osdRef.current;
    const osd = getOpenSeadragon();
    if (!viewer || !osd) return;

    const overlayItems = overlayItemsRef.current;

    const handlePress = (event: CanvasPressEvent) => {
      if (!overlayMoveEnabled || !activeOverlayId) return;
      const targetOverlay = overlaysRef.current.find((overlay) => overlay.id === activeOverlayId);
      const overlayItem = targetOverlay ? overlayItems.get(targetOverlay.id) : null;
      if (!targetOverlay || !overlayItem || !targetOverlay.visible) {
        return;
      }

      const pointer = viewer.viewport.pointFromPixel(event.position, true);
      const bounds = overlayItem.getBounds();

      const withinX = pointer.x >= bounds.x && pointer.x <= bounds.x + bounds.width;
      const withinY = pointer.y >= bounds.y && pointer.y <= bounds.y + bounds.height;
      if (!withinX || !withinY) {
        return;
      }

      dragOffsetRef.current = new osd.Point(pointer.x - bounds.x, pointer.y - bounds.y);
      isDraggingOverlayRef.current = true;
      event.preventDefaultAction = true;
      event.stopHandlers = true;
    };

    const handleDrag = (event: CanvasDragEvent) => {
      if (!overlayMoveEnabled || !isDraggingOverlayRef.current || !activeOverlayId) {
        return;
      }

      const overlayItem = overlayItems.get(activeOverlayId);
      const overlay = overlaysRef.current.find((item) => item.id === activeOverlayId);
      const offset = dragOffsetRef.current;
      if (!overlayItem || !overlay || !offset) {
        return;
      }

      const pointer = viewer.viewport.pointFromPixel(event.position, true);
      const nextX = pointer.x - offset.x;
      const nextY = pointer.y - offset.y;

      overlayItem.setPosition(new osd.Point(nextX, nextY));

      const updatedOverlay: Overlay = {
        ...overlay,
        position: {
          ...overlay.position,
          x: nextX,
          y: nextY,
        },
      };

      upsertOverlay(updatedOverlay);
      lastDraggedOverlayRef.current = updatedOverlay;

      event.preventDefaultAction = true;
      event.stopHandlers = true;
    };

    const finishDrag = () => {
      if (!isDraggingOverlayRef.current) {
        return;
      }
      isDraggingOverlayRef.current = false;

      const finalOverlay = lastDraggedOverlayRef.current;
      dragOffsetRef.current = null;
      lastDraggedOverlayRef.current = null;

      if (finalOverlay) {
        void api
          .updateOverlay(finalOverlay.id, {
            position: {
              x: finalOverlay.position.x,
              y: finalOverlay.position.y,
              width: finalOverlay.position.width,
              rotation: finalOverlay.position.rotation ?? 0,
            },
          })
          .then((saved) => {
            upsertOverlay(saved);
          })
          .catch((error) => {
            console.error("Failed to persist overlay transform", error);
          });
      }
    };

    const handleRelease = (event: CanvasReleaseEvent) => {
      if (isDraggingOverlayRef.current) {
        event.preventDefaultAction = true;
        event.stopHandlers = true;
      }
      finishDrag();
    };

    const handleExit = () => {
      finishDrag();
    };

    viewer.addHandler("canvas-press", handlePress);
    viewer.addHandler("canvas-drag", handleDrag);
    viewer.addHandler("canvas-release", handleRelease);
    viewer.addHandler("canvas-exit", handleExit);

    return () => {
      finishDrag();
      viewer.removeHandler("canvas-press", handlePress);
      viewer.removeHandler("canvas-drag", handleDrag);
      viewer.removeHandler("canvas-release", handleRelease);
      viewer.removeHandler("canvas-exit", handleExit);
    };
  }, [activeOverlayId, overlayMoveEnabled, upsertOverlay]);

  useEffect(() => {
    if (!overlayMoveEnabled) {
      isDraggingOverlayRef.current = false;
      dragOffsetRef.current = null;
      lastDraggedOverlayRef.current = null;
    }
  }, [overlayMoveEnabled]);

  // Draw bounding boxes for search results
  useEffect(() => {
    if (!osdRef.current || !searchResults) return;

    const viewer = osdRef.current;
    
    // Clear existing search overlays
    searchOverlaysRef.current.forEach((overlay) => {
      try {
        viewer.removeOverlay(overlay);
      } catch (e) {
        console.warn("Failed to remove search overlay:", e);
      }
    });
    searchOverlaysRef.current = [];

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

      const osd = getOpenSeadragon();
      if (osd) {
        viewer.addOverlay({
          element: overlayDiv,
          location: new osd.Rect(
            viewportRect.x,
            viewportRect.y,
            viewportRect.width,
            viewportRect.height
          ),
        });
      }

      searchOverlaysRef.current.push(overlayDiv);
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
