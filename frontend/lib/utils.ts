import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    uploaded: 'bg-gray-500',
    processing: 'bg-yellow-500',
    review: 'bg-green-500',
    approved: 'bg-blue-500',
    exported: 'bg-purple-500',
    queued: 'bg-gray-400',
    upscaling: 'bg-yellow-400',
    segmenting: 'bg-yellow-500',
    clustering: 'bg-yellow-600',
    building: 'bg-blue-400',
    generating: 'bg-blue-500',
    done: 'bg-green-500',
    failed: 'bg-red-500',
  };
  return colors[status] || 'bg-gray-500';
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
