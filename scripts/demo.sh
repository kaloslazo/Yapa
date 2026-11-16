#!/usr/bin/env bash
# Levanta la demo completa en local: el motor con la semana de prueba y un reloj que se mueve, y la tienda.
# Uso: scripts/demo.sh            (motor en 8010, tienda en 5173)
#      MOTOR=8020 WEB=5180 scripts/demo.sh
# Luego, en otra terminal: scripts/semana.sh miercoles  (o jueves, viernes, sabado, domingo, siguiente, todo)
set -euo pipefail
cd "$(dirname "$0")/.."

MOTOR="${MOTOR:-8010}"
WEB="${WEB:-5173}"

libre() {  # el motor y Vite reutilizan la dirección, así que un puerto recién cerrado cuenta como libre
  python3 -c "import socket,sys; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('127.0.0.1', int(sys.argv[1])))" "$1" 2>/dev/null
}
for puerto in "$MOTOR" "$WEB"; do
  if ! libre "$puerto"; then
    echo "El puerto $puerto está ocupado. Ciérralo o elige otro: MOTOR=8020 WEB=5180 scripts/demo.sh"
    exit 1
  fi
done

[ -d node_modules ] || npm install

# claves locales (por ejemplo YAPA_GROQ_CLAVE) desde .env, que git ignora
if [ -f .env ]; then set -a; . ./.env; set +a; fi

# con api/.venv (torch y ultralytics, api/requirements-vision.txt) el detector de productos también funciona
PY=python3
[ -x api/.venv/bin/python ] && PY=api/.venv/bin/python
"$PY" api/tools/demo_semana.py --puerto "$MOTOR" &
motor=$!
trap 'kill "$motor" 2>/dev/null' EXIT
sleep 1

cat <<FIN

  Tienda:  http://localhost:$WEB
  Reloj:   http://localhost:$WEB/api/demo/reloj
  Pasos:   YAPA_API=http://127.0.0.1:$MOTOR scripts/semana.sh miercoles   (jueves, viernes, sabado, domingo, siguiente o todo)

  Vecinos en /entrar:  101 (Ana, admin de Los Álamos) PIN 482915 · 105 (Carmen) PIN 739104
  Equipo en /equipo:   admin-yapa / yapa-admin-2026 · compras-demo / compras-yapa-2026 · armado-demo / armado-yapa-2026
                       atencion-demo / atencion-yapa-2026 · porteria-demo / porteria-yapa-2026
                       reparto-demo / reparto-yapa-2026 · frescos-demo / frescos-yapa-2026 (proveedor)
  Todo vive en memoria: Ctrl+C y vuelve a correrlo para empezar de cero.
  Qué mostrar en cada módulo: docs/guia-demo-video.md

FIN

YAPA_API="http://127.0.0.1:$MOTOR" npx vite --port "$WEB" --strictPort
