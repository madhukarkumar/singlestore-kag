import React, { useEffect, useState } from 'react';

interface ProcessingStatusProps {
  taskId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

interface TaskStatus {
  task_id: string;
  status: string;
  message: string;
  current?: number;
  total?: number;
  error?: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ 
  taskId, 
  onComplete,
  onError 
}) => {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`/api/task-status/${taskId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch status');
        }
        const data = await response.json();
        setStatus(data);
        
        // If processing is complete, stop polling and call onComplete
        if (data.status === 'SUCCESS') {
          if (onComplete) {
            onComplete();
          }
        }

        // If failed, stop polling and call onError
        if (data.status === 'FAILURE') {
          const errorMessage = data.error || 'Task failed';
          setError(errorMessage);
          if (onError) {
            onError(errorMessage);
          }
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);
        if (onError) {
          onError(errorMessage);
        }
      }
    };

    // Check immediately
    checkStatus();

    // Then poll every 2 seconds
    const interval = setInterval(checkStatus, 2000);

    // Cleanup interval on unmount
    return () => clearInterval(interval);
  }, [taskId, onComplete, onError]);

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Processing Failed</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return 'bg-green-500';
      case 'FAILURE':
        return 'bg-red-500';
      case 'STARTED':
      case 'PROCESSING':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusMessage = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return 'Processing completed successfully!';
      case 'FAILURE':
        return 'Processing failed. Please try again.';
      case 'STARTED':
        return 'Starting PDF processing...';
      case 'PROCESSING':
        return status.message || 'Processing your PDF...';
      default:
        return 'Waiting to start processing...';
    }
  };

  const progress = status.current && status.total 
    ? Math.round((status.current / status.total) * 100)
    : null;

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Processing Status
        </h3>
        <div className="mt-2 max-w-xl text-sm text-gray-500">
          <p className="font-medium">{getStatusMessage(status.status)}</p>
          {status.message && status.message !== getStatusMessage(status.status) && (
            <p className="mt-1 text-sm">{status.message}</p>
          )}
        </div>
        {['STARTED', 'PROCESSING'].includes(status.status) && (
          <div className="mt-4">
            <div className="relative pt-1">
              <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-200">
                {progress !== null ? (
                  <div 
                    style={{ width: `${progress}%` }}
                    className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${getStatusColor(status.status)}`}
                  />
                ) : (
                  <div className="animate-pulse w-full h-full bg-blue-500" />
                )}
              </div>
              {progress !== null && (
                <div className="text-right">
                  <span className="text-sm font-semibold inline-block text-blue-600">
                    {progress}%
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
        {status.status === 'SUCCESS' && (
          <div className="mt-4">
            <div className="flex items-center text-green-600">
              <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Complete!</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
