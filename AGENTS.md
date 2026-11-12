# AccountManager — contexto para agentes

Lee este archivo antes de cambiar el proyecto. El nombre que ve el usuario es **Rotación de cuentas**. La interfaz está en español y el producto principal es un panel flotante para Windows. Hay una segunda interfaz web local que comparte la lógica, pero tiene sus propios controles.

## Propósito y alcance

El usuario opera varias cuentas de fondeo de futuros y necesita saber qué cuenta le toca, sin mantener una nota diaria. El programa registra únicamente el resultado categórico (**TP**, **SL** o **BE**) y la fecha. No integra bróker, no coloca órdenes y no guarda importes, saldos ni P&L. Funciona localmente y sin dependencias externas en tiempo de ejecución cuando se usa el instalador.

## Reglas de rotación

1. Las cuentas se añaden en el orden en que el usuario quiere empezar. Las cuentas nuevas o recuperadas se colocan al final de la cola.
2. **TP y SL** consumen el turno. La cuenta pasa al final de la cola y queda agotada para la fecha local de Windows. El panel selecciona la siguiente cuenta activa y disponible.
3. **BE** crea un registro, pero no consume el turno, no agota la cuenta y no cambia el orden. Se pueden registrar varios BE seguidos sobre la misma cuenta.
4. Al cambiar la fecha local, el agotamiento deja de aplicar. El orden se conserva y empiezan las cuentas que quedaron pendientes. Los días sin operaciones no alteran la cola. Ejemplo: con A, B y C, si A tiene TP y B tiene SL, el resto del día toca C y el día siguiente empieza C → A → B.
5. Quitar una cuenta la desactiva y conserva sus resultados. Añadir de nuevo el mismo nombre exacto reactiva esa cuenta al final de la cola. Si ya tuvo TP o SL en la fecha actual, sigue agotada ese día. Los nombres se recortan y deben tener entre 1 y 80 caracteres. La unicidad se aplica al nombre exacto.
6. Borrar un registro desde Historial elimina esa fila de SQLite. Si era un TP o SL, pueden cambiar el orden y el agotamiento. La cola se recalcula a partir de los registros que queden.
7. Borrar todos los datos desde Ajustes elimina cuentas, resultados y preferencias de la ventana. El cuadro de confirmación indica que habrá que agregar las cuentas de nuevo y selecciona **No** por defecto.

## Mapa del código

| Ruta relativa | Responsabilidad |
| --- | --- |
| `rotation.py` | Base SQLite, creación y migración del esquema, cálculo de cola, validación y escritura de resultados, cuentas y preferencias. Es la fuente de verdad de la rotación. |
| `floating.py` | Panel de Windows con Tkinter/ttk. `Panel` arma las secciones y actualiza el estado. `ScrollRows` comparte el diseño y el desplazamiento de Cola e Historial. `configure_theme` define la paleta y los estados. |
| `Iniciar.pyw` | Entrada del acceso directo y del ejecutable empaquetado. Crea el directorio de datos, redirige errores a `inicio.log` y arranca el panel sin consola. |
| `Trading.ico` | Icono del panel, del acceso directo, del ejecutable y del instalador. |
| `app.py`, `style.css`, `Iniciar.cmd` | Interfaz web auxiliar, HTML generado en Python y estilos CSS. Usa `http.server` en `127.0.0.1:8765`. |
| `Instalador.nsi` | Instalador NSIS en español, por usuario, para Windows x64. Recibe las rutas de entrada y salida mediante `PAYLOAD` y `OUTPUT`. |
| `Distribucion/` | Artefactos compartibles. La versión existente es 1.0.0 para Windows x64. El ZIP contiene el mismo instalador EXE. |
| `.package-build/` | Herramientas y archivos locales generados para compilar, incluidos PyInstaller, NSIS portátil, bundle y pruebas de empaquetado. Se puede regenerar. |

### Persistencia y flujo de datos

