"use client";

import { useState, useRef } from "react";

interface FileUploadProps {
  onUploadSuccess: (filename: string) => void;
  isUploading: boolean;
  setIsUploading: (value: boolean) => void;
}

export default function FileUpload({
  onUploadSuccess,
  isUploading,
  setIsUploading,
}: FileUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [error, setError] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
        "http://localhost:8000/documents/upload-pdf?namespace=default",
        {
          method: "POST",
          body: formData,
        },
      );

      if (!response.ok) {
        throw new Error("Upload failed. Please try again.");
      }

      const data = await response.json();
      setUploadedFiles((prev) => [...prev, file.name]);
      onUploadSuccess(file.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith(".pdf")) {
        setError("Only PDF files are supported");
        return;
      }
      handleUpload(file);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Upload Documents
      </h2>

      <div
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-gray-500">Processing document...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <p className="text-2xl">📄</p>
            <p className="text-sm font-medium text-gray-600">
              Click to upload PDF
            </p>
            <p className="text-xs text-gray-400">PDF files only</p>
          </div>
        )}
      </div>

      {error && <p className="mt-3 text-sm text-red-500">{error}</p>}

      {uploadedFiles.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium text-gray-600 mb-2">Uploaded:</p>
          <ul className="space-y-1">
            {uploadedFiles.map((filename, index) => (
              <li
                key={index}
                className="flex items-center gap-2 text-sm text-gray-600"
              >
                <span className="text-green-500">✓</span>
                {filename}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
