'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ProcessingStatus } from './ProcessingStatus';
import { fetchWithAuth } from '../utils/api';

interface UploadFormProps {
  onUploadComplete?: () => void;
}

export default function UploadForm({ onUploadComplete }: UploadFormProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const router = useRouter();

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
    if (droppedFile?.type !== 'application/pdf') {
      setError('Please upload a PDF file');
      return;
    }

    if (droppedFile.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB');
      return;
    }

    setFile(droppedFile);
    setError(null);
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (selectedFile.type !== 'application/pdf') {
      setError('Please upload a PDF file');
      return;
    }

    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB');
      return;
    }

    setFile(selectedFile);
    setError(null);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetchWithAuth('/upload-pdf', {
        method: 'POST',
        headers: {
          'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || '',
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setTaskId(data.task_id);
      onUploadComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setUploading(false);
    }
  }, [file, onUploadComplete]);

  const handleProcessingComplete = useCallback(() => {
    router.push('/kb');
  }, [router]);

  const handleProcessingError = useCallback((error: string) => {
    setError(error);
    setTaskId(null);
  }, []);

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-8">Upload PDF Document</h2>

      {!taskId && (
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

      {taskId && (
        <ProcessingStatus
          taskId={taskId}
          onComplete={handleProcessingComplete}
          onError={handleProcessingError}
        />
      )}
    </div>
  );
}
