import {
  SessionSummary,
  ProviderInfo,
  HealthStatus,
  ArtifactData,
  ConfidenceLevel,
  Citation,
  User,
  AuthResponse,
  CustomProviderCreate,
  ProviderTestRequest,
  ProviderTestResponse
} from '../types';

const RAW_API_URL = (import.meta.env.VITE_API_URL || '').trim();
export const API_BASE = RAW_API_URL 
  ? (RAW_API_URL.endsWith('/api') ? RAW_API_URL : `${RAW_API_URL.replace(/\/$/, '')}/api`) 
  : '/api';
const TOKEN_KEY = 'lenny_auth_token';
const CUSTOM_PROVIDERS_KEY = 'lenny_custom_providers';

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function getStoredCustomProviders(): CustomProviderCreate[] {
  try {
    const raw = localStorage.getItem(CUSTOM_PROVIDERS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

export function saveStoredCustomProvider(config: CustomProviderCreate): void {
  const stored = getStoredCustomProviders();
  const existingIdx = stored.findIndex((p) => p.id === config.id || (p.name === config.name && p.model_name === config.model_name));
  if (existingIdx >= 0) {
    stored[existingIdx] = config;
  } else {
    stored.push(config);
  }
  localStorage.setItem(CUSTOM_PROVIDERS_KEY, JSON.stringify(stored));
}

export function removeStoredCustomProvider(providerId: string): void {
  const stored = getStoredCustomProviders().filter((p) => p.id !== providerId);
  localStorage.setItem(CUSTOM_PROVIDERS_KEY, JSON.stringify(stored));
}

export async function restoreStoredCustomProviders(): Promise<void> {
  const stored = getStoredCustomProviders();
  for (const prov of stored) {
    try {
      await addCustomProvider(prov, false);
    } catch (e) {
      console.warn('Failed to restore custom provider:', prov.name, e);
    }
  }
}

function getAuthHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function registerUser(data: { email: string; password: string; full_name?: string }): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(err.detail || 'Registration failed');
  }
  const authRes: AuthResponse = await res.json();
  setAuthToken(authRes.access_token);
  return authRes;
}

export async function loginUser(data: { email: string; password: string }): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Invalid email or password' }));
    throw new Error(err.detail || 'Invalid email or password');
  }
  const authRes: AuthResponse = await res.json();
  setAuthToken(authRes.access_token);
  return authRes;
}

export async function fetchCurrentUser(): Promise<User> {
  const token = getAuthToken();
  if (!token) throw new Error('No auth token stored');
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    removeAuthToken();
    throw new Error('Session expired or invalid');
  }
  return res.json();
}

export function logoutUser(): void {
  removeAuthToken();
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchProviders(): Promise<ProviderInfo[]> {
  const res = await fetch(`${API_BASE}/providers`);
  if (!res.ok) throw new Error('Failed to fetch providers');
  return res.json();
}

export async function selectProvider(provider: string, model?: string, apiKey?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/providers/select`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ provider, model, api_key: apiKey }),
  });
  if (!res.ok) throw new Error('Failed to switch provider');
  return res.json();
}

export async function addCustomProvider(data: CustomProviderCreate, persist: boolean = true): Promise<ProviderInfo> {
  const res = await fetch(`${API_BASE}/providers/custom`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to add custom provider' }));
    throw new Error(err.detail || 'Failed to add custom provider');
  }
  const created: ProviderInfo = await res.json();
  if (persist) {
    saveStoredCustomProvider({ ...data, id: created.id });
  }
  return created;
}

export async function deleteCustomProvider(providerId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/providers/custom/${providerId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to delete custom provider');
  removeStoredCustomProvider(providerId);
  return res.json();
}

export async function testProviderConnection(data: ProviderTestRequest): Promise<ProviderTestResponse> {
  const res = await fetch(`${API_BASE}/providers/test`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Connection test failed' }));
    throw new Error(err.detail || 'Connection test failed');
  }
  return res.json();
}


export async function fetchSessions(): Promise<SessionSummary[]> {
  const res = await fetch(`${API_BASE}/sessions`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch sessions');
  return res.json();
}

export async function createSession(title?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ title: title || 'New Conversation' }),
  });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function fetchSession(sessionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load session');
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to delete session');
  return res.json();
}


export interface StreamCallbacks {
  onSessionInit?: (sessionId: string) => void;
  onRouting?: (data: { skill: string; rationale: string; confidence: number }) => void;
  onGrounding?: (data: {
    confidence_level: ConfidenceLevel;
    confidence_score: number;
    is_refusal: boolean;
    refusal_reason?: string;
    citations: Citation[];
  }) => void;
  onToken?: (token: string) => void;
  onArtifact?: (artifact: ArtifactData) => void;
  onError?: (err: string) => void;
  onDone?: () => void;
}

export async function streamChat(
  message: string,
  sessionId?: string,
  provider?: string,
  callbacks: StreamCallbacks = {}
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        session_id: sessionId,
        message,
        provider,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      callbacks.onError?.(`API Error (${response.status}): ${errText}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError?.('No response body stream');
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmed.slice(6));
            if (data.type === 'session_init') {
              callbacks.onSessionInit?.(data.session_id);
            } else if (data.type === 'routing') {
              callbacks.onRouting?.(data);
            } else if (data.type === 'grounding') {
              callbacks.onGrounding?.(data);
            } else if (data.type === 'chunk') {
              callbacks.onToken?.(data.content);
            } else if (data.type === 'artifact') {
              callbacks.onArtifact?.(data.artifact);
            } else if (data.type === 'done') {
              callbacks.onDone?.();
            }
          } catch (e) {
            console.error('SSE JSON parse error:', e, trimmed);
          }
        }
      }
    }
  } catch (err: any) {
    callbacks.onError?.(`Connection error: ${err.message || err}`);
  }
}
