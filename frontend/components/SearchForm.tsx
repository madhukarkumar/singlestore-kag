'use client';

import React, { useState, ReactElement } from 'react';
import { fetchWithAuth } from '../utils/api';

interface SearchResult {
  content: string;
  vector_score: number;
  text_score: number;
  combined_score: number;
  doc_id: number;
  entities: Array<{
    name: string;
    type: string;
    description: string;
  }>;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  generated_response?: string;
  execution_time: number;
}

export default function SearchForm(): ReactElement {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [isResponseVisible, setIsResponseVisible] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setIsResponseVisible(true);
    setResponse(null);

    try {
      setLoading(true);
      const searchData = { query: query.trim(), top_k: 5 };
      const response = await fetchWithAuth('/kag-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchData),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data: SearchResponse = await response.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 px-4 py-2 rounded-twisty-md border border-twisty-gray-200 
                   focus:outline-none focus:ring-2 focus:ring-twisty-primary/20 
                   focus:border-twisty-primary"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-twisty-primary text-white rounded-twisty-md
                   hover:bg-twisty-primary/90 transition-colors disabled:opacity-50"
        >
          Search
        </button>
      </form>

      {/* Slide-out Response Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-full max-w-2xl bg-white shadow-twisty-lg 
          transform transition-transform duration-300 ease-in-out z-50
          ${isResponseVisible ? 'translate-x-0' : 'translate-x-full'}`}
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-twisty-gray-200">
            <div>
              <h2 className="text-twisty-xl font-twisty font-semibold text-twisty-secondary">
                Search Results
              </h2>
              {response && (
                <p className="text-sm text-twisty-gray-500 mt-1">
                  Response time: {response.execution_time >= 1 
                    ? `${response.execution_time.toFixed(2)}s` 
                    : `${(response.execution_time * 1000).toFixed(0)}ms`}
                </p>
              )}
            </div>
            <button
              onClick={() => setIsResponseVisible(false)}
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

          {/* Response Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {loading ? (
              <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-twisty-primary" />
              </div>
            ) : error ? (
              <div className="text-twisty-error p-4 rounded-twisty-md bg-twisty-error/10">
                {error}
              </div>
            ) : response ? (
              <div className="space-y-6">
                {response.generated_response && (
                  <div className="bg-twisty-gray-50 p-6 rounded-twisty-md">
                    <h3 className="font-semibold mb-4 text-twisty-xl">AI Response</h3>
                    <div className="prose prose-sm max-w-none text-twisty-gray-700 whitespace-pre-wrap leading-relaxed">
                      {response.generated_response.split('\n\n').map((paragraph, index) => {
                        const lines = paragraph.split('\n');
                        let currentList: string[] = [];
                        let isOrderedList = false;
                        
                        return (
                          <div key={index} className="mb-4">
                            {lines.reduce((acc: ReactElement[], line, lineIndex) => {
                              const isBulletPoint = line.startsWith('- ');
                              const isNumberedPoint = line.match(/^\d+\.\s/);
                              
                              if (isBulletPoint || isNumberedPoint) {
                                const content = isBulletPoint ? line.substring(2) : line.substring(line.indexOf(' ') + 1);
                                if (currentList.length === 0) {
                                  isOrderedList = !!isNumberedPoint;
                                }
                                currentList.push(content);
                              } else {
                                if (currentList.length > 0) {
                                  acc.push(
                                    <div key={`list-${lineIndex}`}>
                                      {isOrderedList ? (
                                        <ol className="list-decimal ml-4 my-2">
                                          {currentList.map((item, i) => (
                                            <li key={i}>{item}</li>
                                          ))}
                                        </ol>
                                      ) : (
                                        <ul className="list-disc ml-4 my-2">
                                          {currentList.map((item, i) => (
                                            <li key={i}>{item}</li>
                                          ))}
                                        </ul>
                                      )}
                                    </div>
                                  );
                                  currentList = [];
                                }
                                acc.push(<div key={`text-${lineIndex}`}>{line}</div>);
                              }
                              
                              if (lineIndex === lines.length - 1 && currentList.length > 0) {
                                acc.push(
                                  <div key={`list-end-${lineIndex}`}>
                                    {isOrderedList ? (
                                      <ol className="list-decimal ml-4 my-2">
                                        {currentList.map((item, i) => (
                                          <li key={i}>{item}</li>
                                        ))}
                                      </ol>
                                    ) : (
                                      <ul className="list-disc ml-4 my-2">
                                        {currentList.map((item, i) => (
                                          <li key={i}>{item}</li>
                                        ))}
                                      </ul>
                                    )}
                                  </div>
                                );
                              }
                              
                              return acc;
                            }, [])}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                
                {response.results.map((result, index) => (
                  <div key={index} className="border border-twisty-gray-200 rounded-twisty-md p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="text-sm text-twisty-gray-500">
                        Document ID: {result.doc_id}
                      </div>
                      <div className="text-sm">
                        <span className="text-twisty-primary">
                          Score: {(result.combined_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-twisty-gray-700">{result.content}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Backdrop */}
      {isResponseVisible && (
        <div
          className="fixed inset-0 bg-black/20 transition-opacity duration-300 z-40"
          onClick={() => setIsResponseVisible(false)}
        />
      )}
    </div>
  );
}
