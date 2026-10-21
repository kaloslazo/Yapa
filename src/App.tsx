import { useCallback, useEffect, useMemo, useState } from 'react';
import { AdminPanel } from './components/AdminPanel';
import { AuthDialog, type AuthAudience } from './components/AuthDialog';
import { Catalog } from './components/Catalog';
import { toastDuration } from './utils/toast';
import { CartPanel, MobileCartBar, type CartLine } from './components/CartPanel';
import { CartPage } from './components/CartPage';
import { CheckoutDialog } from './components/CheckoutDialog';
import { HowItWorksSection } from './components/EditorialSections';
import { InviteContext } from './components/InviteCard';
import { InvitePage } from './components/InvitePage';
import { PrivacyPage } from './components/PrivacyPage';
import { Icon } from './components/Icon';
import { NoticeBell } from './components/NoticeBell';
import { OrdersPage, type Claimable, type ClaimRecord, type MyOrders } from './components/OrdersPage';
import { ZonePage, type MyZone } from './components/ZonePage';
import { api, ApiError } from './services/api';
import { toAccount, toCycle, toNotice, toOrder, toProduct, toQuote, toZone } from './services/mappers';
import type { Account, CartState, CycleState, Notice, Order, Product, Quote, RefundDestination, Zone } from './types';
import { cartSubtotal, stepDown, stepUp } from './utils/cart';
import { inviteCodeFromPath, inviteLink } from './utils/invite';
import { noticeTarget } from './utils/notices';
import { canOpenZonePanel, homeFor } from './utils/roles';
import { readStored, writeStored } from './utils/storage';
import './styles.css';

