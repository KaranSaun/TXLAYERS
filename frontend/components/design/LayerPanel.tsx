'use client';

import { Layer } from '@/lib/types';
import { useStore } from '@/lib/store';
import { Eye, EyeOff } from 'lucide-react';

interface LayerPanelProps {
  layers: Layer[];
}

export default function LayerPanel({ layers }: LayerPanelProps) {
  const { visibleLayers, toggleLayer, showAllLayers, hideAllLayers } = useStore();

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Layers</h3>
        <div className="flex gap-2">
          <button
            onClick={showAllLayers}
            className="text-xs px-2 py-1 text-blue-600 hover:bg-blue-50 rounded"
          >
            Show All
          </button>
          <button
            onClick={hideAllLayers}
            className="text-xs px-2 py-1 text-gray-600 hover:bg-gray-100 rounded"
          >
            Hide All
          </button>
        </div>
      </div>

      <div className="space-y-2 max-h-[600px] overflow-y-auto">
        {layers.map((layer) => {
          const isVisible = visibleLayers.has(layer.id);
          
          return (
            <div
              key={layer.id}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <button
                onClick={() => toggleLayer(layer.id)}
                className="flex-shrink-0 p-1 hover:bg-gray-200 rounded"
              >
                {isVisible ? (
                  <Eye size={18} className="text-blue-600" />
                ) : (
                  <EyeOff size={18} className="text-gray-400" />
                )}
              </button>

              <div
                className="w-6 h-6 rounded border border-gray-300 flex-shrink-0"
                style={{ backgroundColor: layer.hex_color }}
              />

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {layer.name}
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span
                    className={`px-1.5 py-0.5 rounded ${
                      layer.role === 'motif' ? 'bg-purple-100 text-purple-700' : 'bg-gray-200 text-gray-700'
                    }`}
                  >
                    {layer.role.toUpperCase()}
                  </span>
                  <span>{layer.coverage_percent.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {layers.length === 0 && (
        <div className="text-center py-8 text-gray-500 text-sm">
          No layers available yet
        </div>
      )}
    </div>
  );
}
