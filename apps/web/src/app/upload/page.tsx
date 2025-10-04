"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, type ProcessingStatus } from "@/lib/api";

type UploadStage = "idle" | "uploading" | "processing" | "complete" | "error";

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  // Upload/processing state
  const [stage, setStage] = useState<UploadStage>("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [datasetId, setDatasetId] = useState<string | null>(null);

  // File selection handler
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file");
      return;
    }

    // Validate file size (500MB max)
    const maxSizeMB = 500;
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSizeMB) {
      setError(`File too large: ${fileSizeMB.toFixed(1)}MB. Maximum: ${maxSizeMB}MB`);
      return;
    }

    setSelectedFile(file);
    setError(null);

    // Generate preview for small images
    if (fileSizeMB < 10) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviewUrl(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }

    // Auto-fill name if empty
    if (!name) {
      const filename = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
      setName(filename);
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const file = e.dataTransfer.files[0];
    if (file) {
      // Simulate file input change
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      if (fileInputRef.current) {
        fileInputRef.current.files = dataTransfer.files;
        handleFileSelect({ target: fileInputRef.current } as any);
      }
    }
  };

  // Poll processing status
  useEffect(() => {
    if (stage !== "processing" || !datasetId) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await api.getProcessingStatus(datasetId);
        setProcessingStatus(status);

        if (status.status === "complete") {
          setStage("complete");
          clearInterval(pollInterval);
        } else if (status.status === "error") {
          setStage("error");
          setError(status.message);
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error("Failed to fetch status:", err);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [stage, datasetId]);

  // Upload handler
  const handleUpload = async () => {
    if (!selectedFile || !name.trim()) {
      setError("Please select a file and provide a name");
      return;
    }

    try {
      setStage("uploading");
      setError(null);
      setUploadProgress(0);

      const response = await api.uploadImage(
        selectedFile,
        name.trim(),
        description.trim() || undefined,
        (progress) => setUploadProgress(progress)
      );

      setDatasetId(response.datasetId);
      setStage("processing");

      // Start polling for status
      const initialStatus = await api.getProcessingStatus(response.datasetId);
      setProcessingStatus(initialStatus);
    } catch (err) {
      setStage("error");
      setError(err instanceof Error ? err.message : "Upload failed");
    }
  };

  // Reset form
  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setName("");
    setDescription("");
    setStage("idle");
    setUploadProgress(0);
    setProcessingStatus(null);
    setError(null);
    setDatasetId(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const canUpload = selectedFile && name.trim() && stage === "idle";
  const isProcessing = stage === "uploading" || stage === "processing";

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-gray-950 via-gray-900 to-blue-950">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="text-blue-400 hover:text-blue-300 transition-colors inline-flex items-center gap-2 mb-4"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </Link>
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Upload Image
          </h1>
          <p className="text-gray-400">
            Upload a high-resolution image to generate a deep-zoom tileset
          </p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 shadow-2xl">
          {/* Upload Form */}
          {stage === "idle" && (
            <>
              {/* File Selector */}
              <div
                className="border-2 border-dashed border-gray-700 rounded-lg p-12 text-center hover:border-blue-500 transition-colors cursor-pointer mb-6"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                {selectedFile ? (
                  <div className="space-y-4">
                    {previewUrl && (
                      <img
                        src={previewUrl}
                        alt="Preview"
                        className="max-w-xs max-h-48 mx-auto rounded-lg shadow-lg"
                      />
                    )}
                    <div>
                      <p className="text-lg font-semibold text-blue-400">{selectedFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleReset();
                      }}
                      className="text-sm text-gray-400 hover:text-white transition-colors"
                    >
                      Choose different file
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <svg
                      className="w-16 h-16 mx-auto text-gray-600"
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
                    <div>
                      <p className="text-lg font-medium text-gray-300">
                        Drop an image here or click to browse
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        Supports JPG, PNG, TIFF • Max 500MB
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Form Fields */}
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Dataset Name <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., Andromeda Galaxy"
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Description (optional)
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Add a description of this image..."
                    rows={3}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  />
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-6 p-4 bg-red-950/50 border border-red-900 rounded-lg text-red-400">
                  <p className="text-sm">{error}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={handleUpload}
                  disabled={!canUpload}
                  className="flex-1 py-3 px-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl disabled:shadow-none"
                >
                  Upload & Process
                </button>
                <Link
                  href="/"
                  className="py-3 px-6 bg-gray-800 text-gray-300 font-semibold rounded-lg hover:bg-gray-700 transition-colors text-center"
                >
                  Cancel
                </Link>
              </div>

              {/* Info Box */}
              <div className="mt-6 p-4 bg-blue-950/30 border border-blue-900/50 rounded-lg">
                <p className="text-sm text-blue-300">
                  <strong>Processing time:</strong> Varies based on image size. A 200MB image may take
                  10-30 minutes. You&apos;ll see real-time progress updates.
                </p>
              </div>
            </>
          )}

          {/* Uploading State */}
          {stage === "uploading" && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <h3 className="text-xl font-semibold text-white mb-2">Uploading...</h3>
                <p className="text-gray-400">
                  {uploadProgress.toFixed(0)}% • {selectedFile?.name}
                </p>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Processing State */}
          {stage === "processing" && processingStatus && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <h3 className="text-xl font-semibold text-white mb-2">Generating Tiles...</h3>
                <p className="text-gray-400">{processingStatus.message}</p>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-600 transition-all duration-300"
                  style={{ width: `${processingStatus.progress}%` }}
                ></div>
              </div>
              <div className="text-center text-sm text-gray-500">
                <p>This may take several minutes depending on image size...</p>
              </div>
            </div>
          )}

          {/* Complete State */}
          {stage === "complete" && processingStatus?.result && datasetId && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Processing Complete!</h3>
                <p className="text-gray-400">Your dataset is ready to explore</p>
              </div>

              <div className="bg-gray-800 rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Dimensions:</span>
                  <span className="text-white font-medium">
                    {processingStatus.result.width} × {processingStatus.result.height}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Zoom Levels:</span>
                  <span className="text-white font-medium">{processingStatus.result.levels}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Total Tiles:</span>
                  <span className="text-white font-medium">{processingStatus.result.totalTiles}</span>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => router.push(`/view/${datasetId}`)}
                  className="flex-1 py-3 px-6 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all shadow-lg hover:shadow-xl"
                >
                  View Dataset
                </button>
                <button
                  onClick={handleReset}
                  className="py-3 px-6 bg-gray-800 text-gray-300 font-semibold rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Upload Another
                </button>
              </div>
            </div>
          )}

          {/* Error State */}
          {stage === "error" && error && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Processing Failed</h3>
                <p className="text-red-400">{error}</p>
              </div>

              <button
                onClick={handleReset}
                className="w-full py-3 px-6 bg-gray-800 text-gray-300 font-semibold rounded-lg hover:bg-gray-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

