// para demos se puede fijar la hora con VITE_YAPA_AHORA, por ejemplo 2026-10-19T10:00:00-05:00
const fixed = import.meta.env.VITE_YAPA_AHORA;

export function now(): Date {
  return fixed ? new Date(fixed) : new Date();
}
