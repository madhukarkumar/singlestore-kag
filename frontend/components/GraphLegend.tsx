'use client';

import { categoryColors } from '@/lib/constants';

interface LegendProps {
  categories: string[];
  onCategoryToggle: (category: string) => void;
  activeCategories: Set<string>;
}

export default function GraphLegend({ categories, onCategoryToggle, activeCategories }: LegendProps) {
  return (
    <div className="absolute top-4 right-4 bg-white/90 p-4 rounded-lg shadow-md backdrop-blur-sm">
      <h3 className="text-sm font-semibold mb-2">Entity Types</h3>
      <div className="space-y-2">
        {categories.map((category, index) => (
          <button
            key={category}
            onClick={() => onCategoryToggle(category)}
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
  );
}
