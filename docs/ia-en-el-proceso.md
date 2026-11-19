# IA en el proceso de desarrollo

Yapa usa IA en dos lugares: **dentro del producto** (lo que ve el usuario) y **en cómo lo construimos**. Esta página resume las dos, con evidencia que se puede revisar en el repositorio.

## 1. IA dentro del producto

| Módulo | Qué hace | Técnica | Costo | Dónde |
|---|---|---|---|---|
| Ruta del reparto | Ordena las paradas y las muestra en un mapa real | Vecino más cercano + 2-opt sobre las zonas (agrupamiento por edificio) | USD 0 (en el navegador) | `src/utils/deliveryRoute.ts`, `RoutePlanner.tsx` |
| Predicción de demanda | Estima lo que pedirá cada zona para cotizar con el mayorista antes del cierre | Regresión lineal por mínimos cuadrados sobre 8 semanas | USD 0 (biblioteca estándar) | `api/src/yapa_sdd/forecast.py`, iteración 68 |
| Asistente de compra | Responde estado del pedido, entrega, ahorro, precios y avance del grupo | Reglas sobre los datos del vecino; Groq solo para lo demás | USD 0 (nivel gratis, 10 preguntas con IA por vecino al día) | `assistant.py`, iteración 70 |
| Cotización del proveedor | Lee la foto o el mensaje del proveedor y llena su lista | Foto: Bedrock (Nova Pro) y Groq de respaldo; mensaje: Groq, con reglas sin IA si no responde | USD 0 (nivel gratis, 20 lecturas al día) | `quote_reader.py`, iteración 69 |
| Arma mi canasta | Propone una canasta a partir de lo que escribe el vecino | Groq (`openai/gpt-oss-120b`) con el catálogo como contexto | USD 0 (10 al día) | `ia.py`, iteración 60 |
| Ayuda para atención | Sugiere categoría y respuesta para reclamos e incidencias | Groq | USD 0 | `ia.py`, iteración 61 |
| Revisión de bolsas por foto | Dice qué productos del pedido se ven en la foto de la bolsa (o de la carga del proveedor) y cuántas piezas | Amazon Nova Pro en Bedrock (cuenta estudiantil) con la lista del pedido; Groq y YOLOv8 Small de 4 clases de respaldo | Créditos estudiantiles de AWS (~USD 0,002 por foto); 150 al día por cuenta | `bag_reader.py` y `bedrock.py` (iteraciones 77 y 78), `vision.py`, `docs/modelo-yolo/banco-18nov.md` |

Principios que seguimos para que la IA sea útil y barata:

- **Primero datos, después IA.** Las consultas frecuentes se responden con reglas sobre el motor; la IA queda para lo que no se puede prever.
- **La IA sugiere, el motor decide.** Ningún módulo de IA cambia precios, pedidos, pagos ni saldo: una persona revisa y confirma.
- **Contexto mínimo.** A la IA solo va lo necesario (por ejemplo, los datos de ese vecino y nunca los de otros) y con respuestas cortas.
- **Límites por día y respaldo.** Groq principal, GitHub Models de respaldo; si fallan, la pantalla sigue funcionando sin IA.
- **Probado sin internet.** Las pruebas usan un proveedor de IA falso (`api/tests/test_ia.py`), así que corren gratis en el CI.

## 2. IA en el proceso de desarrollo

Trabajamos con **Specification-Driven Development (SDD)** y un asistente de programación (Claude Code) como compañero de pair programming. Las instrucciones que sigue el asistente están versionadas en `api/CLAUDE.md`: leer las decisiones del equipo, no inventar reglas de negocio y respetar el orden de commits de cada iteración.

| Uso | Cómo | Evidencia en el repo |
|---|---|---|
| Especificar antes de programar | Cada iteración empieza con una spec: requisito, reglas con código de error, criterios con números y supuestos marcados "a validar por el equipo" | 70 specs en `api/docs/desarrollo/`, 161 commits `docs:` |
| Generar casos de prueba | Las pruebas de aceptación salen de los criterios de la spec y se escriben **antes** del código; se guarda la corrida en rojo | 82 commits `test:`, 79 archivos `*-rojo.txt` en `api/docs/evidencia/desarrollo/` |
| Implementar en pareja | El asistente propone el código mínimo que cumple la spec; el equipo revisa | 110 commits `feat:` |
| Revisión de código asistida | Revisión de seguridad y de correctitud antes de pasar a `main` | Iteraciones 50 y 51 (endurecimiento y cierre de huecos) |
| Documentación técnica | Trazabilidad regla → código → prueba en cada spec, registro y roadmap al día | `99-registro.md`, `00-roadmap.md`, 73 archivos `*-verde.txt` |
| Verificar en el navegador | El asistente levanta la demo, recorre cada rol y compara con capturas | Capturas en `docs/` y la guía `docs/guia-demo-video.md` |

Cifras al 16/11/2026: 430 commits, 70 iteraciones especificadas, 65 archivos de pruebas del motor y 37 de la web, con más de 760 pruebas del motor y más de 210 de la web en verde en cada push (GitHub Actions).

### Ciclo de una iteración con IA

1. `docs:` el asistente redacta la spec a partir del pedido del equipo; el equipo valida los supuestos nuevos.
2. `test:` el asistente escribe las pruebas desde los criterios y se guarda la evidencia en rojo.
3. `feat:` la implementación mínima hasta que todo pasa, sin debilitar pruebas.
4. `docs:` trazabilidad, registro y evidencia en verde; el CI despliega a AWS si todo pasa.

Ejemplo completo: la iteración 70 (`70-asistente-de-compra.md`) va de la spec a producción en cuatro commits, con la evidencia `70-motor-rojo.txt` y `70-motor-verde.txt`.