- **Ejecución desde código:** la base `rotacion.sqlite3` y el log `inicio.log` se guardan en la raíz del proyecto. El panel y la web ejecutados desde código comparten esa base.
- **Ejecución instalada:** la base y el log se guardan en `%LOCALAPPDATA%\RotacionDeCuentas`. Los binarios se instalan por separado en `%LOCALAPPDATA%\Programs\RotacionDeCuentas`. El instalador no importa la base del proyecto y el desinstalador conserva los datos del usuario.
- **Tablas:** `accounts` guarda identificador, nombre, referencia de alta o reactivación (`created_after`) y estado `active`. `entries` guarda identificador autoincremental, cuenta, día ISO y resultado. `window_settings` es una fila opcional con esquina y estado de «Siempre encima».
- **Orden:** `rotation.queue(db, day)` incluye cuentas activas y ordena por su último TP/SL posterior a `created_after`, o por esa referencia de alta cuando aún no hay uno. El desempate usa la existencia de ese resultado y el ID de la cuenta. El agotamiento mira TP/SL del día, incluso si son anteriores a la reactivación. La cuenta en turno es la primera fila disponible. Cola muestra las disponibles primero, conservando el orden relativo, y después las agotadas.
- **Escrituras:** las mutaciones usan conexiones cortas y transacciones SQLite. Al registrar TP, SL o BE, `update()` vuelve a comprobar la fecha, el último ID de operación y la cuenta activa dentro de un `BEGIN IMMEDIATE`. Las consultas de escritura parametrizan los valores. `initialize()` crea las tablas y añade `active` si falta en una base anterior.
- **Lectura del panel:** `Panel.refresh()` consulta la cola y las 20 entradas recientes en una misma transacción de lectura. `poll()` refresca cada 1,5 segundos. Por eso el panel recoge el cambio de día y los cambios hechos desde la web local. `show_notice()` comparte el espacio de «Siguiente» con avisos de registro. Tras añadir o borrar se recupera «Siguiente» de inmediato.
- **Web:** el servidor solo escucha en loopback, comprueba `Host`, exige un token por proceso para los POST y redirige tras una mutación correcta. Renderiza 20 registros recientes y ofrece deshacer el último. La papelera individual de historial, el borrado total y los ajustes de ventana pertenecen al panel de escritorio. La web requiere recargar para ver cambios externos o de fecha.

## Arrancar y desarrollar

Ejecuta estos comandos en PowerShell desde la raíz. El entorno usado para la distribución actual fue Python 3.12 x64 con Tcl/Tk. El código de ejecución utiliza la biblioteca estándar. El panel depende de Windows para el icono, el área útil de la pantalla, la barra de título y el posicionamiento.

```powershell
# Panel con consola para ver errores durante el desarrollo
python -B .\Iniciar.pyw

# Panel de uso diario, sin consola
pythonw -B .\Iniciar.pyw

# Web local
python -B .\app.py
```

El acceso directo de desarrollo apunta a `pythonw.exe -B Iniciar.pyw` y usa `Trading.ico`. La app instalada tiene sus propios accesos al escritorio y al menú Inicio. Ambos lanzadores pueden ejecutarse con permisos normales.

### Comportamiento de interfaz que importa conservar

- Ventana de 384 px de ancho lógico, con altura según el contenido. Se ancla a una de las cuatro esquinas del área de trabajo de la pantalla principal. Por defecto, abajo a la derecha con «Siempre encima» activado.
- La cuenta activa domina la tarjeta. Los botones centrados dicen solo **TP**, **SL** y **BE**, con sus colores. Bajo ellos va «Siguiente» o el estado correspondiente. Sin cuentas se ofrece abrir el formulario. Si todas están agotadas, los botones de registro se ocultan.
- Solo se abre una de las secciones **Cola**, **Historial** y **Ajustes** a la vez. Al seleccionar con ratón se ve el estado seleccionado de la pestaña. El teclado conserva un foco visible.
- Cola muestra dos filas por defecto y permite desplazar las demás. Cada fila tiene papelera. «Agregar una cuenta» es un título desplegable de color estable, con la flecha pegada a la derecha del texto. Historial usa las mismas filas y barra fina, con fecha, resultado y papelera, sin botón separado para deshacer.
- Las texturas redondeadas de ttk se generan dentro de `floating.py`. El fondo de cada textura debe coincidir con la superficie donde se dibuja, también en foco. Se conservan referencias a las imágenes en la ventana para que Tk no las libere.

