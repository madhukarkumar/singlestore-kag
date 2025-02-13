'use client';

import { useState } from 'react';

interface SearchResult {
  doc_id: number;
  content: string;
  vector_score: number;
  text_score: number;
  combined_score: number;
  entities: Array<{
    entity_id: number;
    name: string;
    category: string;
    description?: string;
  }>;
  relationships: Array<{
    source_entity_id: number;
    target_entity_id: number;
    relation_type: string;
    metadata?: Record<string, any>;
  }>;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  generated_response?: string;
  execution_time: number;
}

export default function SearchForm() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('http://localhost:8000/kag-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          top_k: 20,
          debug: false,
        }),
      });

      if (!res.ok) {
        throw new Error(`Search failed: ${res.statusText}`);
      }

      const data: SearchResponse = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
            required
          />
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-blue-300 text-lg font-medium transition-colors"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 mb-6 text-red-700 bg-red-100 rounded-lg border border-red-200">
          <p className="font-medium">Error</p>
          <p>{error}</p>
        </div>
      )}

      {response && (
        <div className="space-y-8">
          {/* AI Generated Response */}
          {response.generated_response && (
            <div className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100">
              <h3 className="text-lg font-semibold mb-3 text-blue-900">AI Response</h3>
              <p className="text-gray-800 leading-relaxed whitespace-pre-line">
                {response.generated_response.split('. ').join('.\n\n')}
              </p>
            </div>
          )}

          {/* Search Results */}
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900 border-b pb-2">
              Search Results
            </h3>
            <div className="space-y-8">
              {response.results.map((result, index) => (
                <div
                  key={`${result.doc_id}-${index}`}
                  className="p-6 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow divide-y divide-gray-100"
                >
                  {/* Relevance Scores */}
                  <div className="flex flex-wrap gap-4 mb-4">
                    {[
                      {
                        label: 'Vector Score',
                        value: result.vector_score,
                        className: 'bg-blue-50 text-blue-700'
                      },
                      {
                        label: 'Text Score',
                        value: result.text_score,
                        className: 'bg-green-50 text-green-700'
                      },
                      {
                        label: 'Combined Score',
                        value: result.combined_score,
                        className: 'bg-purple-50 text-purple-700'
                      }
                    ].map((score, idx) => (
                      <div
                        key={`${result.doc_id}-score-${idx}`}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium ${score.className}`}
                      >
                        {score.label}: {score.value.toFixed(3)}
                      </div>
                    ))}
                  </div>

                  {/* Content */}
                  <div className="py-4">
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">
                      Document Content
                    </h4>
                    <p className="text-gray-800 leading-relaxed whitespace-pre-line">
                      {result.content
                        .split('. ')
                        .map((sentence, idx) => sentence.trim())
                        .filter(sentence => sentence.length > 0)
                        .map((sentence, idx) => (
                          <span key={`${result.doc_id}-sentence-${idx}`}>
                            {sentence}.{'\n\n'}
                          </span>
                        ))}
                    </p>
                  </div>

                  {/* Entities */}
                  {result.entities.length > 0 && (
                    <div className="pt-4" key={`entities-${result.doc_id}`}>
                      <h4 className="text-sm font-semibold text-gray-700 mb-3">
                        Entities Found
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {result.entities.map((entity) => (
                          <div
                            key={`${result.doc_id}-entity-${entity.entity_id}`}
                            className="px-3 py-1.5 bg-gray-50 rounded-full text-sm text-gray-700 flex items-center gap-1.5 border border-gray-200"
                          >
                            <span className="font-medium">{entity.name}</span>
                            <span className="text-gray-500 text-xs">({entity.category})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Execution Time */}
          <div className="text-sm text-gray-500 text-right">
            Query executed in {response.execution_time.toFixed(3)} seconds
          </div>
        </div>
      )}
    </div>
  );
}
