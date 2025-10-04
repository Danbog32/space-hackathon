import React from "react";
import { clsx } from "clsx";

export interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export const Toggle: React.FC<ToggleProps> = ({ checked, onChange, label, disabled }) => {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <div className="relative">
        <input
          type="checkbox"
          className="sr-only"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
        />
        <div
          className={clsx(
            "h-6 w-11 rounded-full transition-colors",
            checked ? "bg-blue-600" : "bg-gray-700",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        />
        <div
          className={clsx(
            "absolute left-1 top-1 h-4 w-4 rounded-full bg-white transition-transform",
            checked && "translate-x-5"
          )}
        />
      </div>
      {label && <span className="text-sm text-gray-300">{label}</span>}
    </label>
  );
};
