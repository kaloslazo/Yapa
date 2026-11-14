#!/usr/bin/env bash
# Hace un día de la semana de la demo (o la semana entera) contra el motor de scripts/demo.sh.
# Uso: scripts/semana.sh miercoles | jueves | viernes | sabado | domingo | siguiente | todo
# Si el motor no está en 8010: YAPA_API=http://127.0.0.1:8020 scripts/semana.sh todo
set -euo pipefail
cd "$(dirname "$0")/.."
python3 api/tools/semana_demo.py "${1:-}"
