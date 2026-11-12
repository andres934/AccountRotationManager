# Rotación de cuentas

Un panel flotante de Windows para saber qué cuenta de fondeo de futuros te toca operar. Registra **TP**, **SL** o **BE** y mantiene el orden de la cola entre sesiones. Los datos se guardan en tu equipo, en SQLite.

El programa registra la cuenta, la fecha y el resultado. No ejecuta operaciones, no se conecta al bróker y no guarda importes o ganancias y pérdidas.

## Instalación y requisitos

- **Windows de 64 bits (x64)** para usar el instalador.
- El instalador incluye Python, Tkinter y SQLite. La aplicación funciona sin conexión a Internet y se instala para el usuario actual con permisos normales.

1. Abre el instalador de Windows x64. Si recibiste el ZIP, descomprímelo primero y ejecuta el EXE que contiene.
2. Sigue el asistente de instalación.
3. Abre **Rotación de cuentas (instalada)** desde el escritorio o **Rotación de cuentas** desde el menú Inicio. El panel se abre sin terminal.

El repositorio contiene el código fuente. Si tienes el instalador, puedes usarlo directamente. Si solo tienes el código, ejecuta el panel desde la fuente o genera el instalador siguiendo [AGENTS.md](AGENTS.md).

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

## Ejecutar desde el código fuente

Para el panel flotante necesitas Windows y **Python 3.12 con Tkinter**, que es el entorno usado para construir esta versión. Desde la raíz del proyecto:

```powershell
# Panel flotante sin terminal
pythonw -B .\Iniciar.pyw

# Web local auxiliar
python -B .\app.py
```

También puedes abrir [Iniciar.cmd](Iniciar.cmd) para iniciar la web. En ambos casos, abre [127.0.0.1:8765](http://127.0.0.1:8765) en el navegador y deja la terminal abierta mientras la uses. La web comparte la base del proyecto con el panel ejecutado desde el código. Ofrece los controles básicos de rotación y un botón para deshacer el último registro. Los ajustes de ventana y las papeleras individuales del Historial están en el panel de escritorio.

Si el panel no abre, revisa `inicio.log` en la misma carpeta que la base de datos. Para la estructura del código, las pruebas y la compilación del instalador, consulta [AGENTS.md](AGENTS.md).
