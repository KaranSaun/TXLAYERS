export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Layer {
  id: string;
  layer_index: number;
  name: string;
  role: string;
  hex_color: string;
  coverage_percent: number;
  mask_storage_path: string;
}

export interface Design {
  id: string;
  user_id: string;
  original_filename: string;
  original_dpi: number | null;
  width_px: number | null;
  height_px: number | null;
  upload_storage_path: string;
  upscaled_storage_path: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  layers: Layer[];
}

export interface DesignListItem {
  id: string;
  original_filename: string;
  status: string;
  created_at: string;
  upload_storage_path: string;
}

export interface Job {
  id: string;
  design_id: string;
  status: string;
  current_step: number;
  total_steps: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface JobProgress {
  id: string;
  design_id: string;
  status: string;
  current_step: number;
  total_steps: number;
  progress_percent: number;
  error_message: string | null;
}

export interface Colorway {
  id: string;
  design_id: string;
  variant_index: number;
  name: string;
  variant_type: string;
  color_map: Record<string, string>;
  tif_storage_path: string;
  preview_storage_path: string;
  created_at: string;
}

export interface ColorwayListItem {
  id: string;
  variant_index: number;
  name: string;
  variant_type: string;
  preview_storage_path: string;
  created_at: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface UploadResponse {
  design_id: string;
  job_id: string;
  message: string;
}
