import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { AdminSkeleton, PartnerSkeleton } from './components/Skeleton';
import { AuthDialog, type AuthAudience, type LoginKind } from './components/AuthDialog';
import { Catalog } from './components/Catalog';
import { toastDuration, type Toast, type ToastTone } from './utils/toast';
import { CartPanel, MobileCartBar, type CartLine } from './components/CartPanel';
import { CartPage } from './components/CartPage';
import { CheckoutDialog } from './components/CheckoutDialog';
import { FaqSection, HowItWorksSection } from './components/EditorialSections';
import { InviteContext } from './components/InviteCard';
import { InvitePage } from './components/InvitePage';
import { PrivacyPage } from './components/PrivacyPage';
import { Icon } from './components/Icon';
import { NoticeBell } from './components/NoticeBell';
import { OrdersPage, type Claimable, type ClaimRecord, type MyOrders } from './components/OrdersPage';
import { ZonePage, type MyZone } from './components/ZonePage';
import { api, ApiError } from './services/api';
import { toAccount, toCycle, toNotice, toOrder, toProduct, toQuote, toZone } from './services/mappers';
import type { Account, CartState, CycleState, Notice, Order, Product, Quote, RefundDestination, Role, Zone } from './types';
import { cartSubtotal, stepDown, stepUp } from './utils/cart';
import { inviteCodeFromPath, inviteLink } from './utils/invite';
import { noticeTarget } from './utils/notices';
import { canOpenZonePanel, homeFor, isNeighborRole, isPartner, isStaff } from './utils/roles';
import { readStored, writeStored } from './utils/storage';
import { formatMoney } from './utils/format';

import './styles.css';

// fecha límite y entrega, en dos datos cortos
function WeekFacts({ open, place }: { open: boolean; place?: string }) {
  return (
    <ul className="week-facts">{open ? <><li><Icon name="calendar" size={18} />Pide hasta el miércoles, 8 p. m.</li><li><Icon name="truck" size={18} />{place ? `Llega el sábado a ${place}` : 'Llega el sábado'}</li></> : <li><Icon name="calendar" size={18} />Pedidos cerrados. Abrimos el lunes.</li>}</ul>
  );
}

// FE-SG-2: el panel del equipo se baja solo cuando se abre
const AdminPanel = lazy(() => import('./components/AdminPanel').then((module) => ({ default: module.AdminPanel })));
const PartnerPanel = lazy(() => import('./components/PartnerPanel').then((module) => ({ default: module.PartnerPanel })));

/* eslint-disable @typescript-eslint/no-explicit-any */
type Raw = Record<string, any>;
type View = 'store' | 'orders' | 'cart' | 'zone';

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

