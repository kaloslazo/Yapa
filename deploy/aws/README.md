# Yapa en AWS (Lightsail)

Reemplaza a la VPS con runner propio (`deploy/vps/`, iteración 52). Todo es simulado: Yapa es un proyecto académico y no cobra dinero real (S-305).

## Qué se arma y cuánto cuesta

| Pieza | Qué es | Costo al mes |
|---|---|---|
| Servidor | Lightsail `nano_3_0`: Ubuntu 24.04, 512 MB, 2 vCPU, 20 GB SSD, 1 TB de tráfico | USD 5 |
| IP fija | IP estática de Lightsail, incluida mientras esté conectada al servidor | USD 0 |
| HTTPS | Caddy con certificado gratis de Let's Encrypt, que se renueva solo | USD 0 |
| Base y fotos | SQLite y la carpeta `fotos/` en el disco del servidor, con respaldo en cada despliegue | USD 0 |
| Pruebas y build | GitHub Actions (como hoy) | USD 0 |
| **Total** | | **≈ USD 5: USD 100 alcanzan para unos 20 meses** |

Por qué así y no otra cosa:

- El motor usa unos 25 MB de RAM (medido) y solo la biblioteca estándar de Python. Atiende con un cerrojo y guarda todo en SQLite (iteraciones 11 y 44), así que una sola máquina chica basta. No hace falta un balanceador, una base de datos administrada ni contenedores.
- Lightsail cobra precio fijo con la IPv4 incluida. En EC2, la misma máquina (`t4g.micro`) más la IPv4 pública y el disco cuestan unos USD 10 al mes.
- La web se construye en GitHub, así que el servidor no necesita Node.

```
GitHub (push a main) ─ pruebas motor y web ─ paquete ─ scp/ssh ─► Lightsail
                                                                   ├─ Caddy :443 (holayapa.app) ─► motor 127.0.0.1:8000
                                                                   └─ /opt/yapa/data: yapa.db y fotos (no se tocan al desplegar)
```

## Armarlo (una sola vez)

1. **Credenciales de la cuenta estudiantil** en un perfil aparte:
   `aws configure --profile utec` (con AWS Academy, pega también el `aws_session_token`).
2. **Crear el servidor:** `AWS_PROFILE=utec deploy/aws/crear.sh`. Genera la llave `~/.ssh/yapa-aws` en tu máquina e importa la parte pública, porque la cuenta estudiantil no deja que AWS la cree. Después crea la máquina en Ohio (`us-east-2`, la única región que permite la cuenta), la IP fija y abre los puertos 22, 80 y 443. Al final imprime la IP.
3. **DNS:** en la zona de Route 53 de `holayapa.app`, crea o cambia los registros `A` de `holayapa.app` y `www.holayapa.app` para que apunten a esa IP. Caddy pide el certificado apenas el dominio apunta al servidor.
4. **Claves del servidor:** entra con `ssh -i ~/.ssh/yapa-aws ubuntu@<IP>` y escribe `/etc/yapa/yapa.env` con `sudo nano /etc/yapa/yapa.env`:
   ```
   YAPA_ADMIN_USUARIO=admin-yapa
   YAPA_ADMIN_CLAVE=<mínimo 10 caracteres>
   YAPA_DEBUG_CLAVE=<mínimo 10 caracteres>
   YAPA_DEMO_PINS=101=482915,105=739104,116=260318
   YAPA_PUBLIC_URL=https://holayapa.app
   ```
   Opcionales: SMTP para los correos, Google para entrar con Google, `YAPA_PLIN_NUMERO` / `YAPA_PLIN_TITULAR` (sin ellos, cuenta simulada) y la IA: `YAPA_GROQ_CLAVE` (gratis en console.groq.com) y, de respaldo, `YAPA_GITHUB_MODELS_CLAVE` (un token de GitHub con permiso de lectura de Models). Después de cambiar el archivo: `sudo systemctl restart yapa`.
5. **Conectar GitHub:**
   ```
   gh secret set AWS_HOST --body <IP>
   gh secret set AWS_SSH_KEY < ~/.ssh/yapa-aws
   ```
6. **Primer despliegue:** sube algo a `main` o vuelve a correr el último flujo. El trabajo **desplegar en AWS** sube el paquete y corre `desplegar.sh`.

## Cómo funciona cada despliegue

`desplegar.sh` (mismo contrato que la VPS):

1. Descomprime la versión en `/opt/yapa/releases/<commit>` y revisa que esté completa.
2. Respalda la base con `sqlite3 .backup` en `/opt/yapa/backups`, donde quedan los 14 últimos respaldos.
3. Cambia `/opt/yapa/current` a la versión nueva y reinicia el servicio `yapa`.
4. Si `/salud` no responde en 40 s, vuelve a la versión anterior y el trabajo falla.

Cada despliegue deja una línea en `/opt/yapa/despliegues.log`. Sin el secreto `AWS_HOST`, el trabajo solo avisa y no falla.

## Comandos útiles en el servidor

```
sudo systemctl status yapa        # estado del motor
sudo journalctl -u yapa -n 50     # últimos mensajes
sudo systemctl restart yapa       # reiniciar
tail /opt/yapa/despliegues.log    # historial de despliegues
```

El servicio y Caddy arrancan solos si la máquina se reinicia, a diferencia del runner de la VPS. Para borrar todo y dejar de gastar: `aws lightsail --region us-east-2 delete-instance --instance-name yapa` y `aws lightsail --region us-east-2 release-static-ip --static-ip-name yapa-ip`.