/* eslint-disable @typescript-eslint/no-explicit-any */
type Raw = Record<string, any>;
type View = 'store' | 'orders' | 'cart' | 'zone';

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
  const [toast, setToast] = useState<{ message: string; tone: 'neutral' | 'success' | 'warning' } | null>(null);
  const [offline, setOffline] = useState(false);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [unreadNotices, setUnreadNotices] = useState(0);
  const [emailNotices, setEmailNotices] = useState(true);
  const [clockOffset, setClockOffset] = useState(0);
  const [inviteCode, setInviteCode] = useState<string | null>(() => inviteCodeFromPath(window.location.pathname));
  const [invite, setInvite] = useState<{ code: string; today: number; total: number } | null>(null);

  const notify = useCallback((message: string, tone: 'neutral' | 'success' | 'warning' = 'neutral') => setToast({ message, tone }), []);
  const fail = useCallback((error: unknown) => notify(error instanceof Error ? error.message : 'Algo salió mal.', 'warning'), [notify]);

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
    if (!account || account.role === 'admin') { setInvite(null); return; }
    loadInvite().catch(() => setInvite(null));
  }, [account, loadInvite]);

  useEffect(() => {
    if (!account || account.role === 'admin') { setMyOrders(null); setMyZone(null); return; }
    if (view === 'orders') loadOrders().catch(fail);
    if (view === 'zone') loadZone().catch(fail);
  }, [account, view, loadOrders, loadZone, fail]);

  const isNeighbor = account !== null && account.role !== 'admin';
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
    const timeout = window.setTimeout(() => setToast(null), toastDuration(toast.tone));
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
  const needAccount = (message: string) => { openAuth('vecino'); notify(message); };
  const goStore = (anchor = 'catalog') => { setAdminOpen(false); setView('store'); go(anchor); window.requestAnimationFrame(() => document.getElementById(anchor)?.scrollIntoView({ behavior: 'smooth', block: 'start' })); };
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
    if (current >= product.maxPerOrder) { notify(`Puedes pedir hasta ${product.maxPerOrder} ${product.unit} de ${product.name}.`, 'warning'); return; }
    setCart((c) => ({ ...c, [product.id]: stepUp(product, c[product.id] || 0) }));
    if (!current) notify(`${product.name} se agregó a tu canasta.`, 'success');
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
    if (account.role === 'admin') { notify('El equipo de Yapa no compra desde esta cuenta.', 'warning'); return; }
    try {
      setQuote(toQuote(await api.post<Raw>('/api/cotizar', { lineas: cartBody() })));
      setConfirmation(null);
      setCheckoutOpen(true);
    } catch (error) { fail(error); }
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
      notify(`Pedido ${order.id} cancelado.`, 'success');
      await Promise.all([loadOrders(), loadAccount(), loadPublic()]);
    } catch (error) { fail(error); }
  };
  const withdraw = async (amount: number) => {
    try {
      await api.post('/api/saldo/devolucion', { monto: amount.toFixed(2) });
      notify('Listo: te devolvemos tu saldo a tu Yape o Plin en hasta 30 días.', 'success');
      await Promise.all([loadOrders(), loadAccount()]);
    } catch (error) { fail(error); }
  };
  const claim = async (form: FormData) => {
    try {
      await api.post('/api/reclamos', form);
      await loadOrders();
    } catch (error) { fail(error); throw error; }
  };

  // --- zona ---

  const zoneAction = (action: () => Promise<unknown>, success: string) => async () => {
    try {
      await action();
      notify(success, 'success');
      await Promise.all([loadZone(), loadAccount(), loadPublic()]);
    } catch (error) { fail(error); }
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
      notify(enabled ? 'Te avisaremos también por correo.' : 'Ya no te mandaremos avisos por correo.', 'success');
    } catch (error) { fail(error); }
  };

  // --- sesión ---

  const login = async (kind: AuthAudience, user: string, secret: string) => finishLogin(toAccount(await api.post<Raw>('/api/sesion', { tipo: kind, usuario: user, secreto: secret })));
  const loginWithGoogle = async (credential: string) => { finishLogin(toAccount(await api.post<Raw>('/api/sesion/google', { credential }))); };
  const finishLogin = (me: Account) => {
    api.setCsrf(me.csrf);
    setAccount(me);
    setAuthOpen(false);
    notify(`Hola, ${me.name.split(' ')[0]}.`, 'success');
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

  const accountZone = zones.find((z) => z.id === account?.zoneId);
  const showAdmin = adminOpen && account?.role === 'admin';

  if (window.location.pathname.replace(/\/$/, '') === '/privacidad') return <PrivacyPage />;
  if (inviteCode) return <InvitePage code={inviteCode} googleClientId={googleClientId} signedIn={Boolean(account)} onJoined={joinedByInvite} onGoHome={goHomeFromInvite} />;

  const inviteState = { url: invite ? inviteLink(window.location.origin, invite.code) : null, today: invite?.today ?? 0, total: invite?.total ?? 0, renew: async () => { try { await loadInvite(true); notify('Listo: tu enlace nuevo ya está activo.', 'success'); } catch (error) { fail(error); } } };

  return (
    <InviteContext.Provider value={inviteState}>
    <div className="app-shell">
      {showAdmin ? <AdminPanel adminName={account?.name ?? ''} notify={notify} onClose={() => { setAdminOpen(false); goStore('catalog'); }} onLogout={() => void logout()} /> : <>
        <a className="skip-link" href="#contenido" onClick={(event) => { event.preventDefault(); const main = document.querySelector('main'); if (main) { main.setAttribute('tabindex', '-1'); main.focus(); main.scrollIntoView(); } }}>Saltar al contenido principal</a>
        <header className="topbar">
          <a className="brand" href="#catalog" aria-label="Yapa, inicio" onClick={(event) => { event.preventDefault(); goStore('catalog'); }}><img className="brand-logo-mark" src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" fetchPriority="high" /><span>yapa</span></a>
          <nav className="main-nav" aria-label="Navegación principal">
            <a className={`nav-link ${view === 'store' ? 'is-active' : ''}`} href="#catalog" onClick={(event) => { event.preventDefault(); goStore('catalog'); }}>Comprar</a>
            <button className={`nav-link ${view === 'orders' ? 'is-active' : ''}`} type="button" onClick={() => openView('orders')}>Mis pedidos</button>
            <button className={`nav-link ${view === 'zone' ? 'is-active' : ''}`} type="button" onClick={() => openView('zone')}>{account && canOpenZonePanel(account.role) ? <><Icon name="crown" size={15} /> Mi zona</> : 'Mi zona'}</button>
            <button className={`nav-link ${view === 'cart' ? 'is-active' : ''}`} type="button" onClick={() => openView('cart')}>Canasta{lines.length ? <span className="nav-badge">{lines.length}</span> : null}</button>
          </nav>
          <div className="topbar-actions">
            {isNeighbor ? <NoticeBell notices={notices} unread={unreadNotices} emailNotices={emailNotices} emailVerified={Boolean(account?.emailVerified)} now={new Date(Date.now() + clockOffset)} onOpenNotice={(notice) => void openNotice(notice)} onReadAll={() => void readAllNotices()} onToggleEmail={(enabled) => void toggleEmailNotices(enabled)} onVerifyEmail={() => openAuth('vecino')} /> : null}
            <button className="location-button" type="button" onClick={() => (account ? openView('zone') : notify('Zonas activas en Lince y Jesús María; La Victoria muy pronto.'))}><Icon name="pin" size={16} /><span>{accountZone?.district ?? 'Lima'} · <strong>{accountZone?.name ?? 'Elige tu zona'}</strong></span><Icon name="chevron" size={15} /></button>
            <button className="account-button" type="button" onClick={() => openAuth('vecino')}><Icon name="user" size={17} /><span>{account ? account.name.split(' ')[0] : 'Ingresar'}</span>{account?.balance ? <span className="balance-chip">{`S/ ${account.balance.toFixed(2)}`}</span> : null}</button>
          </div>
        </header>

        {offline ? <div className="offline-banner" role="alert"><Icon name="warning" size={18} /> No pudimos conectar con Yapa.{import.meta.env.DEV ? <> Levanta el motor con <code>npm run api</code>.</> : null}<button className="text-button" type="button" onClick={retry}>Reintentar</button></div> : null}

        {view === 'orders' ? <OrdersPage data={myOrders} claimables={claimables} claims={claims} onBack={() => goStore('catalog')} onCancel={cancelOrder} onWithdraw={withdraw} onClaim={claim} />
          : view === 'zone' ? <ZonePage data={myZone} zones={zones} userId={Number(account?.user ?? 0)} districts={districts} onBack={() => goStore('catalog')}
            onJoin={(zoneId) => zoneAction(() => api.post(`/api/zonas/${zoneId}/unirme`), 'Te uniste a la zona.')()}
            onLocate={async (lat, lon) => { try { await api.post('/api/ubicacion', { lat, lon }); notify('Ubicación guardada.', 'success'); } catch (error) { fail(error); throw error; } }}
            onCreate={(name, district, lat, lon) => zoneAction(() => api.post('/api/zonas', { nombre: name, distrito: district, lat, lon }), '¡Creaste tu zona! Ahora eres su admin.')()}
            onActivate={(zoneId, kind, contact) => zoneAction(() => api.post(`/api/zonas/${zoneId}/activar`, { tipo: kind, contacto: contact }), 'Tu zona ya recibe pedidos.')()}
            onRequestMerge={(zoneId, target) => zoneAction(() => api.post(`/api/zonas/${zoneId}/unir`, { destino: target }), 'Solicitud enviada: falta que el admin de la otra zona acepte.')()}
            onAnswerMerge={(id, accept) => zoneAction(() => api.post(`/api/solicitudes/${id}/${accept ? 'aceptar' : 'rechazar'}`), accept ? 'Zonas unidas: ahora suman juntas para el mínimo.' : 'Solicitud rechazada.')()}
            onWithdrawMerge={(id) => zoneAction(() => api.post(`/api/solicitudes/${id}/retirar`), 'Solicitud retirada.')()}
            onLeaveGroup={(zoneId) => zoneAction(() => api.post(`/api/zonas/${zoneId}/separar`), 'Tu zona vuelve a contar sola.')()}
            onTransfer={(zoneId, newAdmin) => zoneAction(() => api.post(`/api/zonas/${zoneId}/transferir`, { nuevo: newAdmin }), 'Rol transferido. ¡Gracias por organizar tu edificio!')()} />
            : view === 'cart' ? <CartPage lines={lines} subtotal={subtotal} savings={savings} onAdd={addProduct} onDecrease={decreaseProduct} onCheckout={() => void openCheckout()} onBack={() => goStore('catalog')} />
              : <main id="catalog" className="page-content">
                <section className="welcome-row hero-banner" aria-labelledby="page-title"><div className="welcome-copy"><span className="hero-promise"><Icon name="ok" size={16} /> Nunca pagas más del precio que ves</span><h1 id="page-title">Compra mejor para tu semana</h1><p>Del mercado mayorista a tu portería. Pagas el precio máximo y lo que ahorramos entre vecinos te vuelve como saldo.</p><div className="hero-actions"><button className="primary-button" type="button" onClick={() => document.querySelector('#catalog-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>Ver catálogo <Icon name="arrow" size={17} /></button><a className="text-button" href="#how-it-works" onClick={(event) => { event.preventDefault(); goStore('how-it-works'); }}>Cómo funciona</a></div></div><div className="hero-side"><div className="hero-illustration" role="img" aria-label="Agricultora peruana con una canasta de productos frescos"><span className="hero-note"><Icon name="leaf" size={14} /> Del campo a tu canasta</span><img src="/images/brand/yapa-farmer-banner.webp" alt="Agricultora con una canasta de productos frescos" width="760" height="694" fetchPriority="high" /></div></div></section>
                <section className="delivery-overview" aria-label="Entrega, cobertura y pago"><div className="delivery-facts"><div className="delivery-fact delivery-fact--primary"><span className="delivery-fact-icon"><Icon name="truck" size={20} /></span><div><small>Semana {state?.cycle ?? '—'} · próxima entrega</small><strong>Sábado</strong><span>{state?.open ? 'Pedidos hasta el miércoles a las 20:00' : 'Cerrado para pedidos: vuelve el lunes'}</span></div></div><div className="delivery-fact"><span className="delivery-fact-icon"><Icon name="users" size={19} /></span><div><small>Compramos entre vecinos</small><strong>{state?.minimumGroup ?? 8} pedidos por grupo</strong><span>Si tu grupo no llega, te devolvemos el 100 %</span></div></div><div className="delivery-fact"><span className="delivery-fact-icon"><Icon name="wallet" size={19} /></span><div><small>Pago por adelantado</small><strong>Yape o Plin</strong><span>Con el código que te damos; sin escribir nada</span></div></div></div></section>
                <div className="workspace-grid"><Catalog products={visible} categories={categories} cart={cart} category={category} query={query} onCategoryChange={setCategory} onQueryChange={setQuery} onAdd={addProduct} onDecrease={decreaseProduct} onClearFilters={() => { setCategory('Todos'); setQuery(''); }} /><CartPanel lines={lines} subtotal={subtotal} savings={savings} onAdd={addProduct} onDecrease={decreaseProduct} onCheckout={() => void openCheckout()} onFocusCatalog={() => document.querySelector('#catalog-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' })} /></div>
                <HowItWorksSection />
              </main>}
        {!offline && view === 'store' && lines.length ? <MobileCartBar count={lines.length} subtotal={subtotal} onCheckout={() => void openCheckout()} /> : null}

        <footer className="site-footer"><span>Yapa · compras que rinden · Diseño de Software, UTEC 2026-2</span><div className="footer-actions"><button className="footer-link" type="button" onClick={openAdmin}>Centro de operaciones</button><span>Pagos con Yape y Plin verificados por el equipo</span></div></footer>
      </>}
      <div className="toast-region" aria-live={toast?.tone === 'warning' ? 'assertive' : 'polite'} aria-atomic="true">{toast ? <div className={`toast toast--${toast.tone} is-visible`}><Icon name={toast.tone === 'success' ? 'check' : toast.tone === 'warning' ? 'warning' : 'info'} size={18} /><span>{toast.message}</span></div> : null}</div>
      {!showAdmin ? <>
        <AuthDialog open={authOpen} account={account} initialAudience={authAudience} onClose={() => setAuthOpen(false)} onLogin={login} onLogout={logout} googleClientId={googleClientId} onGoogleLogin={loginWithGoogle} onGoogleLink={async (credential) => { await api.post('/api/cuenta/google', { credential }); await loadAccount(); }} onGoogleUnlink={async () => { await api.post('/api/cuenta/google/desvincular'); await loadAccount(); }} onResetPin={async (user, code, pin) => (await api.post<{ mensaje: string }>('/api/pin/restablecer', { usuario: user, codigo: code, pin })).mensaje} onSendEmail={async (email) => { await api.post('/api/cuenta/correo', { correo: email }); await loadAccount(); }} onVerifyEmail={async (code) => { await api.post('/api/cuenta/correo/verificar', { codigo: code }); await loadAccount(); }} onCreatePin={async (pin) => { await api.post('/api/pin/crear', { pin }); await loadAccount(); }} onForgotPin={async (user) => (await api.post<{ mensaje: string }>('/api/pin/olvide', { usuario: user })).mensaje} onOpenAdmin={openAdmin} onOpenZone={() => openView('zone')} onOpenOrders={() => openView('orders')} />
        <CheckoutDialog open={checkoutOpen} quote={quote} zone={accountZone} cycleOpen={Boolean(state?.open)} confirmation={confirmation} onClose={() => { setCheckoutOpen(false); setConfirmation(null); }} onSubmit={registerOrder} onOpenOrders={() => { setCheckoutOpen(false); setConfirmation(null); openView('orders'); }} />
      </> : null}
    </div>
    </InviteContext.Provider>
  );
}
