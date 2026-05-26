import {
  AuthResponse,
  Design,
  DesignListItem,
  Job,
  JobProgress,
  Colorway,
  ColorwayListItem,
  UploadResponse,
} from './types';

// Hardcoded API URL
const API_URL = 'http://localhost/api';

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

function getAuthHeaders(): HeadersInit {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || error.message || 'Request failed');
  }
  return response.json();
}

export const api = {
  auth: {
    async register(email: string, password: string, name: string): Promise<AuthResponse> {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
      });
      return handleResponse<AuthResponse>(response);
    },

    async login(email: string, password: string): Promise<AuthResponse> {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      return handleResponse<AuthResponse>(response);
    },
  },

  designs: {
    async upload(file: File): Promise<UploadResponse> {
      const formData = new FormData();
      formData.append('file', file);

      const token = getAuthToken();
      const response = await fetch(`${API_URL}/designs/upload`, {
        method: 'POST',
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: formData,
      });
      return handleResponse<UploadResponse>(response);
    },

    async list(): Promise<DesignListItem[]> {
      const response = await fetch(`${API_URL}/designs`, {
        headers: getAuthHeaders(),
      });
      return handleResponse<DesignListItem[]>(response);
    },

    async get(id: string): Promise<Design> {
      const response = await fetch(`${API_URL}/designs/${id}`, {
        headers: getAuthHeaders(),
      });
      return handleResponse<Design>(response);
    },

    async delete(id: string): Promise<{ message: string }> {
      const response = await fetch(`${API_URL}/designs/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      return handleResponse<{ message: string }>(response);
    },
  },

  jobs: {
    async getStatus(id: string): Promise<Job> {
      const response = await fetch(`${API_URL}/jobs/${id}`, {
        headers: getAuthHeaders(),
      });
      return handleResponse<Job>(response);
    },

    async getProgress(id: string): Promise<JobProgress> {
      const response = await fetch(`${API_URL}/jobs/${id}/progress`, {
        headers: getAuthHeaders(),
      });
      return handleResponse<JobProgress>(response);
    },

    streamStatus(id: string, onUpdate: (progress: JobProgress) => void): EventSource {
      const token = getAuthToken();
      const url = `${API_URL}/jobs/${id}/stream`;
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onUpdate(data);
      };

      return eventSource;
    },
  },

  colorways: {
    async list(designId: string): Promise<ColorwayListItem[]> {
      const response = await fetch(`${API_URL}/colorways/designs/${designId}/colorways`, {
        headers: getAuthHeaders(),
      });
      return handleResponse<ColorwayListItem[]>(response);
    },

    async get(id: string): Promise<Colorway> {
      const response = await fetch(`${API_URL}/colorways/${id}`, {
        headers: getAuthHeaders(),
      });
      return handleResponse<Colorway>(response);
    },

    async generate(designId: string): Promise<{ message: string; task_id: string }> {
      const response = await fetch(`${API_URL}/colorways/designs/${designId}/colorways/generate`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
      return handleResponse<{ message: string; task_id: string }>(response);
    },

    async createManual(
      designId: string,
      name: string,
      colorMap: Record<string, string>
    ): Promise<{ message: string; task_id: string }> {
      const response = await fetch(`${API_URL}/colorways/designs/${designId}/colorways/manual`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ name, color_map: colorMap }),
      });
      return handleResponse<{ message: string; task_id: string }>(response);
    },

    getDownloadUrl(id: string, type: 'tif' | 'preview'): string {
      const token = getAuthToken();
      return `${API_URL}/download/colorways/${id}/${type}?token=${token}`;
    },
  },

  download: {
    getMasterTifUrl(designId: string): string {
      const token = getAuthToken();
      return `${API_URL}/download/designs/${designId}/tif?token=${token}`;
    },

    getBundleUrl(designId: string): string {
      const token = getAuthToken();
      return `${API_URL}/download/designs/${designId}/bundle?token=${token}`;
    },
  },
};
