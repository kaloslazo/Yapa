import { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { PhotoProductReview, type ProductCount } from './PhotoProductReview';
import type { PhotoCandidate } from '../utils/photoMatches';
export interface StockTotal { id:string; nombre:string; unidad:string; unidades:number; cantidad:string; disponible:string }
type Stock = { productos:StockTotal[]; repetida?:boolean };
export function SupplierStock({cycle,candidates,onApply}:{cycle:string;candidates:PhotoCandidate[];onApply:(totals:StockTotal[])=>void}) {
 const [stock,setStock]=useState<Stock>({productos:[]});const [error,setError]=useState('');const apply=useRef(onApply);apply.current=onApply;
 useEffect(()=>{let live=true;api.get<Stock>(`/api/proveedor/stock?ciclo=${encodeURIComponent(cycle)}`).then(data=>{if(live){setStock(data);if(data.productos.length)apply.current(data.productos);}}).catch(()=>{if(live)setError('No pudimos recuperar el stock confirmado. No se ha sumado ninguna carga.');});return()=>{live=false;};},[cycle]);
 const confirm=async(file:File,rows:ProductCount[])=>{
  const form=new FormData();form.set('ciclo',cycle);form.set('foto_archivo',file);form.set('conteo',JSON.stringify(rows.map(p=>({id:p.codigo,unidades:p.cantidad,peso:p.peso}))));
  const result=await api.post<Stock>('/api/proveedor/stock/confirmar',form);setStock(result);setError('');onApply(result.productos);return true;
 };
 return <section className="supplier-stock"><h2>Stock confirmado para tu propuesta</h2><p>Acumula cargas revisadas del mismo producto. Para kg, ingresa el peso medido. El total vendible reemplaza la disponibilidad del borrador; el catálogo espera la aprobación del equipo.</p>
 {error?<p role="alert">{error}</p>:null}
 {stock.repetida?<p role="status">Esta foto ya estaba confirmada. No se sumó dos veces.</p>:null}
 {stock.productos.length?<ul className="supplier-stock-totals" aria-label="Stock acumulado">{stock.productos.map(p=><li key={p.id}><strong>{p.nombre}</strong><span>{p.unidades} unidades visibles · {p.cantidad} {p.unidad} confirmados · {p.disponible} {p.unidad} vendibles</span></li>)}</ul>:<p>Todavía no hay cargas confirmadas para esta semana.</p>}
 <PhotoProductReview candidates={candidates} requireWeight title="Añadir una carga al stock" label="Confirmar y acumular stock" onConfirm={confirm}/>
 </section>;
}
