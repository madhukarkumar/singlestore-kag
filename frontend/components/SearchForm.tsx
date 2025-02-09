'use client';

import { useState } from 'react';

interface SearchResult {
  doc_id: number;
  content: string;
  vector_score: number;
  text_score: number;
  combined_score: number;
  entities: Array<{
    id: number;
    name: string;
    category: string;
    description?: string;
  }>;
  relationships: Array<{
    source_id: number;
    target_id: number;
    relationship_type: string;
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
          top_k: 5,
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
    <div className="max-w-4xl mx-auto p-4">
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-blue-300"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-lg">
          {error}
        </div>
      )}

      {response && (
        <div className="space-y-6">
          {response.generated_response && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold mb-2">Generated Response:</h3>
              <p>{response.generated_response}</p>
            </div>
          )}

          <div>
            <h3 className="font-semibold mb-2">Search Results:</h3>
            <div className="space-y-4">
              {response.results.map((result) => (
                <div key={result.doc_id} className="p-4 border border-gray-200 rounded-lg">
                  <div className="mb-2">
                    <p className="text-sm text-gray-600">
                      Scores: Vector {result.vector_score.toFixed(3)}, Text{' '}
                      {result.text_score.toFixed(3)}, Combined{' '}
                      {result.combined_score.toFixed(3)}
                    </p>
                  </div>
                  <p className="mb-4">{result.content}</p>
                  {result.entities.length > 0 && (
                    <div className="text-sm">
                      <p className="font-medium">Entities:</p>
                      <ul className="list-disc list-inside">
                        {result.entities.map((entity) => (
                          <li key={entity.id}>
                            {entity.name} ({entity.category})
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <p className="text-sm text-gray-600">
            Query executed in {response.execution_time.toFixed(3)} seconds
          </p>
        </div>
      )}
    </div>
  );
}
