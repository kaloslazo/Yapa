import { useEffect, useMemo, useState } from 'react';
import { deliveryWindows, windowLabel, zoneById, zones } from '../data/catalog';
import type { OrderRecord, Product } from '../types';
import { Icon } from './Icon';
import { statusLabel } from './OrdersPage';
import { formatMoney } from '../utils/format';
import { MIN_ORDERS_PER_GROUP, SUPPORTED_DISTRICTS, type CycleSettlement } from '../utils/domain';

interface AdminPanelProps {
  products: Product[];
  orders: OrderRecord[];
  adminName: string;
  currentCycle: string;
  cycleOpen: boolean;
  localMode: boolean;
  onClose: () => void;
  onProductUpdate: (id: string, patch: Partial<Pick<Product, 'price' | 'stock'>>) => void;
  onVerify: (order: OrderRecord) => Promise<void>;
  onSettle: (cycle: string) => Promise<CycleSettlement>;
  onRefundPaid: (order: OrderRecord) => Promise<void>;
  onSeedDemo: () => void;
}

type StockFilter = 'all' | 'low';

const groups = [...new Set(zones.filter((zone) => zone.active).map((zone) => zone.groupId))];

export function AdminPanel({ products, orders, adminName, currentCycle, cycleOpen, localMode, onClose, onProductUpdate, onVerify, onSettle, onRefundPaid, onSeedDemo }: AdminPanelProps) {
  const [catalogQuery, setCatalogQuery] = useState('');
  const [stockFilter, setStockFilter] = useState<StockFilter>('all');
  const cycles = useMemo(() => [...new Set([currentCycle, ...orders.map((order) => order.cycleId).filter(Boolean)])].sort().reverse(), [currentCycle, orders]);
  const [cycle, setCycle] = useState(currentCycle);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [settlement, setSettlement] = useState<CycleSettlement | null>(null);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, []);

  useEffect(() => {
    setConfirming(false);
    setSettlement(null);
  }, [cycle]);

  const lowStock = products.filter((product) => product.stock < 15).length;
  const cycleOrders = orders.filter((order) => order.cycleId === cycle);
  const pending = cycleOrders.filter((order) => order.status === 'REGISTRADO');
  const toVerify = pending.filter((order) => order.paymentStatus === 'POR_VERIFICAR');
  const received = cycleOrders.filter((order) => order.paymentStatus === 'VERIFICADO').reduce((sum, order) => sum + order.paidExternal, 0);
  const verifiedByGroup = (groupId: string) => pending.filter((order) => order.paymentStatus === 'VERIFICADO' && zoneById(order.zoneId)?.groupId === groupId).length;
  const groupsReady = groups.filter((groupId) => verifiedByGroup(groupId) >= MIN_ORDERS_PER_GROUP).length;
  const codeCount = new Map<string, number>();
  for (const order of orders) if (order.operationCode) codeCount.set(order.operationCode, (codeCount.get(order.operationCode) ?? 0) + 1);
  const refunds = orders.filter((order) => order.refundToMethod > 0 && !order.refundPaidAt);

  const visibleProducts = useMemo(() => {
    const normalizedQuery = catalogQuery.trim().toLowerCase();
    return products.filter((product) => {
      const matchesQuery = !normalizedQuery || `${product.name} ${product.category}`.toLowerCase().includes(normalizedQuery);
      const matchesStock = stockFilter === 'all' || product.stock < 15;
      return matchesQuery && matchesStock;
    });
  }, [catalogQuery, products, stockFilter]);

  const settle = async () => {
    setBusy(true);
    try {
      setSettlement(await onSettle(cycle));
      setConfirming(false);
    } finally {
      setBusy(false);
    }
  };

  const productName = (id: string) => products.find((product) => product.id === id)?.name ?? id;
  const productUnit = (id: string) => products.find((product) => product.id === id)?.unit ?? '';

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
            <a className="admin-nav-link" href="#admin-cycle"><Icon name="calendar" size={18} /><span>Ciclo</span><strong>{pending.length}</strong></a>
            <a className="admin-nav-link" href="#admin-refunds"><Icon name="wallet" size={18} /><span>Devoluciones</span><strong>{refunds.length}</strong></a>
            <a className="admin-nav-link" href="#admin-catalog"><Icon name="box" size={18} /><span>Catálogo</span><strong>{products.length}</strong></a>
          </nav>

          <div className="admin-sidebar-spacer" />
          <div className="admin-sidebar-note">
            <span className="admin-sidebar-label">Ciclo actual</span>
            <strong>{currentCycle}</strong>
            <span>{cycleOpen ? 'Recibe pedidos hasta el miércoles 20:00' : 'Cerrado para pedidos'}</span>
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
              <div><span className="admin-eyebrow">Operativa de esta semana</span><h2 id="admin-intro-title">{cycleOpen ? 'El ciclo recibe pedidos hasta el miércoles 20:00' : 'El ciclo ya no recibe pedidos'}</h2><p>Verifica los códigos de Yape y Plin y, después de la entrega, liquida el ciclo para devolver el ahorro.</p></div>
              <div className="admin-intro-note"><span className="admin-intro-icon"><Icon name="calendar" size={20} /></span><span><small>Ciclo</small><strong>{currentCycle}</strong></span></div>
            </section>

            <section className="admin-kpis" aria-label="Indicadores del ciclo">
              <div className="admin-kpi"><span className="admin-kpi-label">Pedidos del ciclo</span><strong>{pending.length}</strong><small>sin liquidar</small></div>
              <div className={`admin-kpi ${toVerify.length ? 'admin-kpi--attention' : ''}`}><span className="admin-kpi-label">Pagos por verificar</span><strong>{toVerify.length}</strong><small>{toVerify.length ? 'revisa los códigos' : 'todo verificado'}</small></div>
              <div className="admin-kpi"><span className="admin-kpi-label">Grupos con mínimo</span><strong>{groupsReady} de {groups.length}</strong><small>{MIN_ORDERS_PER_GROUP} pedidos verificados</small></div>
              <div className="admin-kpi"><span className="admin-kpi-label">Recibido por Yape y Plin</span><strong>{formatMoney(received)}</strong><small>pagos verificados</small></div>
            </section>

            <section className="admin-card admin-cycle-card" id="admin-cycle" aria-labelledby="admin-cycle-title">
              <div className="admin-card-heading">
                <div><span className="admin-eyebrow">Ciclo semanal</span><h2 id="admin-cycle-title">Pedidos y liquidación</h2><p>Solo cuentan los pagos verificados. Un grupo de zonas necesita {MIN_ORDERS_PER_GROUP} para que vaya el camión.</p></div>
                <div className="admin-cycle-tools">
                  {localMode ? <button className="secondary-button" type="button" onClick={onSeedDemo}>Cargar pedidos de demo</button> : null}
                  <label className="admin-filter"><span className="sr-only">Ciclo</span><select value={cycle} onChange={(event) => setCycle(event.target.value)}>{cycles.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
                </div>
              </div>

              <div className="admin-groups">{groups.map((groupId) => {
                const count = verifiedByGroup(groupId);
                const groupZones = zones.filter((zone) => zone.groupId === groupId);
                return <div className="admin-group" key={groupId}><div><strong>{groupZones.map((zone) => zone.name).join(' + ')}</strong><small>{groupZones[0].district} · {windowLabel(groupZones[0].deliveryWindow)}</small></div><div className="admin-group-count"><span className={count >= MIN_ORDERS_PER_GROUP ? 'is-ready' : ''}>{count} / {MIN_ORDERS_PER_GROUP}</span><div className="progress-track"><span style={{ width: `${Math.min(count / MIN_ORDERS_PER_GROUP, 1) * 100}%` }} /></div></div></div>;
              })}</div>

              {cycleOrders.length ? <div className="admin-table-wrap"><table className="admin-table admin-orders-table"><caption className="sr-only">Pedidos del ciclo {cycle}</caption><thead><tr><th scope="col">Pedido</th><th scope="col">Vecino</th><th scope="col">Zona</th><th scope="col">Pagó</th><th scope="col">Pago</th><th scope="col">Estado</th><th scope="col">Acción</th></tr></thead><tbody>{cycleOrders.map((order) => {
                const repeated = order.operationCode && (codeCount.get(order.operationCode) ?? 0) > 1;
                return <tr key={order.id}>
                  <td><strong className="admin-order-code">{order.orderCode}</strong></td>
                  <td>{order.customerName || order.userId.slice(0, 8)}</td>
                  <td>{zoneById(order.zoneId)?.name ?? order.district}</td>
                  <td><strong>{formatMoney(order.total)}</strong>{order.paidBalance ? <small className="admin-cell-note">{formatMoney(order.paidBalance)} con saldo</small> : null}</td>
                  <td>{order.paymentMethod === 'SALDO' ? 'Saldo' : `${order.paymentMethod === 'PLIN' ? 'Plin' : 'Yape'} ${order.operationCode}`}{repeated ? <small className="admin-cell-warning">Código repetido</small> : null}</td>
                  <td><span className={`admin-order-status admin-order-status--${order.status === 'REGISTRADO' ? order.paymentStatus.toLowerCase() : order.status.toLowerCase()}`}>{statusLabel(order)}</span>{order.status === 'LIQUIDADO' ? <small className="admin-cell-note">costó {formatMoney(order.finalTotal ?? 0)} · devuelto {formatMoney(order.refundToBalance)}</small> : null}</td>
                  <td>{order.status === 'REGISTRADO' && order.paymentStatus === 'POR_VERIFICAR' ? <button className="admin-row-button" type="button" onClick={() => void onVerify(order)}>Verificar</button> : <span className="admin-muted">—</span>}</td>
                </tr>;
              })}</tbody></table></div> : <div className="admin-orders-empty"><span className="admin-empty-icon"><Icon name="truck" size={23} /></span><div><strong>Este ciclo todavía no tiene pedidos</strong><p>Cuando los vecinos paguen con Yape o Plin, aparecerán aquí para verificar el código.</p></div></div>}

              <div className="admin-settle">
                {settlement ? <div className="admin-settle-result">
                  <strong>Ciclo {cycle} liquidado</strong>
                  <p>Volvió a saldo {formatMoney(settlement.totalToBalance)} · a reembolsar por Yape o Plin {formatMoney(settlement.totalToMethod)}.</p>
                  {settlement.products.length ? <ul>{settlement.products.map((item) => <li key={item.productId}>{productName(item.productId)}: {item.totalQuantity} {productUnit(item.productId)} entre todos · {item.tierFrom ? `tramo desde ${item.tierFrom}` : 'sin tramo'} · {formatMoney(item.finalPrice)}</li>)}</ul> : null}
                </div> : pending.length ? <>
                  <p>{cycleOpen && cycle === currentCycle ? 'El ciclo sigue abierto. Liquida después de la entrega del sábado.' : 'Liquidar calcula el precio final por tramo, el envío real por zona y devuelve el ahorro como saldo.'}</p>
                  {confirming ? <div className="admin-settle-actions"><button className="primary-button" type="button" disabled={busy} onClick={() => void settle()}>{busy ? 'Liquidando…' : `Confirmar: liquidar ${pending.length} pedidos`}</button><button className="secondary-button" type="button" onClick={() => setConfirming(false)}>Cancelar</button></div> : <button className="primary-button" type="button" onClick={() => setConfirming(true)}>Liquidar ciclo {cycle} <Icon name="arrow" size={17} /></button>}
                </> : <p>No quedan pedidos por liquidar en este ciclo.</p>}
              </div>
            </section>

            <section className="admin-card" id="admin-refunds" aria-labelledby="admin-refunds-title">
              <div className="admin-card-heading"><div><span className="admin-eyebrow">Devoluciones</span><h2 id="admin-refunds-title">Por devolver a Yape o Plin</h2><p>Zonas que no llegaron al mínimo y cancelaciones con devolución al medio de pago. Plazo: hasta 30 días.</p></div><span className="admin-order-count">{refunds.length} pendientes</span></div>
              {refunds.length ? <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th scope="col">Pedido</th><th scope="col">Vecino</th><th scope="col">Motivo</th><th scope="col">Monto</th><th scope="col">Acción</th></tr></thead><tbody>{refunds.map((order) => <tr key={order.id}><td><strong className="admin-order-code">{order.orderCode}</strong></td><td>{order.customerName || order.userId.slice(0, 8)}</td><td>{order.status === 'NO_ATENDIDO' ? 'Zona sin mínimo' : 'Cancelación'}</td><td><strong>{formatMoney(order.refundToMethod)}</strong> a {order.paymentMethod === 'PLIN' ? 'Plin' : 'Yape'}</td><td><button className="admin-row-button" type="button" onClick={() => void onRefundPaid(order)}>Marcar devuelto</button></td></tr>)}</tbody></table></div> : <p className="admin-muted">No hay devoluciones pendientes.</p>}
            </section>

            <section className="admin-layout-grid" aria-label="Gestión de catálogo y operación">
              <div className="admin-card admin-catalog-card" id="admin-catalog">
                <div className="admin-card-heading"><div><span className="admin-eyebrow">Inventario</span><h2>Catálogo</h2><p>Precio máximo y lo que el proveedor puede vender este ciclo.</p></div><span className="admin-save-note"><span className="admin-save-dot" />Guardado automático</span></div>
                <div className="admin-toolbar"><label className="admin-search"><Icon name="search" size={17} /><span className="sr-only">Buscar en el catálogo</span><input type="search" value={catalogQuery} onChange={(event) => setCatalogQuery(event.target.value)} placeholder="Buscar producto" autoComplete="off" /></label><label className="admin-filter"><span className="sr-only">Filtrar inventario</span><select value={stockFilter} onChange={(event) => setStockFilter(event.target.value as StockFilter)}><option value="all">Todos los productos</option><option value="low">Solo stock bajo</option></select></label></div>
                <div className="admin-table-wrap">
                  <table className="admin-table">
                    <caption className="sr-only">Catálogo editable de Yapa</caption>
                    <thead><tr><th scope="col">Producto</th><th scope="col">Precio máximo</th><th scope="col">Tramos</th><th scope="col">Stock</th><th scope="col">Estado</th></tr></thead>
                    <tbody>
                      {visibleProducts.map((product) => {
                        const isLowStock = product.stock < 15;
                        return <tr key={product.id}><td><div className="admin-product-cell"><span className={`admin-product-art product-visual--${product.art}`}><img src={product.image} alt="" width="720" height="720" /></span><span><strong>{product.name}</strong><small>por {product.unit}</small></span></div></td><td><label className="admin-inline-field"><span className="sr-only">Precio de {product.name}</span><span>S/</span><input type="number" min="0" step="0.1" value={product.price} onChange={(event) => onProductUpdate(product.id, { price: Number(event.target.value) })} inputMode="decimal" /></label></td><td><small className="admin-tiers">{product.tiers.slice(1).map((tier) => `${tier.from}+ ${formatMoney(tier.price)}`).join(' · ') || '—'}</small></td><td><label className="admin-inline-field"><span className="sr-only">Stock de {product.name}</span><input type="number" min="0" step="1" value={product.stock} onChange={(event) => onProductUpdate(product.id, { stock: Number(event.target.value) })} inputMode="numeric" /></label></td><td><span className={`admin-stock-status ${isLowStock ? 'is-low' : 'is-ok'}`}><i aria-hidden="true" />{isLowStock ? 'Reponer' : 'Disponible'}</span></td></tr>;
                      })}
                    </tbody>
                  </table>
                  {!visibleProducts.length ? <div className="admin-table-empty"><Icon name="search" size={21} /><strong>No encontramos productos</strong><span>Prueba con otra búsqueda o cambia el filtro.</span></div> : null}
                </div>
              </div>

              <aside className="admin-side-stack">
                <section className="admin-card admin-operation-card"><div className="admin-card-heading"><div><span className="admin-eyebrow">Despacho</span><h2>Ventanas por zona</h2></div><Icon name="truck" size={21} /></div><div className="admin-operation-day"><strong>Sábado</strong><span>Yapa asigna la ventana; recibe la portería</span></div><div className="admin-window-list">{deliveryWindows.map((window) => <div key={window.code}><span>{window.label}</span><small>{zones.filter((zone) => zone.active && zone.deliveryWindow === window.code).map((zone) => zone.name).join(', ') || 'sin zonas'}</small></div>)}</div></section>
                <section className="admin-card admin-coverage-card"><span className="admin-eyebrow">Cobertura piloto</span><h2>Distritos activos</h2><div className="admin-district-list">{SUPPORTED_DISTRICTS.map((district) => <span key={district}><Icon name="pin" size={14} />{district}</span>)}</div><p>Parada de S/ 40 por zona, repartida entre sus pedidos con tope de S/ 5.</p></section>
              </aside>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
