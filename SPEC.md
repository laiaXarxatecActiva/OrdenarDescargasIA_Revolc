# SPEC.md — Organizador de Descargas

> Este archivo es la especificación del proyecto para un agente de codificación (OpenClaw / opencode). No es el material de clase ni la ficha de diseño (esos son documentos para humanos); este es el documento que el agente debe  leer para saber qué construir.
> 
> **Primera tarea del agente al leer este SPEC.md:** crear una carpeta `agents/` en la raíz de este proyecto y, dentro, un archivo `AGENTS.md` que resuma este proyecto en el formato que el propio agente use para recordar contexto entre sesiones (convenciones de código, comandos, estructura de carpetas, estado actual). El contenido exacto de `AGENTS.md` lo decide el agente según su propio formato habitual; este SPEC.md es la fuente de verdad sobre los requisitos.

## Estado actual del proyecto

- Ahora mismo esta carpeta de proyecto solo contiene este `SPEC.md` y un archivo para lercura del ser humano `OrdenarDescargas.md`.
- **Ningún script existe todavía.** El agente debe crear el código desde cero a partir
  de este documento.
- Los ficheros de este proyecto (SPEC.md, AGENTS.md, código) viven en esta
  carpeta de proyecto, **no** dentro de la carpeta de Descargas del sistema.
  La carpeta de Descargas es únicamente el *objetivo* que el código debe
  vigilar y ordenar, no el lugar donde vive el proyecto.

## Objetivo

Crear una automatización que ordene automáticamente la carpeta de
Descargas/Downloads del usuario, moviendo cada archivo nuevo a una
subcarpeta según su tipo, en cuanto la descarga termina.

## Qué debe entregar el agente

Dos implementaciones independientes y funcionalmente equivalentes:

1. **Versión agente**: pensada para ejecutarse mediante el propio agente de
   IA (OpenClaw/OpenRouter) con las herramientas disponibles en este entorno.
2. **Versión script (sin IA)**: un script determinista, sin llamadas a
   ningún proveedor de IA, que hace exactamente lo mismo. Es el plan de
   respaldo si la IA falla o no está disponible, así que no puede depender
   de ella para nada, ni siquiera para casos dudosos.

Ambas versiones deben cumplir *todas* las reglas de este documento de forma
idéntica. Ninguna debe comportarse de forma distinta a la otra en ningún
caso de la sección "Pruebas de aceptación".

## Carpeta a vigilar

La carpeta de Descargas/Downloads real del sistema (detectar automáticamente
su ruta y nombre real — puede llamarse "Descargas" o "Downloads" según el
idioma del sistema — en vez de asumir un nombre fijo).

## Categorías y subcarpetas

Crear, si no existen, estas subcarpetas dentro de Descargas:

| Carpeta        | Extensiones                                                                                |
| -------------- | ------------------------------------------------------------------------------------------ |
| `Audio`        | mp3, wav, flac, aac, ogg, m4a, wma, opus                                                   |
| `Video`        | mp4, mkv, avi, mov, wmv, flv, webm, m4v                                                    |
| `PDFs`         | pdf *(carpeta propia, separada de Documentos — es el tipo de archivo que más se descarga)* |
| `Documentos`   | odt, doc, docx, txt, rtf, xls, xlsx, ppt, pptx, csv, ods, odp, md                          |
| `Imagenes`     | jpg, jpeg, png, gif, bmp, svg, webp, tiff, ico                                             |
| `Comprimidos`  | zip, rar, 7z, tar, gz, xz, bz2                                                             |
| `Instaladores` | appimage, deb, rpm, sh, run                                                                |
| `Otros`        | cualquier extensión no listada arriba, y archivos sin extensión                            |

**Regla de cierre:** ningún archivo puede quedar en la raíz de Descargas sin
pasar a una subcarpeta. Si una extensión no está en la tabla, va a `Otros`.

**Extensiones a ignorar** (marcadores de descarga en curso, nunca mover
mientras tengan esta extensión): `.crdownload`, `.part`, `.tmp`, `.download` (y equivalentes de otros navegadores/SO si se detectan).

## Comportamiento del evento

- El proceso arranca como mucho una vez al encender el equipo (al iniciar
  sesión) y a partir de ahí se queda escuchando eventos del sistema de
  archivos en Descargas de forma continua durante el resto del uso — no
  debe funcionar por sondeo periódico (polling) ni requerir que el usuario
  lo relance cada vez.
