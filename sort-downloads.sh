#!/usr/bin/env bash
#
# sort-downloads.sh
# Vigila la carpeta de Descargas y ordena los archivos nuevos en subcarpetas
# según su extensión, usando inotifywait (eventos en tiempo real).
# Nunca borra, ejecuta ni cambia permisos de archivos.
#
# Requiere: inotify-tools  ->  sudo pacman -S inotify-tools
#

set -u

# == CONFIGURACIÓN ==

# Carpeta a vigilar: la que indique el sistema (xdg), o Descargas / Downloads
DOWNLOAD_DIR="$(xdg-user-dir DOWNLOAD 2>/dev/null)"
if [ -z "$DOWNLOAD_DIR" ] || [ "$DOWNLOAD_DIR" = "$HOME" ]; then
  if [ -d "$HOME/Descargas" ]; then
    DOWNLOAD_DIR="$HOME/Descargas"
  else
    DOWNLOAD_DIR="$HOME/Downloads"
  fi
fi

# El log se guarda junto al script (fuera de Descargas)
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/organizar_descargas.log"

# true = al arrancar, ordena también lo que ya hay en Descargas
SORT_EXISTING=true

# Extensiones de descargas en curso: nunca se tocan
IGNORE_EXTENSIONS="crdownload part tmp download"

# Categoría -> extensiones (minúsculas, sin punto). Lo demás va a "Otros".
declare -A CATEGORIES=(
  ["Audio"]="mp3 wav flac aac ogg m4a wma opus"
  ["Video"]="mp4 mkv avi mov wmv flv webm m4v"
  ["PDFs"]="pdf"
  ["Documentos"]="odt doc docx txt rtf xls xlsx ppt pptx csv ods odp md"
  ["Imagenes"]="jpg jpeg png gif bmp svg webp tiff ico"
  ["Comprimidos"]="zip rar 7z tar gz xz bz2"
  ["Instaladores"]="appimage deb rpm sh run"
)
FALLBACK_CATEGORY="Otros"

# == EVITAR INSTANCIAS DUPLICADAS ==

LOCK_FILE="${XDG_RUNTIME_DIR:-/tmp}/sort-downloads.lock"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "sort-downloads.sh ya se está ejecutando. Saliendo." >&2
  exit 1
fi

# == DEPENDENCIAS ==

if ! command -v inotifywait >/dev/null 2>&1; then
  echo "Falta inotify-tools. Instálalo con: sudo pacman -S inotify-tools" >&2
  exit 1
fi

# == TABLAS DE BÚSQUEDA (extensión -> categoría / ignorar) ==

declare -A EXT_MAP=()
for cat in "${!CATEGORIES[@]}"; do
  for ext in ${CATEGORIES[$cat]}; do
    EXT_MAP["$ext"]="$cat"
  done
done

declare -A IGNORE_MAP=()
for ext in $IGNORE_EXTENSIONS; do
  IGNORE_MAP["$ext"]=1
done

# == FUNCIONES ==

log_event() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') | $*" >> "$LOG_FILE"
}

# Espera a que el tamaño y la fecha del archivo dejen de cambiar
wait_until_stable() {
  local path="$1" tries=0 max_tries=40
  local prev="" cur
  while [ "$tries" -lt "$max_tries" ]; do
    [ -f "$path" ] || return 1
    cur="$(stat -c '%s-%Y' "$path" 2>/dev/null)" || return 1
    if [ "$cur" = "$prev" ]; then
      return 0
    fi
    prev="$cur"
    tries=$((tries + 1))
    sleep 0.5
  done
  return 1
}

# Devuelve un nombre libre en el destino: archivo.txt, archivo_2.txt, archivo_3.txt...
generate_dest_name() {
  local dest_dir="$1" filename="$2"
  local base="${filename%.*}" ext=""
  if [[ "$filename" == *.* ]]; then
    ext=".${filename##*.}"
  else
    base="$filename"
  fi
  local name="$filename" counter=1
  while [ -e "${dest_dir}/${name}" ]; do
    counter=$((counter + 1))
    name="${base}_${counter}${ext}"
  done
  echo "$name"
}

process_file() {
  local path="$1"
  local name="${path##*/}"

  # Solo archivos normales, y nada oculto (los navegadores usan ocultos temporales)
  [[ "$name" == .* ]] && return
  [ -f "$path" ] || return
  [ -L "$path" ] && return

  local ext="" category="$FALLBACK_CATEGORY"
  if [[ "$name" == *.* ]]; then
    ext="${name##*.}"
    ext="${ext,,}"
  fi

  if [ -n "$ext" ]; then
    # Descarga en curso: no tocar
    [ -n "${IGNORE_MAP[$ext]:-}" ] && return
    category="${EXT_MAP[$ext]:-$FALLBACK_CATEGORY}"
  fi

  if ! wait_until_stable "$path"; then
    log_event "AVISO: '$name' no terminó de escribirse a tiempo, se omite"
    return
  fi

  local dest_dir="${DOWNLOAD_DIR}/${category}"
  mkdir -p "$dest_dir"

  local dest_name dest_path
  dest_name="$(generate_dest_name "$dest_dir" "$name")"
  dest_path="${dest_dir}/${dest_name}"

  # mv -n: nunca sobrescribe nada
  if mv -n -- "$path" "$dest_path" 2>/dev/null; then
    log_event "OK: $name -> ${category}/${dest_name}"
  else
    log_event "ERROR: no se pudo mover '$name' a ${category}/"
  fi
}

# == INICIO ==

mkdir -p "$DOWNLOAD_DIR"
for cat in "${!CATEGORIES[@]}" "$FALLBACK_CATEGORY"; do
  mkdir -p "${DOWNLOAD_DIR}/${cat}"
done

log_event "=== Iniciando organizador de descargas ==="
log_event "Vigilando: $DOWNLOAD_DIR"

# Arranca inotifywait como coproceso: si el script se para, se para con él.
# close_write = archivo terminado de escribir; moved_to = renombrado (p. ej. .part -> final)
# 9>&- evita que inotifywait herede el bloqueo de instancia única.
coproc INOTIFY {
  inotifywait -m -q -e close_write -e moved_to --format '%w%f' "$DOWNLOAD_DIR" 9>&-
}

cleanup() {
  kill "$INOTIFY_PID" 2>/dev/null
}
trap cleanup EXIT
trap 'exit 0' INT TERM

# Ordenar lo que ya estaba en Descargas (los eventos nuevos quedan en cola mientras tanto)
if [ "$SORT_EXISTING" = true ]; then
  for f in "$DOWNLOAD_DIR"/*; do
    [ -e "$f" ] && process_file "$f"
  done
fi

# == BUCLE PRINCIPAL ==
while IFS= read -r ARCHIVO <&"${INOTIFY[0]}"; do
  process_file "$ARCHIVO"
done

log_event "El observador de archivos se detuvo"