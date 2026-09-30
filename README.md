# README - Ordenar Descargas

## Descripción
Proyecto para ordenar automáticamente los archivos de la carpeta de Descargas/Downloads según su extensión. Hay **dos formas** de tenerlo funcionando, y están documentadas por separado:

| | Automatización 1: Script Bash | Automatización 2: OpenClaw (IA) |
|---|---|---|
| **Qué es** | `sort-downloads.sh`, un script independiente | Automatización creada y gestionada con OpenClaw |
| **Cómo funciona** | Vigila la carpeta en tiempo real con `inotifywait` | Se ejecuta periódicamente (cada 10 min) desde OpenClaw Gateway |
| **Depende de OpenClaw** | No | Sí |
| **Estado** | **Principal** | Alternativa / complementaria |

> El script Bash es el núcleo del proyecto. La automatización de OpenClaw es una capa opcional por encima que lo lanza y lo mantiene activo.

---

# Automatización 1: Script Bash (`sort-downloads.sh`)

## Características
- **Clasificación por extensión** en 8 categorías: Audio, Video, PDFs, Documentos, Imagenes, Comprimidos, Instaladores, Otros
- **Tiempo real**: usa `inotifywait` (eventos `close_write` y `moved_to`) en vez de revisar la carpeta cada cierto tiempo
- **Detección de descargas en curso**: ignora `.crdownload`, `.part`, `.tmp`, `.download`
- **Ignora archivos ocultos y enlaces simbólicos** (los navegadores usan ocultos temporales)
- **Verificación de estabilidad**: espera a que el tamaño y la fecha del archivo dejen de cambiar (hasta ~20 s)
- **Manejo de duplicados**: añade `_2`, `_3`, etc. si ya existe un archivo con el mismo nombre
- **Ordena lo existente al arrancar** (configurable con `SORT_EXISTING`)
- **Instancia única**: usa un bloqueo (`flock`) para evitar que se ejecuten dos copias a la vez
- **Detección automática de la carpeta**: usa `xdg-user-dir DOWNLOAD`, o `~/Descargas` / `~/Downloads`
- **Logging**: registra movimientos, avisos y errores en `organizar_descargas.log` (junto al script)
- **Sin destrucción**: nunca borra, ejecuta ni cambia permisos; el movimiento usa `mv -n`, que jamás sobrescribe

## Instalación

### Requisitos
- Arch Linux (u otro sistema con inotify-tools)
- `inotifywait` (parte de inotify-tools)
- Bash 4+ (usa arrays asociativos y `coproc`)

### Instalación en Arch Linux
```bash
sudo pacman -S inotify-tools
```

### Clonar el Proyecto
```bash
cd /Ordenar_Descargas
# El código está ya aquí
```

## Uso

### Ejecutar manualmente (para pruebas)
```bash
cd /Ordenar_Descargas
./sort-downloads.sh
```

### Ejecutar en segundo plano
```bash
cd /Ordenar_Descargas
./sort-downloads.sh &
```

### Detener el script
```bash
pkill -f sort-downloads.sh
```

### Ver el log en tiempo real
```bash
tail -f /Ordenar_Descargas/organizar_descargas.log
```

## Configuración
Todo se cambia en la sección `CONFIGURACIÓN` de `/Ordenar_Descargas/sort-downloads.sh`:

- **`CATEGORIES`**: array asociativo categoría → extensiones (minúsculas, sin punto). Añade o quita extensiones aquí.
- **`IGNORE_EXTENSIONS`**: extensiones de descargas en curso que nunca se tocan.
- **`FALLBACK_CATEGORY`**: carpeta para lo que no encaja en ninguna categoría (por defecto `Otros`).
- **`SORT_EXISTING`**: `true` para ordenar también lo que ya hay en Descargas al arrancar.
- **`DOWNLOAD_DIR`**: se detecta solo; edítalo si quieres forzar otra carpeta.

## Cómo funciona

### Arquitectura
- `inotifywait` se lanza como **coproceso**: si el script se detiene, el observador se detiene con él.
- **Eventos que vigila**: `close_write` (archivo terminado de escribir) y `moved_to` (renombrado, p. ej. `.part` → nombre final).
- **Bucle principal**: lee cada ruta que emite `inotifywait` y la procesa (`process_file`).
- **Al inicio**: crea todas las carpetas de categoría y, si `SORT_EXISTING=true`, ordena lo que ya había (los eventos nuevos quedan en cola mientras tanto).

### Reglas de seguridad
- Nunca ejecuta archivos
- Nunca cambia permisos
- Nunca borra archivos ni carpetas
- Nunca sobrescribe (`mv -n` + nombres únicos para duplicados)
- Solo toca archivos dentro de la carpeta de descargas y sus subcarpetas
- Se ejecuta como usuario normal (sin sudo)

## Arranque automático (opcional, sin OpenClaw)
El script por sí solo no se inicia al encender el equipo. Si no vas a usar la Automatización 2, puedes arrancarlo con un servicio de usuario de systemd, por ejemplo `~/.config/systemd/user/sort-downloads.service`:

