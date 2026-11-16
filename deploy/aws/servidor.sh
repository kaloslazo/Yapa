#!/bin/bash
# Prepara el servidor de Yapa en AWS (Ubuntu 24.04). Corre una sola vez, como root, al crear la máquina (user-data).
# Deja: Python 3.12, Caddy con HTTPS automático, el usuario yapa, el servicio yapa y el script de despliegue.
set -euo pipefail

DOMINIO="${DOMINIO:-holayapa.app}"

# 512 MB de RAM: un poco de swap para que apt y Python no se queden sin memoria
if [ ! -f /swapfile ]; then
  fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q python3 sqlite3 curl debian-keyring debian-archive-keyring apt-transport-https gnupg unattended-upgrades
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
apt-get update -q && apt-get install -y -q caddy

# usuario sin login que corre el motor; la base y las fotos viven en /opt/yapa/data y no se tocan al desplegar
id yapa >/dev/null 2>&1 || useradd --system --home /opt/yapa --shell /usr/sbin/nologin yapa
mkdir -p /opt/yapa/releases /opt/yapa/data/fotos /opt/yapa/backups /opt/yapa/bin /etc/yapa
chown -R yapa:yapa /opt/yapa/data /opt/yapa/backups
[ -f /etc/yapa/yapa.env ] || install -m 600 /dev/null /etc/yapa/yapa.env  # las claves se escriben aparte (README)

cat > /etc/systemd/system/yapa.service <<'UNIT'
[Unit]
Description=Yapa (motor y web)
After=network-online.target

[Service]
User=yapa
WorkingDirectory=/opt/yapa/data
Environment=PYTHONPATH=/opt/yapa/current/api/src PYTHONUNBUFFERED=1
EnvironmentFile=/etc/yapa/yapa.env
ExecStart=/usr/bin/python3 -m yapa_sdd.web --base /opt/yapa/data/yapa.db --sembrar-demo --puerto 8000 --estaticos /opt/yapa/current/dist
Restart=always
RestartSec=3
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/opt/yapa/data
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT

# Caddy pide y renueva el certificado de Let's Encrypt solo; el motor escucha solo en 127.0.0.1
cat > /etc/caddy/Caddyfile <<CADDY
${DOMINIO}, www.${DOMINIO} {
	encode zstd gzip
	reverse_proxy 127.0.0.1:8000
}
CADDY

# detector de productos por foto (YOLO, iteración 63 de Aaron): torch CPU y ultralytics en un entorno aparte.
# Necesita el plan small_3_0 (2 GB): el modelo usa ~540 MB y en 512 MB tumbaría al motor.
if [ "${VISION:-1}" = 1 ]; then
  apt-get install -y -q python3-venv libgl1 libglib2.0-0t64
  [ -x /opt/yapa/venv/bin/python ] || python3 -m venv /opt/yapa/venv
  /opt/yapa/venv/bin/pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu
  /opt/yapa/venv/bin/pip install -q ultralytics==8.4.211  # igual que api/requirements-vision.txt
  mkdir -p /etc/systemd/system/yapa.service.d
  cat > /etc/systemd/system/yapa.service.d/vision.conf <<'UNIT'
# detector de productos (YOLO): el motor corre con el Python del entorno que tiene torch y ultralytics
[Service]
Environment=YOLO_CONFIG_DIR=/opt/yapa/data/.ultralytics MPLCONFIGDIR=/opt/yapa/data/.matplotlib YOLO_OFFLINE=1
ExecStart=
ExecStart=/opt/yapa/venv/bin/python -m yapa_sdd.web --base /opt/yapa/data/yapa.db --sembrar-demo --puerto 8000 --estaticos /opt/yapa/current/dist
UNIT
fi

systemctl daemon-reload
systemctl enable yapa caddy
systemctl restart caddy
echo "listo: falta el primer despliegue (deploy/aws/README.md)"
