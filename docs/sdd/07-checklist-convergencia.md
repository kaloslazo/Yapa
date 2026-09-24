# Checklist de convergencia · iteración 2

- [x] Las ambigüedades y decisiones se registraron antes del código (`10-clarificaciones-v2.md`, primer commit de la iteración).
- [x] Cada regla (RP-01..RP-15, LQ-01..LQ-09) tiene al menos un criterio y una prueba (`06-trazabilidad.md`).
- [x] Las pruebas verifican el **código de error** del contrato, no el texto del mensaje.
- [x] Hay casos de frontera: cierre a las 20:00:00, mínimo sin redondeo, último stock disponible, tope de envío.
- [x] Las pruebas se ejecutaron en rojo antes del código (`docs/evidencia/01`, `02`) y en verde al final (`03`).
- [x] Los cambios de spec durante la implementación entraron primero como `docs:` y `test:`.
- [x] El cliente no puede enviar el precio ni la zona; salen del sistema.
- [x] La demo es ejecutable por consola (`docs/evidencia/04-demo-consola.txt`).
- [x] Lo que está fuera de alcance está declarado con su motivo.
- [ ] Supuestos S-01..S-12 validados por Kalos y Aaron.
- [ ] Precios del mercado de barrio (competidor real en frescos) medidos en campo.
