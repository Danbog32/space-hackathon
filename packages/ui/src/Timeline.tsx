import React from "react";
import { clsx } from "clsx";

export interface TimelineItem {
  id: string;
  label: string;
  timestamp: string;
}

export interface TimelineProps {
  items: TimelineItem[];
  selected?: string;
  onSelect: (id: string) => void;
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({ items, selected, onSelect, className }) => {
  return (
    <div className={clsx("flex flex-col gap-2", className)}>
      <label className="text-sm font-medium text-gray-300">Timeline</label>
      <select
        value={selected || ""}
        onChange={(e) => onSelect(e.target.value)}
        className="rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.label} - {item.timestamp}
          </option>
        ))}
      </select>
      <div className="relative h-2 w-full rounded-full bg-gray-800">
        {items.map((item, idx) => (
          <button
            key={item.id}
            onClick={() => onSelect(item.id)}
            className={clsx(
              "absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full border-2 transition-colors",
              selected === item.id
                ? "border-blue-500 bg-blue-500"
                : "border-gray-600 bg-gray-700 hover:border-gray-500"
            )}
            style={{ left: `${(idx / (items.length - 1)) * 100}%` }}
            title={item.label}
          />
        ))}
      </div>
    </div>
  );
};
