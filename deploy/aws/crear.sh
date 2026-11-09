#!/bin/bash
# Crea el servidor de Yapa en AWS Lightsail (una sola vez). Uso:
#   AWS_PROFILE=utec deploy/aws/crear.sh
# Lightsail "nano" con IPv4 (512 MB, 2 vCPU, 20 GB SSD, 1 TB de tráfico): unos USD 5 al mes con la IP fija incluida,
# así USD 100 de crédito alcanzan para más de un año y medio. El motor de Yapa usa ~60 MB de RAM y SQLite.
set -euo pipefail

REGION="${REGION:-us-east-2}"  # la cuenta estudiantil de UTEC solo permite Ohio
ZONA_AWS="${ZONA_AWS:-${REGION}a}"
NOMBRE="${NOMBRE:-yapa}"
PLAN="${PLAN:-nano_3_0}"
LLAVE="${LLAVE:-$HOME/.ssh/yapa-aws}"
DOMINIO="${DOMINIO:-holayapa.app}"
AQUI="$(cd "$(dirname "$0")" && pwd)"
aws_ls() { aws lightsail --region "$REGION" "$@"; }

# la cuenta estudiantil no deja que AWS cree la llave: se genera aquí y se importa solo la parte pública (sin comentario)
[ -f "$LLAVE" ] || ssh-keygen -t rsa -b 4096 -N "" -C "$NOMBRE-aws" -f "$LLAVE" -q
aws_ls get-key-pair --key-pair-name "$NOMBRE-llave" >/dev/null 2>&1 || \
  aws_ls import-key-pair --key-pair-name "$NOMBRE-llave" --public-key-base64 "$(awk '{print $1" "$2}' "$LLAVE.pub")" >/dev/null

aws_ls create-instances --instance-names "$NOMBRE" --availability-zone "$ZONA_AWS" --blueprint-id ubuntu_24_04 \
  --bundle-id "$PLAN" --key-pair-name "$NOMBRE-llave" --tags key=proyecto,value=yapa >/dev/null
echo "creando $NOMBRE..."
until [ "$(aws_ls get-instance-state --instance-name "$NOMBRE" --query state.name --output text)" = running ]; do sleep 5; done

aws_ls allocate-static-ip --static-ip-name "$NOMBRE-ip" >/dev/null
aws_ls attach-static-ip --static-ip-name "$NOMBRE-ip" --instance-name "$NOMBRE" >/dev/null
aws_ls put-instance-public-ports --instance-name "$NOMBRE" --port-infos \
  fromPort=22,toPort=22,protocol=tcp fromPort=80,toPort=80,protocol=tcp fromPort=443,toPort=443,protocol=tcp >/dev/null
IP="$(aws_ls get-static-ip --static-ip-name "$NOMBRE-ip" --query staticIp.ipAddress --output text)"

# Lightsail antepone su propio script al user-data y lo corre con sh: servidor.sh se corre por SSH, con bash
until ssh -i "$LLAVE" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 "ubuntu@$IP" true 2>/dev/null; do sleep 5; done
scp -i "$LLAVE" "$AQUI/servidor.sh" "ubuntu@$IP:/tmp/servidor.sh"
ssh -i "$LLAVE" "ubuntu@$IP" "sudo DOMINIO=$DOMINIO bash /tmp/servidor.sh"

echo "Servidor listo en $IP. Siguiente paso (README):"
echo "  1. Apunta el registro A de $DOMINIO (y www) a $IP en Route 53."
echo "  2. gh secret set AWS_HOST --body $IP && gh secret set AWS_SSH_KEY < $LLAVE"
echo "  3. Escribe las claves en /etc/yapa/yapa.env del servidor y sube a main."
