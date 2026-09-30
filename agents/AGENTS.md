# AGENTS.md — Ordenar Descargas (Automatización)

## Resumen del Proyecto
Automatización que vigila la carpeta de Descargas/Downloads del sistema y mueve cada archivo descargado a una subcarpeta según su extensión, usando inotifywait para eventos en tiempo real (sin polling).

## Ubicación del Proyecto
`Ordenar_Descargas`

## Archivos Principales
- `SPEC.md` — Especificación técnica completa (fuente de verdad)
- `OrdenarDescargas.md` — Ficha de diseño humana (referencia)
- `sort-downloads.sh` — Script bash determinista (versión sin IA)
- `organizar_descargas.log` — Registro de movimientos y errores
- `agents/AGENTS.md` — Este archivo (contexto para sesiones futuras)

## Comandos Clave

### Ejecutar script manualmente (para pruebas)
```bash
cd Ordenar_Descargas
./sort-downloads.sh
```

### Ver log en tiempo real
```bash
tail -f organizar_descargas.log
```

### Ver estado de la automatización (OpenClaw)
```bash
openclaw automations list --all
```

## Categorías y Extensiones
| Carpeta | Extensiones |
|---------|-------------|
| Audio | mp3, wav, flac, aac, ogg, m4a, wma, opus |
| Video | mp4, mkv, avi, mov, wmv, flv, webm, m4v |
| PDFs | pdf |
| Documentos | odt, doc, docx, txt, rtf, xls, xlsx, ppt, pptx, csv, ods, odp, md |
| Imagenes | jpg, jpeg, png, gif, bmp, svg, webp, tiff, ico |
| Comprimidos | zip, rar, 7z, tar, gz, xz, bz2 |
| Instaladores | appimage, deb, rpm, sh, run |
| Otros | Cualquier otra extensión o sin extensión |

## Extensiones Ignoradas (descargas en curso)
`.crdownload`, `.part`, `.tmp`, `.download`

## Reglas Críticas (NO VIOLAR)
1. **Nunca borrar** archivos o carpetas
2. **Nunca ejecutar** archivos (ni para inspeccionar)
3. **Nunca cambiar permisos** (chmod, icacls, etc.)
4. **Solo tocar** Descargas/ y sus subcarpetas
5. **Ejecutar como usuario normal** (sin root/sudo)
6. **Manejar duplicados** con sufijo `_2`, `_3`...
7. **Log fuera de Descargas** (en carpeta del proyecto)

## Estado Actual (2026-09-27)
- ✅ Script bash creado: `sort-downloads.sh`
- ✅ Carpetas de categorías ya existen en `~/Descargas/`
- ✅ Script hecho ejecutable
- ⏳ Automatización para inicio automático pendiente

## Pruebas de Aceptación (según SPEC.md)
1. Descargar imagen → aparece en `Imagenes`
2. Descargar PDF → aparece en `PDFs` (no en Documentos)
3. Descargar sin extensión → aparece en `Otros`
4. Descargar mismo archivo 2-3 veces → se conservan `_2`, `_3`...
5. Archivo `.crdownload`/`.part`/`.tmp` → no se toca hasta finalizar
6. Error al mover → archivo queda en Descargas, error en log
7. Reiniciar PC → proceso arranca solo, no reprocesa lo ya movido

## Arquitectura del Script
- **inotifywait** -bucle `while true` con eventos `create` y `moved_to`
- **Verificación de estabilidad** - espera tamaño estable + legibilidad
- **Clasificación** - por extensión (case-insensitive), orden de prioridad fijo
- **Manejo duplicados** - contador incremental `_N` antes de la extensión
- **Logging** - timestamp + archivo + destino + renombrado/error

## Dependencias del Sistema
- `inotifywait` (inotify-tools) — disponible en Arch Linux
- `bash`, `mv`, `mkdir`, `stat`, `grep`, `sleep` — estándar