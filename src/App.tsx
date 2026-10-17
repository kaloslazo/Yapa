import { useEffect, useMemo, useState } from 'react';
import { DEFAULT_ZONE_ID, products as initialCatalog, windowLabel, zoneById, zones } from './data/catalog';
import { AdminPanel } from './components/AdminPanel';
import { AuthDialog, type AuthAudience } from './components/AuthDialog';
import { Catalog } from './components/Catalog';
import { CartPanel } from './components/CartPanel';
import { CartPage } from './components/CartPage';
import { CheckoutDialog } from './components/CheckoutDialog';
import { HowItWorksSection } from './components/EditorialSections';
import { Icon } from './components/Icon';
import { OrdersPage } from './components/OrdersPage';
import { getCurrentAccount, getSessionAccount, isAdminAccount, saveAccountZone } from './services/auth';
import { createOrder, loadCatalog, loadOrders, saveLocalCatalog, seedLocalDemo, updateOrder, updateProduct as persistProductUpdate, withTiers } from './services/database';
import { persistenceMode, appwriteReady } from './services/appwrite';
import type { AccountProfile, CartState, Category, OrderConfirmation, OrderRecord, OrderSelection, Product, RefundDestination } from './types';
import { categories } from './types';
import { balanceOf, cancelOrder, canCheckout, createOrderCode, cycleId, isCycleOpen, maxPerLine, MIN_SUBTOTAL, quoteOrder, settleCycle, validateCheckout } from './utils/domain';
import { now } from './utils/clock';
import { readStored, writeStored } from './utils/storage';
import { formatMoney } from './utils/format';
import './styles.css';

const DEFAULT_SELECTION: OrderSelection = {
  zoneId: DEFAULT_ZONE_ID,
  reference: '',
  paymentMethod: 'YAPE',
  operationCode: '',
  useBalance: 0,
};

type CustomerView = 'store' | 'orders' | 'cart';

function initialCustomerView(): CustomerView {
  if (window.location.hash === '#orders') return 'orders';
  if (window.location.hash === '#cart') return 'cart';
  return 'store';
}

function initialCategory(): Category {
  const value = new URLSearchParams(window.location.search).get('category');
  return value && categories.includes(value as Category) ? value as Category : 'Todos';
}

