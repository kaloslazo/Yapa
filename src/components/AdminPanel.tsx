import { useEffect, useMemo, useState } from 'react';
import { deliveryWindows } from '../data/catalog';
import type { OrderRecord, Product } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { SUPPORTED_DISTRICTS } from '../utils/domain';

interface AdminPanelProps {
  products: Product[];
  orders: OrderRecord[];
  adminName: string;
  onClose: () => void;
  onProductUpdate: (id: string, patch: Partial<Pick<Product, 'price' | 'stock'>>) => void;
}

type StockFilter = 'all' | 'low';

function formatOrderDate(value: string) {
  return new Intl.DateTimeFormat('es-PE', { day: '2-digit', month: 'short' }).format(new Date(value));
}

function windowLabel(code: string) {
  return deliveryWindows.find((window) => window.code === code)?.label || code;
}

export function AdminPanel({ products, orders, adminName, onClose, onProductUpdate }: AdminPanelProps) {
  const [catalogQuery, setCatalogQuery] = useState('');
  const [stockFilter, setStockFilter] = useState<StockFilter>('all');

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, []);

  const lowStock = products.filter((product) => product.stock < 15).length;
  const totalRevenue = orders.reduce((total, order) => total + order.total, 0);

  const visibleProducts = useMemo(() => {
    const normalizedQuery = catalogQuery.trim().toLowerCase();
    return products.filter((product) => {
      const matchesQuery = !normalizedQuery || `${product.name} ${product.category}`.toLowerCase().includes(normalizedQuery);
      const matchesStock = stockFilter === 'all' || product.stock < 15;
      return matchesQuery && matchesStock;
    });
  }, [catalogQuery, products, stockFilter]);

  return (
    <div className="admin-view">
      <a className="skip-link" href="#admin-overview">Saltar al contenido principal</a>
      <div className="admin-shell">
        <aside className="admin-sidebar" aria-label="Navegación de operaciones">
          <a className="admin-brand" href="#admin-overview" aria-label="Yapa, centro de operaciones">
            <img src="/images/brand/yapa-mark.png" alt="" width="512" height="512" />
            <span><strong>yapa</strong><small>operaciones</small></span>
          </a>

          <div className="admin-sidebar-label">Centro de control</div>
          <nav className="admin-nav" aria-label="Secciones del panel">
            <a className="admin-nav-link is-active" href="#admin-overview"><Icon name="box" size={18} weight="duotone" /><span>Resumen</span></a>
            <a className="admin-nav-link" href="#admin-catalog"><Icon name="box" size={18} /><span>Catálogo</span><strong>{products.length}</strong></a>
            <a className="admin-nav-link" href="#admin-orders"><Icon name="truck" size={18} /><span>Pedidos</span><strong>{orders.length}</strong></a>
          </nav>

          <div className="admin-sidebar-spacer" />
          <div className="admin-sidebar-note">
            <span className="admin-sidebar-label">Próxima salida</span>
            <strong>Sábado</strong>
            <span>3 ventanas · 3 distritos</span>
          </div>
          <a className="admin-back-link" href="#catalog" onClick={(event) => { event.preventDefault(); onClose(); }}><Icon name="arrow" size={16} className="admin-back-arrow" />Volver a la tienda</a>
          <div className="admin-sidebar-user"><span className="admin-avatar"><Icon name="user" size={17} /></span><span><small>Sesión activa</small><strong>{adminName || 'Administración'}</strong></span></div>
        </aside>

        <main className="admin-main" id="admin-overview">
          <header className="admin-topbar">
            <div><span className="admin-eyebrow">Centro de operaciones</span><h1>Resumen</h1></div>
            <div className="admin-top-actions"><a className="admin-store-link" href="#catalog" onClick={(event) => { event.preventDefault(); onClose(); }}>Tienda <Icon name="arrow" size={16} /></a></div>
          </header>

          <div className="admin-page-content">
            <section className="admin-intro" aria-labelledby="admin-intro-title">
              <div><span className="admin-eyebrow">Operativa de esta semana</span><h2 id="admin-intro-title">Todo listo para la próxima entrega</h2><p>Revisa el inventario y ten a la mano los pedidos que entran para el sábado.</p></div>
              <div className="admin-intro-note"><span className="admin-intro-icon"><Icon name="calendar" size={20} /></span><span><small>Próxima ventana</small><strong>Sábado · 09:00 – 12:00</strong></span></div>
            </section>

            <section className="admin-kpis" aria-label="Indicadores de Yapa">
              <div className="admin-kpi"><span className="admin-kpi-label">Catálogo activo</span><strong>{products.length}</strong><small>productos publicados</small></div>
              <div className={`admin-kpi ${lowStock ? 'admin-kpi--attention' : ''}`}><span className="admin-kpi-label">Reponer pronto</span><strong>{lowStock}</strong><small>{lowStock ? 'requieren una revisión' : 'sin alertas de stock'}</small></div>
              <div className="admin-kpi"><span className="admin-kpi-label">Pedidos registrados</span><strong>{orders.length}</strong><small>{orders.length ? 'en el historial' : 'aún no hay pedidos'}</small></div>
              <div className="admin-kpi"><span className="admin-kpi-label">Venta registrada</span><strong>{formatMoney(totalRevenue)}</strong><small>pagos simulados</small></div>
            </section>

            <section className="admin-layout-grid" aria-label="Gestión de catálogo y operación">
              <div className="admin-card admin-catalog-card" id="admin-catalog">
                <div className="admin-card-heading"><div><span className="admin-eyebrow">Inventario</span><h2>Catálogo</h2><p>Actualiza precio y stock desde una sola vista.</p></div><span className="admin-save-note"><span className="admin-save-dot" />Guardado automático</span></div>
                <div className="admin-toolbar"><label className="admin-search"><Icon name="search" size={17} /><span className="sr-only">Buscar en el catálogo</span><input type="search" value={catalogQuery} onChange={(event) => setCatalogQuery(event.target.value)} placeholder="Buscar producto" autoComplete="off" /></label><label className="admin-filter"><span className="sr-only">Filtrar inventario</span><select value={stockFilter} onChange={(event) => setStockFilter(event.target.value as StockFilter)}><option value="all">Todos los productos</option><option value="low">Solo stock bajo</option></select></label></div>
                <div className="admin-table-wrap">
                  <table className="admin-table">
                    <caption className="sr-only">Catálogo editable de Yapa</caption>
                    <thead><tr><th scope="col">Producto</th><th scope="col">Categoría</th><th scope="col">Precio</th><th scope="col">Stock</th><th scope="col">Estado</th></tr></thead>
                    <tbody>
                      {visibleProducts.map((product) => {
                        const isLowStock = product.stock < 15;
                        return <tr key={product.id}><td><div className="admin-product-cell"><span className={`admin-product-art product-visual--${product.art}`}><img src={product.image} alt="" width="720" height="720" /></span><span><strong>{product.name}</strong><small>por {product.unit}</small></span></div></td><td><span className="admin-category">{product.category}</span></td><td><label className="admin-inline-field"><span className="sr-only">Precio de {product.name}</span><span>S/</span><input type="number" min="0" step="0.1" value={product.price} onChange={(event) => onProductUpdate(product.id, { price: Number(event.target.value) })} inputMode="decimal" /></label></td><td><label className="admin-inline-field"><span className="sr-only">Stock de {product.name}</span><input type="number" min="0" step="1" value={product.stock} onChange={(event) => onProductUpdate(product.id, { stock: Number(event.target.value) })} inputMode="numeric" /></label></td><td><span className={`admin-stock-status ${isLowStock ? 'is-low' : 'is-ok'}`}><i aria-hidden="true" />{isLowStock ? 'Reponer' : 'Disponible'}</span></td></tr>;
                      })}
                    </tbody>
                  </table>
                  {!visibleProducts.length ? <div className="admin-table-empty"><Icon name="search" size={21} /><strong>No encontramos productos</strong><span>Prueba con otra búsqueda o cambia el filtro.</span></div> : null}
                </div>
              </div>

              <aside className="admin-side-stack">
                <section className="admin-card admin-operation-card"><div className="admin-card-heading"><div><span className="admin-eyebrow">Despacho</span><h2>Próxima salida</h2></div><Icon name="truck" size={21} /></div><div className="admin-operation-day"><strong>Sábado</strong><span>Entrega semanal</span></div><div className="admin-window-list">{deliveryWindows.map((window) => <div key={window.code}><span>{window.label}</span><small>{window.capacity}</small></div>)}</div></section>
                <section className="admin-card admin-coverage-card"><span className="admin-eyebrow">Cobertura piloto</span><h2>Distritos activos</h2><div className="admin-district-list">{SUPPORTED_DISTRICTS.map((district) => <span key={district}><Icon name="pin" size={14} />{district}</span>)}</div><p>La dirección final se valida al registrar cada pedido.</p></section>
              </aside>
            </section>

            <section className="admin-card admin-orders-card" id="admin-orders" aria-labelledby="admin-orders-title"><div className="admin-card-heading"><div><span className="admin-eyebrow">Seguimiento</span><h2 id="admin-orders-title">Pedidos recientes</h2><p>Consulta la información operativa de cada canasta.</p></div><span className="admin-order-count">{orders.length} {orders.length === 1 ? 'pedido' : 'pedidos'}</span></div>{orders.length ? <div className="admin-table-wrap"><table className="admin-table admin-orders-table"><caption className="sr-only">Pedidos recientes de Yapa</caption><thead><tr><th scope="col">Pedido</th><th scope="col">Entrega</th><th scope="col">Distrito</th><th scope="col">Estado</th><th scope="col">Total</th><th scope="col">Fecha</th></tr></thead><tbody>{orders.map((order) => <tr key={order.id || order.orderCode}><td><strong className="admin-order-code">{order.orderCode}</strong></td><td>{windowLabel(order.deliveryWindow)}</td><td>{order.district}</td><td><span className="admin-order-status">{order.status}</span></td><td><strong>{formatMoney(order.total)}</strong></td><td>{formatOrderDate(order.createdAt)}</td></tr>)}</tbody></table></div> : <div className="admin-orders-empty"><span className="admin-empty-icon"><Icon name="truck" size={23} /></span><div><strong>Los pedidos del sábado aparecerán aquí.</strong><p>Cuando alguien complete su compra, podrás revisar distrito, ventana y total desde esta sección.</p></div></div>}</section>
          </div>
        </main>
      </div>
    </div>
  );
}
