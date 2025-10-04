"use client";

import { Panel, Timeline } from "@astro-zoom/ui";
import type { TimelineItem } from "@astro-zoom/ui";

interface TimeBarProps {
  items: TimelineItem[];
  selected: string;
  onSelect: (id: string) => void;
}

export function TimeBar({ items, selected, onSelect }: TimeBarProps) {
  return (
    <Panel className="w-96 p-4">
      <Timeline items={items} selected={selected} onSelect={onSelect} />
    </Panel>
  );
}
