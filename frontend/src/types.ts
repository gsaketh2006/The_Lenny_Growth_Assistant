export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';

export interface Citation {
  chunk_id: string;
  episode_id: string;
  episode_title: string;
  guest_name: string;
  episode_url?: string;
  publication_date?: string;
  snippet: string;
  similarity_score: number;
}

export interface ArtifactData {
  id?: string;
  title: string;
  artifact_type: 'markdown' | 'html' | 'growth_experiment';
  content: string;
  structured_data?: any;
  version?: number;
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  skill_used?: string;
  routing_rationale?: string;
  confidence_level?: ConfidenceLevel;
  confidence_score?: number;
  citations?: Citation[];
  artifact?: ArtifactData;
  created_at?: string;
  isStreaming?: boolean;
}

export interface SessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ProviderInfo {
  id: string;
  name: string;
  is_available: boolean;
  is_active: boolean;
  current_model: string;
  available_models: string[];
  notes?: string;
  is_custom?: boolean;
}

export interface CustomProviderCreate {
  id?: string;
  name: string;
  api_type: 'openai_compatible' | 'anthropic_compatible' | 'ollama_compatible';
  base_url: string;
  model_name: string;
  api_key?: string;
  notes?: string;
}

export interface ProviderTestRequest {
  api_type: 'openai_compatible' | 'anthropic_compatible' | 'ollama_compatible';
  base_url: string;
  model_name: string;
  api_key?: string;
}

export interface ProviderTestResponse {
  success: boolean;
  latency_ms: number;
  message: string;
  sample_output?: string;
}


export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface HealthStatus {
  status: string;
  database_connected: boolean;
  active_provider: string;
  ollama_online: boolean;
  transcripts_indexed_count: number;
  version: string;
}

