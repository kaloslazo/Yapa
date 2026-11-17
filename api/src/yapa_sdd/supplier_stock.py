"""Stock confirmado por foto; independiente del catálogo publicado y de sus reservas."""
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
import hashlib
from . import partners, cycle
from .domain import BusinessRuleError

def _supplier(store, user):
    account=partners.active(store,user,partners.SUPPLIER)
    if not account:
        raise BusinessRuleError('NOT_AUTHORIZED','Solo el proveedor puede confirmar su stock.')
    return account.supplier_id

def snapshot(store,user,cycle_id):
    supplier=_supplier(store,user);cycle.check_cycle_id(cycle_id)
    groups={}
    for (owner,week,_),batch in store.supplier_stock_batches.items():
        if (owner,week)!=(supplier,cycle_id):continue
        for row in batch['filas']:
            total=groups.setdefault(row['id'],{'unidades':0,'cantidad':Decimal('0')})
            total['unidades']+=row['unidades'];total['cantidad']+=row['cantidad']
    products=[]
    for code,total in sorted(groups.items()):
        product=store.catalog_for(cycle_id).get(code)
        if product is None:continue
        available=(total['cantidad']/product.step).to_integral_value(rounding=ROUND_FLOOR)*product.step
        products.append({'id':code,'nombre':product.name,'unidad':product.unit,'unidades':total['unidades'],
                         'cantidad':format(total['cantidad'].normalize(),'f'),'disponible':format(available.normalize(),'f')})
    return {'ciclo':cycle_id,'productos':products}

def confirm(store,user,cycle_id,rows,upload,now):
    supplier=_supplier(store,user)
    if cycle_id != cycle.add_weeks(cycle.cycle_id(now),1):
        raise BusinessRuleError('INVALID_STOCK_CYCLE','Confirma stock para la próxima semana de tu propuesta.')
    if not upload or not upload[1]:raise BusinessRuleError('PHOTO_REQUIRED','Falta la foto de esta carga.')
    content=upload[1]
    if len(content)>8*1024*1024:raise BusinessRuleError('PHOTO_TOO_LARGE','La foto pesa más de 8 MB.')
    if not (content.startswith(b'\xff\xd8\xff') or content.startswith(b'\x89PNG\r\n\x1a\n') or (content.startswith(b'RIFF') and content[8:12]==b'WEBP')):
        raise BusinessRuleError('INVALID_PHOTO','Usa una foto JPG, PNG o WebP.')
    if not isinstance(rows,list) or not 1<=len(rows)<=30:
        raise BusinessRuleError('INVALID_STOCK_ITEM','Confirma entre 1 y 30 filas de productos.')
    clean=[]
    for row in rows:
        product=store.catalog_for(cycle_id).get(row.get('id')) if isinstance(row,dict) else None
        units=row.get('unidades') if isinstance(row,dict) else None
        if not product or product.supplier_id!=supplier or not product.active or type(units) is not int or not 1<=units<=300:
            raise BusinessRuleError('INVALID_STOCK_ITEM','Elige productos de tu lista y unidades enteras entre 1 y 300.')
        quantity=Decimal(units)
        if product.unit=='kg':
            try:quantity=Decimal(str(row.get('peso')))
            except InvalidOperation:quantity=Decimal('NaN')
            if not quantity.is_finite() or not 0<quantity<=100000:
                raise BusinessRuleError('WEIGHT_REQUIRED',f'Ingresa el peso medido en kg de {product.name}; la foto solo cuenta unidades.')
        clean.append({'id':product.product_id,'unidades':units,'cantidad':quantity})
    # Se valida toda la carga antes de escribir. El bloqueo de la API serializa esta operación.
    key=(supplier,cycle_id,hashlib.sha256(content).hexdigest())
    previous=store.supplier_stock_batches.get(key)
    repeated=previous is not None
    if previous is not None and previous['filas']!=clean:
        raise BusinessRuleError('STOCK_ALREADY_CONFIRMED','Esta foto ya fue confirmada con otro conteo; no se sumó de nuevo.')
    if not repeated:store.supplier_stock_batches[key]={'filas':clean,'por':user,'hora':now}
    return snapshot(store,user,cycle_id)|{'repetida':repeated}
