#!/usr/bin/env bash
set -euo pipefail

# Instalador de IG Gateway en un VPS con Docker
# Uso: bash install.sh [--port PORT] [--poll-interval SECONDS]

PORT=80
POLL_INTERVAL="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"; shift 2;;
    --poll-interval)
      POLL_INTERVAL="$2"; shift 2;;
    *)
      echo "Argumento desconocido: $1"; exit 1;;
  esac
done

echo "[+] Puerto: $PORT"
echo "[+] POLL_INTERVAL: $POLL_INTERVAL s"

need_sudo() {
  if [ "$(id -u)" -ne 0 ]; then
    echo sudo
  else
    echo ""
  fi
}

SUDO="$(need_sudo)"

echo "[+] Instalando Docker si es necesario"
if ! command -v docker >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    $SUDO apt-get update -y
    $SUDO apt-get install -y ca-certificates curl gnupg lsb-release
    curl -fsSL https://get.docker.com | $SUDO sh
  elif command -v yum >/dev/null 2>&1; then
    $SUDO yum install -y curl
    curl -fsSL https://get.docker.com | $SUDO sh
  else
    echo "No se pudo instalar Docker automáticamente. Instálalo manualmente y reintenta."; exit 1
  fi
fi

echo "[+] Creando directorios persistentes"
$SUDO mkdir -p /opt/ig-gateway/data /opt/ig-gateway/sessions

echo "[+] Construyendo imagen"
docker build -t ig-gateway .

echo "[+] Deteniendo contenedor previo (si existe)"
if docker ps -a --format '{{.Names}}' | grep -q '^ig-gateway$'; then
  $SUDO docker rm -f ig-gateway || true
fi

echo "[+] Ejecutando contenedor"
$SUDO docker run -d --name ig-gateway \
  -p ${PORT}:8000 \
  -e POLL_INTERVAL="${POLL_INTERVAL}" \
  ig-gateway

echo "[+] Listo. Accede a: http://$(hostname -I | awk '{print $1}'):${PORT}/ui"
echo "    Salud: http://$(hostname -I | awk '{print $1}'):${PORT}/health"
echo "    Logs: docker logs -f ig-gateway"