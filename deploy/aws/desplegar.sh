#!/bin/bash
# Pone una versión nueva de Yapa en el servidor de AWS. Lo llama GitHub Actions por SSH después de que pasan las pruebas.
# Uso: sudo /opt/yapa/bin/desplegar.sh /tmp/yapa-<commit>.tar.gz <commit>
# Mismo contrato que el despliegue de la VPS (iteración 52): respalda la base, cambia la versión y, si /salud no
# responde en 40 s, vuelve a la anterior. La base y las fotos (/opt/yapa/data) nunca se tocan.
set -euo pipefail

PAQUETE="$1"
VERSION="${2:-manual-$(date +%s)}"
DESTINO="/opt/yapa/releases/$VERSION"
ACTUAL="$(readlink -f /opt/yapa/current || true)"
LOG=/opt/yapa/despliegues.log

rm -rf "$DESTINO" && mkdir -p "$DESTINO"
tar -xzf "$PAQUETE" -C "$DESTINO"
if [ ! -f "$DESTINO/dist/index.html" ] || [ ! -f "$DESTINO/api/src/yapa_sdd/web/__main__.py" ]; then
  echo "$(date -Is) $VERSION rechazado: paquete incompleto" >> "$LOG"; rm -rf "$DESTINO"; exit 1
fi

if [ -f /opt/yapa/data/yapa.db ]; then  # respaldo consistente aunque el motor esté escribiendo
  sqlite3 /opt/yapa/data/yapa.db ".backup /opt/yapa/backups/yapa-$(date +%Y%m%d-%H%M%S).db"
  ls -1t /opt/yapa/backups/*.db | tail -n +15 | xargs -r rm -f  # quedan los 14 últimos
fi

ln -sfn "$DESTINO" /opt/yapa/current
systemctl restart yapa
for _ in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8000/salud >/dev/null 2>&1; then
    echo "$(date -Is) $VERSION en línea" >> "$LOG"
    ls -1dt /opt/yapa/releases/* | tail -n +4 | xargs -r rm -rf  # quedan las 3 últimas versiones
    rm -f "$PAQUETE"
    exit 0
  fi
  sleep 2
done

echo "$(date -Is) $VERSION no respondió /salud: vuelve a la anterior" >> "$LOG"
if [ -n "$ACTUAL" ] && [ -d "$ACTUAL" ]; then ln -sfn "$ACTUAL" /opt/yapa/current && systemctl restart yapa; fi
exit 1
