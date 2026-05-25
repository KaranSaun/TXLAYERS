'use client';

import { ColorwayListItem } from '@/lib/types';
import { api } from '@/lib/api';
import { Download } from 'lucide-react';

const VARIANT_TYPE_LABELS: Record<string, string> = {
  hue_shift: 'Hue Shift',
  background_swap: 'Background',
  seasonal: 'Seasonal',
  complementary: 'Complementary',
  monochromatic: 'Monochromatic',
  motif_only: 'Motif Only',
  full: 'Full Design',
  manual: 'Manual',
};

interface ColorwayCarouselProps {
  colorways: ColorwayListItem[];
}

export default function ColorwayCarousel({ colorways }: ColorwayCarouselProps) {
  // Deduplicate by name — keep only first occurrence
  const seen = new Set<string>();
  const unique = colorways.filter((c) => {
    if (seen.has(c.name)) return false;
    seen.add(c.name);
    return true;
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {unique.map((colorway) => (
        <div
          key={colorway.id}
          className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow"
        >
          {/* Preview image */}
          <div className="aspect-square bg-gray-100 overflow-hidden">
            <img
              src={api.colorways.getDownloadUrl(colorway.id, 'preview')}
              alt={colorway.name}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
                (e.target as HTMLImageElement).parentElement!.innerHTML =
                  '<div class="w-full h-full flex items-center justify-center text-gray-400 text-sm">Preview unavailable</div>';
              }}
            />
          </div>

          <div className="p-4">
            <h3 className="font-semibold text-gray-900 mb-1">{colorway.name}</h3>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">
                {VARIANT_TYPE_LABELS[colorway.variant_type] || colorway.variant_type}
              </span>
              <span className="text-xs text-gray-400">Variant #{colorway.variant_index + 1}</span>
            </div>
            <a
              href={api.colorways.getDownloadUrl(colorway.id, 'tif')}
              download
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <Download size={16} />
              Download TIFF
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