## Compilar el instalador

Las carpetas de compilación y distribución están excluidas de Git y se generan localmente. La compilación existente se hizo con PyInstaller **6.22.3** y NSIS **3.11**. PyInstaller genera un bundle `onedir` sin consola con Python, Tk y SQLite. NSIS comprime ese bundle en un único instalador. Si falta NSIS, prepara la versión portátil oficial en `.package-build\nsis-3.11` o adapta la ruta al compilador disponible.

```powershell
$project = (Get-Location).Path
$build = Join-Path $project '.package-build'
$output = Join-Path $project 'Distribucion'
$tools = Join-Path $build 'python-tools'
$payload = Join-Path $build 'dist\RotacionDeCuentas'
$installer = Join-Path $output 'RotacionDeCuentas-1.0.0-Windows-x64.exe'

New-Item -ItemType Directory -Force -Path $build, $output | Out-Null
python -B -m pip install --target $tools 'pyinstaller==6.22.3'
if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar PyInstaller.' }

$previousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = $tools
    python -B -m PyInstaller --noconfirm --onedir --windowed --name RotacionDeCuentas `
        --icon "$project\Trading.ico" --add-data "$project\Trading.ico:." `
        --distpath "$build\dist" --workpath "$build\work" --specpath $build "$project\Iniciar.pyw"
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo empaquetar el panel.' }
} finally {
    $env:PYTHONPATH = $previousPythonPath
}

& "$build\nsis-3.11\makensis.exe" /WX "/DPAYLOAD=$payload" "/DOUTPUT=$installer" "$project\Instalador.nsi"
if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar el instalador.' }
Compress-Archive -LiteralPath $installer -DestinationPath ([IO.Path]::ChangeExtension($installer, '.zip')) -Force
```

Para publicar una revisión, actualiza la versión del script NSIS (`VERSION` y `VIProductVersion`) y el nombre de salida. Verifica que solo se empaqueta el bundle de PyInstaller. No distribuyas la base, el log, el perfil de pruebas ni toda la carpeta del proyecto. El instalador 1.0.0 no está firmado. Se verificó que el ejecutable empaquetado abre el panel y crea una base vacía, pero no consta una prueba completa de instalación y desinstalación en un perfil limpio.

## Verificar cambios

No hay una suite automatizada versionada en la raíz. Para probar sin tocar las cuentas reales, usa una base temporal y asígnala a `rotation.DATABASE` **antes** de llamar a `rotation.initialize()`. No uses el botón de borrado total sobre la base real como prueba.

```python
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

import rotation

with TemporaryDirectory() as directory:
    rotation.DATABASE = Path(directory) / "test.sqlite3"
    rotation.initialize()
    day = "2026-01-01"
    with closing(rotation.connect()) as db, db:
        rotation.update(db, {"action": "add", "name": "Cuenta A"}, day)
    with closing(rotation.connect()) as db:
        assert rotation.queue(db, day)[0]["name"] == "Cuenta A"
```

- **Rotación:** prueba BE repetido, TP y SL, agotamiento total, cambio de fecha, añadir y reactivar, eliminar un registro intermedio y el recálculo de «Siguiente». Comprueba una base anterior si tocas el esquema.
- **Interfaz:** prueba sin cuentas, con dos o más cuentas, nombres largos, confirmación y cancelación de papeleras, borrado total en una base ficticia, navegación por teclado y las cuatro esquinas. Si cambias la web, revisa sus formularios y la respuesta a un turno desactualizado.
- **Distribución:** lanza el EXE del bundle con `LOCALAPPDATA` apuntando a un directorio de prueba y comprueba que aparece la ventana y que SQLite empieza vacío. Para validar accesos, instalación y desinstalación, usa un perfil limpio o una máquina de prueba.
