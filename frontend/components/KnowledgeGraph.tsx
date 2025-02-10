'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { Spinner } from '@/components/Spinner';

// Dynamically import ForceGraph to avoid SSR issues
const ForceGraph2D = dynamic(() => import('react-force-graph').then(mod => mod.ForceGraph2D), {
  ssr: false,
  loading: () => <Spinner />
});

interface GraphNode {
  id: string;
  name: string;
  category: string;
  group: number;
  val: number;
}

interface GraphLink {
  source: string;
  target: string;
  type: string;
  value: number;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface GraphResponse {
  data: GraphData;
  execution_time: number;
}

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const graphRef = useRef<any>(null);

  // Color scale for different entity categories
  const categoryColors = [
    '#4f46e5', // indigo-600
    '#0891b2', // cyan-600
    '#0d9488', // teal-600
    '#059669', // emerald-600
    '#16a34a', // green-600
    '#ca8a04', // yellow-600
    '#dc2626', // red-600
    '#9333ea', // purple-600
    '#2563eb', // blue-600
    '#db2777', // pink-600
  ];

  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        const response = await fetch('http://localhost:8000/graph-data');
        if (!response.ok) {
          throw new Error('Failed to fetch graph data');
        }
        const data: GraphResponse = await response.json();
        setGraphData(data.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, []);

  if (loading) return <Spinner />;
  if (error) return <div className="text-red-600">Error: {error}</div>;
  if (!graphData) return null;

  return (
    <div className="w-full h-[500px] bg-white rounded-lg shadow-lg p-4 relative mb-8">
      <div className="absolute inset-0">
        <ForceGraph2D
          ref={graphRef}
          width={graphRef.current?.container?.clientWidth || 800}
          height={graphRef.current?.container?.clientHeight || 500}
          graphData={graphData}
          nodeLabel="name"
          nodeColor={node => categoryColors[node.group % categoryColors.length]}
          nodeVal={node => node.val}
          linkLabel="type"
          linkWidth={link => Math.sqrt(link.value)}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={2}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 12/globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            const textWidth = ctx.measureText(label).width;
            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.fillRect(
              node.x - bckgDimensions[0] / 2,
              node.y - bckgDimensions[1] / 2,
              ...bckgDimensions
            );

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = categoryColors[node.group % categoryColors.length];
            ctx.fillText(label, node.x, node.y);
          }}
          nodePointerAreaPaint={(node, color, ctx) => {
            ctx.fillStyle = color;
            const size = Math.sqrt(node.val) * 5;
            ctx.beginPath();
            ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
            ctx.fill();
          }}
          cooldownTicks={100}
          onEngineStop={() => {
            if (graphRef.current) {
              graphRef.current.zoomToFit(400, 50);
            }
          }}
        />
      </div>
    </div>
  );
}
