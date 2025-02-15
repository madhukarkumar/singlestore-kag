// Base API URL and API key from environment variables
export const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || '',
  }
};

// Fetch wrapper with authentication
export const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) => {
  const url = endpoint.startsWith('http') ? endpoint : `${API_CONFIG.baseURL}${endpoint}`;
  const headers = {
    ...API_CONFIG.headers,
    ...options.headers,
  };
  
  return fetch(url, {
    ...options,
    headers,
  });
};

// Common fetch options for JSON requests
const defaultOptions: RequestInit = {
  headers: {
    'Content-Type': 'application/json',
  }
};

// API endpoints
export const endpoints = {
  kbData: '/kbdata',
  config: '/config',
  upload: '/upload-pdf',
  search: '/kag-search',
  graph: '/graph-data',
  taskStatus: (taskId: string) => `/task-status/${taskId}`,
  cancelProcessing: '/cancel-processing',
} as const;

// Response types
export interface APIErrorResponse {
  detail: string;
}

// API client functions
export const api = {
  // GET request wrapper
  async get<T>(endpoint: keyof typeof endpoints, params?: Record<string, string>): Promise<T> {
    let urlStr: string;
    if (typeof endpoints[endpoint] === 'function') {
      urlStr = `${API_CONFIG.baseURL}${(endpoints[endpoint] as Function)(params?.taskId)}`;
    } else {
      const url = new URL(endpoints[endpoint], API_CONFIG.baseURL);
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (key !== 'taskId') { // Skip taskId as it's handled above
            url.searchParams.append(key, value);
          }
        });
      }
      urlStr = url.toString();
    }

    const response = await fetchWithAuth(urlStr, defaultOptions);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || 'API request failed');
    }
    return response.json();
  },

  // POST request wrapper
  async post<T>(endpoint: keyof typeof endpoints, data?: any): Promise<T> {
    const response = await fetchWithAuth(`${API_CONFIG.baseURL}${endpoints[endpoint]}`, {
      ...defaultOptions,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || 'API request failed');
    }
    return response.json();
  },

  // File upload wrapper
  async uploadFile<T>(endpoint: keyof typeof endpoints, file: File): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetchWithAuth(`${API_CONFIG.baseURL}${endpoints[endpoint]}`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || 'File upload failed');
    }
    return response.json();
  },
};
