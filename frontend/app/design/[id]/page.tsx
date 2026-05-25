'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { useStore } from '@/lib/store';
import { Design, JobProgress } from '@/lib/types';
import { getStatusColor } from '@/lib/utils';
import LayerPanel from '@/components/design/LayerPanel';
import DesignViewer from '@/components/design/DesignViewer';
import { ArrowLeft, Download, Palette } from 'lucide-react';

export default function DesignDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { setDesign, currentDesign } = useStore();
  
  const [loading, setLoading] = useState(true);
  const [jobProgress, setJobProgress] = useState<JobProgress | null>(null);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    if (params.id) {
      loadDesign(params.id as string);
    }
  }, [params.id]);

  const loadDesign = async (id: string) => {
    try {
      const design = await api.designs.get(id);
      setDesign(design);
      
      if (design.status === 'processing') {
        pollJobStatus(id);
      }
    } catch (error) {
      console.error('Failed to load design:', error);
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = async (designId: string) => {
    setPolling(true);
    const interval = setInterval(async () => {
      try {
        const design = await api.designs.get(designId);
        setDesign(design);
        
        if (design.status !== 'processing') {
          clearInterval(interval);
          setPolling(false);
        }
      } catch (error) {
        clearInterval(interval);
        setPolling(false);
      }
    }, 3000);
  };

  const handleGenerateColorways = async () => {
    if (!currentDesign) return;
    
    try {
      await api.colorways.generate(currentDesign.id);
      alert('Colorway generation started!');
      router.push(`/design/${currentDesign.id}/colorways`);
    } catch (error: any) {
      alert(error.message || 'Failed to generate colorways');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading design...</div>
      </div>
    );
  }

  if (!currentDesign) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Design not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="p-2 hover:bg-gray-100 rounded-md transition-colors"
              >
                <ArrowLeft size={20} />
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  {currentDesign.original_filename}
                </h1>
                <span
                  className={`inline-block px-2 py-1 rounded-full text-xs font-medium text-white ${getStatusColor(
                    currentDesign.status
                  )}`}
                >
                  {currentDesign.status.toUpperCase()}
                </span>
              </div>
            </div>
            
            <div className="flex gap-2">
              {currentDesign.status === 'review' && (
                <>
                  <button
                    onClick={handleGenerateColorways}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                  >
                    <Palette size={20} />
                    Generate Colorways
                  </button>
                  <a
                    href={api.download.getMasterTifUrl(currentDesign.id)}
                    download
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    <Download size={20} />
                    Download TIFF
                  </a>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {polling && (
          <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <p className="text-yellow-800">Processing design... This may take a few minutes.</p>
          </div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-4">
              <DesignViewer design={currentDesign} />
            </div>
          </div>
          
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-4">
              <LayerPanel layers={currentDesign.layers} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