export default function App() {
  const [category, setCategory] = useState<Category>(initialCategory);
  const [query, setQuery] = useState(() => new URLSearchParams(window.location.search).get('q') || '');
  const [catalog, setCatalog] = useState<Product[]>(() => readStored('yapa.catalog', initialCatalog).map(withTiers));
  const [cart, setCart] = useState<CartState>(() => readStored('yapa.cart', {}));
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(() => window.location.hash === '#admin');
  const [customerView, setCustomerView] = useState<CustomerView>(initialCustomerView);
  const [authAudience, setAuthAudience] = useState<AuthAudience>('user');
  const [authReturnView, setAuthReturnView] = useState<CustomerView | null>(null);
  const [confirmation, setConfirmation] = useState<OrderConfirmation | null>(null);
  const [selection, setSelection] = useState<OrderSelection>(DEFAULT_SELECTION);
  const [account, setAccount] = useState<AccountProfile | null>(() => appwriteReady ? null : getCurrentAccount());
  const [dataReady, setDataReady] = useState(false);
  const [toast, setToast] = useState<{ message: string; tone: 'neutral' | 'success' | 'warning' } | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([loadCatalog(), getSessionAccount()]).then(([nextCatalog, nextAccount]) => {
      if (!active) return;
      setCatalog(nextCatalog);
      setAccount(nextAccount);
      setDataReady(true);
    }).catch((error) => {
      if (!active) return;
      setDataReady(true);
      setToast({ message: error instanceof Error ? error.message : 'No pudimos cargar la información de Yapa.', tone: 'warning' });
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!dataReady) return;
    if (!account) {
      setOrders([]);
      return;
    }
    let active = true;
    loadOrders(account.id, isAdminAccount(account)).then((nextOrders) => {
      if (active) setOrders(nextOrders);
    }).catch((error) => {
      if (active) setToast({ message: error instanceof Error ? error.message : 'No pudimos cargar tus pedidos.', tone: 'warning' });
    });
    return () => { active = false; };
  }, [account, dataReady]);

  useEffect(() => {
    saveLocalCatalog(catalog);
  }, [catalog]);

  useEffect(() => {
    writeStored('yapa.cart', cart);
  }, [cart]);

  useEffect(() => {
    if (!toast) return;
    const timeout = window.setTimeout(() => setToast(null), 2800);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  useEffect(() => {
    const syncViewFromUrl = () => {
      const hash = window.location.hash;
      setAdminOpen(hash === '#admin');
      setCustomerView(hash === '#orders' ? 'orders' : hash === '#cart' ? 'cart' : 'store');
    };
    window.addEventListener('hashchange', syncViewFromUrl);
    window.addEventListener('popstate', syncViewFromUrl);
    return () => {
      window.removeEventListener('hashchange', syncViewFromUrl);
      window.removeEventListener('popstate', syncViewFromUrl);
    };
  }, []);

  useEffect(() => {
    if (!dataReady || !adminOpen || (account && isAdminAccount(account))) return;
    setAdminOpen(false);
    setCustomerView('store');
    if (window.location.hash === '#admin') window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}#catalog`);
  }, [account, adminOpen, dataReady]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (category === 'Todos') params.delete('category');
    else params.set('category', category);
    if (query) params.set('q', query);
    else params.delete('q');
    const search = params.toString();
    window.history.replaceState(null, '', `${window.location.pathname}${search ? `?${search}` : ''}${window.location.hash}`);
  }, [category, query]);

  const visibleProducts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return catalog.filter((product) => {
      const matchesCategory = category === 'Todos' || product.category === category;
      const matchesQuery = !normalizedQuery || `${product.name} ${product.category} ${product.detail}`.toLowerCase().includes(normalizedQuery);
      return matchesCategory && matchesQuery;
    });
  }, [catalog, category, query]);

  const lines = useMemo(() => Object.entries(cart).flatMap(([id, quantity]) => {
    const product = catalog.find((item) => item.id === id);
    return product ? [{ product, quantity }] : [];
  }), [cart, catalog]);
  const quote = useMemo(() => quoteOrder(lines), [lines]);
  const subtotal = quote.subtotal;
  const clock = now();
  const currentCycle = cycleId(clock);
  const cycleOpen = isCycleOpen(clock);
  const myOrders = useMemo(() => orders.filter((order) => order.userId === account?.id), [orders, account]);
  const balance = balanceOf(myOrders);
  const accountZone = zoneById(account?.zoneId);
  const initialSelection = useMemo(() => ({ ...selection, zoneId: account?.zoneId ?? selection.zoneId }), [selection, account]);

  const addProduct = (product: Product) => {
    const currentQuantity = cart[product.id] || 0;
    if (currentQuantity >= product.stock) {
      setToast({ message: `${product.name} no tiene más stock disponible.`, tone: 'warning' });
      return;
    }
    if (currentQuantity >= maxPerLine(product)) {
      setToast({ message: `Puedes pedir hasta ${maxPerLine(product)} ${product.unit} de ${product.name}.`, tone: 'warning' });
      return;
    }
    setCart((current) => ({ ...current, [product.id]: (current[product.id] || 0) + 1 }));
    setToast({ message: `${product.name} se agregó a tu canasta.`, tone: 'success' });
  };

  const decreaseProduct = (product: Product) => {
    setCart((current) => {
      const next = { ...current };
      const quantity = (next[product.id] || 0) - 1;
      if (quantity <= 0) delete next[product.id];
      else next[product.id] = quantity;
      return next;
    });
  };

  const openCheckout = () => {
    if (!account) {
      openAuth('user');
      setToast({ message: 'Ingresa a tu cuenta para registrar el pedido.', tone: 'neutral' });
      return;
    }
    if (!canCheckout(subtotal)) {
      setToast({ message: `Te faltan ${formatMoney(MIN_SUBTOTAL - subtotal)} para llegar al mínimo de S/ 50.00.`, tone: 'warning' });
      return;
    }
    if (!cycleOpen) {
      setToast({ message: 'El ciclo está cerrado: los pedidos se reciben de lunes a miércoles hasta las 20:00.', tone: 'warning' });
      return;
    }
    setConfirmation(null);
    setCheckoutOpen(true);
  };

  const registerOrder = async (nextSelection: OrderSelection) => {
    if (!account) {
      openAuth('user');
      return;
    }
    const moment = now();
    const error = validateCheckout({
      subtotal: quote.subtotal, total: quote.total, zone: zoneById(nextSelection.zoneId), now: moment, orders: myOrders,
      paymentMethod: nextSelection.paymentMethod, operationCode: nextSelection.operationCode, useBalance: nextSelection.useBalance,
    });
    if (error) throw new Error(error);
    const buyer = account.zoneId === nextSelection.zoneId ? account : await saveAccountZone(account, nextSelection.zoneId);
    if (buyer !== account) setAccount(buyer);
    const nextOrder = await createOrder({ account: buyer, selection: nextSelection, lines, quote, cycleId: cycleId(moment), orderCode: createOrderCode(Date.now() % 1000000) });
    setSelection({ ...nextSelection, operationCode: '', useBalance: 0 });
    setOrders((current) => [nextOrder, ...current]);
    setConfirmation(nextOrder);
    setCart({});
  };

  const applyPatch = async (order: OrderRecord, patch: Partial<OrderRecord>) => {
    await updateOrder(order.id, patch);
    setOrders((current) => current.map((item) => (item.id === order.id ? { ...item, ...patch } : item)));
  };

  const cancel = async (order: OrderRecord, destination: RefundDestination) => {
    try {
      await applyPatch(order, cancelOrder(order, destination));
      setToast({ message: `Pedido ${order.orderCode} cancelado.`, tone: 'success' });
    } catch (error) {
      setToast({ message: error instanceof Error ? error.message : 'No pudimos cancelar el pedido.', tone: 'warning' });
    }
  };

  const verify = async (order: OrderRecord) => {
    try {
      await applyPatch(order, { paymentStatus: 'VERIFICADO' });
      setToast({ message: `Pago del pedido ${order.orderCode} verificado.`, tone: 'success' });
    } catch (error) {
      setToast({ message: error instanceof Error ? error.message : 'No pudimos verificar el pago.', tone: 'warning' });
    }
  };

  // liquidación: se calcula todo primero y recién después se guarda cada pedido
  const settle = async (cycle: string) => {
    const result = settleCycle(orders, cycle, zones, catalog);
    for (const item of result.orders) {
      const order = orders.find((candidate) => candidate.id === item.orderId);
      if (order) await updateOrder(order.id, { status: item.status, finalTotal: item.finalTotal, deliveryFinal: item.deliveryFinal, refundToBalance: item.refundToBalance, refundToMethod: item.refundToMethod });
    }
    const byId = new Map(result.orders.map((item) => [item.orderId, item]));
    setOrders((current) => current.map((order) => (byId.has(order.id) ? { ...order, ...byId.get(order.id) } : order)));
    setToast({ message: `Ciclo ${cycle} liquidado: ${formatMoney(result.totalToBalance)} volvió a saldo.`, tone: 'success' });
    return result;
  };

  const markRefundPaid = async (order: OrderRecord) => {
    try {
      await applyPatch(order, { refundPaidAt: new Date().toISOString() });
    } catch (error) {
      setToast({ message: error instanceof Error ? error.message : 'No pudimos registrar la devolución.', tone: 'warning' });
    }
  };

  const seedDemo = () => {
    setOrders(seedLocalDemo(catalog, currentCycle));
    setToast({ message: 'Se cargaron 13 pedidos de demo en el ciclo actual.', tone: 'success' });
  };

  const closeCheckout = () => {
    setCheckoutOpen(false);
    setConfirmation(null);
  };

  const clearFilters = () => {
    setCategory('Todos');
    setQuery('');
  };

  const updateProduct = (id: string, patch: Partial<Pick<Product, 'price' | 'stock'>>) => {
    const previous = catalog.find((product) => product.id === id);
    setCatalog((current) => current.map((product) => product.id === id ? withTiers({ ...product, ...patch }) : product));
    void persistProductUpdate(id, patch).catch((error) => {
      if (previous) setCatalog((current) => current.map((product) => product.id === id ? previous : product));
      setToast({ message: error instanceof Error ? error.message : 'No pudimos guardar el cambio.', tone: 'warning' });
    });
  };

  const showInfo = (message: string) => setToast({ message, tone: 'neutral' });
  const openAuth = (audience: AuthAudience = 'user', returnView: CustomerView | null = null) => {
    setAuthAudience(audience);
    setAuthReturnView(returnView);
    setAuthOpen(true);
  };
  const openOrders = () => {
    if (!account) {
      openAuth('user', 'orders');
      setToast({ message: 'Ingresa para ver tus pedidos.', tone: 'neutral' });
      return;
    }
    setCustomerView('orders');
    window.history.pushState(null, '', `${window.location.pathname}${window.location.search}#orders`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  const openCart = () => {
    setCustomerView('cart');
    window.history.pushState(null, '', `${window.location.pathname}${window.location.search}#cart`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  const goToStore = (anchor = 'catalog') => {
    setAdminOpen(false);
    setCustomerView('store');
    window.history.pushState(null, '', `${window.location.pathname}${window.location.search}#${anchor}`);
    window.requestAnimationFrame(() => document.getElementById(anchor)?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  };
  const openAdmin = () => {
    if (!account) {
      openAuth('admin');
      setToast({ message: 'Ingresa con una cuenta administradora para continuar.', tone: 'neutral' });
      return;
    }
    if (!isAdminAccount(account)) {
      setToast({ message: 'Esta sección está reservada para el equipo administrador.', tone: 'warning' });
      return;
    }
    setAdminOpen(true);
    window.history.pushState(null, '', `${window.location.pathname}${window.location.search}#admin`);
  };

  const closeAdmin = () => {
    setAdminOpen(false);
    window.history.pushState(null, '', `${window.location.pathname}${window.location.search}#catalog`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const showAdminView = adminOpen && dataReady && Boolean(account && isAdminAccount(account));

  return (
    <div className="app-shell">
      {showAdminView ? <AdminPanel products={catalog} orders={orders} adminName={account?.name || ''} currentCycle={currentCycle} cycleOpen={cycleOpen} localMode={persistenceMode === 'local'} onClose={closeAdmin} onProductUpdate={updateProduct} onVerify={verify} onSettle={settle} onRefundPaid={markRefundPaid} onSeedDemo={seedDemo} /> : <>
        <a className="skip-link" href="#catalog-title">Saltar al contenido principal</a>
        <header className="topbar">
          <a className="brand" href="#catalog" aria-label="Yapa, inicio"><img className="brand-logo-mark" src="/images/brand/yapa-mark.png" alt="" width="512" height="512" fetchPriority="high" /><span>yapa</span></a>
          <nav className="main-nav" aria-label="Navegación principal"><a className={`nav-link ${customerView === 'store' ? 'is-active' : ''}`} href="#catalog" onClick={(event) => { event.preventDefault(); goToStore('catalog'); }}>Comprar</a><a className={`nav-link ${customerView === 'store' && window.location.hash === '#how-it-works' ? 'is-active' : ''}`} href="#how-it-works" onClick={(event) => { event.preventDefault(); goToStore('how-it-works'); }}>Cómo funciona</a><button className={`nav-link ${customerView === 'orders' ? 'is-active' : ''}`} type="button" onClick={openOrders}>Mis pedidos</button><button className={`nav-link ${customerView === 'cart' ? 'is-active' : ''}`} type="button" onClick={openCart}>Canasta</button></nav>
          <div className="topbar-actions"><button className="location-button" type="button" onClick={() => showInfo(accountZone ? `Tu zona: ${accountZone.name}. Entrega el sábado de ${windowLabel(accountZone.deliveryWindow)}.` : 'Zonas activas en Lince y Jesús María; La Victoria muy pronto.')}><Icon name="pin" size={16} /><span>{accountZone?.district ?? 'Lima'} · <strong>{accountZone?.name ?? 'Elige tu zona'}</strong></span><Icon name="chevron" size={15} /></button><button className="account-button" type="button" onClick={() => openAuth('user')}><Icon name="user" size={17} /><span>{account?.name || 'Ingresar'}</span></button></div>
        </header>

        {customerView === 'orders' ? <OrdersPage orders={myOrders} balance={balance} now={clock} onBack={() => goToStore('catalog')} onCancel={cancel} /> : customerView === 'cart' ? <CartPage lines={lines} subtotal={subtotal} delivery={quote.delivery} total={quote.total} onAdd={addProduct} onDecrease={decreaseProduct} onCheckout={openCheckout} onBack={() => goToStore('catalog')} /> : <main id="catalog" className="page-content">
          <section className="welcome-row hero-banner" aria-labelledby="page-title"><div className="welcome-copy"><h1 id="page-title">Compra mejor para tu semana</h1><p>Del mayorista a tu mesa, con precios que rinden y entrega en tu zona.</p><div className="hero-actions"><button className="primary-button" type="button" onClick={() => document.querySelector('#catalog-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>Ver catálogo <Icon name="arrow" size={17} /></button><a className="text-button" href="#how-it-works" onClick={(event) => { event.preventDefault(); goToStore('how-it-works'); }}>Cómo funciona</a></div></div><div className="hero-side"><div className="hero-illustration" role="img" aria-label="Agricultora peruana con una canasta de productos frescos"><span className="hero-note"><Icon name="pin" size={14} /> Del campo a tu canasta</span><img src="/images/brand/yapa-farmer-banner.png" alt="Agricultora con una canasta de arroz, tomates, plátanos y papas" width="760" height="694" fetchPriority="high" /></div></div></section>
          <section className="delivery-overview" aria-label="Entrega, cobertura y pago"><div className="delivery-facts"><div className="delivery-fact delivery-fact--primary"><span className="delivery-fact-icon"><Icon name="truck" size={20} /></span><div><small>Ciclo {currentCycle} · próxima entrega</small><strong>Sábado</strong><span>{cycleOpen ? 'Pedidos hasta el miércoles a las 20:00' : 'Cerrado para pedidos: vuelve el lunes'}</span></div></div><div className="delivery-fact"><span className="delivery-fact-icon"><Icon name="pin" size={19} /></span><div><small>Cobertura actual</small><strong>Lince, Jesús María y La Victoria</strong><span>La ventana la asigna Yapa a cada zona</span></div></div><div className="delivery-fact"><span className="delivery-fact-icon"><Icon name="wallet" size={19} /></span><div><small>Pago por adelantado</small><strong>Yape o Plin</strong><span>Lo que ahorremos te vuelve como saldo</span></div></div></div></section>

          <div className="workspace-grid"><Catalog products={visibleProducts} cart={cart} category={category} query={query} onCategoryChange={setCategory} onQueryChange={setQuery} onAdd={addProduct} onClearFilters={clearFilters} /><CartPanel lines={lines} cart={cart} subtotal={subtotal} delivery={quote.delivery} total={quote.total} onAdd={addProduct} onDecrease={decreaseProduct} onCheckout={openCheckout} onFocusCatalog={() => document.querySelector('#catalog-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' })} /></div>
          <HowItWorksSection />
        </main>}

        <footer className="site-footer"><span>Yapa · compras que rinden</span><div className="footer-actions"><button className="footer-link" type="button" onClick={openAdmin}>Panel admin</button><span>{persistenceMode === 'appwrite' ? 'Datos conectados · pagos simulados' : 'Modo local · pagos simulados'}</span></div></footer>
      </>}
      <div className="toast-region" aria-live="polite" aria-atomic="true">{toast ? <div className={`toast toast--${toast.tone} is-visible`}><Icon name={toast.tone === 'success' ? 'check' : 'box'} size={18} /><span>{toast.message}</span></div> : null}</div>
      {!showAdminView ? <><AuthDialog open={authOpen} currentAccount={account} initialAudience={authAudience} onClose={() => { setAuthOpen(false); setAuthReturnView(null); }} onSignedOut={() => { setAccount(null); setOrders([]); setCustomerView('store'); setAuthReturnView(null); }} onOpenAdmin={openAdmin} onAuthenticated={(nextAccount, audience) => { setAccount(nextAccount); setToast({ message: `Listo, ${nextAccount.name}. Tu cuenta de Yapa está preparada.`, tone: 'success' }); if (audience === 'admin' && isAdminAccount(nextAccount)) { setAdminOpen(true); window.history.pushState(null, '', `${window.location.pathname}${window.location.search}#admin`); } else if (authReturnView) { const nextView = authReturnView; setAuthOpen(false); setAuthReturnView(null); setCustomerView(nextView); window.history.pushState(null, '', `${window.location.pathname}${window.location.search}#${nextView}`); window.scrollTo({ top: 0, behavior: 'smooth' }); } }} />
        <CheckoutDialog open={checkoutOpen} subtotal={subtotal} delivery={quote.delivery} total={quote.total} balance={balance} cycleOpen={cycleOpen} confirmation={confirmation} initialSelection={initialSelection} onClose={closeCheckout} onSubmit={registerOrder} />
        </> : null}
    </div>
  );
}
