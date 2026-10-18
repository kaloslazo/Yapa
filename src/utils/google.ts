export interface GoogleCredentialResponse {
  credential: string;
}

interface GoogleIdApi {
  initialize: (config: { client_id: string; callback: (response: GoogleCredentialResponse) => void }) => void;
  renderButton: (element: HTMLElement, options: Record<string, unknown>) => void;
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleIdApi } };
  }
}

const SCRIPT_URL = 'https://accounts.google.com/gsi/client';
let loading: Promise<void> | null = null;

// GO-07: el script de Google solo se pide cuando hay un Client ID y se muestra el botón
export function loadGoogle(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve();
  if (!loading) {
    loading = new Promise<void>((resolve, reject) => {
      const script = document.createElement('script');
      script.src = SCRIPT_URL;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => { loading = null; reject(new Error('No pudimos cargar Google.')); };
      document.head.appendChild(script);
    });
  }
  return loading;
}
