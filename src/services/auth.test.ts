import { beforeEach, describe, expect, it, vi } from 'vitest';

const rows = new Map<string, Record<string, unknown>>();
const notFound = Object.assign(new Error('Row not found'), { code: 404 });
const conflict = Object.assign(new Error('Row already exists'), { code: 409 });

const tables = {
  getRow: vi.fn(async ({ rowId }: { rowId: string }) => {
    await Promise.resolve();
    const row = rows.get(rowId);
    if (!row) throw notFound;
    return row;
  }),
  createRow: vi.fn(async ({ rowId, data }: { rowId: string; data: Record<string, unknown> }) => {
    await Promise.resolve();
    if (rows.has(rowId)) throw conflict;
    rows.set(rowId, data);
    return data;
  }),
};

const session = { labels: [] as string[] };

vi.mock('./appwrite', () => ({
  adminLabel: 'admin',
  appwriteReady: true,
  appwriteAccount: { get: async () => ({ $id: 'u1', email: 'vecina@yapa.pe', name: 'Vecina', labels: session.labels }) },
  appwriteTables: tables,
  databaseId: 'yapa',
  tableIds: { profiles: 'profiles' },
  profilePermissions: () => [],
}));

const { getSessionAccount } = await import('./auth');

describe('perfil de Appwrite al iniciar sesión', () => {
  beforeEach(() => {
    rows.clear();
    session.labels = [];
    vi.clearAllMocks();
  });

  it('el rol de admin sale de la etiqueta, no del campo role que el usuario puede editar', async () => {
    rows.set('u1', { name: 'Vecina', role: 'admin' });
    expect((await getSessionAccount())?.role).toBe('customer');
    session.labels = ['admin'];
    expect((await getSessionAccount())?.role).toBe('admin');
  });

  it('dos cargas a la vez (StrictMode) crean el perfil una sola vez y no fallan', async () => {
    const [first, second] = await Promise.all([getSessionAccount(), getSessionAccount()]);
    expect(first?.id).toBe('u1');
    expect(second?.id).toBe('u1');
    expect(tables.createRow).toHaveBeenCalledTimes(1);
  });

  it('si el perfil ya existe cuando intenta crearlo, lo lee en vez de fallar', async () => {
    tables.getRow.mockRejectedValueOnce(notFound);
    rows.set('u1', { name: 'Vecina', phone: '987654321', district: 'Lince', role: 'customer' });
    const account = await getSessionAccount();
    expect(account?.phone).toBe('987654321');
  });
});
