'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { ColorwayListItem } from '@/lib/types';
import ColorwayCarousel from '@/components/colorway/ColorwayCarousel';
import { ArrowLeft, Download } from 'lucide-react';

export default function ColorwaysPage() {
  const router = useRouter();
  const params = useParams();
  
  const [colorways, setColorways] = useState<ColorwayListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      loadColorways(params.id as string);
    }
  }, [params.id]);

  const loadColorways = async (designId: string) => {
    try {
      const data = await api.colorways.list(designId);
      setColorways(data);
    } catch (error) {
      console.error('Failed to load colorways:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push(`/design/${params.id}`)}
                className="p-2 hover:bg-gray-100 rounded-md transition-colors"
              >
                <ArrowLeft size={20} />
              </button>
              <h1 className="text-xl font-bold text-gray-900">Colorway Variants</h1>
            </div>
            
            {colorways.length > 0 && (
              <a
                href={api.download.getBundleUrl(params.id as string)}
                download
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <Download size={20} />
                Download All (ZIP)
              </a>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading colorways...</div>
        ) : colorways.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No colorways generated yet.
          </div>
        ) : (
          <ColorwayCarousel colorways={colorways} />
        )}
      </main>
    </div>
  );
}
