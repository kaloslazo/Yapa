import { lazy, Suspense, useCallback, useEffect, useMemo, useState, type CSSProperties } from 'react';
import { AdminSkeleton, PartnerSkeleton } from './components/Skeleton';
import { AuthPage, type LoginKind } from './components/AuthPage';
import { AccountPage } from './components/AccountPage';
import { BasketAssistant } from './components/BasketAssistant';
import { ExplorePage } from './components/ExplorePage';
import { HomePage } from './components/HomePage';
import { ProductPage } from './components/ProductPage';
import { toastDuration, type Toast, type ToastTone } from './utils/toast';
import { CartBar, type CartLine } from './components/CartPanel';
import { CartPage } from './components/CartPage';
import { PayPage } from './components/PayPage';
import { HowItWorks } from './components/EditorialSections';
import { Sheet } from './components/Sheet';
import { InviteContext } from './components/InviteCard';
import { InvitePage } from './components/InvitePage';
import { PrivacyPage } from './components/PrivacyPage';
import { Icon, type IconName } from './components/Icon';
import { NoticeBell } from './components/NoticeBell';
import { OrdersPage, type Claimable, type ClaimRecord, type MyOrders } from './components/OrdersPage';
import { ZonePage, type MyZone } from './components/ZonePage';
import { api, ApiError } from './services/api';
import { toAccount, toCycle, toNotice, toOrder, toProduct, toQuote, toZone } from './services/mappers';
import type { Account, CartState, CycleState, Notice, Order, Product, Quote, RefundDestination, Role, Zone } from './types';
import { cartSubtotal, mergeSuggestion, stepDown, stepUp } from './utils/cart';
import { closeCountdown } from './utils/landing';
import { deliveryDay, type Chip } from './utils/shop';
import { inviteCodeFromPath, inviteLink } from './utils/invite';
import { noticeTarget } from './utils/notices';
import { canOpenZonePanel, homeFor, isNeighborRole, isPartner, isStaff } from './utils/roles';
import { readStored, writeStored } from './utils/storage';
import { formatMoney } from './utils/format';
import { authHref, authRouteFromLocation, type AuthPageId, type ReturnView, type StaffLoginKind } from './utils/authRoutes';

import './styles.css';

// FE-SG-2: el panel del equipo se baja solo cuando se abre
const AdminPanel = lazy(() => import('./components/AdminPanel').then((module) => ({ default: module.AdminPanel })));
const PartnerPanel = lazy(() => import('./components/PartnerPanel').then((module) => ({ default: module.PartnerPanel })));

/* eslint-disable @typescript-eslint/no-explicit-any */
type Raw = Record<string, any>;
type View = 'store' | 'explore' | 'product' | 'orders' | 'cart' | 'pay' | 'zone' | 'account';

// saludo al entrar según el rol; el vecino recibe el de su saldo
const WELCOME: Partial<Record<Role, string>> = {
  admin: 'Entraste al centro de operaciones.',
  compras: 'Aquí ves lo que hay que comprar esta semana.',
  armador: 'Aquí tienes los pedidos por armar.',
  atencion: 'Aquí tienes los reclamos, devoluciones y pedidos de PIN.',
  porteria: 'Aquí ves las bolsas que llegan a tu edificio.',
  transportista: 'Aquí tienes las paradas de la semana.',
  proveedor: 'Aquí ves lo que te compramos y mandas tu lista.',
};

// #explorar/tuberculos y #producto/PAPA-AMARILLA llevan un dato después de la barra
const HASH_VIEW: Record<string, View> = { orders: 'orders', cart: 'cart', pagar: 'pay', zone: 'zone', cuenta: 'account', explorar: 'explore', producto: 'product' };
const routeFromHash = () => {
  const [head, param] = window.location.hash.slice(1).split('/');
  return { view: HASH_VIEW[head] ?? 'store', param: param ? decodeURIComponent(param) : null };
};
const viewFromHash = (): View => routeFromHash().view;
const VIEW_HASH: Record<View, string> = { store: 'catalog', explore: 'explorar', product: 'producto', orders: 'orders', cart: 'cart', pay: 'pagar', zone: 'zone', account: 'cuenta' };
const RETURN_TO_VIEW: Record<ReturnView, View> = { cart: 'cart', orders: 'orders', zone: 'zone', cuenta: 'account' };
const authRouteNow = () => authRouteFromLocation(window.location.pathname, window.location.search);

