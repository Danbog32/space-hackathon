"use client";

import {
  type ChangeEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Input, Toggle } from "@astro-zoom/ui";
import { api } from "@/lib/api";
import { useViewerStore } from "@/store/viewerStore";
import type { Dataset, Overlay, OverlayPosition } from "@astro-zoom/proto";

interface OverlayManagerProps {
  datasetId: string;
}

const POSITION_FIELDS: Array<{ key: keyof OverlayPosition; label: string; step: number }> = [
  { key: "x", label: "X", step: 0.01 },
  { key: "y", label: "Y", step: 0.01 },
  { key: "width", label: "Width", step: 0.05 },
  { key: "rotation", label: "Rotation", step: 1 },
];

export function OverlayManager({ datasetId }: OverlayManagerProps) {
  const overlays = useViewerStore((state) => state.overlays);
  const upsertOverlay = useViewerStore((state) => state.upsertOverlay);
  const removeOverlay = useViewerStore((state) => state.removeOverlay);
  const activeOverlayId = useViewerStore((state) => state.activeOverlayId);
  const setActiveOverlayId = useViewerStore((state) => state.setActiveOverlayId);
  const overlayMoveEnabled = useViewerStore((state) => state.overlayMoveEnabled);
  const setOverlayMoveEnabled = useViewerStore((state) => state.setOverlayMoveEnabled);

  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const updateTimersRef = useRef<Map<string, number>>(new Map());
  const updateBufferRef = useRef<Map<string, Parameters<typeof api.updateOverlay>[1]>>(new Map());

  const [isBusy, setIsBusy] = useState(false);
  const [busyMode, setBusyMode] = useState<"none" | "upload" | "link">("none");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");

  const { data: datasets } = useQuery<Dataset[]>({
    queryKey: ["datasets"],
    queryFn: api.getDatasets,
  });

  const otherDatasets = useMemo(
    () => (datasets ?? []).filter((dataset) => dataset.id !== datasetId),
    [datasets, datasetId]
  );

  const datasetNameById = useMemo(() => {
    const map = new Map<string, string>();
    (datasets ?? []).forEach((dataset) => {
      map.set(dataset.id, dataset.name);
    });
    return map;
  }, [datasets]);

  const sortedOverlays = useMemo(
    () => [...overlays].sort((a, b) => a.name.localeCompare(b.name)),
    [overlays]
  );

  const flushUpdate = useCallback(
    async (overlayId: string) => {
      const payload = updateBufferRef.current.get(overlayId);
      if (!payload) return;

      updateBufferRef.current.delete(overlayId);
      updateTimersRef.current.delete(overlayId);

      try {
        const saved = await api.updateOverlay(overlayId, payload);
        upsertOverlay(saved);
        await queryClient.invalidateQueries({ queryKey: ["overlays", datasetId] });
      } catch (error) {
        console.error("Failed to update overlay", error);
      }
    },
    [datasetId, queryClient, upsertOverlay]
  );

  const queueUpdate = useCallback(
    (
      overlayId: string,
      payload: Parameters<typeof api.updateOverlay>[1],
      optimistic?: Overlay
    ) => {
      if (optimistic) {
        upsertOverlay(optimistic);
      }

      const existingPayload = updateBufferRef.current.get(overlayId) ?? {};
      let nextPayload: Parameters<typeof api.updateOverlay>[1] = {
        ...existingPayload,
        ...payload,
      };

      if (payload.position) {
        nextPayload = {
          ...nextPayload,
          position: {
            ...(existingPayload.position ?? {}),
            ...payload.position,
          },
        };
      }

      updateBufferRef.current.set(overlayId, nextPayload);

      const existingTimer = updateTimersRef.current.get(overlayId);
      if (existingTimer) {
        window.clearTimeout(existingTimer);
      }

      const timeoutId = window.setTimeout(() => {
        void flushUpdate(overlayId);
      }, 300);
      updateTimersRef.current.set(overlayId, timeoutId);
    },
    [flushUpdate, upsertOverlay]
  );

  useEffect(() => {
    return () => {
      updateTimersRef.current.forEach((timerId) => window.clearTimeout(timerId));
      updateTimersRef.current.clear();
      updateBufferRef.current.clear();
    };
  }, []);

  const handleVisibilityToggle = (overlay: Overlay, visible: boolean) => {
    const optimistic: Overlay = { ...overlay, visible };
    queueUpdate(overlay.id, { visible }, optimistic);
  };

  const handleOpacityChange = (overlay: Overlay, value: number) => {
    const opacity = Math.min(1, Math.max(0, value));
    const optimistic: Overlay = { ...overlay, opacity };
    queueUpdate(overlay.id, { opacity }, optimistic);
  };

  const handlePositionChange = (
    overlay: Overlay,
    key: keyof OverlayPosition,
    value: number
  ) => {
    if (Number.isNaN(value)) return;
    const optimistic: Overlay = {
      ...overlay,
      position: {
        ...overlay.position,
        [key]: key === "width" ? Math.max(0.01, value) : value,
      },
    };
    queueUpdate(overlay.id, { position: optimistic.position }, optimistic);
  };

  const handleNameChange = (overlay: Overlay, name: string) => {
    const optimistic: Overlay = { ...overlay, name };
    queueUpdate(overlay.id, { name }, optimistic);
  };

  const handleDelete = async (overlay: Overlay) => {
    try {
      await api.deleteOverlay(overlay.id);
      removeOverlay(overlay.id);
      await queryClient.invalidateQueries({ queryKey: ["overlays", datasetId] });
      if (activeOverlayId === overlay.id) {
        setActiveOverlayId(null);
      }
    } catch (error) {
      console.error("Failed to delete overlay", error);
    }
  };

  const pollOverlayStatus = async (overlayId: string) => {
    const maxAttempts = 120;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      const status = await api.getOverlayStatus(overlayId);
      setStatusMessage(status.message);
      if (status.status === "complete") {
        await queryClient.invalidateQueries({ queryKey: ["overlays", datasetId] });
        setStatusMessage(null);
        return;
      }
      if (status.status === "error") {
        setErrorMessage(status.message);
        setStatusMessage(null);
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
    setStatusMessage("Overlay processing is taking longer than expected");
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsBusy(true);
    setBusyMode("upload");
    setUploadProgress(0);
    setErrorMessage(null);
    setStatusMessage("Uploading overlay...");

    try {
      const defaultName = file.name.replace(/\.[^/.]+$/, "");
      const response = await api.uploadOverlay({
        file,
        datasetId,
        name: defaultName,
        position: { x: 0, y: 0, width: 1, rotation: 0 },
        onProgress: setUploadProgress,
      });

      setStatusMessage("Processing overlay tiles...");
      await pollOverlayStatus(response.overlayId);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Overlay upload failed");
      setStatusMessage(null);
    } finally {
      setIsBusy(false);
      setBusyMode("none");
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleCreateFromDataset = async () => {
    if (!selectedDatasetId) {
      setErrorMessage("Select a dataset to add as an overlay");
      return;
    }

    setIsBusy(true);
    setBusyMode("link");
    setErrorMessage(null);
    setStatusMessage("Linking overlay dataset...");

    try {
      const overlay = await api.createOverlayFromDataset({
        datasetId,
        sourceDatasetId: selectedDatasetId,
        position: { x: 0, y: 0, width: 1, rotation: 0 },
      });

      upsertOverlay(overlay);
      await queryClient.invalidateQueries({ queryKey: ["overlays", datasetId] });
      setStatusMessage("Overlay linked to existing dataset.");
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to create overlay from dataset"
      );
      setStatusMessage(null);
    } finally {
      setIsBusy(false);
      setBusyMode("none");
      setSelectedDatasetId("");
    }
  };

  const handleToggleMoveMode = () => {
    if (!overlayMoveEnabled) {
      if (sortedOverlays.length === 0) {
        setErrorMessage("Add or link an overlay before enabling move mode");
        return;
      }
      if (!activeOverlayId && sortedOverlays.length > 0) {
        setActiveOverlayId(sortedOverlays[0].id);
      }
    }
    setOverlayMoveEnabled(!overlayMoveEnabled);
  };

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900/95 p-4 shadow-lg">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">Overlays</h3>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={isBusy}
          >
            {busyMode === "upload" ? "Uploading..." : "Add Overlay"}
          </Button>
          <Button
            variant={overlayMoveEnabled ? "primary" : "ghost"}
            size="sm"
            onClick={handleToggleMoveMode}
            disabled={isBusy}
          >
            {overlayMoveEnabled ? "Disable Move Mode" : "Enable Move Mode"}
          </Button>
        </div>
      </div>

      <div className="mb-4">
        <p className="mb-1 text-xs text-gray-400">Overlay an existing dataset</p>
        <div className="flex gap-2">
          <select
            className="flex-1 rounded-md border border-gray-800 bg-gray-900 px-2 py-1 text-sm text-gray-100 focus:border-blue-500 focus:outline-none"
            value={selectedDatasetId}
            onChange={(event) => setSelectedDatasetId(event.target.value)}
            disabled={isBusy || (datasets !== undefined && otherDatasets.length === 0)}
          >
            <option value="">Select dataset</option>
            {otherDatasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.name.slice(0, 10)}
              </option>
            ))}
          </select>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCreateFromDataset}
            disabled={isBusy || !selectedDatasetId}
          >
            {busyMode === "link" ? "Linking..." : "Add From Dataset"}
          </Button>
        </div>
        {datasets && otherDatasets.length === 0 && (
          <p className="mt-1 text-[11px] text-gray-500">Upload another dataset to enable linking.</p>
        )}
      </div>

      {busyMode === "upload" && (
        <div className="mb-3 space-y-1 text-xs text-gray-300">
          <div className="h-2 w-full overflow-hidden rounded-full bg-gray-800">
            <div
              className="h-full bg-blue-500 transition-all"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p>{statusMessage ?? ""}</p>
        </div>
      )}

      {errorMessage && <p className="mb-2 text-xs text-red-400">{errorMessage}</p>}

      {busyMode !== "upload" && statusMessage && (
        <p className="mb-3 text-xs text-gray-400">{statusMessage}</p>
      )}

      {sortedOverlays.length === 0 ? (
        <p className="text-xs text-gray-500">No overlays yet. Upload one to get started.</p>
      ) : (
        <div className="space-y-3">
          {sortedOverlays.map((overlay) => {
            const isActive = overlay.id === activeOverlayId;
            return (
              <div
                key={overlay.id}
                className={`rounded-md border p-3 ${
                  isActive ? "border-blue-500 bg-blue-950/30" : "border-gray-800 bg-black/30"
                }`}
              >
                <div className="mb-2 flex items-start justify-between gap-2">
                  <Input
                    value={overlay.name}
                    onChange={(event) => handleNameChange(overlay, event.target.value)}
                    className="flex-1"
                    placeholder="Overlay name"
                  />
                  <Button
                    variant={isActive ? "primary" : "ghost"}
                    size="sm"
                    onClick={() => setActiveOverlayId(isActive ? null : overlay.id)}
                    disabled={isBusy && busyMode === "upload"}
                  >
                    {isActive
                      ? overlayMoveEnabled
                        ? "Moving"
                        : "Selected"
                      : overlayMoveEnabled
                      ? "Set Active"
                      : "Edit Placement"}
                  </Button>
                </div>

                <div className="mb-2 flex items-center justify-between">
                  <Toggle
                    checked={overlay.visible}
                    onChange={(next) => handleVisibilityToggle(overlay, next)}
                    label={overlay.visible ? "Visible" : "Hidden"}
                  />
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(overlay)}>
                    Remove
                  </Button>
                </div>

                <div className="mb-2">
                  <label className="flex items-center justify-between text-xs text-gray-400">
                    <span>Opacity</span>
                    <span>{Math.round(overlay.opacity * 100)}%</span>
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.01}
                    value={overlay.opacity}
                    onChange={(event) => handleOpacityChange(overlay, Number(event.target.value))}
                    className="mt-1 w-full"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  {POSITION_FIELDS.map(({ key, label, step }) => (
                    <div key={key} className="flex flex-col gap-1">
                      <label className="text-gray-400">{label}</label>
                      <input
                        type="number"
                        step={step}
                        value={overlay.position[key] ?? 0}
                        onChange={(event) =>
                          handlePositionChange(overlay, key, Number(event.target.value))
                        }
                        className="rounded-md border border-gray-800 bg-gray-900 px-2 py-1 text-gray-100 focus:border-blue-500 focus:outline-none"
                      />
                    </div>
                  ))}
                </div>

                {overlay.sourceDatasetId && (
                  <p className="mt-2 text-[10px] uppercase tracking-wide text-gray-500">
                    Source dataset: {datasetNameById.get(overlay.sourceDatasetId) ?? overlay.sourceDatasetId}
                  </p>
                )}

                {overlay.metadata?.width && overlay.metadata?.height && (
                  <p className="mt-2 text-[10px] uppercase tracking-wide text-gray-500">
                    Source size: {overlay.metadata.width.toLocaleString()} × {" "}
                    {overlay.metadata.height.toLocaleString()}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
