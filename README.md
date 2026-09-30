# README - Ordenar Descargas (Automatización)

## Descripción
Automatización para ordenar automáticamente archivos en la carpeta de Descargas/Downloads según su extensión, usando inotifywait para eventos en tiempo real.

## Características
- **Clasificación por extensión** en 8 categorías: Audio, Video, PDFs, Documentos, Imágenes, Comprimidos, Instaladores, Otros
- **Detección de descargas en curso** (ignorando .crdownload, .part, .tmp, .download)
- **Verificación de estabilidad** - espera a que el archivo termine de escribirse
- **Manejo de duplicados** - añade `_2`, `_3`, etc. si existe archivo con mismo nombre
- **Logging** - registra todos los movimientos y errores en `organizar_descargas.log`
- **Sin destrucción** - nunca borra, ejecuta ni cambia permisos de archivos
- **Arranque automático** - inicia al encender el equipo (mediante OpenClaw Gateway)

## Instalación

### Requisitos
- Arch Linux (u otro sistema con inotify-tools)
- `inotifywait` (parte de inotify-tools)
- Bash

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

### Ejecutar el Script manualmente (para pruebas)
```bash
cd /Ordenar_Descargas
./sort-downloads.sh
```

### Detener el Script
```bash
pkill -f sort-downloads.sh
```

### Ver Log en tiempo real
```bash
tail -f /Ordenar_Descargas/organizar_descargas.log
```

### Estado de la Automatización (OpenClaw)
```bash
openclaw automations list --all
```

## Control de la Automatización

### En OpenClaw Gateway
- **Estado actual**: Ejecutándose (si está activo)
- **Próxima ejecución**: Cada 10 minutos (ejecución periódica)
- **Log**: `organizar_descargas.log`
- **Salida**: `sort-downloads.out` / `sort-downloads.err` (si la automatización lanza el script)

### Pausar/Reanudar
- Desactivar la automatización en `openclaw automations list --all`
- Activar de nuevo cuando se desee reanudar

### Reiniciar
```bash
openclaw automations list --all  # Obtener ID
openclaw automations update <id>   # Editar configuración
```

## Pruebas de Aceptación

Ejecute las pruebas manualmente:

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

### 3. Sin Extensión
```bash
# Descargar un archivo sin extensión
# Debe aparecer en ~/Descargas/Otros/
```

### 4. Duplicados
```bash
# Descargar mismo archivo 2-3 veces
# Debe generar: archivo, archivo_2, archivo_3...
```

### 5. Descarga en Curso
```bash
# Iniciar descarga -> aparecerá .crdownload/.part/.tmp
# Debe ser ignorado hasta que finalice
```

### 6. Error al Mover
```bash
# Simular error (permisos, disco lleno, etc.)
# Debe quedar en Descargas y registrar error en log
```

### 7. Persistencia entre Sesiones
```bash
# Reiniciar equipo o contenedor
# El proceso debe arrancar automáticamente
# No reprocesar archivos ya movidos
```

## Configuración

### Modificar Categorías o Extensiones
Editar `/Ordenar_Descargas/sort-downloads.sh`
- Array `CATEGORIES` para agregar/quitar extensiones
- Variable `IGNORE_EXTENSIONS` para nuevas extensiones a ignorar

### Cambiar Intervalo de Ejecución Periódica
Editar la automatización en OpenClaw:
```bash
# El script se ejecuta cada 10 minutos por defecto
# Para cambiar, editar la automatización y actualizar el schedule everyMs
```

### Ubicación del Log
- **Principal**: `/Ordenar_Descargas/organizar_descargas.log`
- **Opcional**: `$PROJECT_DIR/sort-downloads.out` / `$PROJECT_DIR/sort-downloads.err`

## Información Técnica

### Arquitectura
- **Bucle principal**: `while true` usando `inotifywait`
- **Eventos vigila**: `create` y `moved_to` en la carpeta de descargas
- **Detección de estabilidad**: Tamaño estable + verificación de legibilidad
- **Manejo de carpetas**: Crea todas las carpetas de categoría al inicio

### Reglas de Seguridad
- Nunca ejecuta archivos (`exec`, `subprocess`, `os.system`)
- Nunca cambia permisos (`chmod`, `icacls`)
- Nunca borra archivos o carpetas
- Solo toca archivos dentro de la carpeta de descargas y subcarpetas
- Ejecuta como usuario normal (sin sudo)

### Estructura de Directorios
```
/Ordenar_Descargas/
├── sort-downloads.sh           # Script principal
├── organizar_descargas.log     # Log de movimientos y errores
├── sort-downloads.out          # Salida del script (si se lanza)
├── sort-downloads.err          # Errores del script (si se lanza)
├── README.md                   # Este archivo
├── SPEC.md                     # Especificación técnica
├── OrdenarDescargas.md          # Ficha de diseño humana
└── agents/
    └── AGENTS.md               # Contexto del agente
```

## Mantenimiento

### Reiniciar el Servicio
```bash
# Detener
pkill -f sort-downloads.sh

# Reiniciar manualmente (si la automatización no lo hizo)
cd /Ordenar_Descargas
./sort-downloads.sh &
```

### Verificar Estado
```bash
# 1. Verificar si el proceso está corriendo
ps aux | grep sort-downloads.sh | grep -v grep

# 2. Verificar log reciente
 tail -10 /Ordenar_Descargas/organizar_descargas.log

# 3. Verificar carpeta de descargas
ls -la /home/user/Descargas/
```

### Diagnosticar Problemas
- **Script no inicia**: Verificar permisos, dependencias, sintaxis del script
- **No detecta descargas**: Verificar que inotifywait está instalado, que la carpeta de descargas es correcta
- **Errores en log**: Revisar `organizar_descargas.log` para detalles
- **No hay actividad**: Esperar a que se complete una descarga o ejecutar una prueba manualmente

## Problemas Conocidos y Soluciones

### 1. inotifywait no está instalado
```bash
sudo pacman -S inotify-tools
```

### 2. La carpeta de descargas no es ~/Descargas o ~/Downloads
Editar `DOWNLOAD_DIR` en el script o verificar la estructura del sistema

### 3. El script se cierra inesperadamente
Revisar logs en `sort-downloads.err`

### 4. El script lanza muchos procesos
El script incluye protección contra múltiples instancias

## Modificaciones Futuras

### Próximas Mejoras (Ficha de Diseño)
1. **Subcarpetas por Proyecto/Fecha**: Dentro de cada categoría
2. **Extracción de Metadatos**: Clasificar por autor, fecha, etc.
3. **Verificación con VirusTotal**: Opcional para archivos ejecutables
4. **Notificación al Usuario**: Alertas cuando se mueve un archivo
5. **Monitoreo de Espacio en Disco**: Advertir si una categoría está llena

## Licencia
Automatización interna para uso personal. No redistribuir sin permiso.

## Autor
user Lleixa Pegueroles

## Fecha de Creación
27/9/2026