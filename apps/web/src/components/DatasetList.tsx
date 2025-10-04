"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

export function DatasetList() {
  const {
    data: datasets,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["datasets"],
    queryFn: api.getDatasets,
  });

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse rounded-lg border border-gray-800 bg-gray-900 p-6">
            <div className="h-6 bg-gray-800 rounded mb-3"></div>
            <div className="h-4 bg-gray-800 rounded w-2/3"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-900 bg-red-950/20 p-6 text-red-400">
        <p className="font-semibold">Error loading datasets</p>
        <p className="text-sm mt-1">{(error as Error).message}</p>
      </div>
    );
  }

  if (!datasets || datasets.length === 0) {
    return (
      <div className="rounded-lg border border-gray-800 bg-gray-900 p-8 text-center text-gray-500">
        <p>No datasets available</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {datasets.map((dataset) => (
        <Link
          key={dataset.id}
          href={`/view/${dataset.id}`}
          className="group rounded-lg border border-gray-800 bg-gray-900 p-6 transition-all hover:border-blue-600 hover:bg-gray-800"
        >
          <h3 className="text-xl font-semibold mb-2 group-hover:text-blue-400 transition-colors">
            {dataset.name}
          </h3>
          {dataset.description && (
            <p className="text-sm text-gray-400 mb-3">{dataset.description}</p>
          )}
          <div className="flex gap-2 text-xs text-gray-500">
            <span className="px-2 py-1 rounded bg-gray-800">{dataset.tileType.toUpperCase()}</span>
            <span className="px-2 py-1 rounded bg-gray-800">
              {dataset.pixelSize[0]} × {dataset.pixelSize[1]}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}
