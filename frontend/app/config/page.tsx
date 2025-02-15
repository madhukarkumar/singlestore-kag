'use client';

import { useEffect, useState } from 'react';
import { Spinner } from '@/components/Spinner';
import NavHeader from '@/components/NavHeader';
import { api } from '../../utils/api';

interface ConfigFormData {
  knowledge_creation: {
    chunking: {
      semantic_rules: string[];
      overlap_size: number;
      min_chunk_size: number;
      max_chunk_size: number;
    };
    entity_extraction: {
      model: string;
      confidence_threshold: number;
      min_description_length: number;
      max_description_length: number;
      description_required: boolean;
      system_prompt: string;
      extraction_prompt_template: string;
    };
  };
  retrieval: {
    search: {
      top_k: number;
      vector_weight: number;
      text_weight: number;
      exact_phrase_weight: number;
      single_term_weight: number;
      proximity_distance: number;
      min_score_threshold: number;
      min_similarity_score: number;
      context_window_size: number;
    };
    response_generation: {
      temperature: number;
      max_tokens: number;
      citation_style: string;
      include_confidence: boolean;
      prompt_template: string;
    };
  };
}

export default function ConfigPage() {
  const [config, setConfig] = useState<ConfigFormData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const data = await api.get<ConfigFormData>('config');
        setConfig(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config) return;

    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await api.post('config', config);
      setSuccessMessage('Configuration saved successfully! Please restart the server for changes to take effect.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while saving');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (path: string[], value: string | number | boolean) => {
    setConfig(prevConfig => {
      if (!prevConfig) return null;
      
      const newConfig = JSON.parse(JSON.stringify(prevConfig));
      let current = newConfig;
      
      for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]];
      }
      
      current[path[path.length - 1]] = value;
      return newConfig;
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100">
        <NavHeader />
        <div className="container mx-auto px-4 py-8">
          <div className="flex justify-center items-center h-64">
            <Spinner />
          </div>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="min-h-screen bg-gray-100">
        <NavHeader />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-red-600">
            Failed to load configuration
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <NavHeader />
      <div className="container mx-auto px-4 py-8">
        <form onSubmit={handleSubmit} className="space-y-6 bg-white shadow-sm rounded-lg p-6">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-semibold mb-6">Configuration Settings</h2>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="space-y-6">
                {/* Chunking Configuration */}
                <section className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-4">Chunking Configuration</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Overlap Size</label>
                      <input
                        type="number"
                        value={config.knowledge_creation.chunking.overlap_size}
                        onChange={(e) => handleInputChange(['knowledge_creation', 'chunking', 'overlap_size'], parseInt(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Minimum Chunk Size</label>
                      <input
                        type="number"
                        value={config.knowledge_creation.chunking.min_chunk_size}
                        onChange={(e) => handleInputChange(['knowledge_creation', 'chunking', 'min_chunk_size'], parseInt(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Maximum Chunk Size</label>
                      <input
                        type="number"
                        value={config.knowledge_creation.chunking.max_chunk_size}
                        onChange={(e) => handleInputChange(['knowledge_creation', 'chunking', 'max_chunk_size'], parseInt(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </section>

                {/* Entity Extraction Configuration */}
                <section className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-4">Entity Extraction Configuration</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Model</label>
                      <input
                        type="text"
                        value={config.knowledge_creation.entity_extraction.model}
                        onChange={(e) => handleInputChange(['knowledge_creation', 'entity_extraction', 'model'], e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Confidence Threshold</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        value={config.knowledge_creation.entity_extraction.confidence_threshold}
                        onChange={(e) => handleInputChange(['knowledge_creation', 'entity_extraction', 'confidence_threshold'], parseFloat(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </section>

                {/* Search Configuration */}
                <section className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-4">Search Configuration</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Top K Results</label>
                      <input
                        type="number"
                        value={config.retrieval.search.top_k}
                        onChange={(e) => handleInputChange(['retrieval', 'search', 'top_k'], parseInt(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Vector Weight</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        value={config.retrieval.search.vector_weight}
                        onChange={(e) => handleInputChange(['retrieval', 'search', 'vector_weight'], parseFloat(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Text Weight</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        value={config.retrieval.search.text_weight}
                        onChange={(e) => handleInputChange(['retrieval', 'search', 'text_weight'], parseFloat(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </section>

                {/* Response Generation Configuration */}
                <section className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-4">Response Generation Configuration</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Temperature</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        value={config.retrieval.response_generation.temperature}
                        onChange={(e) => handleInputChange(['retrieval', 'response_generation', 'temperature'], parseFloat(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Max Tokens</label>
                      <input
                        type="number"
                        value={config.retrieval.response_generation.max_tokens}
                        onChange={(e) => handleInputChange(['retrieval', 'response_generation', 'max_tokens'], parseInt(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Citation Style</label>
                      <input
                        type="text"
                        value={config.retrieval.response_generation.citation_style}
                        onChange={(e) => handleInputChange(['retrieval', 'response_generation', 'citation_style'], e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={config.retrieval.response_generation.include_confidence}
                        onChange={(e) => handleInputChange(['retrieval', 'response_generation', 'include_confidence'], e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label className="ml-2 block text-sm text-gray-900">Include Confidence Scores</label>
                    </div>
                  </div>
                </section>

                {error && (
                  <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-8">
                    <p className="text-red-700">{error}</p>
                  </div>
                )}
                
                {successMessage && (
                  <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-8">
                    <p className="text-green-700">{successMessage}</p>
                  </div>
                )}

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save Configuration'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
