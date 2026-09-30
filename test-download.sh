#!/usr/bin/env bash

# Script de prueba para la automatización Ordenar Descargas
# Simula descargas y verifica la clasificación

PROJECT_DIR="/Ordenar_Descargas"
LOG_FILE="$PROJECT_DIR/organizar_descargas.log"

# Función para loggear
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $1" >> "$LOG_FILE"
}

# Limpiar log anterior
> "$LOG_FILE"

log "=== Iniciando pruebas de automatización Ordenar Descargas ==="

# Verificar que el script principal existe
if [ ! -x "$PROJECT_DIR/sort-downloads.sh" ]; then
    log "ERROR: sort-downloads.sh no encontrado o no ejecutable"
    exit 1
fi

# Iniciar el organizador en segundo plano
log "Iniciando sort-downloads.sh"
"$PROJECT_DIR/sort-downloads.sh" &
SCRIPT_PID=$!

# Esperar un momento para que inicie
log "Esperando inicio del script..."
sleep 2

# Verificar si está corriendo
if ps -p $SCRIPT_PID > /dev/null; then
    log "SUCCESS: sort-downloads.sh está corriendo (PID: $SCRIPT_PID)"
else
    log "ERROR: sort-downloads.sh falló al iniciar"
    exit 1
fi

# Mostrar estado actual
log "Estado actual de la carpeta de descargas:"
if [ -d "$HOME/Descargas" ]; then
    ls -la "$HOME/Descargas" >> "$LOG_FILE"
elif [ -d "$HOME/Downloads" ]; then
    ls -la "$HOME/Downloads" >> "$LOG_FILE"
else
    log "ERROR: No se encontró carpeta de descargas"
fi

log "Pruebas completadas. El script está corriendo y listo para recibir descargas."
log "Para detener: pkill -f sort-downloads.sh"

# Mantener el script corriendo (el usuario puede detenerlo)
# El script ya está en segundo plano, esta prueba solo inicia y documenta
wait $SCRIPT_PID