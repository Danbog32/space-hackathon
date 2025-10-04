"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { UploadPrompt } from "./UploadPrompt";

export function DatasetList() {
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const {
    data: datasets,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["datasets"],
    queryFn: api.getDatasets,
  });

  const deleteMutation = useMutation({
    mutationFn: (datasetId: string) => api.deleteDataset(datasetId),
    onMutate: async (datasetId) => {
      setDeletingId(datasetId);
      
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["datasets"] });
      
      // Snapshot the previous value
      const previousDatasets = queryClient.getQueryData(["datasets"]);
      
      // Optimistically update to remove the dataset
      queryClient.setQueryData(["datasets"], (old: any) => 
        old?.filter((ds: any) => ds.id !== datasetId)
      );
      
      return { previousDatasets };
    },
    onError: (err, datasetId, context) => {
      // Rollback on error
      if (context?.previousDatasets) {
        queryClient.setQueryData(["datasets"], context.previousDatasets);
      }
      alert(`Failed to delete dataset: ${err instanceof Error ? err.message : 'Unknown error'}`);
    },
    onSuccess: (data, datasetId) => {
      // Show warning if partial deletion
      if (data.warnings && data.warnings.length > 0) {
        console.warn('Dataset deleted with warnings:', data.warnings);
        alert(`Dataset deleted with warnings:\n${data.warnings.join('\n')}`);
      }
    },
    onSettled: () => {
      setDeletingId(null);
      // Refetch to ensure we have the latest data
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });

  const handleDelete = (e: React.MouseEvent, datasetId: string, datasetName: string) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (confirm(`Are you sure you want to delete "${datasetName}"?\n\nThis will permanently remove all tiles and data.`)) {
      deleteMutation.mutate(datasetId);
    }
  };

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
      <div className="grid gap-4 md:grid-cols-1">
        <UploadPrompt />
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {datasets.map((dataset) => (
        <div
          key={dataset.id}
          className="relative group rounded-lg border border-gray-800 bg-gray-900 transition-all hover:border-blue-600"
        >
          <Link
            href={`/view/${dataset.id}`}
            className="block p-6 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <h3 className="text-xl font-semibold mb-2 group-hover:text-blue-400 transition-colors pr-8">
              {dataset.name.slice(0, 20)}...
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
          
          {/* Delete Button */}
          <button
            onClick={(e) => handleDelete(e, dataset.id, dataset.name)}
            disabled={deletingId === dataset.id}
            className="absolute top-4 right-4 p-2 rounded-lg bg-gray-800 text-gray-400 hover:bg-red-900 hover:text-red-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed z-10"
            title="Delete dataset"
          >
            {deletingId === dataset.id ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            )}
          </button>
        </div>
      ))}
      <UploadPrompt />
    </div>
  );
}
