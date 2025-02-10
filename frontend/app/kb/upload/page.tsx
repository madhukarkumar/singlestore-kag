'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ProcessingStatus } from '@/components/ProcessingStatus';

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [docId, setDocId] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);
  const router = useRouter();

  const validateFile = (file: File): string | null => {
    if (!file.type || file.type !== 'application/pdf') {
      return 'Only PDF files are allowed';
    }
    if (file.size > 50 * 1024 * 1024) { // 50MB
      return 'File size must be less than 50MB';
    }
    return null;
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    const validationError = validateFile(droppedFile);
    
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setFile(droppedFile);
    setError(null);
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    const validationError = validateFile(selectedFile);
    
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setFile(selectedFile);
    setError(null);
  }, []);

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
      }

      const data = await response.json();
      setDocId(data.doc_id);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleProcessingComplete = useCallback(() => {
    router.push('/kb');
  }, [router]);

  const handleProcessingCancel = useCallback(() => {
    setDocId(null);
    setFile(null);
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-8">Upload PDF Document</h1>

        {!docId && (
          <>
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center ${
                isDragging
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="space-y-4">
                <div className="text-gray-600">
                  Drag and drop your PDF here, or{' '}
                  <label className="text-blue-500 hover:text-blue-600 cursor-pointer">
                    browse
                    <input
                      type="file"
                      className="hidden"
                      accept="application/pdf"
                      onChange={handleFileChange}
                    />
                  </label>
                </div>
                <div className="text-sm text-gray-500">
                  Maximum file size: 50MB
                </div>
              </div>
            </div>

            {file && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{file.name}</div>
                    <div className="text-sm text-gray-500">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </div>
                  </div>
                  <button
                    onClick={() => setFile(null)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}

            {error && (
              <div className="mt-4 p-3 bg-red-50 text-red-700 rounded">
                {error}
              </div>
            )}

            <div className="mt-6">
              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className={`w-full py-2 px-4 rounded-lg ${
                  !file || uploading
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                {uploading ? 'Uploading...' : 'Upload PDF'}
              </button>
            </div>
          </>
        )}

        {docId && (
          <ProcessingStatus
            docId={docId}
            onComplete={handleProcessingComplete}
            onCancel={handleProcessingCancel}
          />
        )}
      </div>
    </div>
  );
}
