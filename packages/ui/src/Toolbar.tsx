import React from "react";
import { clsx } from "clsx";

export interface ToolbarProps {
  children: React.ReactNode;
  className?: string;
  position?: "top" | "bottom" | "left" | "right";
}

export const Toolbar: React.FC<ToolbarProps> = ({ children, className, position = "top" }) => {
  const positions = {
    top: "top-0 left-0 right-0 flex-row",
    bottom: "bottom-0 left-0 right-0 flex-row",
    left: "top-0 left-0 bottom-0 flex-col",
    right: "top-0 right-0 bottom-0 flex-col",
  };

  return (
    <div
      className={clsx(
        "absolute z-10 flex items-center gap-2 bg-gray-900/90 p-2 backdrop-blur-sm",
        positions[position],
        className
      )}
    >
      {children}
    </div>
  );
};
