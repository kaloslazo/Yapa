# 05 · Antecedentes: por qué fracasaron y qué reglas le dejan a Yapa

Investigación web del 23/09/2026. Se contrastó con lo que dice `Proyecto/Idea_inicial.pdf`. Lo que no se pudo confirmar con una fuente está marcado **no verificado**.

## Patrón común

Todos cerraron o se retiraron. Las causas que más se repiten son cinco:

- se acabó el capital;
- subsidios;
- expansión prematura a otros países;
- inventario o tiendas propias;
- unit economics negativos.

La prensa casi siempre lo resume como "no levantaron más capital". Pero eso es **cómo** murieron, no **por qué**: el porqué es que cada pedido perdía plata. La Idea inicial ya lo decía así.

## Casos

| Caso | Años | Modelo | Causa documentada | Fuente |
|---|---|---|---|---|
| **Favo** (Perú) | 2019 – 29/02/2024 | Compra grupal con líderes comunitarios con comisión. Serie A de US$ 26.5M (Tiger Global). | Salió de Brasil en jun-2022 por alza de tasas y flujo de caja. En Perú la presionaron los supermercados, Rappi y PedidosYa. Una causa unitaria publicada (recompra o CAC) está **no verificada**. | [Gestión 26/02/2024](https://gestion.pe/economia/empresas/startup-peruana-favo-cierra-operacion-que-paso-con-este-supermercado-online-empresas-startup-innovacion-comercio-electronico-tecnologia-noticia/) |
| **Freshmart** (Perú) | 2016–2024 | Supermercado 100 % online. Jüsto lo compró en oct-2021. En 2022 abrió una tienda física y dark store en Miraflores. | Cierre en nov-2024 por reestructuración de Jüsto, que se enfocó en México. | [Gestión 26/11/2024](https://gestion.pe/economia/empresas/freshmart-dice-adios-el-motivo-del-cierre-y-los-planes-que-tenia-en-peru-empresas-supermercado-online-justo-noticia/) |
| **Muni** (CO/MX/BR) | 2019 – 25/11/2022 | Líderes comunitarios que vendían por catálogo a sus vecinos. Unos US$ 27–30M. | Lo admite su fundadora: unit economics nunca sostenibles, costo de recaptar clientes, logística compleja, ticket bajo con CAC en alza y entrada a México y Brasil "sin estar lista". No cerró su Serie B. | [Bloomberg Línea](https://www.bloomberglinea.com/2022/11/24/startup-colombiana-cierra-ante-la-imposibilidad-de-levantar-mas-capital/) · [Startupeable](https://startupeable.com/muni/) |
| **Facily** (Brasil) | 2018– | Compra grupal por WhatsApp con puntos de recojo (5 % de comisión). Unicornio en 2021. | Despidió al 30 % del personal en abr-2022. La cifra de "perdió ~90 % del volumen" de la Idea inicial está **no verificada**. | [Startups.com.br](https://startups.com.br/negocios/brazilian-e-commerce-firm-facily-slashes-workforce-by-30/) |
| **Merqueo** (Colombia) | ~2017–2025 | E-grocery con **dark stores e inventario propio**. | Reorganización en 2023 con pasivos de COP 25.2 mil millones. Fracasaron la venta a Falabella y el financiamiento. Cierre en jul-2025. | [Infobae 11/07/2025](https://www.infobae.com/colombia/2025/07/11/fracasa-la-expansion-de-merqueo-la-empresa-cierra-definitivamente/) |
| **Frubana** (CO/MX/BR) | 2018–2025 | B2B de frutas y verduras para restaurantes. Unos US$ 271M. | Salió de Colombia y México en feb-2024 (tasas, inflación, falta de recursos) y cerró Brasil en 2025. | [Bloomberg Línea](https://www.bloomberglinea.com/2024/02/18/las-razones-por-las-que-la-startup-colombiana-frubana-cerrara-en-colombia-y-mexico/) · [Forbes CO](https://forbes.co/2025/08/14/negocios/frubana-pone-fin-a-sus-operaciones/) |
| **Missfresh** (China) | 2014–2022 | Delivery en minutos desde **almacenes propios**. Más de US$ 2 mil millones. | Colapsó en jul-2022 con cientos de proveedores impagos. Nasdaq la deslistó en 2023. | [SCMP](https://www.scmp.com/tech/big-tech/article/3187012/delivery-firm-missfresh-collapses-another-nasdaq-listed-chinese-firm) |
| **Meituan Youxuan** (China) | 2020–2025 | Pedido hoy y recojo mañana donde un líder de barrio. | En dic-2020 los reguladores prohibieron vender bajo costo, y **al cortar el subsidio el volumen cayó en picada**. Cerró casi todo el país en jun-2025. | [KrASIA](https://kr-asia.com/after-the-cash-burn-what-remains-of-chinas-community-group-buying-boom) |
| **Jokr** (Perú) | –2023 | Quick commerce. | Vendió su unidad de Perú a InRetail a inicios de 2023. | [LatinFinance](https://latinfinance.com/daily-brief/2023/02/13/jokr-exits-mexico-after-peru-sale/) |

## Lecciones convertidas en reglas candidatas para Yapa

Cada una se enlaza con una decisión de `04_decisiones_pendientes.md`.

| # | Regla candidata | Respaldo | Decisión |
|---|---|---|---|
| L1 | Si al cierre no se alcanza el **umbral de activación** por zona o punto, no se compra y se devuelve todo. | Muni (ticket bajo); Meituan (el volumen sin subsidio no alcanza) | D-02 |
| L2 | **Cero subsidio**: precio ≥ costo mayorista + merma + reparto. El envío gratis solo se permite si el cálculo lo cubre. | Meituan, Muni, Favo | D-17, D-23 |
| L3 | **Sin inventario ni dark store**: se compra solo lo pedido y cerrado. | Merqueo, Missfresh, Freshmart | D-21 |
| L4 | **No abrir otra zona** hasta que las tres actuales cubran costos. | Muni, Favo (Brasil), Frubana | nueva (P1) |
| L5 | **Recompra en la semana 4** como métrica principal del piloto. | Muni (costo de recaptar) | D-25 |
| L6 | **Tope de CAC** ≤ margen de las primeras 3–4 compras. | Muni | D-25 |
| L7 | **Cobrar como máximo lo mostrado**; el delivery se informa y se acepta antes; no se redondea hacia arriba. | Ley 29571, arts. 4.1, 4.2 y 44 | **D-03**, D-07 |
| L8 | **Cobrar antes de comprar**: las transferencias se verifican antes de ir al mayorista; no se financia al cliente. | Merqueo, Favo (flujo de caja) | **D-14** |
| L9 | **Tope a la contraentrega** y bloqueo tras un pedido no recibido. | Facily (no bancarizados); la tasa de rechazo está **no verificada** | D-15 |
| L10 | **Merma presupuestada** dentro del precio; el faltante se reembolsa el mismo sábado. | Meituan (perecibles) | D-16, D-18 |
| L11 | **Puntos o líderes sin sueldo fijo** (si se usan). | Favo, Facily, Muni | D-01 |
| L12 | **Cada ciclo debe cerrar con margen positivo**, sin depender de levantar capital. | Favo, Muni, Merqueo, Frubana | D-17 |

## Datos legales (Perú), verificados

- **Ley 29571, art. 4.2:** *"Los consumidores no pueden ser obligados al pago de sumas o recargos adicionales al precio fijado"*. La excepción son servicios como el transporte, siempre que se informen antes y el consumidor los acepte expresamente. La carga de la prueba es del proveedor.
  - Esto choca directamente con **RN-21**, que cobra un saldo en la puerta, y con **RN-22**, que retiene el pedido si el cliente no paga ese saldo.
  - [Texto de la ley](https://www.digesa.minsa.gob.pe/NormasLegales/Normas/Ley_29571.pdf)
- **Art. 4.1:** el precio exhibido tiene que ser el total, con tributos y cargos incluidos. Por eso la IGV tiene que ir dentro del precio desde el diseño (H1.13).
- **Art. 44:** prohíbe redondear en perjuicio del consumidor (relacionado con D-07).
- **Libro de Reclamaciones virtual:** lo regula el D.S. 011-2011-PCM, modificado por el D.S. 101-2022-PCM (plazo de respuesta de 15 días hábiles). La **Ley 32495 (11/11/2025)** lo hace obligatorio para plataformas de comercio electrónico, con un enlace visible en todo momento. Para Yapa esto ya no es opcional (H1.14).
  - [Nota PRCP](https://www.prcp.com.pe/blog/client-memo-plataformas-digitales-de-comercio-electronico-se-encuentran-obligadas-a-contar-con-un-libro-de-reclamaciones) · [El Peruano](https://busquedas.elperuano.pe/dispositivo/NL/2095978-1)

## Horario del mayorista y efecto en el ciclo

- **Santa Anita (GMML):** la actividad fuerte es de madrugada; "a la una de la madrugada ya es tarde" ([Wikipedia](https://es.wikipedia.org/wiki/Gran_Mercado_Mayorista_de_Lima)). El horario oficial exacto está **no verificado**; se puede confirmar con EMMSA al (01) 518-2800.
- **Caquetá (frutas):** directorios indican 5:00–20:00 (fuente secundaria).
- **Efecto:** la compra se hace en la madrugada del jueves (o del viernes). RN-11, que verifica transferencias hasta el jueves 12:00, deja comprar sin saber quién pagó. Por eso **D-14 es P0**.

## Correcciones a la Idea inicial

- Freshmart: la compra de Jüsto fue en **oct-2021** (la Idea también lo dice así, correcto). El cierre no fue por "rechazo al modelo digital" como causa única: la fuente atribuye el cierre a la **reestructuración de la matriz**. Hay que matizarlo en la exposición.
- Facily: "perdió ~90 % del volumen" → **no verificado**. No hay que citarlo como dato duro.
