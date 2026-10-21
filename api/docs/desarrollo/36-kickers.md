# Iteración 36 · Menos etiquetas sobre los títulos

## Requisito

Como persona que usa Yapa, quiero llegar al título de cada pantalla sin etiquetas pequeñas que repiten lo que ya dice el título.

## Criterio

Se quitan las etiquetas que solo repiten el título o la sección ("Tu cuenta", "Tu saldo", "Caja", "Padrón", "Centro de operaciones", "Resumen de compra", etc.). Se mantienen las que dan un dato que el título no tiene: la semana ("Semana 2026-W40"), una regla ("Mínimo de 8 por grupo", "Plazo: hasta 30 días", "Vigencia: 14 días"), un paso ("Último paso") o una pregunta ("¿Algo faltó o llegó mal?"). La promesa "Nunca pagas más del precio que ves" se queda: es el mensaje de confianza de la portada.

## Resultado

Se quitaron 16 etiquetas; las demás se mantienen. Sin cambios de reglas ni de datos; se verifica en el navegador.

## Trazabilidad

| Cambio | Código |
|---|---|
| etiqueta opcional en `Card` y 16 etiquetas quitadas | `AdminPanel.tsx`, `CartPage.tsx`, `OrdersPage.tsx`, `ZonePage.tsx` |
