'use client';

import { Design } from '@/lib/types';
import { useStore } from '@/lib/store';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api';

function getLayerImageUrl(maskStoragePath: string): string {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : '';
  return `${API_URL}/download/layers/${encodeURIComponent(maskStoragePath)}?token=${token}`;
}

function getDesignImageUrl(uploadStoragePath: string): string {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : '';
  return `${API_URL}/download/preview/${encodeURIComponent(uploadStoragePath)}?token=${token}`;
}

interface DesignViewerProps {
  design: Design;
}

export default function DesignViewer({ design }: DesignViewerProps) {
  const { visibleLayers } = useStore();

  const visibleLayerList = design.layers.filter((l) => visibleLayers.has(l.id));

  return (
    <div className="relative w-full bg-gray-100 rounded-lg overflow-hidden" style={{ minHeight: '400px' }}>
      {design.layers.length === 0 ? (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400">
          Processing design...
        </div>
      ) : (
        <div className="relative w-full h-full">
          {/* Base image */}
          <img
            src={getDesignImageUrl(design.upload_storage_path)}
            alt="Design"
            className="w-full h-auto block"
            style={{ opacity: visibleLayerList.length > 0 ? 0.3 : 1 }}
          />
          {/* Layer overlays — stacked using mix-blend-mode multiply */}
          {visibleLayerList.map((layer) => (
            <img
              key={layer.id}
              src={getLayerImageUrl(layer.mask_storage_path)}
              alt={layer.name}
              className="absolute inset-0 w-full h-full object-cover"
              style={{ mixBlendMode: 'multiply', opacity: 0.85 }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
