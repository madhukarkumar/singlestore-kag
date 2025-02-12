'use client';

import { useEffect, useRef, useState, useMemo } from 'react';
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

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [activeCategories, setActiveCategories] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<string>>(new Set());
  const [graphZoomLevel, setGraphZoomLevel] = useState<number>(1);

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
        console.log('Raw graph data:', data.data);
        setGraphData(data.data);
        // Initialize active categories
        if (data.data.nodes.length > 0) {
          const categories = new Set(data.data.nodes.map(node => node.category));
          setActiveCategories(categories);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, []);

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node === selectedNode ? null : node);
    if (node) {
      // Highlight connected links
      const connectedLinks = new Set(
        graphData?.links
          .filter(link => link.source === node.id || link.target === node.id)
          .map(link => `${link.source}-${link.target}`)
      );
      setHighlightLinks(connectedLinks);
    } else {
      setHighlightLinks(new Set());
    }
  };

  const handleCategoryToggle = (category: string) => {
    setActiveCategories(prev => {
      const newCategories = new Set(prev);
      if (newCategories.has(category)) {
        newCategories.delete(category);
      } else {
        newCategories.add(category);
      }
      return newCategories;
    });
  };

  const processedData = useMemo(() => {
    if (!graphData) return { nodes: [], links: [] };
    
    console.log('Processing graph data:', { 
      originalNodes: graphData.nodes.length,
      originalLinks: graphData.links.length 
    });
    
    // Filter nodes by active categories
    const filteredNodes = graphData.nodes.filter(node => 
      activeCategories.has(node.category)
    );
    
    // Create a set of valid node IDs
    const validNodeIds = new Set(filteredNodes.map(node => node.id));
    
    // Filter and process links
    const filteredLinks = graphData.links.filter(link => {
      const sourceValid = validNodeIds.has(link.source);
      const targetValid = validNodeIds.has(link.target);
      return sourceValid && targetValid;
    });

    console.log('Processed graph data:', {
      filteredNodes: filteredNodes.length,
      filteredLinks: filteredLinks.length,
      sampleLink: filteredLinks[0],
      validNodeIds: Array.from(validNodeIds).slice(0, 5)
    });

    return {
      nodes: filteredNodes,
      links: filteredLinks.map(link => ({
        ...link,
        source: String(link.source),
        target: String(link.target)
      }))
    };
  }, [graphData, activeCategories]);

  if (loading) return <Spinner />;
  if (error) return <div className="text-red-600">Error: {error}</div>;
  if (!graphData) return null;

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-lg p-4 relative overflow-hidden">
      {/* Graph Controls */}
      <div className="absolute top-4 left-4 z-10 flex space-x-2">
        <button
          onClick={() => graphRef.current?.zoomToFit(400)}
          className="bg-white/90 p-2 rounded-lg shadow-md hover:bg-gray-100 transition-colors"
          title="Fit to view"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0-4l5-5m11 5l-5-5m5 5v4m0-4h-4" />
          </svg>
        </button>
        <button
          onClick={() => graphRef.current?.centerAt(0, 0, 1000)}
          className="bg-white/90 p-2 rounded-lg shadow-md hover:bg-gray-100 transition-colors"
          title="Center view"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-white/90 p-4 rounded-lg shadow-md backdrop-blur-sm">
        <h3 className="text-sm font-semibold mb-2">Entity Types</h3>
        <div className="space-y-2">
          {Array.from(new Set(graphData.nodes.map(node => node.category))).map((category, index) => (
            <button
              key={category}
              onClick={() => handleCategoryToggle(category)}
              className={`flex items-center space-x-2 px-2 py-1 rounded hover:bg-gray-100 w-full text-left transition-colors ${
                activeCategories.has(category) ? 'opacity-100' : 'opacity-50'
              }`}
            >
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: categoryColors[index % categoryColors.length] }}
              />
              <span className="text-sm">{category}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Selected Node Info */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 bg-white/90 p-4 rounded-lg shadow-md backdrop-blur-sm max-w-xs">
          <h3 className="font-semibold mb-2">{selectedNode.name}</h3>
          <p className="text-sm text-gray-600">Type: {selectedNode.category}</p>
          <p className="text-sm text-gray-600">
            Connections: {graphData.links.filter(link => 
              link.source === selectedNode.id || link.target === selectedNode.id
            ).length}
          </p>
        </div>
      )}

      <div className="absolute inset-0">
        <ForceGraph2D
          ref={graphRef}
          graphData={processedData}
          nodeLabel="name"
          nodeColor={node => {
            const color = categoryColors[
              Array.from(new Set(graphData.nodes.map(n => n.category)))
                .indexOf(node.category) % categoryColors.length
            ];
            return selectedNode ? 
              (selectedNode.id === node.id ? color : `${color}66`) : 
              color;
          }}
          nodeVal={node => node.val * (selectedNode?.id === node.id ? 1.5 : 1)}
          linkSource="source"
          linkTarget="target"
          linkLabel={link => link.type}
          linkColor={() => '#4f46e5'}
          linkWidth={2}
          linkDirectionalParticles={4}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleSpeed={0.005}
          linkDirectionalParticleColor={() => '#4f46e5'}
          linkCurvature={0.1}
          cooldownTicks={100}
          onNodeClick={handleNodeClick}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 12/globalScale;
            ctx.font = `${fontSize}px Inter, system-ui, -apple-system, sans-serif`;
            const textWidth = ctx.measureText(label).width;
            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

            ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            ctx.fillRect(
              node.x - bckgDimensions[0] / 2,
              node.y - bckgDimensions[1] / 2,
              ...bckgDimensions
            );

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = selectedNode && selectedNode.id !== node.id ? 
              '#666' : 
              categoryColors[
                Array.from(new Set(graphData.nodes.map(n => n.category)))
                  .indexOf(node.category) % categoryColors.length
              ];
            ctx.fillText(label, node.x, node.y);
          }}
        />
      </div>
    </div>
  );
}
