// cliente de la API del motor (api/src/yapa_sdd/web/api.py): cookie de sesión y token CSRF (S-155)

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

type Fetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export function createApi(fetchImpl: Fetch = (input, init) => fetch(input, init)) {
  let csrf = '';

  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers = new Headers();
    let payload: BodyInit | undefined;
    if (body instanceof FormData) {
      payload = body; // fotos (S-151): el navegador pone el multipart
    } else if (body !== undefined) {
      headers.set('Content-Type', 'application/json');
      payload = JSON.stringify(body);
    }
    if (method !== 'GET' && csrf) headers.set('X-Yapa-CSRF', csrf);
    let response: Response;
    try {
      response = await fetchImpl(path, { method, headers, body: payload, credentials: 'include' });
    } catch {
      throw new ApiError(0, 'NETWORK', 'No pudimos conectar con Yapa. Revisa que el servidor esté encendido.');
    }
    const text = await response.text();
    let data: any = null; // eslint-disable-line @typescript-eslint/no-explicit-any
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      // FE-SG-1: un proxy caído responde HTML; se muestra como cualquier error de Yapa
      throw new ApiError(response.status, 'BAD_RESPONSE', 'Yapa no respondió bien. Intenta de nuevo en un momento.');
    }
    if (!response.ok) {
      const error = data?.error ?? {};
      throw new ApiError(response.status, error.codigo ?? 'ERROR', error.mensaje ?? 'Algo salió mal. Intenta de nuevo.');
    }
    return data as T;
  }

  return {
    setCsrf(token: string) { csrf = token; },
    get: <T>(path: string) => request<T>('GET', path),
    post: <T>(path: string, body: unknown = {}) => request<T>('POST', path, body),
    delete: <T>(path: string) => request<T>('DELETE', path),
  };
}

export const api = createApi();
