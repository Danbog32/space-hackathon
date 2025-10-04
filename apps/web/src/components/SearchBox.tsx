"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Panel, Input, Button } from "@astro-zoom/ui";
import { api } from "@/lib/api";
import { useViewerStore } from "@/store/viewerStore";

interface SearchBoxProps {
  datasetId: string;
}

export function SearchBox({ datasetId }: SearchBoxProps) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const setSearchResults = useViewerStore((state) => state.setSearchResults);
  const selectSearchResult = useViewerStore((state) => state.selectSearchResult);
  const searchResults = useViewerStore((state) => state.searchResults);

  const searchMutation = useMutation({
    mutationFn: (q: string) => api.search(q, datasetId),
    onSuccess: (data) => {
      setSearchResults(data.results);
      setIsOpen(true);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      searchMutation.mutate(query);
    }
  };

  return (
    <div className="w-80">
      <Panel className="p-4">
        <form onSubmit={handleSearch} className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold mb-2">AI Search</h3>
            <Input
              placeholder="Search for features... (e.g., crater, galaxy)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <Button type="submit" className="w-full" disabled={searchMutation.isPending}>
            {searchMutation.isPending ? "Searching..." : "Search"}
          </Button>
        </form>

        {searchMutation.isError && (
          <div className="mt-3 text-xs text-red-400">
            Search failed. Make sure AI service is running.
          </div>
        )}

        {isOpen && searchResults.length > 0 && (
          <div className="mt-4 max-h-64 overflow-y-auto">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold">Results ({searchResults.length})</h4>
              <button
                onClick={() => setIsOpen(false)}
                className="text-xs text-gray-400 hover:text-white"
              >
                Hide
              </button>
            </div>
            <div className="space-y-2">
              {searchResults.map((result, idx) => (
                <button
                  key={idx}
                  onClick={() => selectSearchResult(result)}
                  className="w-full text-left p-2 rounded bg-gray-800 hover:bg-gray-700 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <span className="text-xs text-gray-400">Result {idx + 1}</span>
                    <span className="text-xs text-blue-400">
                      {(result.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {result.bbox.x.toFixed(0)}, {result.bbox.y.toFixed(0)} •{" "}
                    {result.bbox.width.toFixed(0)} × {result.bbox.height.toFixed(0)}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}
