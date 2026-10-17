import { ID } from 'appwrite';
import { adminLabel, appwriteAccount, appwriteReady, appwriteTables, databaseId, profilePermissions, tableIds } from './appwrite';
import { readStored, writeStored } from '../utils/storage';
import type { AccountProfile } from '../types';

interface AccountRecord extends AccountProfile {
  password: string;
}

const ACCOUNTS_KEY = 'yapa.accounts';
const CURRENT_ACCOUNT_KEY = 'yapa.current-account';
const DEMO_ADMIN_EMAIL = 'admin@yapa.pe';
const DEMO_ADMIN_PASSWORD = 'admin123';

function normalizeEmail(email: string) {
  return email.trim().toLowerCase();
}

function toProfile(record: Partial<AccountRecord> & { id: string; email: string }): AccountProfile {
  return {
    id: record.id,
    name: record.name || record.email.split('@')[0],
    phone: record.phone || '',
    district: record.district || 'Lince',
    email: normalizeEmail(record.email),
    role: record.role === 'admin' ? 'admin' : 'customer',
  };
}

function getLocalAccounts() {
  const accounts = readStored<AccountRecord[]>(ACCOUNTS_KEY, []);
  const hasDemoAdmin = accounts.some((account) => normalizeEmail(account.email) === DEMO_ADMIN_EMAIL);
  if (hasDemoAdmin) return accounts;

  const demoAdmin: AccountRecord = {
    id: 'local-demo-admin',
    name: 'Admin Yapa',
    phone: '',
    district: 'Lince',
    email: DEMO_ADMIN_EMAIL,
    role: 'admin',
    password: DEMO_ADMIN_PASSWORD,
  };
  const next = [...accounts, demoAdmin];
  writeStored(ACCOUNTS_KEY, next);
  return next;
}

function isErrorCode(error: unknown, code: number) {
  return typeof error === 'object' && error !== null && 'code' in error && (error as { code?: number }).code === code;
}

function appwriteErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

// el rol sale de la etiqueta de Appwrite (solo se cambia desde la consola o con la API key);
// el campo role del perfil no sirve porque cada usuario puede editar su propia fila
function accountRole(user: { labels?: string[] }): AccountProfile['role'] {
  return user.labels?.includes(adminLabel) ? 'admin' : 'customer';
}

async function readAppwriteProfile(userId: string, fallback: AccountProfile): Promise<AccountProfile> {
  const row = await appwriteTables!.getRow({ databaseId, tableId: tableIds.profiles, rowId: userId });
  const data = row as Record<string, unknown>;
  return toProfile({
    ...fallback,
    id: userId,
    name: String(data.name || fallback.name),
    phone: String(data.phone || fallback.phone),
    district: String(data.district || fallback.district),
    email: fallback.email,
  });
}

async function readOrCreateProfile(userId: string, fallback: AccountProfile): Promise<AccountProfile> {
  try {
    return await readAppwriteProfile(userId, fallback);
  } catch (error) {
    if (!isErrorCode(error, 404)) throw new Error(`No pudimos cargar tu perfil: ${appwriteErrorMessage(error, 'error desconocido')}`);
  }

  try {
    await appwriteTables!.createRow({
      databaseId,
      tableId: tableIds.profiles,
      rowId: userId,
      data: {
        email: fallback.email,
        name: fallback.name,
        phone: fallback.phone,
        district: fallback.district,
        role: 'customer',
        createdAt: new Date().toISOString(),
      },
      permissions: profilePermissions(userId),
    });
    return fallback;
  } catch (error) {
    if (!isErrorCode(error, 409)) throw error;
    // otra carga ya creó el perfil: se lee ese; si no se puede leer, se sigue con los datos de la cuenta
    return readAppwriteProfile(userId, fallback).catch(() => fallback);
  }
}

// StrictMode monta dos veces en desarrollo: sin esto, dos cargas a la vez intentan crear el mismo perfil
const profileRequests = new Map<string, Promise<AccountProfile>>();

function loadAppwriteProfile(userId: string, fallback: AccountProfile): Promise<AccountProfile> {
  if (!appwriteAccount || !appwriteTables || !appwriteReady) return Promise.resolve(fallback);
  const pending = profileRequests.get(userId);
  if (pending) return pending;
  const request = readOrCreateProfile(userId, fallback).finally(() => profileRequests.delete(userId));
  profileRequests.set(userId, request);
  return request;
}

async function getAppwriteUser() {
  if (!appwriteAccount || !appwriteReady) return null;
  try {
    return await appwriteAccount.get();
  } catch (error) {
    if (isErrorCode(error, 404) || isErrorCode(error, 401)) return null;
    throw new Error(`No pudimos validar tu sesión: ${appwriteErrorMessage(error, 'error desconocido')}`);
  }
}