const viewFromHash = (): View => ({ '#orders': 'orders', '#cart': 'cart', '#zone': 'zone' } as Record<string, View>)[window.location.hash] ?? 'store';

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
  const [view, setView] = useState<View>(viewFromHash);
  const [adminOpen, setAdminOpen] = useState(() => window.location.hash === '#admin');
  const [authOpen, setAuthOpen] = useState(false);
  const [authAudience, setAuthAudience] = useState<AuthAudience>('vecino');
  const [checkoutOpen, setCheckoutOpen] = useState(false);
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
    const sync = () => { setAdminOpen(window.location.hash === '#admin'); setView(viewFromHash()); };
    window.addEventListener('hashchange', sync);
    window.addEventListener('popstate', sync);
    return () => { window.removeEventListener('hashchange', sync); window.removeEventListener('popstate', sync); };
  }, []);

  // --- navegación ---

  const go = (hash: string) => { window.history.pushState(null, '', `${window.location.pathname}${window.location.search}#${hash}`); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const openAuth = (audience: AuthAudience = 'vecino') => { setAuthAudience(audience); setAuthOpen(true); };
  const needAccount = (message: string) => { openAuth('vecino'); notify(message, 'neutral', 'Tu canasta se queda guardada mientras entras.'); };
  // 'catalog' es el <main> entero: basta con volver arriba; bajar hasta él lo pegaba bajo el encabezado
  const goStore = (anchor = 'catalog') => { setAdminOpen(false); setView('store'); go(anchor); if (anchor !== 'catalog') window.requestAnimationFrame(() => document.getElementById(anchor)?.scrollIntoView({ behavior: 'smooth', block: 'start' })); };
  const openView = (next: View) => {
    if ((next === 'orders' || next === 'zone') && !account) { needAccount('Entra a tu cuenta para continuar.'); return; }
    setAdminOpen(false); setView(next); go(next);
  };
  const openAdmin = () => {
    if (account?.role !== 'admin') { openAuth('admin'); return; }
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
    if (!current) notify(`${product.name} está en tu canasta`, 'success', `${formatMoney(product.price)} / ${product.unit}. Si pedimos más entre todos, baja.`, { label: 'Ver canasta', run: () => openView('cart') });
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
    if (!account) { needAccount('Entra a tu cuenta para registrar el pedido.'); return; }
    if (!isNeighborRole(account.role)) { notify('Esta cuenta no es de vecino', 'warning', 'Para comprar, entra con una cuenta de vecino.'); return; }
    try {
      setQuote(toQuote(await api.post<Raw>('/api/cotizar', { lineas: cartBody() })));
      setConfirmation(null);
      setCheckoutOpen(true);
    } catch (error) { fail(error, 'No pudimos preparar tu pedido'); }
  };
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
    setAuthOpen(false);
    notify(`Hola, ${me.name.split(' ')[0]}`, 'success', WELCOME[me.role] ?? (me.balance ? `Tienes ${formatMoney(me.balance)} de saldo para tu próxima compra.` : 'Ya puedes armar tu canasta de la semana.'));
    if (homeFor(me.role) === 'operaciones') { setAdminOpen(true); go('admin'); }
    return me;
  };
  const logout = async () => {
    try { await api.delete('/api/sesion'); } catch { /* la sesión ya no existe */ }
    api.setCsrf('');
    setAccount(null);
    setAuthOpen(false);
    setAdminOpen(false);
    setView('store');
    go('catalog');
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
    <div className="toast-region" aria-live={toast?.tone === 'warning' ? 'assertive' : 'polite'} aria-atomic="true">{toast ? <div className={`toast toast--${toast.tone} is-visible`} role={toast.tone === 'warning' ? 'alert' : 'status'}>
      <span className="toast-icon"><Icon name={toast.tone === 'success' ? 'check' : toast.tone === 'warning' ? 'warning' : 'info'} size={18} weight="bold" /></span>
      <div className="toast-copy"><strong>{toast.title}</strong>{toast.detail ? <span>{toast.detail}</span> : null}{toast.action ? <button className="toast-action" type="button" onClick={() => { toast.action?.run(); setToast(null); }}>{toast.action.label}</button> : null}</div>
      <button className="toast-close" type="button" onClick={() => setToast(null)} aria-label="Cerrar aviso"><Icon name="close" size={16} /></button>
    </div> : null}</div>
  );

  if (window.location.pathname.replace(/\/$/, '') === '/privacidad') return <PrivacyPage />;
  if (account && isPartner(account.role)) return <Suspense fallback={<div className="partner-view"><main className="partner-main"><PartnerSkeleton /></main></div>}><PartnerPanel account={account} notify={notify} onLogout={() => void logout()} />{toastRegion}</Suspense>;
  if (account && staffOnly) return <div className="app-shell"><Suspense fallback={<div className="admin-view admin-view--loading"><AdminSkeleton /></div>}><AdminPanel adminName={account.name} role={account.role} notify={notify} onLogout={() => void logout()} /></Suspense>{toastRegion}</div>;
  if (inviteCode) return <InvitePage code={inviteCode} googleClientId={googleClientId} signedIn={Boolean(account)} onJoined={joinedByInvite} onGoHome={goHomeFromInvite} />;

  const inviteState = { url: invite ? inviteLink(window.location.origin, invite.code) : null, today: invite?.today ?? 0, total: invite?.total ?? 0, renew: async () => { try { await loadInvite(true); notify('Tu enlace nuevo ya está activo', 'success', 'El anterior dejó de funcionar. Compártelo solo con vecinos de tu zona.'); } catch (error) { fail(error, 'No pudimos renovar tu enlace'); } } };

  const firstName = account?.name.split(' ')[0];
  const scrollToCatalog = () => document.querySelector('#catalog-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  const tabs: Array<{ id: View; label: string; icon: 'store' | 'receipt' | 'basket' | 'map' }> = [
    { id: 'store', label: 'Comprar', icon: 'store' },
    { id: 'orders', label: 'Pedidos', icon: 'receipt' },
    { id: 'cart', label: 'Canasta', icon: 'basket' },
    { id: 'zone', label: 'Mi zona', icon: 'map' },
  ];
  const openTab = (id: View) => (id === 'store' ? goStore('catalog') : openView(id));

  return (
    <InviteContext.Provider value={inviteState}>
    <div className={`app-shell ${showAdmin ? '' : 'has-tab-bar'}`}>
      {account?.viewingAs ? <div className="view-as-bar" role="status"><span>Estás viendo Yapa como <strong>{account.name}</strong> ({account.role === 'admin_zona' ? 'admin de zona' : 'vecino'}).</span><button type="button" onClick={() => void backFromView()}>Volver a mi cuenta</button></div> : null}
      {showAdmin ? <Suspense fallback={<div className="admin-view admin-view--loading"><AdminSkeleton /></div>}><AdminPanel adminName={account?.name ?? ''} role="admin" notify={notify} onClose={() => { setAdminOpen(false); goStore('catalog'); }} onLogout={() => void logout()} onViewAs={account?.canViewAs ? viewAs : undefined} /></Suspense> : <>
        <a className="skip-link" href="#contenido" onClick={(event) => { event.preventDefault(); const main = document.querySelector('main'); if (main) { main.setAttribute('tabindex', '-1'); main.focus(); main.scrollIntoView(); } }}>Saltar al contenido principal</a>
        <header className="topbar">
          <a className="brand" href="#catalog" aria-label="Yapa, inicio" onClick={(event) => { event.preventDefault(); goStore('catalog'); }}><img className="brand-logo-mark" src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" fetchPriority="high" /><span>yapa</span></a>
          <nav className="main-nav" aria-label="Navegación principal">
            {tabs.map((tab) => <button key={tab.id} className={`nav-link ${view === tab.id ? 'is-active' : ''}`} type="button" aria-current={view === tab.id ? 'page' : undefined} onClick={() => openTab(tab.id)}>{tab.id === 'zone' && account && canOpenZonePanel(account.role) ? <Icon name="crown" size={15} /> : null}{tab.id === 'store' ? 'Comprar' : tab.id === 'orders' ? 'Mis pedidos' : tab.label}{tab.id === 'cart' && lines.length ? <span className="nav-badge">{lines.length}</span> : null}</button>)}
          </nav>
          <div className="topbar-actions">
            {isNeighbor ? <NoticeBell notices={notices} unread={unreadNotices} emailNotices={emailNotices} emailVerified={Boolean(account?.emailVerified)} now={new Date(Date.now() + clockOffset)} onOpenNotice={(notice) => void openNotice(notice)} onReadAll={() => void readAllNotices()} onToggleEmail={(enabled) => void toggleEmailNotices(enabled)} onVerifyEmail={() => openAuth('vecino')} /> : null}
            <button className="location-button" type="button" onClick={() => (account ? openView('zone') : notify('Dónde entregamos', 'neutral', 'Lince y Jesús María ya reciben pedidos. La Victoria abre muy pronto.'))}><Icon name="pin" size={16} /><span>{accountZone?.name ?? 'Elige tu zona'}</span></button>
            <button className="account-button" type="button" onClick={() => openAuth('vecino')} aria-label={account ? `Tu cuenta, ${firstName}` : 'Entrar a Yapa'}>{account ? <span className="account-avatar" aria-hidden="true">{firstName?.charAt(0).toUpperCase()}</span> : <Icon name="user" size={17} />}<span className="account-label">{account ? firstName : 'Entrar'}</span></button>
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
            : view === 'cart' ? <CartPage lines={lines} subtotal={subtotal} savings={savings} onAdd={addProduct} onDecrease={decreaseProduct} onCheckout={() => void openCheckout()} onBack={() => goStore('catalog')} />
              : <main id="catalog" className="page-content">
                {account ? (
                  <section className="week-status" aria-labelledby="page-title">
                    <div>
                      <h1 id="page-title">Hola, {firstName}</h1>
                      <WeekFacts open={Boolean(state?.open)} place={accountZone?.name} />
                    </div>
                    {isNeighbor && (account.balance ?? 0) > 0 ? <button className="balance-link" type="button" onClick={() => openView('orders')}><span>Tu saldo</span><strong>{formatMoney(account.balance ?? 0)}</strong><Icon name="arrow" size={16} /></button> : null}
                  </section>
                ) : <>
                  <section className="hero" aria-labelledby="page-title">
                    <div className="hero-copy">
                      <h1 id="page-title">El mercado mayorista, en tu portería.</h1>
                      <p className="hero-lead">Juntamos los pedidos de tu edificio para comprar al por mayor. Pagas el precio máximo y lo que ahorremos entre todos vuelve a tu saldo.</p>
                      <div className="hero-actions"><button className="primary-button" type="button" onClick={scrollToCatalog}>Ver el catálogo</button><button className="secondary-button" type="button" onClick={() => openAuth('vecino')}>Ya tengo cuenta</button></div>
                      <WeekFacts open={Boolean(state?.open)} />
                    </div>
                    <div className="hero-art"><img src="/images/brand/yapa-farmer-banner.webp" alt="Agricultora con una canasta de productos frescos" width="760" height="694" fetchPriority="high" /></div>
                  </section>
                  <HowItWorksSection />
                </>}
                <div className="workspace-grid"><Catalog products={visible} categories={categories} cart={cart} category={category} query={query} onCategoryChange={setCategory} onQueryChange={setQuery} onAdd={addProduct} onDecrease={decreaseProduct} onClearFilters={() => { setCategory('Todos'); setQuery(''); }} /><CartPanel lines={lines} subtotal={subtotal} savings={savings} onAdd={addProduct} onDecrease={decreaseProduct} onCheckout={() => void openCheckout()} onFocusCatalog={scrollToCatalog} /></div>
                {account ? <HowItWorksSection /> : <FaqSection />}
              </main>}
        </div>
        {!offline && view === 'store' && lines.length ? <MobileCartBar count={lines.length} subtotal={subtotal} onCheckout={() => void openCheckout()} onOpenCart={() => openView('cart')} /> : null}

        <footer className={`site-footer ${view === 'store' ? '' : 'site-footer--secondary'}`}>
          <div className="footer-brand"><span className="brand"><img className="brand-logo-mark" src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" loading="lazy" /><span>yapa</span></span><p>Compras que rinden, entre vecinos.</p></div>
          <nav className="footer-links" aria-label="Enlaces"><a href="#how-it-works" onClick={(event) => { event.preventDefault(); goStore('how-it-works'); }}>Cómo funciona</a><a href="/privacidad">Privacidad</a><button className="footer-link" type="button" onClick={openAdmin}>Equipo Yapa</button></nav>
          <small>© {new Date().getFullYear()} Yapa · Lima, Perú · Pagos con Yape y Plin</small>
        </footer>

        <nav className="tab-bar" aria-label="Navegación">
          {tabs.map((tab) => <button key={tab.id} type="button" className={view === tab.id ? 'is-active' : ''} aria-current={view === tab.id ? 'page' : undefined} onClick={() => openTab(tab.id)}><span className="tab-icon"><Icon name={tab.icon} size={23} weight={view === tab.id ? 'fill' : 'regular'} />{tab.id === 'cart' && lines.length ? <span className="tab-count">{lines.length}</span> : null}</span>{tab.label}</button>)}
          <button type="button" onClick={() => openAuth('vecino')}><span className="tab-icon">{account ? <span className="account-avatar account-avatar--sm" aria-hidden="true">{firstName?.charAt(0).toUpperCase()}</span> : <Icon name="user" size={23} />}</span>{account ? 'Cuenta' : 'Entrar'}</button>
        </nav>
      </>}
      {toastRegion}
      {!showAdmin ? <>
        <AuthDialog open={authOpen} account={account} initialAudience={authAudience} onClose={() => setAuthOpen(false)} onLogin={login} onLogout={logout} googleClientId={googleClientId} onGoogleLogin={loginWithGoogle} onGoogleLink={async (credential) => { await api.post('/api/cuenta/google', { credential }); await loadAccount(); }} onGoogleUnlink={async () => { await api.post('/api/cuenta/google/desvincular'); await loadAccount(); }} onResetPin={async (user, code, pin) => (await api.post<{ mensaje: string }>('/api/pin/restablecer', { usuario: user, codigo: code, pin })).mensaje} onSendEmail={async (email) => { await api.post('/api/cuenta/correo', { correo: email }); await loadAccount(); }} onVerifyEmail={async (code) => { await api.post('/api/cuenta/correo/verificar', { codigo: code }); await loadAccount(); }} onCreatePin={async (pin) => { await api.post('/api/pin/crear', { pin }); await loadAccount(); }} onForgotPin={async (user) => (await api.post<{ mensaje: string }>('/api/pin/olvide', { usuario: user })).mensaje} onOpenAdmin={openAdmin} onOpenZone={() => openView('zone')} onOpenOrders={() => openView('orders')} />
        <CheckoutDialog open={checkoutOpen} quote={quote} zone={accountZone} cycleOpen={Boolean(state?.open)} confirmation={confirmation} onClose={() => { setCheckoutOpen(false); setConfirmation(null); }} onSubmit={registerOrder} onOpenOrders={() => { setCheckoutOpen(false); setConfirmation(null); openView('orders'); }} />
      </> : null}
    </div>
    </InviteContext.Provider>
  );
}
