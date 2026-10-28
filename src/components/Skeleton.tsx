// mientras llegan los datos: la forma de la página en gris suave, sin texto que salte
export function AdminSkeleton() {
  return (
    <div className="skeleton-page" aria-busy="true" aria-label="Cargando">
      <div className="skeleton-card skeleton-card--intro"><span className="skeleton skeleton-line skeleton-line--title" /><span className="skeleton skeleton-line skeleton-line--wide" /></div>
      <div className="skeleton-kpis">{[0, 1, 2, 3].map((i) => <div key={i} className="skeleton-card"><span className="skeleton skeleton-line skeleton-line--short" /><span className="skeleton skeleton-line skeleton-line--number" /></div>)}</div>
      <div className="skeleton-card">
        <span className="skeleton skeleton-line skeleton-line--title" />
        {[0, 1, 2, 3, 4].map((i) => <span key={i} className="skeleton skeleton-row" />)}
      </div>
    </div>
  );
}

export function PartnerSkeleton() {
  return (
    <div className="skeleton-page" aria-busy="true" aria-label="Cargando">
      <span className="skeleton skeleton-line skeleton-line--title" />
      <span className="skeleton skeleton-pill" />
      {[0, 1].map((i) => <div key={i} className="skeleton-card skeleton-card--tall"><span className="skeleton skeleton-line skeleton-line--title" /><span className="skeleton skeleton-row" /><span className="skeleton skeleton-row" /><span className="skeleton skeleton-line skeleton-line--short" /></div>)}
    </div>
  );
}
