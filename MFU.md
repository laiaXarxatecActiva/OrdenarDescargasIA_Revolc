# MFU.md — Manual Para el Usuario (Ordenar Descargas)

## ¿Qué hace?

Vigila tu carpeta de descargas (`Descargas` o `Downloads`, la detecta el propio script) en tiempo real con `inotifywait`. Cuando un archivo termina de escribirse, lo clasifica por extensión y lo mueve a una subcarpeta dentro de esa misma carpeta:

`Audio`, `Video`, `PDFs`, `Documentos`, `Imagenes`, `Comprimidos`, `Instaladores` y `Otros` (todo lo que no encaja en las anteriores o no tiene extensión).

Nunca borra archivos, ni los ejecuta, ni cambia permisos. Tampoco sobrescribe nada.

## Archivos del proyecto

- **Script:** `sort-downloads.sh`
- **Log:** `organizar_descargas.log` (se guarda junto al script, nunca dentro de Descargas)
- **Carpeta:** `Ordenar_Descargas`

## Requisitos

```bash
sudo pacman -S --needed inotify-tools
```

Si `inotifywait` no está instalado, el script se para al arrancar y muestra un mensaje de error.

## Cómo arrancar

```bash
cd /Ordenar_Descargas
nohup setsid ./sort-downloads.sh >/dev/null 2>&1 &
sleep 2
pgrep -af "sort-downloads|inotifywait"
```

- `nohup setsid` hace que siga funcionando aunque cierres la terminal.
- Si todo va bien verás `bash ./sort-downloads.sh` (una o dos líneas, la segunda es un subproceso normal) y una línea de `inotifywait`.
- Solo puede haber **una instancia** a la vez: si lo lanzas por segunda vez, el script muestra «ya se está ejecutando» y sale.

## Cómo comprobar que funciona

```bash
tail -f organizar_descargas.log
```

Cada movimiento queda registrado así: `OK: informe.pdf -> PDFs/informe.pdf`.

Prueba rápida:

```bash
DL="$(xdg-user-dir DOWNLOAD)"
touch "$DL/prueba.txt"
sleep 3
ls "$DL/Documentos"
```

## Cómo detener

```bash
pkill -f sort-downloads.sh
sleep 1
pgrep -af "sort-downloads|inotifywait"   # no debería salir nada
```

Al pararse, el script cierra también su `inotifywait`, así que no quedan procesos huérfanos.

## Arranque automático al iniciar sesión (opcional)

Crea un servicio de usuario de systemd:

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/sort-downloads.service <<'EOF'
[Unit]
Description=Auto-sort Downloads folder

[Service]
ExecStart=/Ordenar_Descargas/sort-downloads.sh
Restart=on-failure

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now sort-downloads.service
```

Comandos útiles con el servicio:

```bash
systemctl --user status sort-downloads.service    # ver el estado
systemctl --user restart sort-downloads.service   # reiniciar tras editar el script
systemctl --user disable --now sort-downloads.service   # desactivarlo
```

Si usas el servicio, **no lo lances además a mano** (saldría «ya se está ejecutando»). Para pararlo usa `systemctl`, no `pkill`, porque `Restart=on-failure` y `pkill` pueden dar resultados confusos.

## Detalles importantes

- **Detección de archivos terminados:** reacciona a los eventos `close_write` (archivo terminado de escribir) y `moved_to` (por ejemplo, cuando el navegador renombra `.part` al nombre final). Además espera a que el tamaño y la fecha del archivo dejen de cambiar antes de moverlo.
- **Ignora descargas en curso:** `.crdownload`, `.part`, `.tmp` y `.download`, y también cualquier archivo oculto (nombre que empieza por punto).
- **Nombres repetidos:** si ya existe un archivo con ese nombre en el destino, crea `archivo_2.ext`, `archivo_3.ext`, etc.
- **Archivos que ya estaban:** al arrancar **sí** ordena lo que ya hay suelto en Descargas. Si no quieres esto, cambia `SORT_EXISTING=true` por `SORT_EXISTING=false` al principio del script.
- **Subcarpetas:** solo vigila los archivos directamente dentro de Descargas; no entra en carpetas ni las mueve.
- **Categorías nuevas:** se editan en el bloque `CATEGORIES` al principio del script.

## Si algo falla

| Síntoma                       | Qué mirar                                                                              |
| ----------------------------- | -------------------------------------------------------------------------------------- |
| No mueve nada                 | `pgrep -af sort-downloads` (¿está corriendo?) y `tail organizar_descargas.log`         |
| Dice «ya se está ejecutando»  | Ya hay una instancia viva; páralo con `pkill -f sort-downloads.sh` y vuelve a lanzarlo |
| Error de `inotifywait`        | `sudo pacman -S --needed inotify-tools`                                                |
| Un archivo se queda sin mover | Busca `AVISO` o `ERROR` en el log                                                      |

## Si editas el script

1. Haz una copia de seguridad: `cp sort-downloads.sh sort-downloads.sh.bak`
2. Edita y comprueba la sintaxis: `bash -n sort-downloads.sh && echo OK`
3. Reinicia: `pkill -f sort-downloads.sh` y vuelve a arrancarlo (o `systemctl --user restart sort-downloads.service` si usas el servicio).
