'use client';

import { useEffect, useState } from 'react';

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

export default function KBPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<KBStats | null>(null);

  useEffect(() => {
    const fetchData = async () => {
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
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">
          Error: {error}
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Knowledge Base Statistics</h1>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-blue-50 p-6 rounded-xl">
          <div className="text-blue-700 text-2xl font-bold">{data.total_documents}</div>
          <div className="text-blue-600">Total Documents</div>
        </div>
        <div className="bg-green-50 p-6 rounded-xl">
          <div className="text-green-700 text-2xl font-bold">{data.total_chunks}</div>
          <div className="text-green-600">Total Chunks</div>
        </div>
        <div className="bg-purple-50 p-6 rounded-xl">
          <div className="text-purple-700 text-2xl font-bold">{data.total_entities}</div>
          <div className="text-purple-600">Total Entities</div>
        </div>
        <div className="bg-orange-50 p-6 rounded-xl">
          <div className="text-orange-700 text-2xl font-bold">{data.total_relationships}</div>
          <div className="text-orange-600">Total Relationships</div>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">Documents</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chunks</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entities</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Relationships</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.documents.map((doc) => (
                <tr key={doc.doc_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{doc.title}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{doc.file_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{doc.total_chunks}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{doc.total_entities}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{doc.total_relationships}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      doc.status === 'processed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {doc.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-4 text-sm text-gray-500 text-right">
        Last updated: {new Date(data.last_updated).toLocaleString()}
      </div>
    </div>
  );
}
