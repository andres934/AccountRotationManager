# Rotación de cuentas

Un panel flotante de Windows para saber qué cuenta de fondeo de futuros te toca operar. Registra **TP**, **SL** o **BE** y mantiene el orden de la cola entre sesiones. Los datos se guardan en tu equipo, en SQLite.

El programa registra la cuenta, la fecha y el resultado. No ejecuta operaciones, no se conecta al bróker y no guarda importes o ganancias y pérdidas.

## Inicio rápido si descargaste el código de GitHub

Extrae el ZIP completo y abre la carpeta que contiene estos dos archivos. Con Python instalado en Windows, haz doble clic en el archivo que corresponda:

| Quiero abrir | Archivo que debes ejecutar |
| --- | --- |
| **El panel flotante** | [`Iniciar.pyw`](Iniciar.pyw). Abre la aplicación de escritorio sin terminal. |
| **La versión web** | [`Iniciar.cmd`](Iniciar.cmd). Deja la terminal abierta y entra en [127.0.0.1:8765](http://127.0.0.1:8765). |

Si Windows no abre `Iniciar.pyw` con doble clic, abre PowerShell en esa carpeta y ejecuta `pythonw -B .\Iniciar.pyw`. Si aún no tienes Python, sigue los [pasos de preparación](#ejecutar-desde-github-sin-el-instalador).

## Instalación y requisitos

- **Windows de 64 bits (x64)** para usar el instalador.
- El instalador incluye Python, Tkinter y SQLite. La aplicación funciona sin conexión a Internet y se instala para el usuario actual con permisos normales.

1. Abre el instalador de Windows x64. Si recibiste el ZIP, descomprímelo primero y ejecuta el EXE que contiene.
2. Sigue el asistente de instalación.
3. Abre **Rotación de cuentas (instalada)** desde el escritorio o **Rotación de cuentas** desde el menú Inicio. El panel se abre sin terminal.

El repositorio contiene el código fuente. Si tienes el instalador, puedes usarlo directamente. Si solo tienes el código, abre [`Iniciar.pyw`](Iniciar.pyw) para usar el panel o [`Iniciar.cmd`](Iniciar.cmd) para iniciar la web local.

El instalador no tiene firma digital, por lo que Windows puede mostrar un aviso de SmartScreen. Si vas a compartir el programa, envía el EXE o el ZIP de la carpeta `Distribucion`. El ZIP contiene ese mismo EXE. Cada usuario empieza con una base vacía.

## Primer uso

1. Pulsa **Agregar una cuenta** desde el panel vacío o abre **Cola → Agregar una cuenta**.
2. Escribe el nombre de la primera cuenta y pulsa **Añadir**. Agrega las demás en el orden en que quieres empezar.
3. Opera la cuenta que aparece en **Turno actual**. Cuando termine la operación, pulsa el resultado correspondiente.

| Resultado | Efecto en la cola |
| --- | --- |
| **TP** · Take profit | Agota la cuenta por hoy y la envía al final de la cola. |
| **SL** · Stop loss | Agota la cuenta por hoy y la envía al final de la cola. |
| **BE** · Break even | Guarda el resultado y mantiene la misma cuenta en turno. |

**Siguiente** indica qué cuenta disponible viene después. Si todas quedan agotadas, el panel espera al cambio de día según la fecha local de Windows. Las cuentas vuelven a estar disponibles y conservan el orden de la cola. Por ejemplo, si empiezas con A, B y C y registras TP para A y SL para B, el día siguiente empieza por C, seguida de A y B.

## Cola, Historial y Ajustes

- **Cola** muestra hasta dos cuentas a la vez. Desplázate para ver el resto. La papelera retira una cuenta de la rotación y conserva sus resultados anteriores. Si vuelves a añadirla con el mismo nombre exacto, se reincorpora al final de la cola.
- **Historial** muestra hasta 20 registros recientes con la cuenta, la fecha y el resultado. Cada papelera pide confirmación y borra solo su registro. Si borras un TP o SL, puede cambiar la cuenta en turno.
- **Ajustes** permite elegir una de las cuatro esquinas de la pantalla principal y activar **Siempre encima**. El panel recuerda ambas preferencias. La posición inicial es abajo a la derecha.
- **Borrar todos los datos**, en Ajustes, elimina las cuentas, el historial y las preferencias tras pedir confirmación. Tendrás que añadir las cuentas de nuevo.

## Datos y copias de seguridad

| Forma de ejecución | Ubicación de la base |
| --- | --- |
| Aplicación instalada | `%LOCALAPPDATA%\RotacionDeCuentas\rotacion.sqlite3` |
| Panel o web ejecutados desde el código fuente | `rotacion.sqlite3`, junto al código del proyecto |

Para guardar una copia, cierra la aplicación y, si la estás usando, la web local. Copia `rotacion.sqlite3` a otra carpeta. Para restaurarla, cierra de nuevo ambas interfaces y coloca la copia en la ubicación correspondiente. Esto reemplaza los datos actuales de esa instalación. Las preferencias de la ventana también están en la base.

Desinstalar el programa conserva la base. La versión instalada y la que se ejecuta desde el código usan ubicaciones distintas.

## Ejecutar desde GitHub sin el instalador

### 1. Descargar el código

En [GitHub](https://github.com/andres934/AccountRotationManager), pulsa **Code → Download ZIP** y extrae todo el contenido. Abre en PowerShell la carpeta extraída que contiene `Iniciar.pyw`. Puedes hacerlo desde el Explorador de archivos escribiendo `powershell` en la barra de direcciones y pulsando **Intro**.

Si ya tienes Git, también puedes clonar el proyecto desde PowerShell:

```powershell
git clone https://github.com/andres934/AccountRotationManager.git
cd AccountRotationManager
```

### 2. Preparar Python

Necesitas Windows y **Python con Tkinter**. El proyecto se ha probado con Python 3.12. Si vas a instalarlo, usa el instalador completo de [Python para Windows](https://www.python.org/downloads/windows/), marca **Add Python to PATH** y conserva la opción **tcl/tk and IDLE**. Abre una terminal nueva después de instalarlo.

Comprueba la instalación:

```powershell
python --version
python -c "import tkinter, sqlite3; print('Tkinter y SQLite disponibles')"
```

Tkinter y SQLite vienen con la instalación completa de Python. No necesitas instalar paquetes con `pip`.

### 3. Abrir el panel flotante con Iniciar.pyw

Haz doble clic en [`Iniciar.pyw`](Iniciar.pyw) desde el Explorador de archivos. Si Windows te pide elegir una aplicación para abrirlo, abre PowerShell en esa misma carpeta y ejecuta:

```powershell
pythonw -B .\Iniciar.pyw
```

Se abrirá el panel flotante sin terminal. La primera vez se creará `rotacion.sqlite3` junto al código. Mantén los archivos en la misma carpeta y guárdala en un lugar donde tu usuario pueda escribir.

Si `pythonw` no abre la ventana, prueba `python -B .\Iniciar.pyw` y consulta `inicio.log`, que se guarda junto a la base de datos.

### Abrir la web local con Iniciar.cmd

Haz doble clic en [`Iniciar.cmd`](Iniciar.cmd) o ejecuta `python -B .\app.py` desde la raíz. Entra en [127.0.0.1:8765](http://127.0.0.1:8765) y deja la terminal abierta mientras uses la web. Ambas interfaces ejecutadas desde el código comparten la base local. La web ofrece los controles básicos de rotación y permite deshacer el último registro. Los ajustes de ventana y el borrado individual de registros están en el panel flotante.

Para compilar un instalador propio o consultar cómo está construido el proyecto, lee [AGENTS.md](AGENTS.md).
