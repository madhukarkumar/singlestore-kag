# SingleStore Knowledge Graph Frontend

A modern Next.js application for visualizing and interacting with the SingleStore Knowledge Graph system.

## Features

- **Interactive Knowledge Graph**
  - Force-directed graph visualization
  - Category-based node coloring
  - Dynamic node sizing based on connections
  - Zoom and pan controls
  - Node dragging and hover tooltips

- **Search Interface**
  - Natural language search
  - AI-generated responses
  - Relevance scoring
  - Entity highlighting
  - Real-time results

- **Document Management**
  - PDF upload with progress tracking
  - Document statistics dashboard
  - Processing status updates
  - Error handling and recovery

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm
- Backend API endpoint

### Environment Setup

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000  # or your deployed backend URL on Railway
NEXT_PUBLIC_API_KEY=exampleKey
```

### Installation

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## API Integration

The frontend communicates with the backend through the following endpoints:

1. **Search API**
   ```typescript
   // POST /kag-search
   interface SearchRequest {
     query: string;
     top_k: number;
   }

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
   ```

2. **Knowledge Base Stats**
   ```typescript
   // GET /kbdata
   interface KBStats {
     total_documents: number;
     total_chunks: number;
     total_entities: number;
     total_relationships: number;
     documents: DocumentStats[];
     last_updated: string;
   }
   ```

3. **Graph Data**
   ```typescript
   // GET /graph-data
   interface GraphData {
     nodes: GraphNode[];
     links: GraphLink[];
   }
   ```

## Deployment

### Railway Deployment

1. **Connect Repository**
   - Link your GitHub repository to Railway
   - Select the frontend directory as the source

2. **Configure Build**
   ```bash
   # Build command
   pnpm install && pnpm build

   # Start command
   pnpm start
   ```

3. **Environment Variables**
   Add to Railway dashboard:
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_API_KEY`

### Manual Build

```bash
# Production build
pnpm build

# Start production server
pnpm start
```

## Development

### Code Structure

```
frontend/
├── app/              # Next.js app router pages
├── components/       # React components
│   ├── KnowledgeGraph.tsx    # Graph visualization
│   ├── SearchForm.tsx        # Search interface
│   └── ...
├── utils/           # Utility functions
│   └── api.ts       # API client
└── public/          # Static assets
```

### Key Components

- `KnowledgeGraph`: Force-directed graph visualization
- `SearchForm`: Search interface with AI responses
- `NavHeader`: Navigation and layout component
- `ProcessingStatus`: Upload progress tracking

### Styling

- Tailwind CSS for styling
- Custom theme configuration in `tailwind.config.ts`
- Responsive design with mobile-first approach

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
