'use client';

import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';

interface ProcessingStatusProps {
  taskId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

interface TaskStatus {
  task_id: string;
  status: 'SUCCESS' | 'FAILURE' | 'STARTED' | 'PROCESSING';
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
        const data = await api.get<TaskStatus>('taskStatus', { taskId });
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

  const getStatusText = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return 'Processing Complete';
      case 'FAILURE':
        return 'Processing Failed';
      case 'STARTED':
        return 'Processing Started';
      case 'PROCESSING':
        return 'Processing...';
      default:
        return 'Unknown Status';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <div className={`h-2.5 w-2.5 rounded-full ${getStatusColor(status.status)}`}></div>
        <span className="text-sm font-medium text-gray-900">
          {getStatusText(status.status)}
        </span>
      </div>
      {status.message && (
        <p className="text-sm text-gray-500">{status.message}</p>
      )}
      {status.current !== undefined && status.total !== undefined && (
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full"
            style={{ width: `${(status.current / status.total) * 100}%` }}
          ></div>
        </div>
      )}
    </div>
  );
};