- Debe esperar a que el archivo termine de escribirse (tamaño estable /
  archivo no abierto en escritura) antes de moverlo, para no mover un
  archivo a medio descargar.

## Duplicados

Si al mover un archivo ya existe otro con el mismo nombre en la carpeta de
destino, el archivo nuevo se guarda igualmente añadiendo `_2` al nombre
(antes de la extensión). Si `_2` también existe, se prueba `_3`, y así
sucesivamente. Nunca se sobrescribe ni se borra ninguna versión anterior;
todas las versiones se conservan.

## Permisos — límites técnicos obligatorios

El código (en ambas versiones) **no puede, bajo ninguna circunstancia**:

- Borrar ningún archivo o carpeta.
- Ejecutar ningún archivo (ni el propio archivo descargado ni ningún otro),
  ni siquiera para inspeccionarlo.
- Cambiar permisos de ningún archivo o carpeta.
- Tocar nada fuera de la carpeta de Descargas y sus propias subcarpetas.
- Requerir ni asumir privilegios de administrador/root. Debe ejecutarse
  siempre como el usuario normal del sistema.

Lo único que el código puede hacer es: comprobar si una carpeta existe,
crearla si no existe, y mover/renombrar archivos dentro de Descargas.

El agente debe verificar esto revisando que el código no contiene ninguna
llamada de borrado, ejecución o cambio de permisos antes de darlo por
terminado (por ejemplo, buscando `rm`, `delete`, `exec`, `subprocess`, `os.system`, `chmod`, `icacls` u operaciones equivalentes en el lenguaje
usado, y confirmando que ninguna se aplica al archivo descargado ni a nada
fuera de las subcarpetas de destino).

## Registro (log)

Cada movimiento (o error al mover) debe quedar registrado con fecha/hora,
nombre de archivo, carpeta de destino y si hubo renombrado por duplicado.
El log vive fuera de Descargas (por ejemplo, en la carpeta del propio
proyecto o en una ruta de datos de usuario), no dentro de las carpetas que
se están organizando.

Si un archivo no se puede mover (p. ej. no se puede crear la carpeta
destino o falla el sistema de archivos), debe quedarse donde está,
registrarse el error en el log, y el proceso debe seguir vigilando el
resto de descargas con normalidad (un fallo no debe detener el proceso
completo).

## Pruebas de aceptación (deben pasar en ambas versiones)

1. **Normal**: descargar una imagen → aparece en `Imagenes`, ya no está en
   la raíz de Descargas.
2. **PDF**: descargar un PDF → aparece en `PDFs`, no en `Documentos`.
3. **Sin extensión**: descargar un archivo sin extensión → aparece en `Otros`.
4. **Repetido**: descargar el mismo nombre de archivo dos (y tres) veces →
   se conservan todas las versiones con sufijo `_2`, `_3`...
5. **Descarga en curso**: mientras un archivo tiene extensión `.crdownload`/`.part`/`.tmp`, no se toca; solo se mueve cuando termina y
   toma su nombre final.
6. **Fallo al mover**: si el destino no se puede crear o escribir, el
   archivo original permanece intacto en Descargas y el error queda en el
   log.
7. **Persistencia entre sesiones**: al reiniciar el equipo, el proceso
   vuelve a arrancar solo y sigue vigilando, sin reprocesar lo que ya se
   movió antes.

## Fuera de alcance (no hacer, ni siquiera como mejora espontánea)

- No clasificar por contenido del archivo, solo por extensión.
- No renombrar archivos salvo por la regla de duplicados `_N`.
- No mover ni tocar nada que no esté directamente en la raíz de Descargas
  (por ejemplo, no entrar en subcarpetas que el usuario haya creado a mano
  dentro de Descargas).
- No añadir borrado, ejecución, compresión, subida a la nube, ni ninguna
  función no pedida aquí, aunque parezca una mejora razonable.

## Referencia de contexto (no vinculante)

El documento humano de diseño de este mismo proyecto es una ficha de
diseño de automatización (con problema, valor, evento, entradas, reglas de
decisión, pruebas de aceptación, etc.) elaborada para un curso. Este
SPEC.md resume y formaliza esos mismos requisitos para que el agente los
implemente; en caso de cualquier diferencia entre ambos, este SPEC.md es el
que manda para la implementación.
