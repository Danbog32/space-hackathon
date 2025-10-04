"use client";

import Link from "next/link";
import { Button } from "@astro-zoom/ui";
import { useViewerStore } from "@/store/viewerStore";
import type { Dataset } from "@astro-zoom/proto";

interface ViewerToolbarProps {
  dataset: Dataset;
}

export function ViewerToolbar({ dataset }: ViewerToolbarProps) {
  const mode = useViewerStore((state) => state.mode);
  const setMode = useViewerStore((state) => state.setMode);
  const kioskMode = useViewerStore((state) => state.kioskMode);
  const toggleKioskMode = useViewerStore((state) => state.toggleKioskMode);

  return (
    <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between bg-gray-900/90 p-4 backdrop-blur-sm">
      <div className="flex items-center gap-4">
        <Link href="/" className="text-xl font-bold text-blue-400 hover:text-blue-300">
          ← Astro-Zoom
        </Link>
        <div className="h-6 w-px bg-gray-700" />
        <div>
          <h2 className="font-semibold">{dataset.name}</h2>
          {dataset.description && <p className="text-xs text-gray-400">{dataset.description}</p>}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant={mode === "explore" ? "primary" : "ghost"}
          size="sm"
          onClick={() => setMode("explore")}
        >
          Explore (1)
        </Button>
        <Button
          variant={mode === "compare" ? "primary" : "ghost"}
          size="sm"
          onClick={() => setMode("compare")}
        >
          Compare (2)
        </Button>
        <Button
          variant={mode === "annotate" ? "primary" : "ghost"}
          size="sm"
          onClick={() => setMode("annotate")}
        >
          Annotate (3)
        </Button>
        <Button
          variant={mode === "time" ? "primary" : "ghost"}
          size="sm"
          onClick={() => setMode("time")}
        >
          Time
        </Button>

        <div className="h-6 w-px bg-gray-700 mx-2" />

        <Button variant="ghost" size="sm" onClick={toggleKioskMode}>
          {kioskMode ? "Exit Kiosk" : "Kiosk"}
        </Button>
      </div>
    </div>
  );
}
