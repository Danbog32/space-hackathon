import React from "react";
import { clsx } from "clsx";

export interface PanelProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
  onClose?: () => void;
}

export const Panel: React.FC<PanelProps> = ({ children, title, className, onClose }) => {
  return (
    <div
      className={clsx(
        "rounded-lg border border-gray-700 bg-gray-900/95 p-4 shadow-xl backdrop-blur-sm",
        className
      )}
    >
      {(title || onClose) && (
        <div className="mb-3 flex items-center justify-between">
          {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white focus:outline-none"
              aria-label="Close"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>
      )}
      <div className="text-gray-300">{children}</div>
    </div>
  );
};
