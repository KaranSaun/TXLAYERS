'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useStore } from '@/lib/store';
import { DesignListItem } from '@/lib/types';
import { formatDate, getStatusColor } from '@/lib/utils';
import DropZone from '@/components/upload/DropZone';
import { LogOut, Upload } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout, isAuthenticated } = useStore();
  
  const [designs, setDesigns] = useState<DesignListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/');
      return;
    }
    
    loadDesigns();
  }, []);

  const loadDesigns = async () => {
    try {
      const data = await api.designs.list();
      setDesigns(data);
    } catch (error) {
      console.error('Failed to load designs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    try {
      const response = await api.designs.upload(file);
      router.push(`/design/${response.design_id}`);
    } catch (error: any) {
      alert(error.message || 'Upload failed');
      setUploading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">TexLayerAI</h1>
            {user && <p className="text-sm text-gray-600">{user.name}</p>}
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Upload size={24} />
            Upload New Design
          </h2>
          <DropZone onFileSelect={handleFileUpload} disabled={uploading} />
          {uploading && (
            <div className="mt-4 text-center text-blue-600 font-medium">
              Uploading and processing...
            </div>
          )}
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Designs</h2>
          
          {loading ? (
            <div className="text-center py-12 text-gray-500">Loading designs...</div>
          ) : designs.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No designs yet. Upload your first design above!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {designs.map((design) => (
                <div
                  key={design.id}
                  className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer overflow-hidden"
                  onClick={() => router.push(`/design/${design.id}`)}
                >
                  <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                    <div className="text-gray-400 text-sm">Design Preview</div>
                  </div>
                  
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 truncate mb-2">
                      {design.original_filename}
                    </h3>
                    
                    <div className="flex items-center justify-between mb-2">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium text-white ${getStatusColor(
                          design.status
                        )}`}
                      >
                        {design.status.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatDate(design.created_at)}
                      </span>
                    </div>
                    
                    <button className="w-full mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium">
                      Open Design
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
