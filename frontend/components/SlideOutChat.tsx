'use client';

import { useState, useEffect } from 'react';
import SearchForm from './SearchForm';

interface SlideOutChatProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SlideOutChat({ isOpen, onClose }: SlideOutChatProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/20 transition-opacity duration-300 z-40
          ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />

      {/* Slide-out panel */}
      <div
        className={`fixed right-0 top-0 h-full w-full max-w-2xl bg-white shadow-twisty-lg 
          transform transition-transform duration-300 ease-in-out z-50
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-twisty-gray-200">
            <h2 className="text-twisty-xl font-twisty font-semibold text-twisty-secondary">
              Chat
            </h2>
            <button
              onClick={onClose}
              className="p-2 text-twisty-gray-500 hover:text-twisty-gray-700 rounded-full 
                hover:bg-twisty-gray-100 transition-colors"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Chat content */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            <SearchForm />
          </div>
        </div>
      </div>
    </>
  );
}