export default function App() {
  const [catalog, setCatalog] = useState<Product[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [state, setState] = useState<CycleState | null>(null);
  const [districts, setDistricts] = useState<string[]>([]);
  const [account, setAccount] = useState<Account | null>(null);
  const [googleClientId, setGoogleClientId] = useState<string | null>(null);
  const [cart, setCart] = useState<CartState>(() => readStored('yapa.cart', {}));
  const [category, setCategory] = useState('Todos');
  const [query, setQuery] = useState('');
  const [sheet, setSheet] = useState<string | null>(null); // producto abierto en su ficha, o 'como-funciona'
  const [view, setView] = useState<View>(viewFromHash);
  const [routeParam, setRouteParam] = useState<string | null>(() => routeFromHash().param); // grupo de Explorar o producto abierto
  const [exploreChip, setExploreChip] = useState<Chip>('todo');
  const [adminOpen, setAdminOpen] = useState(() => window.location.hash === '#admin');
  const [authRoute, setAuthRoute] = useState(authRouteNow); // /entrar y /equipo: el acceso tiene su propia página
  const [quoting, setQuoting] = useState(false); // la canasta pide la cotización antes de pasar al pago
  const [quote, setQuote] = useState<Quote | null>(null);
  const [confirmation, setConfirmation] = useState<Order | null>(null);
  const [myOrders, setMyOrders] = useState<MyOrders | null>(null);
  const [claimables, setClaimables] = useState<Claimable[]>([]);
  const [claims, setClaims] = useState<ClaimRecord[]>([]);
  const [myZone, setMyZone] = useState<MyZone | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);
  const [offline, setOffline] = useState(false);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [unreadNotices, setUnreadNotices] = useState(0);
  const [emailNotices, setEmailNotices] = useState(true);
  const [clockOffset, setClockOffset] = useState(0);
  const [inviteCode, setInviteCode] = useState<string | null>(() => inviteCodeFromPath(window.location.pathname));
  const [invite, setInvite] = useState<{ code: string; today: number; total: number } | null>(null);

  const notify = useCallback((title: string, tone: ToastTone = 'neutral', detail?: string, action?: Toast['action']) => setToast({ title, tone, detail, action }), []);
  // con contexto, el título dice qué falló y el detalle trae el motivo que da el motor
  const fail = useCallback((error: unknown, context?: string) => {
    const reason = error instanceof Error ? error.message : 'Revisa tu conexión e inténtalo otra vez.';
    if (context) notify(context, 'warning', reason); else notify(reason, 'warning');
  }, [notify]);

  // --- carga ---

  const loadPublic = useCallback(async () => {
    const [estado, catalogo, zonas] = await Promise.all([api.get<Raw>('/api/estado'), api.get<Raw>('/api/catalogo'), api.get<Raw>('/api/zonas')]);
    setState(toCycle(estado));
    setClockOffset(new Date(estado.ahora).getTime() - Date.now());
    setDistricts(estado.distritos);
    setGoogleClientId(estado.google_client_id ?? null);
    setCatalog(catalogo.productos.map(toProduct));
    setZones(zonas.zonas.map(toZone));
  }, []);

  const loadAccount = useCallback(async () => {
    try {
      const me = toAccount(await api.get<Raw>('/api/sesion'));
      api.setCsrf(me.csrf);
      setAccount(me);
      return me;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) { setAccount(null); return null; }
      throw error;
    }
  }, []);

  const loadOrders = useCallback(async () => {
    const [mine, rec] = await Promise.all([api.get<Raw>('/api/mis-pedidos'), api.get<Raw>('/api/reclamos')]);
    setMyOrders({ orders: mine.pedidos.map(toOrder), balance: Number(mine.saldo), returned: Number(mine.devuelto_total), supermarketSaving: Number(mine.ahorro_supermercado), refunds: mine.devoluciones.map((r: Raw) => ({ id: r.id, amount: Number(r.monto), reason: r.motivo, status: r.estado })) });
    setClaimables(rec.reclamables.map((c: Raw) => ({ order: c.pedido, product: c.producto, name: c.nombre, quantity: Number(c.cantidad) })));
    setClaims(rec.reclamos.map((c: Raw) => ({ id: c.id, order: c.pedido, product: c.producto, quantity: Number(c.cantidad), reason: c.motivo, status: c.estado, returned: Number(c.devuelto) })));
  }, []);

  const loadNotices = useCallback(async () => {
    const raw = await api.get<Raw>('/api/avisos');
    setNotices(raw.avisos.map(toNotice));
    setUnreadNotices(raw.sin_leer);
    setEmailNotices(Boolean(raw.correo_avisos));
  }, []);

  const loadZone = useCallback(async () => {
    const raw = await api.get<Raw>('/api/mi-zona');
    const a = raw.administra;
    setMyZone({
      zone: raw.zona ? toZone(raw.zona) : null,
      progress: raw.avance ? { verified: raw.avance.verificados, minimum: raw.avance.minimo, cycle: raw.avance.ciclo } : null,
      referralCode: raw.codigo_referido,
      radius: raw.radio_m,
      mergeDistance: raw.union_m,
      admin: a ? {
        ...toZone(a),
        neighbors: a.vecinos.length, // en el panel, "vecinos" es la lista, no el número
        progress: { verified: a.avance.verificados, minimum: a.avance.minimo, cycle: a.avance.ciclo },
        neighborsList: a.vecinos.map((v: Raw) => ({ id: v.id, name: v.nombre, ordered: v.pidio })),
        nearby: a.cercanas.map((z: Raw) => ({ ...toZone(z), distance: z.distancia_m, sameGroup: z.mismo_grupo, reason: z.motivo ?? '' })),
        requests: a.solicitudes.map((r: Raw) => ({ id: r.id, zone: r.zona, name: r.nombre })),
        sent: a.enviadas.map((r: Raw) => ({ id: r.id, zone: r.zona, name: r.nombre })),
        benefits: { freeDelivery: a.beneficios.envio_gratis, discountPct: Number(a.beneficios.descuento_pct), discountActive: a.beneficios.descuento_activo, discountUntil: a.beneficios.descuento_hasta },
        referralCode: a.codigo_referido,
      } : null,
    });
  }, []);

  const retry = useCallback(() => { Promise.all([loadPublic(), loadAccount()]).then(() => setOffline(false)).catch((error) => { setOffline(true); fail(error); }); }, [loadPublic, loadAccount, fail]);
  useEffect(() => { retry(); }, [retry]);

  const loadInvite = useCallback(async (renew = false) => {
    const raw = await (renew ? api.post<Raw>('/api/mi-invitacion/renovar') : api.get<Raw>('/api/mi-invitacion'));
    setInvite({ code: raw.codigo, today: raw.hoy, total: raw.total });
  }, []);
  useEffect(() => {
    if (!account || !isNeighborRole(account.role)) { setInvite(null); return; }
    loadInvite().catch(() => setInvite(null));
  }, [account, loadInvite]);

  useEffect(() => {
    if (!account || !isNeighborRole(account.role)) { setMyOrders(null); setMyZone(null); return; }
    if (view === 'orders') loadOrders().catch(fail);
    if (view === 'zone') loadZone().catch(fail);
    if (view === 'store') loadZone().catch(() => undefined); // iteración 62: el avance del grupo en el Inicio; si falla, la tarjeta queda como está
  }, [account, view, loadOrders, loadZone, fail]);

  const isNeighbor = account !== null && isNeighborRole(account.role);
  const accountUser = account?.user;
  useEffect(() => {
    if (!isNeighbor) { setNotices([]); setUnreadNotices(0); return; }
    const refresh = () => { loadNotices().catch(() => undefined); }; // AV-13: al sondear no se molesta con errores
    const visible = () => { if (document.visibilityState === 'visible') refresh(); };
    refresh();
    const timer = window.setInterval(refresh, 60000);
    document.addEventListener('visibilitychange', visible);
    return () => { window.clearInterval(timer); document.removeEventListener('visibilitychange', visible); };
  }, [isNeighbor, accountUser, loadNotices]);

  useEffect(() => { writeStored('yapa.cart', cart); }, [cart]);
  useEffect(() => {
    if (!toast) return;
    const timeout = window.setTimeout(() => setToast(null), toastDuration(toast.tone, toast.detail));
    return () => window.clearTimeout(timeout);
  }, [toast]);
  useEffect(() => {
    const sync = () => { setAdminOpen(window.location.hash === '#admin'); setView(viewFromHash()); setRouteParam(routeFromHash().param); setAuthRoute(authRouteNow()); };
    window.addEventListener('hashchange', sync);
    window.addEventListener('popstate', sync);
    return () => { window.removeEventListener('hashchange', sync); window.removeEventListener('popstate', sync); };
  }, []);

  // --- navegación ---

  const go = (hash: string) => { window.history.pushState(null, '', `${window.location.pathname}${window.location.search}#${hash}`); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const openAuth = (page: AuthPageId = 'entrar', options: { rol?: StaffLoginKind; volver?: ReturnView } = {}) => {
    window.history.pushState(null, '', authHref(page, options));
    setAuthRoute(authRouteNow());
  };
  // vuelve a la tienda sin dejar /entrar en el historial: Atrás no reabre el acceso
  const leaveAuth = (next: View = 'store') => {
    window.history.replaceState(null, '', `/#${VIEW_HASH[next]}`);
    setAuthRoute({ page: null });
    setAdminOpen(false);
    setView(next);
    window.scrollTo({ top: 0 });
  };
  const needAccount = (message: string, volver?: ReturnView) => { openAuth('entrar', { volver }); notify(message, 'neutral', 'Tu canasta se queda guardada mientras entras.'); };
  const openAccount = () => (account ? openView('account') : openAuth('entrar'));
  // con la sesión ya abierta, /entrar y /equipo no tienen nada que mostrar
  useEffect(() => {
    if (!account || !authRoute.page) return;
    leaveAuth(authRoute.volver ? RETURN_TO_VIEW[authRoute.volver] : 'store');
    if (homeFor(account.role) === 'operaciones') { setAdminOpen(true); go('admin'); }
  }, [account, authRoute.page]);
  // 'catalog' es el <main> entero: basta con volver arriba; bajar hasta él lo pegaba bajo el encabezado
  const goStore = (anchor = 'catalog') => { setAdminOpen(false); setView('store'); go(anchor); if (anchor !== 'catalog') window.requestAnimationFrame(() => document.getElementById(anchor)?.scrollIntoView({ behavior: 'smooth', block: 'start' })); };
  const openView = (next: View) => {
    if ((next === 'orders' || next === 'zone' || next === 'account') && !account) { needAccount('Entra a tu cuenta para continuar.', next === 'account' ? 'cuenta' : next); return; }
    setAdminOpen(false); setView(next); go(VIEW_HASH[next]);
  };
  const openExplore = (group: string | null = null, chip: Chip = 'todo') => { setAdminOpen(false); setExploreChip(chip); setRouteParam(group); setView('explore'); go(group ? `explorar/${group}` : 'explorar'); };
  const openProduct = (product: Product) => { setAdminOpen(false); setRouteParam(product.id); setView('product'); go(`producto/${encodeURIComponent(product.id)}`); };
  // volver dentro de Yapa; si la ficha se abrió desde un enlace, volver es ir al inicio
  const goBack = () => (window.history.length > 1 ? window.history.back() : goStore('catalog'));
  const shareProduct = async (product: Product) => {
    const url = `${window.location.origin}/#producto/${encodeURIComponent(product.id)}`;
    try {
      if (typeof navigator.share === 'function') { await navigator.share({ title: `${product.name} en Yapa`, text: `${product.name} a ${formatMoney(product.price)} esta semana en Yapa`, url }); return; }
      await navigator.clipboard.writeText(url);
      notify('Copiamos el enlace', 'success', 'Pégalo en WhatsApp para pasárselo a un vecino.');
    } catch { /* el vecino canceló o el navegador no deja copiar */ }
  };
  const openAdmin = () => {
    if (account?.role !== 'admin') { openAuth('equipo', { rol: 'admin' }); return; }
    setAdminOpen(true); go('admin');
  };

  // --- carrito ---

  const lines: CartLine[] = useMemo(() => Object.entries(cart).flatMap(([id, quantity]) => {
    const product = catalog.find((item) => item.id === id);
    return product && quantity > 0 ? [{ product, quantity }] : [];
  }), [cart, catalog]);
  const subtotal = cartSubtotal(lines);
  const savings = lines.reduce((sum, { product, quantity }) => sum + (product.supermarket && product.supermarket.price > product.price ? (product.supermarket.price - product.price) * quantity : 0), 0);
  const categories = useMemo(() => [...new Set(catalog.map((p) => p.category))], [catalog]);
  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return catalog.filter((p) => (category === 'Todos' || p.category === category) && (!q || `${p.name} ${p.category} ${p.detail}`.toLowerCase().includes(q)));
  }, [catalog, category, query]);

  const addProduct = (product: Product) => {
    const current = cart[product.id] || 0;
    if (current >= product.maxPerOrder) { notify(`Llegaste al máximo de ${product.name}`, 'warning', `Cada vecino puede pedir hasta ${product.maxPerOrder} ${product.unit} por semana, para que alcance para todos.`); return; }
    setCart((c) => ({ ...c, [product.id]: stepUp(product, c[product.id] || 0) }));
  };
  const applySuggestion = (suggested: Array<{ id: string; quantity: number }>) => { // iteración 60
    setCart((c) => mergeSuggestion(c, suggested, Object.fromEntries(catalog.map((p) => [p.id, p.maxPerOrder]))));
    notify('Agregamos la canasta sugerida', 'success', 'Revísala y cambia lo que quieras antes de pagar.', { label: 'Ver canasta', run: () => openView('cart') });
  };
  const decreaseProduct = (product: Product) => setCart((c) => {
    const next = { ...c };
    const quantity = stepDown(product, next[product.id] || 0);
    if (quantity <= 0) delete next[product.id]; else next[product.id] = quantity;
    return next;
  });
  const cartBody = () => Object.fromEntries(lines.map(({ product, quantity }) => [product.id, String(quantity)]));

  // --- pedido ---

  const openCheckout = async () => {
    if (!account) { needAccount('Entra a tu cuenta para registrar el pedido.', 'cart'); return; }
    if (!isNeighborRole(account.role)) { notify('Esta cuenta no es de vecino', 'warning', 'Para comprar, entra con una cuenta de vecino.'); return; }
    setQuoting(true);
    try {
      setQuote(toQuote(await api.post<Raw>('/api/cotizar', { lineas: cartBody() })));
      setConfirmation(null);
      openView('pay');
    } catch (error) { fail(error, 'No pudimos preparar tu pedido'); } finally { setQuoting(false); }
  };
  const clearCart = () => {
    const previous = cart;
    setCart({});
    notify('Vaciaste tu canasta', 'neutral', undefined, { label: 'Deshacer', run: () => setCart(previous) });
  };
  // al salir del pago se olvida la cotización y la confirmación: la próxima vez se cotiza de nuevo
  useEffect(() => { if (view !== 'pay') { setConfirmation(null); setQuote(null); } }, [view]);
  const registerOrder = async (method: 'YAPE' | 'PLIN', useBalance: boolean) => {
    const order = toOrder(await api.post<Raw>('/api/pedidos', { lineas: cartBody(), metodo: method, usar_saldo: useBalance }));
    setConfirmation(order);
    setCart({});
    void loadPublic();
    void loadAccount();
  };
  const cancelOrder = async (order: Order, destination: RefundDestination) => {
    try {
      await api.post(`/api/pedidos/${order.id}/cancelar`, { destino: destination });
      notify(`Cancelaste el pedido ${order.id}`, 'success', destination === 'SALDO' ? 'Lo que pagaste ya está en tu saldo para tu próxima compra.' : 'Te devolvemos el pago a tu Yape o Plin en los próximos días.');
      await Promise.all([loadOrders(), loadAccount(), loadPublic()]);
    } catch (error) { fail(error, 'No pudimos cancelar el pedido'); }
  };
  const withdraw = async (amount: number) => {
    try {
      await api.post('/api/saldo/devolucion', { monto: amount.toFixed(2) });
      notify(`Pediste la devolución de ${formatMoney(amount)}`, 'success', 'Te llega a tu Yape o Plin en hasta 30 días. Te avisamos cuando la hagamos.');
      await Promise.all([loadOrders(), loadAccount()]);
    } catch (error) { fail(error, 'No pudimos pedir la devolución'); }
  };
  const claim = async (form: FormData) => {
    try {
      await api.post('/api/reclamos', form);
      await loadOrders();
    } catch (error) { fail(error, 'No pudimos enviar tu reclamo'); throw error; }
  };

  // --- zona ---

  const zoneAction = (action: () => Promise<unknown>, success: string, detail?: string) => async () => {
    try {
      await action();
      notify(success, 'success', detail);
      await Promise.all([loadZone(), loadAccount(), loadPublic()]);
    } catch (error) { fail(error, 'No pudimos completar el cambio en tu zona'); }
  };

  // --- avisos ---

  const openNotice = async (notice: Notice) => {
    try {
      if (!notice.read) await api.post('/api/avisos/leer', { id: notice.id });
      await loadNotices();
    } catch (error) { fail(error); }
    openView(noticeTarget(notice.kind));
  };
  const readAllNotices = async () => {
    try { await api.post('/api/avisos/leer', {}); await loadNotices(); } catch (error) { fail(error); }
  };
  const toggleEmailNotices = async (enabled: boolean) => {
    try {
      await api.post('/api/avisos/preferencias', { avisos_correo: enabled });
      setEmailNotices(enabled);
      notify(enabled ? 'Avisos por correo activados' : 'Avisos por correo desactivados', 'success', enabled ? 'Te escribimos cuando tu pedido avance o haya saldo nuevo.' : 'Seguirás viendo todo en la campana de avisos.');
    } catch (error) { fail(error); }
  };

  // --- sesión ---

  const login = async (kind: LoginKind, user: string, secret: string) => finishLogin(toAccount(await api.post<Raw>('/api/sesion', { tipo: kind, usuario: user, secreto: secret })));
  const loginWithGoogle = async (credential: string) => { finishLogin(toAccount(await api.post<Raw>('/api/sesion/google', { credential }))); };
  const finishLogin = (me: Account) => {
    api.setCsrf(me.csrf);
    setAccount(me);
    const back = authRoute.volver;
    leaveAuth(back ? RETURN_TO_VIEW[back] : 'store');
    notify(`Hola, ${me.name.split(' ')[0]}`, 'success', WELCOME[me.role] ?? (me.balance ? `Tienes ${formatMoney(me.balance)} de saldo para tu próxima compra.` : 'Ya puedes armar tu canasta de la semana.'));
    if (homeFor(me.role) === 'operaciones') { setAdminOpen(true); go('admin'); }
    return me;
  };
  const logout = async () => {
    try { await api.delete('/api/sesion'); } catch { /* la sesión ya no existe */ }
    api.setCsrf('');
    setAccount(null);
    leaveAuth('store');
  };

  const joinedByInvite = (raw: Raw) => {
    window.history.replaceState(null, '', '/');
    setInviteCode(null);
    finishLogin(toAccount(raw));
  };
  const goHomeFromInvite = () => { window.history.replaceState(null, '', '/'); setInviteCode(null); };

  // iteración 48: el admin global abre la pantalla de otra persona y vuelve
  const viewAs = async (customerId: number) => {
    try {
      const me = toAccount(await api.post<Raw>('/api/admin/ver-como', { usuario: customerId }));
      api.setCsrf(me.csrf);
      setAccount(me);
      setAdminOpen(false);
      goStore('catalog');
      notify(`Viendo Yapa como ${me.name.split(' ')[0]}`, 'neutral', 'No puedes mover dinero desde esta vista. Usa la barra de arriba para volver.');
    } catch (error) { fail(error); }
  };
  const backFromView = async () => {
    try {
      const me = toAccount(await api.post<Raw>('/api/sesion/volver'));
      api.setCsrf(me.csrf);
      setAccount(me);
      setAdminOpen(true);
      go('admin');
    } catch (error) { fail(error); }
  };

  const accountZone = zones.find((z) => z.id === account?.zoneId);
  const showAdmin = adminOpen && account?.role === 'admin';
  const staffOnly = account && account.role !== 'admin' && isStaff(account.role); // compras, armado y atención no compran

  const toastRegion = (
    <div className="toast-region" aria-live={toast?.tone === 'warning' ? 'assertive' : 'polite'} aria-atomic="true">{toast ? <div key={`${toast.title}|${toast.detail ?? ''}`} className={`toast toast--${toast.tone} is-visible`} role={toast.tone === 'warning' ? 'alert' : 'status'} style={{ '--toast-ms': `${toastDuration(toast.tone, toast.detail)}ms` } as CSSProperties}>
      <span className="toast-icon"><Icon name={toast.tone === 'success' ? 'check' : toast.tone === 'warning' ? 'warning' : 'info'} size={18} weight="bold" /></span>
      <div className="toast-copy"><strong>{toast.title}</strong>{toast.detail ? <span>{toast.detail}</span> : null}{toast.action ? <button className="toast-action" type="button" onClick={() => { toast.action?.run(); setToast(null); }}>{toast.action.label}</button> : null}</div>
      <button className="toast-close" type="button" onClick={() => setToast(null)} aria-label="Cerrar aviso"><Icon name="close" size={16} /></button>
      <span className="toast-timer" aria-hidden="true" />
    </div> : null}</div>
  );

  if (window.location.pathname.replace(/\/$/, '') === '/privacidad') return <PrivacyPage />;
  if (authRoute.page && !account) return <><AuthPage page={authRoute.page} initialRole={authRoute.rol} googleClientId={googleClientId} onLogin={login} onGoogleLogin={loginWithGoogle}
    onForgotPin={async (user) => (await api.post<{ mensaje: string }>('/api/pin/olvide', { usuario: user })).mensaje}
    onResetPin={async (user, code, pin) => (await api.post<{ mensaje: string }>('/api/pin/restablecer', { usuario: user, codigo: code, pin })).mensaje}
    onSwitch={(page) => { window.history.replaceState(null, '', authHref(page, { volver: authRoute.volver })); setAuthRoute(authRouteNow()); }}
    onBack={() => leaveAuth('store')} />{toastRegion}</>;
  if (account && isPartner(account.role)) return <Suspense fallback={<div className="partner-view"><main className="partner-main"><PartnerSkeleton /></main></div>}><PartnerPanel account={account} notify={notify} onLogout={() => void logout()} />{toastRegion}</Suspense>;
  if (account && staffOnly) return <div className="app-shell"><Suspense fallback={<div className="admin-view admin-view--loading"><AdminSkeleton /></div>}><AdminPanel adminName={account.name} role={account.role} notify={notify} onLogout={() => void logout()} /></Suspense>{toastRegion}</div>;
  if (inviteCode) return <InvitePage code={inviteCode} googleClientId={googleClientId} signedIn={Boolean(account)} onJoined={joinedByInvite} onGoHome={goHomeFromInvite} />;

  const inviteState = { url: invite ? inviteLink(window.location.origin, invite.code) : null, today: invite?.today ?? 0, total: invite?.total ?? 0, renew: async () => { try { await loadInvite(true); notify('Tu enlace nuevo ya está activo', 'success', 'El anterior dejó de funcionar. Compártelo solo con vecinos de tu zona.'); } catch (error) { fail(error, 'No pudimos renovar tu enlace'); } } };

  const firstName = account?.name.split(' ')[0];
  const now = new Date(Date.now() + clockOffset);
  const countdown = closeCountdown(now); // tarjeta de la semana: cuánto falta para el cierre del miércoles
  const cycleOpen = state ? state.open : countdown.open;
  const delivery = deliveryDay(now);
  const searchFor = (value: string) => { setQuery(value); if (view !== 'store') goStore('catalog'); };
  const tabs: Array<{ id: View; label: string; icon: IconName }> = [
    { id: 'store', label: 'Inicio', icon: 'home' },
    { id: 'explore', label: 'Explorar', icon: 'grid' },
    { id: 'cart', label: 'Canasta', icon: 'basket' },
    { id: 'orders', label: 'Pedidos', icon: 'receipt' },
  ];
  const navItems: Array<{ id: View; label: string }> = [{ id: 'store', label: 'Inicio' }, { id: 'explore', label: 'Explorar' }, { id: 'orders', label: 'Mis pedidos' }, ...(account ? [{ id: 'zone' as View, label: 'Mi zona' }] : [])];
  const openTab = (id: View) => (id === 'store' ? goStore('catalog') : id === 'explore' ? openExplore() : openView(id));

  return (
    <InviteContext.Provider value={inviteState}>
    <div className={`app-shell ${showAdmin ? '' : `has-tab-bar view-${view} is-store`}`}>
      {account?.viewingAs ? <div className="view-as-bar" role="status"><span>Estás viendo Yapa como <strong>{account.name}</strong> ({account.role === 'admin_zona' ? 'admin de zona' : 'vecino'}).</span><button type="button" onClick={() => void backFromView()}>Volver a mi cuenta</button></div> : null}
      {showAdmin ? <Suspense fallback={<div className="admin-view admin-view--loading"><AdminSkeleton /></div>}><AdminPanel adminName={account?.name ?? ''} role="admin" notify={notify} onClose={() => { setAdminOpen(false); goStore('catalog'); }} onLogout={() => void logout()} onViewAs={account?.canViewAs ? viewAs : undefined} /></Suspense> : <>
        <a className="skip-link" href="#contenido" onClick={(event) => { event.preventDefault(); const main = document.querySelector('main'); if (main) { main.setAttribute('tabindex', '-1'); main.focus(); main.scrollIntoView(); } }}>Saltar al contenido principal</a>
        <header className="topbar">
          <a className="brand" href="#catalog" aria-label="Yapa, inicio" onClick={(event) => { event.preventDefault(); goStore('catalog'); }}><img className="brand-logo-mark" src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" fetchPriority="high" /><span>yapa</span></a>
          <button className="where-button" type="button" onClick={() => (account ? openView('zone') : notify('Dónde entregamos', 'neutral', 'Lince y Jesús María ya reciben pedidos. La Victoria abre muy pronto.'))}><span className="where-pin"><Icon name="pin" size={18} weight="fill" /></span><span className="where-copy"><small>Entrega el sábado en</small><strong>{accountZone?.name ?? 'Lince y Jesús María'}<Icon name="chevron" size={14} /></strong></span></button>
          <div className="top-search-row">
            <label className="top-search"><Icon name="search" size={18} /><span className="sr-only">Buscar productos</span><input name="product-search" type="search" value={query} onChange={(event) => searchFor(event.target.value)} placeholder="Buscar papa, limón, lejía" autoComplete="off" /></label>
            <button className="filter-button" type="button" onClick={() => openExplore()} aria-label="Ver categorías y filtros"><Icon name="sliders" size={20} /></button>
          </div>
          <nav className="main-nav" aria-label="Navegación principal">
            {navItems.map((item) => <button key={item.id} className={`nav-link ${view === item.id ? 'is-active' : ''}`} type="button" aria-current={view === item.id ? 'page' : undefined} onClick={() => openTab(item.id)}>{item.id === 'zone' && account && canOpenZonePanel(account.role) ? <Icon name="crown" size={15} /> : null}{item.label}</button>)}
          </nav>
          <div className="topbar-actions">
            {isNeighbor ? <NoticeBell notices={notices} unread={unreadNotices} emailNotices={emailNotices} emailVerified={Boolean(account?.emailVerified)} now={new Date(Date.now() + clockOffset)} onOpenNotice={(notice) => void openNotice(notice)} onReadAll={() => void readAllNotices()} onToggleEmail={(enabled) => void toggleEmailNotices(enabled)} onVerifyEmail={openAccount} /> : null}
            <button className="account-button" type="button" onClick={openAccount} aria-label={account ? `Tu cuenta, ${firstName}` : 'Entrar a Yapa'}>{account ? <span className="account-avatar" aria-hidden="true">{firstName?.charAt(0).toUpperCase()}</span> : null}<span className="account-label">{account ? firstName : 'Entrar'}</span></button>
            <button className={`cart-button ${view === 'cart' ? 'is-active' : ''}`} type="button" onClick={() => openView('cart')} aria-label={`Canasta, ${lines.length} ${lines.length === 1 ? 'producto' : 'productos'}`}><Icon name="basket" size={20} /><span className="cart-button-label">{lines.length ? formatMoney(subtotal) : 'Canasta'}</span>{lines.length ? <span className="cart-button-count" key={lines.length}>{lines.length}</span> : null}</button>
          </div>
        </header>

        {offline ? <div className="offline-banner" role="alert"><Icon name="warning" size={18} /><span><strong>Sin conexión con Yapa.</strong> Tu canasta sigue guardada en este equipo.{import.meta.env.DEV ? <> Levanta el motor con <code>npm run api</code>.</> : null}</span><button className="text-button" type="button" onClick={retry}>Reintentar</button></div> : null}

        <div className="view" key={view}>
        {view === 'orders' ? <OrdersPage data={myOrders} claimables={claimables} claims={claims} onBack={() => goStore('catalog')} onCancel={cancelOrder} onWithdraw={withdraw} onClaim={claim} />
          : view === 'zone' ? <ZonePage data={myZone} zones={zones} userId={Number(account?.user ?? 0)} districts={districts} onBack={() => goStore('catalog')}
            onJoin={(zoneId) => zoneAction(() => api.post(`/api/zonas/${zoneId}/unirme`), 'Ya eres parte de la zona', 'Tus pedidos suman con los de tus vecinos para llegar al mínimo.')()}
            onLocate={async (lat, lon) => { try { await api.post('/api/ubicacion', { lat, lon }); notify('Guardamos tu ubicación', 'success', 'Te mostramos las zonas que te quedan cerca.'); } catch (error) { fail(error, 'No pudimos guardar tu ubicación'); throw error; } }}
            onCreate={(name, district, lat, lon) => zoneAction(() => api.post('/api/zonas', { nombre: name, distrito: district, lat, lon }), `Creaste la zona ${name}`, 'Ahora eres su admin. Falta indicar quién recibe los pedidos para activarla.')()}
            onActivate={(zoneId, kind, contact) => zoneAction(() => api.post(`/api/zonas/${zoneId}/activar`, { tipo: kind, contacto: contact }), 'Tu zona ya recibe pedidos', 'Comparte tu enlace con los vecinos del edificio para llegar al mínimo.')()}
            onRequestMerge={(zoneId, target) => zoneAction(() => api.post(`/api/zonas/${zoneId}/unir`, { destino: target }), 'Enviamos tu solicitud', 'Falta que el admin de la otra zona la acepte. Te avisamos cuando responda.')()}
            onAnswerMerge={(id, accept) => zoneAction(() => api.post(`/api/solicitudes/${id}/${accept ? 'aceptar' : 'rechazar'}`), accept ? 'Zonas unidas' : 'Rechazaste la solicitud', accept ? 'Desde ahora sus pedidos suman juntos para llegar al mínimo.' : 'La otra zona sigue contando por su cuenta.')()}
            onWithdrawMerge={(id) => zoneAction(() => api.post(`/api/solicitudes/${id}/retirar`), 'Retiraste la solicitud', 'Tu zona sigue contando sola.')()}
            onLeaveGroup={(zoneId) => zoneAction(() => api.post(`/api/zonas/${zoneId}/separar`), 'Tu zona vuelve a contar sola', 'Para llegar al mínimo cuentan solo los pedidos de tu zona.')()}
            onTransfer={(zoneId, newAdmin) => zoneAction(() => api.post(`/api/zonas/${zoneId}/transferir`, { nuevo: newAdmin }), 'Transferiste el rol de admin', '¡Gracias por organizar tu edificio! Sigues en la zona como vecino.')()} />
            : view === 'account' && account ? <AccountPage account={account} googleClientId={googleClientId} onLogout={logout} onOpenAdmin={openAdmin} onOpenZone={() => openView('zone')} onOpenOrders={() => openView('orders')}
              onGoogleLink={async (credential) => { await api.post('/api/cuenta/google', { credential }); await loadAccount(); }} onGoogleUnlink={async () => { await api.post('/api/cuenta/google/desvincular'); await loadAccount(); }}
              onSendEmail={async (email) => { await api.post('/api/cuenta/correo', { correo: email }); await loadAccount(); }} onVerifyEmail={async (code) => { await api.post('/api/cuenta/correo/verificar', { codigo: code }); await loadAccount(); }}
              onCreatePin={async (pin) => { await api.post('/api/pin/crear', { pin }); await loadAccount(); }}
              onWithdraw={async (confirmation) => { await api.post('/api/cuenta/retirar-consentimiento', { confirmar: confirmation }); api.setCsrf(''); setAccount(null); leaveAuth('store'); notify('Cerramos tu cuenta', 'success', 'Borramos tus datos personales. Gracias por haber comprado con Yapa.'); }} />
            : view === 'cart' ? <CartPage lines={lines} subtotal={subtotal} savings={savings} busy={quoting} onAdd={addProduct} onDecrease={decreaseProduct} onOpen={openProduct} onCheckout={() => void openCheckout()} onClear={clearCart} onBack={() => goStore('catalog')} />
            : view === 'pay' ? <PayPage quote={quote} zone={accountZone} delivery={delivery} cycleOpen={Boolean(state?.open)} confirmation={confirmation} onSubmit={registerOrder} onBack={() => openView('cart')} onOpenOrders={() => openView('orders')} onKeepShopping={() => goStore('catalog')} />
              : view === 'explore' ? <ExplorePage key={`${routeParam ?? 'todo'}-${exploreChip}`} products={catalog} group={routeParam} initialChip={exploreChip} cart={cart} onAdd={addProduct} onDecrease={decreaseProduct} onOpen={openProduct} onGroup={(group) => openExplore(group)} />
              : view === 'product' ? (catalog.length ? <ProductPage product={catalog.find((p) => p.id === routeParam)} quantity={cart[routeParam ?? ''] || 0} delivery={delivery} onAdd={addProduct} onDecrease={decreaseProduct} onBack={goBack} onCart={() => openView('cart')} onShare={(product) => void shareProduct(product)} /> : <main className="page-content product-page" aria-busy="true" />)
              : <HomePage products={catalog} results={visible} query={query} cart={cart} cycleOpen={cycleOpen} countdown={countdown.text} countdownParts={countdown.parts} delivery={delivery} signedIn={Boolean(account)} balance={isNeighbor ? account?.balance ?? 0 : 0}
                group={isNeighbor ? myZone?.progress : null}
                assistant={account && state?.ai && state.open ? <BasketAssistant onApply={applySuggestion} /> : null}
                onAdd={addProduct} onDecrease={decreaseProduct} onOpen={openProduct} onGroup={(group) => openExplore(group)} onExplore={(chip) => openExplore(null, chip)}
                onHow={() => setSheet('como-funciona')} onLogin={() => openAuth('entrar')} onBalance={() => openView('orders')} onClearSearch={() => setQuery('')} />}
        </div>
        {!offline && (view === 'store' || view === 'explore') && lines.length && !sheet ? <CartBar count={lines.length} subtotal={subtotal} onOpenCart={() => openView('cart')} /> : null}

        <footer className={`site-footer ${view === 'store' ? '' : 'site-footer--secondary'}`}>
          <div className="footer-brand"><span className="brand"><img className="brand-logo-mark" src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" loading="lazy" /><span>yapa</span></span><p>Compras que rinden, entre vecinos.</p></div>
          <nav className="footer-links" aria-label="Enlaces"><a href="#catalog" onClick={(event) => { event.preventDefault(); setSheet('como-funciona'); }}>Cómo funciona</a><a href="/privacidad">Privacidad</a><button className="footer-link" type="button" onClick={openAdmin}>Equipo Yapa</button></nav>
          <small>© {new Date().getFullYear()} Yapa · Lima, Perú · Pagos con Yape y Plin</small>
        </footer>

        <nav className="tab-bar" aria-label="Navegación">
          {tabs.map((tab) => <button key={tab.id} type="button" className={view === tab.id ? 'is-active' : ''} aria-current={view === tab.id ? 'page' : undefined} onClick={() => openTab(tab.id)}><span className="tab-icon"><Icon name={tab.icon} size={23} weight={view === tab.id ? 'fill' : 'regular'} />{tab.id === 'cart' && lines.length ? <span className="tab-count">{lines.length}</span> : null}</span>{tab.label}</button>)}
          <button type="button" className={view === 'account' ? 'is-active' : ''} aria-current={view === 'account' ? 'page' : undefined} onClick={openAccount}><span className="tab-icon">{account ? <span className="account-avatar account-avatar--sm" aria-hidden="true">{firstName?.charAt(0).toUpperCase()}</span> : <Icon name="user" size={23} />}</span>{account ? 'Cuenta' : 'Entrar'}</button>
        </nav>
      </>}
      {toastRegion}
      {!showAdmin && sheet === 'como-funciona' ? <Sheet label="Cómo funciona" onClose={() => setSheet(null)}><HowItWorks /></Sheet> : null}
    </div>
    </InviteContext.Provider>
  );
}
