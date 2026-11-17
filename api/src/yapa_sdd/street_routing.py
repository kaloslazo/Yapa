"""Trazado OSRM bajo petición; no decide entregas ni modifica el orden propuesto."""
import json,math,os,threading,time,urllib.request
from collections import OrderedDict
from urllib.parse import urlsplit
from .domain import BusinessRuleError

_cache=OrderedDict();_lock=threading.Lock();_last_attempt=0.0
def clear_cache():
    global _last_attempt
    with _lock:_cache.clear();_last_attempt=0.0

def fetch_route(url):
    request=urllib.request.Request(url,headers={'User-Agent':'Yapa-academico/1.0','Accept':'application/json'})
    with urllib.request.urlopen(request,timeout=7) as response:
        raw=response.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError('respuesta demasiado grande')
    return json.loads(raw)

def _coordinate(point):
    return isinstance(point,(list,tuple)) and len(point)==2 and all(type(x) in (int,float) and math.isfinite(x) for x in point) and abs(point[0])<=180 and abs(point[1])<=90

def street_route(points):
    global _last_attempt
    if not isinstance(points,(list,tuple)) or not 2<=len(points)<=25 or not all(_coordinate(p) for p in points):
        raise BusinessRuleError('INVALID_ROUTE','Elige entre 2 y 25 paradas con coordenadas válidas.')
    base=os.environ.get('YAPA_ROUTING_URL','https://router.project-osrm.org').rstrip('/')
    if urlsplit(base).scheme not in ('https','http') or not urlsplit(base).netloc:
        raise BusinessRuleError('ROUTE_UNAVAILABLE','El servicio de rutas no está configurado correctamente.')
    key=(base,tuple(tuple(p) for p in points));now=time.monotonic()
    if not _lock.acquire(blocking=False):raise BusinessRuleError('ROUTE_BUSY','Hay una ruta en cálculo. Intenta de nuevo en unos segundos.')
    try:
        cached=_cache.get(key)
        if cached and now-cached[0]<600:return cached[1]
        if now-_last_attempt<1:raise BusinessRuleError('ROUTE_BUSY','Espera un segundo antes de calcular otra ruta.')
        _last_attempt=now
        coordinates=';'.join(f'{lon:.6f},{lat:.6f}' for lon,lat in points)
        try:
            data=fetch_route(f'{base}/route/v1/driving/{coordinates}?overview=full&geometries=geojson&steps=false')
            if data.get('code')!='Ok':raise ValueError('sin ruta')
            route=data['routes'][0];geometry=route['geometry']['coordinates']
            distance,duration=route['distance'],route['duration']
            if not isinstance(geometry,list) or not 2<=len(geometry)<=10000 or not all(_coordinate(p) for p in geometry):raise ValueError('geometría inválida')
            if not all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in [distance,duration]):raise ValueError('métricas inválidas')
            result={'distancia_m':distance,'duracion_s':duration,'coordenadas':geometry,'fuente':'OSRM','aviso':'Recorrido por calles del orden elegido; tiempo estimado sin tráfico en tiempo real.'}
        except Exception as error:
            raise BusinessRuleError('ROUTE_UNAVAILABLE','No pudimos trazar por calles. Conservamos el orden y los enlaces de navegación; reintenta después.') from error
        _cache[key]=(now,result);_cache.move_to_end(key)
        while len(_cache)>64:_cache.popitem(last=False)
        return result
    finally:_lock.release()
