"use client";

import { useEffect, useMemo, useRef } from "react";
import OpenSeadragon from "openseadragon";
import { api } from "@/lib/api";
import { useViewerStore } from "@/store/viewerStore";
import type { Overlay } from "@astro-zoom/proto";

interface DeepZoomViewerProps {
  tileSource: string;
}

export function DeepZoomViewer({ tileSource }: DeepZoomViewerProps) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const osdRef = useRef<OpenSeadragon.Viewer | null>(null);
  const overlayItemsRef = useRef<Map<string, OpenSeadragon.TiledImage>>(new Map());
  const overlaysRef = useRef<Overlay[]>([]);
  const lastDraggedOverlayRef = useRef<Overlay | null>(null);
  const dragOffsetRef = useRef<OpenSeadragon.Point | null>(null);
  const isDraggingOverlayRef = useRef(false);
  const selectedSearchResult = useViewerStore((state) => state.selectedSearchResult);
  const overlays = useViewerStore((state) => state.overlays);
  const upsertOverlay = useViewerStore((state) => state.upsertOverlay);
  const activeOverlayId = useViewerStore((state) => state.activeOverlayId);

  useEffect(() => {
    if (!viewerRef.current || osdRef.current) return;

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
        overlayItemsRef.current.clear();
      }
    };
  }, [tileSource]);

  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000", []);

  useEffect(() => {
    overlaysRef.current = overlays;
  }, [overlays]);

  useEffect(() => {
    const viewer = osdRef.current;
    if (!viewer) return;

    const overlayItems = overlayItemsRef.current;
    const knownIds = new Set(overlays.map((overlay) => overlay.id));

    // Remove overlays that no longer exist
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
          success: ({ item }) => {
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
        target.setPosition(new OpenSeadragon.Point(overlay.position.x, overlay.position.y));
        if (typeof target.setRotation === "function") {
          target.setRotation(overlay.position.rotation ?? 0);
        }
      }
    });
  }, [apiBase, overlays]);

  useEffect(() => {
    const viewer = osdRef.current;
    if (!viewer) return;

    const overlayItems = overlayItemsRef.current;

    const handlePress = (event: OpenSeadragon.ViewerEvent<any>) => {
      if (!activeOverlayId) return;
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

      dragOffsetRef.current = new OpenSeadragon.Point(pointer.x - bounds.x, pointer.y - bounds.y);
      isDraggingOverlayRef.current = true;
      viewer.setMouseNavEnabled(false);
      event.preventDefaultAction = true;
      event.stopHandlers = true;
    };

    const handleDrag = (event: OpenSeadragon.ViewerEvent<any>) => {
      if (!isDraggingOverlayRef.current || !activeOverlayId) {
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

      overlayItem.setPosition(new OpenSeadragon.Point(nextX, nextY));

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
      viewer.setMouseNavEnabled(true);

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

    const handleRelease = (event: OpenSeadragon.ViewerEvent<any>) => {
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
  }, [activeOverlayId, upsertOverlay]);

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
