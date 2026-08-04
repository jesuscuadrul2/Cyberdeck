'''#!/bin/bash

# ==========================================
# CYBERDECK NETWORK, DOCKER & CLOUD SWITCH MAESTRO
# ==========================================

# 🚩 Archivo bandera para forzar el modo servidor
OVERRIDE_FILE="/tmp/cyberdeck_force_server.lock"

# Configuración de Rclone
RCLONE_REMOTE="secret:"
RCLONE_MOUNT_POINT="/mnt/ssd/media/nube"

echo "Iniciando escaneo de ubicación y hardware..."

echo "Buscando salida a internet..."
INTENTOS=0
MAX_INTENTOS=10

until ping -c 1 8.8.8.8 &> /dev/null; do
  sleep 1
  ((INTENTOS++))
  if [ $INTENTOS -ge $MAX_INTENTOS ]; then
    echo "⚠️ Ping a Google fallido. Procediendo a evaluación local..."
    break
  fi
done

ROUTER_IP="192.168.1.254"

# 🛠️ Interfaz Ethernet real descubierta en NetworkManager
NET_PROFILE="Wired connection 1"

# Flota completa de tus servicios Docker
DOCKERS=(
  portainer flaresolverr heimdall jellyfin sonarr radarr bazarr prowlarr 
  qbittorrent requestrr immich_server immich_postgres immich_machine_learning 
  immich_redis nextcloud nextcloud_db homeassistant syncthing kiwix-server 
  lidarr calibre-web esphome lobechat pragmata_db pragmata_adminer 
  pragmata_calculator pragmata_bot pragmata_grafana pragmata_dashboard
)

# Leemos el método actual de forma limpia y tolerante a fallos
CURRENT_METHOD=$(nmcli -g ipv4.method connection show "$NET_PROFILE" 2>/dev/null || echo "unknown")

# Verificamos si hay un cable de red conectado físicamente al puerto
CABLE_STATE=$(cat /sys/class/net/eth0/carrier 2>/dev/null || echo "0")

# Función auxiliar: Evalúa si el contenedor existe realmente en el motor antes de actuar
safe_docker_action() {
    local action=$1
    shift
    for container in "$@"; do
        if docker ps -a --format '{{.Names}}' | grep -Eq "^${container}$"; then
            docker "$action" "$container" &> /dev/null
        fi
    done
}

# CONDICIÓN MAESTRA: Si hay cable físico (1) Y el router responde
if [ "$CABLE_STATE" == "1" ] && ping -c 1 -W 2 $ROUTER_IP &> /dev/null; then
    echo "🟢 [ESTADO: EN BASE] Cable RJ45 detectado y conectado a la red local."
    
    if [ "$CURRENT_METHOD" != "manual" ]; then
        echo "Cambiando a IP Fija y reiniciando red..."
        sudo nmcli connection modify "$NET_PROFILE" ipv4.method manual ipv4.addresses 192.168.1.200/24 ipv4.gateway 192.168.1.254 ipv4.dns "192.168.1.254,8.8.8.8"
        sudo nmcli connection up "$NET_PROFILE" &> /dev/null
    else
        echo "🛡️ La red ya tiene su IP estática. Sin parpadeos."
    fi
    
    echo "Despertando la flota de Dockers..."
    safe_docker_action start "${DOCKERS[@]}"

    echo "☁️ Conectando nube encriptada (Rclone)..."
    if ! mountpoint -q "$RCLONE_MOUNT_POINT"; then
        rclone mount "$RCLONE_REMOTE" "$RCLONE_MOUNT_POINT" --vfs-cache-mode writes --daemon
    else
        echo "🛡️ La nube ya está conectada."
    fi

    echo "✅ Cyberdeck operativo al 100%."

else
    if [ "$CABLE_STATE" == "0" ]; then
        echo "🟡 [ESTADO: NÓMADA] RJ45 desconectado (Operando por WiFi o sin red)."
    else
        echo "🟡 [ESTADO: NÓMADA] Cable conectado, pero en red externa."
    fi
    
    if [ "$CURRENT_METHOD" != "auto" ]; then
        echo "Liberando IP de eth0 y reiniciando red a DHCP..."
        sudo nmcli connection modify "$NET_PROFILE" ipv4.method auto
        sudo nmcli connection up "$NET_PROFILE" &> /dev/null
    else
        echo "🛡️ La red eth0 ya está libre (DHCP). Sin parpadeos."
    fi
    
    # 🛡️ PROTECCIÓN DE DOCKERS (OVERRIDE MANUAL)
    if [ -f "$OVERRIDE_FILE" ]; then
        echo "⚠️ [OVERRIDE MANUAL ACTIVADO] Bandera detectada. Manteniendo Dockers encendidos..."
        
        echo "☁️ Conectando nube encriptada (Rclone)..."
        if ! mountpoint -q "$RCLONE_MOUNT_POINT"; then
            rclone mount "$RCLONE_REMOTE" "$RCLONE_MOUNT_POINT" --vfs-cache-mode writes --daemon
        else
            echo "🛡️ La nube ya está conectada."
        fi
    else
        echo "Hibernando contenedores para ahorrar recursos..."
        safe_docker_action stop "${DOCKERS[@]}"
        
        echo "☁️ Desconectando nube para ahorrar recursos..."
        if mountpoint -q "$RCLONE_MOUNT_POINT"; then
            fusermount -uz "$RCLONE_MOUNT_POINT"
        fi
        
        echo "💤 Modo ahorro activado."
    fi
f
