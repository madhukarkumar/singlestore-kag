'use client';

import { useEffect, useState, useCallback } from 'react';
import { Spinner } from '../../components/Spinner';
import KnowledgeGraph from '../../components/KnowledgeGraph';
import SearchForm from '../../components/SearchForm';
import { ProcessingStatus } from '../../components/ProcessingStatus';
import NavHeader from '../../components/NavHeader';

interface DocumentStats {
  doc_id: number;
  title: string;
  total_chunks: number;
  total_entities: number;
  total_relationships: number;
  created_at: string;
  file_type: string;
  status: string;
}

interface KBStats {
  total_documents: number;
  total_chunks: number;
  total_entities: number;
  total_relationships: number;
  documents: DocumentStats[];
  last_updated: string;
}

interface KBDataResponse {
  stats: KBStats;
  execution_time: number;
}

export default function NewHomePage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<KBStats | null>(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);

  const fetchKBData = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/kbdata');
      if (!response.ok) {
        throw new Error('Failed to fetch KB data');
      }
      const result: KBDataResponse = await response.json();
      setData(result.stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKBData();
  }, [fetchKBData]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadingFile(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      setTaskId(result.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    }
  };

  return (
    <div className="min-h-screen bg-twisty-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-twisty-gray-200 px-6 py-4">
        <div className="flex flex-col space-y-4">
          <h1 className="text-twisty-2xl font-twisty font-semibold text-twisty-secondary">
            Knowledge Assistant
          </h1>
          <NavHeader />
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column */}
          <div className="space-y-8">
            {/* Stats Section */}
            <section className="bg-white rounded-twisty-lg p-6 shadow-twisty-md">
              <h2 className="text-twisty-xl font-twisty font-semibold text-twisty-secondary mb-6">
                Knowledge Base Statistics
              </h2>
              {loading ? (
                <div className="flex justify-center">
                  <Spinner />
                </div>
              ) : error ? (
                <div className="text-twisty-error">{error}</div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-twisty-gray-50 p-4 rounded-twisty-md">
                    <p className="text-twisty-gray-600 text-twisty-sm">Documents</p>
                    <p className="text-twisty-2xl font-semibold text-twisty-secondary">
                      {data?.total_documents}
                    </p>
                  </div>
                  <div className="bg-twisty-gray-50 p-4 rounded-twisty-md">
                    <p className="text-twisty-gray-600 text-twisty-sm">Chunks</p>
                    <p className="text-twisty-2xl font-semibold text-twisty-secondary">
                      {data?.total_chunks}
                    </p>
                  </div>
                  <div className="bg-twisty-gray-50 p-4 rounded-twisty-md">
                    <p className="text-twisty-gray-600 text-twisty-sm">Entities</p>
                    <p className="text-twisty-2xl font-semibold text-twisty-secondary">
                      {data?.total_entities}
                    </p>
                  </div>
                  <div className="bg-twisty-gray-50 p-4 rounded-twisty-md">
                    <p className="text-twisty-gray-600 text-twisty-sm">Relationships</p>
                    <p className="text-twisty-2xl font-semibold text-twisty-secondary">
                      {data?.total_relationships}
                    </p>
                  </div>
                </div>
              )}
            </section>

            {/* Upload Section */}
            <section className="bg-white rounded-twisty-lg p-6 shadow-twisty-md">
              <h2 className="text-twisty-xl font-twisty font-semibold text-twisty-secondary mb-6">
                Upload Document
              </h2>
              <div className="space-y-4">
                <label className="block">
                  <span className="text-twisty-gray-700">Select PDF file</span>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileUpload}
                    className="mt-1 block w-full text-twisty-sm text-twisty-gray-700
                             file:mr-4 file:py-2 file:px-4
                             file:rounded-twisty-md file:border-0
                             file:text-sm file:font-semibold
                             file:bg-twisty-primary file:text-white
                             hover:file:bg-twisty-primary/90"
                  />
                </label>
                {taskId && <ProcessingStatus taskId={taskId} onComplete={fetchKBData} />}
              </div>
            </section>
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Search Section */}
            <section className="bg-white rounded-twisty-lg p-6 shadow-twisty-md">
              <h2 className="text-twisty-xl font-twisty font-semibold text-twisty-secondary mb-6">
                Ask Knowledge Base
              </h2>
              <SearchForm />
            </section>

            {/* Knowledge Graph Section */}
            <section className="bg-white rounded-lg p-6 shadow-md">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Knowledge Graph
              </h2>
              <div className="h-[500px]">
                <KnowledgeGraph />
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