export async function registerAccount(input: Omit<AccountRecord, 'id' | 'role'>): Promise<AccountProfile> {
  const email = normalizeEmail(input.email);
  if (appwriteReady && appwriteAccount) {
    try {
      const activeUser = await getAppwriteUser();
      if (activeUser) throw new Error('Ya hay una cuenta abierta en este dispositivo. Cierra sesión antes de crear otra.');
      const user = await appwriteAccount.create({ userId: ID.unique(), email, password: input.password, name: input.name });
      await appwriteAccount.createEmailPasswordSession({ email, password: input.password });
      const profile = await loadAppwriteProfile(user.$id, { ...input, id: user.$id, email, role: 'customer' });
      writeStored(CURRENT_ACCOUNT_KEY, profile);
      return profile;
    } catch (error) {
      throw new Error(appwriteErrorMessage(error, 'No pudimos crear tu cuenta en Yapa.'));
    }
  }

  const records = getLocalAccounts();
  if (records.some((record) => normalizeEmail(record.email) === email)) {
    throw new Error('Ya existe una cuenta con ese correo. Intenta ingresar.');
  }
  const profile = toProfile({ ...input, id: crypto.randomUUID(), email, role: 'customer' });
  writeStored(ACCOUNTS_KEY, [...records, { ...profile, password: input.password }]);
  writeStored(CURRENT_ACCOUNT_KEY, profile);
  return profile;
}

export async function loginAccount(emailInput: string, password: string): Promise<AccountProfile> {
  const email = normalizeEmail(emailInput);
  if (appwriteReady && appwriteAccount) {
    try {
      const activeUser = await getAppwriteUser();
      if (activeUser) {
        if (normalizeEmail(activeUser.email || '') !== email) {
          throw new Error('Ya hay otra cuenta abierta. Cierra sesión para cambiar de usuario.');
        }
        const profile = await loadAppwriteProfile(activeUser.$id, {
          id: activeUser.$id,
          name: activeUser.name || email.split('@')[0],
          phone: '',
          district: 'Lince',
          email: activeUser.email || email,
          role: accountRole(activeUser),
        });
        writeStored(CURRENT_ACCOUNT_KEY, profile);
        return profile;
      }
      await appwriteAccount.createEmailPasswordSession({ email, password });
      const user = await appwriteAccount.get();
      const profile = await loadAppwriteProfile(user.$id, {
        id: user.$id,
        name: user.name || email.split('@')[0],
        phone: '',
        district: 'Lince',
        email: user.email || email,
        role: accountRole(user),
      });
      writeStored(CURRENT_ACCOUNT_KEY, profile);
      return profile;
    } catch (error) {
      throw new Error(appwriteErrorMessage(error, 'Correo o contraseña incorrectos.'));
    }
  }

  const record = getLocalAccounts().find((item) => normalizeEmail(item.email) === email && item.password === password);
  if (!record) throw new Error('Correo o contraseña incorrectos.');
  const profile = toProfile(record);
  writeStored(CURRENT_ACCOUNT_KEY, profile);
  return profile;
}

export async function getSessionAccount(): Promise<AccountProfile | null> {
  if (!appwriteReady || !appwriteAccount) return getCurrentAccount();
  const user = await getAppwriteUser();
  if (!user) {
    window.localStorage.removeItem(CURRENT_ACCOUNT_KEY);
    return null;
  }
  const profile = await loadAppwriteProfile(user.$id, {
    id: user.$id,
    name: user.name || user.email?.split('@')[0] || 'Amigo',
    phone: '',
    district: 'Lince',
    email: user.email || '',
    role: accountRole(user),
  });
  writeStored(CURRENT_ACCOUNT_KEY, profile);
  return profile;
}

export function getCurrentAccount(): AccountProfile | null {
  const stored = readStored<Partial<AccountProfile> | null>(CURRENT_ACCOUNT_KEY, null);
  return stored?.id && stored.email ? toProfile(stored as AccountProfile) : null;
}

export async function signOutAccount(): Promise<void> {
  if (appwriteReady && appwriteAccount) {
    try {
      await appwriteAccount.deleteSession({ sessionId: 'current' });
    } catch (error) {
      if (!isErrorCode(error, 404) && !isErrorCode(error, 401)) {
        throw new Error(appwriteErrorMessage(error, 'No pudimos cerrar tu sesión.'));
      }
    }
  }
  window.localStorage.removeItem(CURRENT_ACCOUNT_KEY);
}

export async function requestPasswordReset(emailInput: string): Promise<void> {
  const email = normalizeEmail(emailInput);
  if (!appwriteReady || !appwriteAccount) throw new Error('La recuperación por correo requiere conectar Appwrite.');
  try {
    await appwriteAccount.createRecovery({ email, url: window.location.origin });
  } catch (error) {
    throw new Error(appwriteErrorMessage(error, 'No pudimos enviar el correo de recuperación.'));
  }
}

export function isAdminAccount(account: AccountProfile | null) {
  return account?.role === 'admin';
}

export const authMode: 'appwrite' | 'local' = appwriteReady ? 'appwrite' : 'local';
export const localDemoAdmin = { email: DEMO_ADMIN_EMAIL, password: DEMO_ADMIN_PASSWORD };
