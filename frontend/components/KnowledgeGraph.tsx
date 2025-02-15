'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { Spinner } from '@/components/Spinner';
import { fetchWithAuth } from '../utils/api';
import { ForceGraphMethods } from 'react-force-graph-2d';

// Import ForceGraph2D with no SSR
const ForceGraph2D = dynamic(
  () => import('react-force-graph-2d').then(mod => mod.default),
  { ssr: false }
);

// Base node type from API
interface GraphNode {
  id: string;
  name: string;
  category: string;
  val: number;
}

// Base link type from API
interface GraphLink {
  source: string;
  target: string;
  type: string;
  value: number;
}

// Graph data structure from API
interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// Runtime link type with node references
interface RuntimeLink {
  source: GraphNode;
  target: GraphNode;
  type: string;
  value: number;
}

// Runtime graph data structure
interface RuntimeGraphData {
  nodes: GraphNode[];
  links: RuntimeLink[];
}

interface GraphResponse {
  data: GraphData;
  execution_time: number;
}

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [runtimeData, setRuntimeData] = useState<RuntimeGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const fgRef = useRef<ForceGraphMethods>(null!);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        const response = await fetchWithAuth('/graph-data');
        if (!response.ok) {
          throw new Error('Failed to fetch graph data');
        }
        const data: GraphResponse = await response.json();
        console.log('Raw response:', response.status);
        console.log('Full data object:', data);
        console.log('Graph data:', data.data);
        
        if (!data.data || !data.data.nodes || !data.data.links) {
          throw new Error('Invalid graph data format');
        }

        // Debug raw link data
        console.log('Raw links before processing:', data.data.links[0]);
        
        // Process links to ensure source/target are references to node objects
        const processedData: GraphData = {
          nodes: data.data.nodes,
          links: data.data.links
        };

        // Create runtime data with node references
        const nodesById = Object.fromEntries(
          data.data.nodes.map(node => [node.id, node])
        );
        
        const runtimeProcessedData: RuntimeGraphData = {
          nodes: processedData.nodes,
          links: processedData.links.map(link => ({
            ...link,
            source: nodesById[link.source],
            target: nodesById[link.target]
          }))
        };

        // Debug nodes map
        console.log('Nodes by ID:', nodesById);
        
        // Debug processed link data
        console.log('Processed links example:', runtimeProcessedData.links[0]);
        
        // Extract unique categories from nodes
        const uniqueCategories = Array.from(new Set(data.data.nodes.map(node => node.category)));
        console.log('Extracted categories:', uniqueCategories);

        setGraphData(processedData);
        setRuntimeData(runtimeProcessedData);
        setCategories(uniqueCategories);
        setSelectedCategories(new Set(uniqueCategories));
      } catch (err) {
        console.error('Error fetching graph data:', err); // Debug log
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, []);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        setDimensions({ width: clientWidth, height: clientHeight });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 text-center p-4">
        Error: {error}
      </div>
    );
  }

  if (!graphData || !runtimeData || categories.length === 0) {
    console.log('Render condition failed:', { graphData, categoriesLength: categories.length });
    return (
      <div className="text-gray-500 text-center p-4">
        No graph data available
      </div>
    );
  }

  const filteredData = {
    nodes: graphData.nodes.filter(node => selectedCategories.has(node.category)),
    links: runtimeData.links.filter(link => {
      // Debug link filtering
      console.log('Filtering link:', {
        link,
        sourceNode: link.source,
        targetNode: link.target,
        sourceCategory: link.source?.category,
        targetCategory: link.target?.category
      });
      
      // Check if both source and target nodes exist and their categories are selected
      return link.source && 
             link.target && 
             selectedCategories.has(link.source.category) && 
             selectedCategories.has(link.target.category);
    })
  };

  // Debug filtered results
  console.log('Filtering results:', {
    totalNodes: graphData.nodes.length,
    totalLinks: graphData.links.length,
    filteredNodes: filteredData.nodes.length,
    filteredLinks: filteredData.links.length,
    selectedCategories: Array.from(selectedCategories)
  });

  // Debug filtered data before rendering
  console.log('Filtered data before render:', {
    nodeCount: filteredData.nodes.length,
    linkCount: filteredData.links.length,
    sampleLink: filteredData.links[0],
    sampleNode: filteredData.nodes[0]
  });

  return (
    <div ref={containerRef} className="w-full h-[600px] relative border rounded-lg overflow-hidden">
      {categories.length > 0 && (
        <div className="absolute top-4 right-4 z-10 bg-white p-4 rounded-lg shadow-md">
          <h3 className="text-sm font-medium mb-2">Filter by Category</h3>
          <div className="space-y-2">
            {categories.map(category => (
              <label key={category} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={selectedCategories.has(category)}
                  onChange={() => {
                    const newSelected = new Set(selectedCategories);
                    if (newSelected.has(category)) {
                      newSelected.delete(category);
                    } else {
                      newSelected.add(category);
                    }
                    setSelectedCategories(newSelected);
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{category}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <ForceGraph2D
        ref={fgRef}
        graphData={filteredData}
        nodeLabel={node => {
          const n = node as GraphNode;
          return `${n.name}\nCategory: ${n.category}`;
        }}
        width={dimensions.width}
        height={dimensions.height}
        nodeColor={node => {
          const n = node as GraphNode;
          if (!selectedCategories.has(n.category)) return '#E2E8F0';
          // Use category-based colors
          switch (n.category.toLowerCase()) {
            case 'person': return '#4299E1';  // blue
            case 'organization': return '#48BB78';  // green
            case 'location': return '#F6AD55';  // orange
            case 'event': return '#F687B3';  // pink
            case 'concept': return '#9F7AEA';  // purple
            default: return '#718096';  // gray
          }
        }}
        nodeRelSize={4}
        nodeVal={node => {
          const n = node as GraphNode;
          return Math.sqrt(n.val * 100) + 1;  // Scale node size based on connections
        }}
        linkWidth={2}
        linkColor={() => '#999'}
        linkDirectionalParticles={1}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={0.5}
        cooldownTicks={100}
        onEngineStop={() => {
          if (fgRef.current) {
            fgRef.current.zoomToFit(400, 100); // Increased padding
          }
        }}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const n = node as GraphNode;
          const label = n.name;
          const fontSize = Math.max(14/globalScale, 1.5);  // Ensure minimum readable size
          ctx.font = `${fontSize}px Sans-Serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          
          // Draw background for better readability
          const textWidth = ctx.measureText(label).width;
          const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);
          ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
          ctx.fillRect(
            node.x! - bckgDimensions[0] / 2,
            node.y! - bckgDimensions[1] / 2,
            bckgDimensions[0],
            bckgDimensions[1]
          );
          
          // Draw text
          ctx.fillStyle = selectedCategories.has(n.category) ? '#2D3748' : '#A0AEC0';
          ctx.fillText(label, node.x!, node.y!);
        }}
      />
    </div>
  );
}
