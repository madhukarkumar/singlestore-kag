'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ProcessingStatus } from '@/components/ProcessingStatus';
import NavHeader from '@/components/NavHeader';
import UploadForm from '@/components/UploadForm';

export default function Upload() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
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
    if (uploading) return; // Prevent multiple uploads

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
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const data = await response.json();
      setTaskId(data.task_id);
      setFile(null); // Clear the file after successful upload
    } catch (error) {
      console.error('Upload error:', error);
      setError(error instanceof Error ? error.message : 'Failed to upload file');
      setTaskId(null);
    } finally {
      setUploading(false);
    }
  };

  const handleProcessingComplete = useCallback(() => {
    // Show success state for 2 seconds before redirecting
    setTimeout(() => {
      router.push('/kb');
    }, 2000);
  }, [router]);

  const handleProcessingError = useCallback((errorMessage: string) => {
    setTaskId(null);
    setFile(null);
    setError(errorMessage);
  }, []);

  return (
    <main className="min-h-screen bg-gray-50">
      <NavHeader />
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <UploadForm
            isDragging={isDragging}
            file={file}
            error={error}
            uploading={uploading}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onFileChange={handleFileChange}
            onUpload={handleUpload}
          />
          {taskId && (
            <ProcessingStatus
              taskId={taskId}
              onComplete={handleProcessingComplete}
              onError={handleProcessingError}
            />
          )}
        </div>
      </div>
    </main>
  );
}
