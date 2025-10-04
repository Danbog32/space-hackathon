"use client";

import Link from "next/link";

/**
 * UploadPrompt - A call-to-action component for uploading images
 * Can be shown when no datasets exist or as an additional option
 */
export function UploadPrompt() {
  return (
    <Link
      href="/upload"
      className="group relative overflow-hidden rounded-lg border-2 border-dashed border-gray-700 bg-gray-900/50 p-8 transition-all hover:border-blue-500 hover:bg-gray-900"
    >
      <div className="flex flex-col items-center justify-center space-y-4 text-center">
        {/* Icon */}
        <div className="rounded-full bg-gradient-to-br from-blue-500/20 to-purple-600/20 p-4 group-hover:scale-110 transition-transform">
          <svg
            className="w-12 h-12 text-blue-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
        </div>

        {/* Text */}
        <div>
          <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
            Upload Your Own Image
          </h3>
          <p className="text-sm text-gray-400">
            Transform high-resolution images into interactive deep-zoom experiences
          </p>
        </div>

        {/* Features */}
        <div className="flex flex-wrap justify-center gap-2 text-xs">
          <span className="px-2 py-1 rounded bg-gray-800 text-gray-400">
            JPG, PNG, TIFF
          </span>
          <span className="px-2 py-1 rounded bg-gray-800 text-gray-400">
            Up to 500MB
          </span>
          <span className="px-2 py-1 rounded bg-gray-800 text-gray-400">
            Auto-processing
          </span>
        </div>
      </div>

      {/* Glow effect on hover */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-600/5 opacity-0 group-hover:opacity-100 transition-opacity" />
    </Link>
  );
}

