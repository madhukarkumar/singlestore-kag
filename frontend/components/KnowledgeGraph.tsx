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
  const containerRef = useRef<HTMLDivElement>(null);

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

  // Center graph on mount and data load
  useEffect(() => {
    if (graphRef.current && graphData) {
      // Wait a bit for the graph to stabilize
      setTimeout(() => {
        graphRef.current.zoomToFit(400, 50);
        graphRef.current.centerAt(0, 0, 1000);
      }, 500);
    }
  }, [graphData]);

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

  return (
    <div ref={containerRef} className="relative w-full h-full flex items-center justify-center overflow-hidden">
      {loading ? (
        <div className="absolute inset-0 flex items-center justify-center">
          <Spinner />
        </div>
      ) : error ? (
        <div className="text-red-600">{error}</div>
      ) : (
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
            const nodeColor = categoryColors[
              Array.from(new Set(graphData.nodes.map(n => n.category)))
                .indexOf(node.category) % categoryColors.length
            ];
            
            // Draw circle
            ctx.beginPath();
            ctx.fillStyle = nodeColor;
            const size = 4 / globalScale;  // Fixed 4px radius (8px diameter)
            ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
            ctx.fill();
            
            // Draw label
            ctx.font = `${fontSize}px Inter, system-ui, -apple-system, sans-serif`;
            const textWidth = ctx.measureText(label).width;
            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

            // Position label below the circle
            const labelY = node.y + size + fontSize/2;
            
            ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            ctx.fillRect(
              node.x - bckgDimensions[0] / 2,
              labelY - bckgDimensions[1] / 2,
              ...bckgDimensions
            );

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = selectedNode && selectedNode.id !== node.id ? 
              '#666' : 
              nodeColor;
            ctx.fillText(label, node.x, labelY);
          }}
          width={containerRef.current?.clientWidth || 800}
          height={containerRef.current?.clientHeight || 500}
        />
      )}
    </div>
  );
}
