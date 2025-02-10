'use client';

import { useEffect, useState } from 'react';
import { Spinner } from './Spinner';

export type ProcessingStep = 'started' | 'chunking' | 'embeddings' | 'entities' | 'relationships' | 'completed' | 'failed';

interface ProcessingStatusProps {
  docId: number;
  onComplete?: () => void;
  onCancel?: () => void;
}

interface ProcessingState {
  currentStep: ProcessingStep;
  errorMessage?: string;
  fileName: string;
}

const STEP_DESCRIPTIONS: Record<ProcessingStep, string> = {
  started: 'Processing started',
  chunking: 'Creating semantic chunks',
  embeddings: 'Generating embeddings',
  entities: 'Extracting entities',
  relationships: 'Identifying relationships',
  completed: 'Processing completed',
  failed: 'Processing failed'
};

const STEP_ORDER: ProcessingStep[] = ['started', 'chunking', 'embeddings', 'entities', 'relationships', 'completed'];

export function ProcessingStatus({ docId, onComplete, onCancel }: ProcessingStatusProps) {
  const [status, setStatus] = useState<ProcessingState | null>(null);
  const [polling, setPolling] = useState(true);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/processing-status/${docId}`);
        const data = await response.json();
        
        setStatus(data);

        if (data.currentStep === 'completed') {
          setPolling(false);
          onComplete?.();
        } else if (data.currentStep === 'failed') {
          setPolling(false);
        } else if (polling) {
          timeoutId = setTimeout(pollStatus, 2000);
        }
      } catch (error) {
        console.error('Error polling status:', error);
        setPolling(false);
      }
    };

    if (polling) {
      pollStatus();
    }

    return () => {
      clearTimeout(timeoutId);
    };
  }, [docId, polling, onComplete]);

  const handleCancel = async () => {
    try {
      await fetch(`/api/cancel-processing/${docId}`, { method: 'DELETE' });
      setPolling(false);
      onCancel?.();
    } catch (error) {
      console.error('Error canceling processing:', error);
    }
  };

  if (!status) {
    return <Spinner />;
  }

  const currentStepIndex = STEP_ORDER.indexOf(status.currentStep);

  return (
    <div className="w-full max-w-2xl mx-auto bg-white shadow-sm rounded-lg p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Processing: {status.fileName}</h3>
      </div>

      <div className="space-y-4">
        {STEP_ORDER.map((step, index) => {
          const isCompleted = index < currentStepIndex;
          const isCurrent = index === currentStepIndex;
          const isPending = index > currentStepIndex;

          return (
            <div
              key={step}
              className={`flex items-center ${
                isPending ? 'text-gray-400' : 'text-gray-900'
              }`}
            >
              <div
                className={`w-6 h-6 flex items-center justify-center rounded-full mr-3 ${
                  isCompleted
                    ? 'bg-green-500'
                    : isCurrent
                    ? 'bg-blue-500'
                    : 'bg-gray-200'
                }`}
              >
                {isCompleted ? (
                  <CheckIcon className="w-4 h-4 text-white" />
                ) : isCurrent ? (
                  <div className="w-4 h-4">
                    <Spinner />
                  </div>
                ) : (
                  <div className="w-2 h-2 bg-gray-400 rounded-full" />
                )}
              </div>
              <span className="flex-1">{STEP_DESCRIPTIONS[step]}</span>
            </div>
          );
        })}
      </div>

      {status.errorMessage && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 rounded">
          {status.errorMessage}
        </div>
      )}

      {status.currentStep !== 'completed' && status.currentStep !== 'failed' && (
        <button
          onClick={handleCancel}
          className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Cancel Processing
        </button>
      )}
    </div>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}
