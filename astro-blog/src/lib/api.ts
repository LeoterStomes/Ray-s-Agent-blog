import { API } from './constants';

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
}

class ApiError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = 'ApiError';
  }
}

/** 创建带超时的 fetch */
function fetchWithTimeout(url: string, config: RequestInit, timeoutMs: number): Promise<Response> {
  if (!AbortController || timeoutMs <= 0) {
    return fetch(url, config);
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, { ...config, signal: controller.signal }).finally(() => clearTimeout(timer));
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;

  const { body, ...init } = options;

  const config: RequestInit = {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { token } : {}),
      ...(init.headers as Record<string, string>),
    },
  };

  if (body && typeof body !== 'string') {
    config.body = JSON.stringify(body);
  }

  const url = `${API.BASE}${path}`;

  let res: Response;
  try {
    res = await fetchWithTimeout(url, config, API.TIMEOUT);
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('TIMEOUT', '请求超时，请稍后重试');
    }
    throw new ApiError('NETWORK', '网络连接失败，请检查网络后重试');
  }

  const json = await res.json().catch(() => null);

  if (!json || json.code !== '200') {
    const msg = json?.msg || `请求失败 (${res.status})`;
    throw new ApiError(json?.code || String(res.status), msg);
  }

  return json.data as T;
}

export { request, ApiError };
export type { RequestOptions };