```ini
[Unit]
Description=Ordenar Descargas

[Service]
ExecStart=/Ordenar_Descargas/sort-downloads.sh
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now sort-downloads.service
```

---

# Automatización 2: OpenClaw (con IA)

Esta automatización está creada con OpenClaw y se encarga de **lanzar `sort-downloads.sh` y mantenerlo activo**. No sustituye al script: la lógica de clasificación sigue estando en el `.sh`. Gracias a ella el proceso arranca al encender el equipo mediante OpenClaw Gateway.

> Es opcional. Si el script ya lo arrancas por otra vía (a mano o con systemd), no la necesitas.

## Estado y control

### Ver el estado
```bash
openclaw automations list --all
```

### En OpenClaw Gateway
- **Estado actual**: Ejecutándose (si está activo)
- **Ejecución periódica**: cada 10 minutos
- **Log**: `organizar_descargas.log` (el mismo que usa el script)
- **Salida**: `sort-downloads.out` / `sort-downloads.err` (si la automatización lanza el script)

### Pausar / Reanudar
- Desactivar la automatización en `openclaw automations list --all`
- Activarla de nuevo cuando se desee reanudar

### Editar / Reiniciar
```bash
openclaw automations list --all    # Obtener ID
openclaw automations update <id>   # Editar configuración
```

### Cambiar el intervalo de ejecución
Editar la automatización en OpenClaw y actualizar el `schedule` (`everyMs`). Por defecto son 10 minutos.

> Como el script tiene protección contra instancias duplicadas, si OpenClaw lo relanza mientras ya está corriendo, la segunda copia sale sin hacer nada.

---

# Común a ambas

## Estructura de directorios
```
/Ordenar_Descargas/
├── sort-downloads.sh           # Script principal (Automatización 1)
├── organizar_descargas.log     # Log de movimientos y errores
├── sort-downloads.out          # Salida del script (si lo lanza OpenClaw)
├── sort-downloads.err          # Errores del script (si lo lanza OpenClaw)
├── README.md                   # Este archivo
├── SPEC.md                     # Especificación técnica
├── OrdenarDescargas.md         # Ficha de diseño humana
└── agents/
    └── AGENTS.md               # Contexto del agente (Automatización 2)
```

## Pruebas de Aceptación
Ejecute las pruebas manualmente (sirven para ambas automatizaciones):

### 1. Normal (Imagen)
```bash
# Descargar una imagen
# Esperar a que aparezca en ~/Descargas/Imagenes/
# Verificar con: ls ~/Descargas/Imagenes/
```

### 2. PDF
```bash
# Descargar un PDF
# Debe aparecer en ~/Descargas/PDFs/
# No en ~/Descargas/Documentos/
```

### 3. Sin extensión
```bash
# Descargar un archivo sin extensión
# Debe aparecer en ~/Descargas/Otros/
```

### 4. Duplicados
```bash
# Descargar el mismo archivo 2-3 veces
# Debe generar: archivo, archivo_2, archivo_3...
```

### 5. Descarga en curso
```bash
# Iniciar descarga -> aparecerá .crdownload/.part/.tmp
# Debe ser ignorado hasta que finalice
```

### 6. Error al mover
```bash
# Simular error (permisos, disco lleno, etc.)
# Debe quedar en Descargas y registrar error en el log
```

### 7. Persistencia entre sesiones
```bash
# Reiniciar equipo o contenedor
# El proceso debe arrancar automáticamente (OpenClaw o systemd)
# No reprocesar archivos ya movidos
```

## Mantenimiento

### Verificar estado
```bash
# 1. Verificar si el proceso está corriendo
ps aux | grep sort-downloads.sh | grep -v grep

# 2. Verificar log reciente
tail -10 /Ordenar_Descargas/organizar_descargas.log

# 3. Verificar carpeta de descargas
ls -la ~/Descargas/
```

### Reiniciar manualmente
```bash
pkill -f sort-downloads.sh
cd /Ordenar_Descargas
./sort-downloads.sh &
```

### Diagnosticar problemas
- **Script no inicia**: verificar permisos de ejecución, dependencias y sintaxis
- **No detecta descargas**: verificar que `inotifywait` está instalado y que la carpeta de descargas es la correcta
- **Errores en el log**: revisar `organizar_descargas.log`
- **No hay actividad**: esperar a que se complete una descarga o ejecutar una prueba manual

## Problemas conocidos y soluciones

### 1. `inotifywait` no está instalado
```bash
sudo pacman -S inotify-tools
```

### 2. La carpeta de descargas no es ~/Descargas ni ~/Downloads
El script usa `xdg-user-dir DOWNLOAD`; si no da la carpeta correcta, editar `DOWNLOAD_DIR` en el script.

### 3. El script se cierra inesperadamente
Revisar el log y, si lo lanza OpenClaw, `sort-downloads.err`.

### 4. "sort-downloads.sh ya se está ejecutando"
Es normal: el bloqueo de instancia única impide dos copias a la vez.
