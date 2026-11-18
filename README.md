# Motorhaus

Tienda de autos con dos caras que comparten **la misma base de datos SQL Server (`MOTORHAUS`)**:

- **Tienda web** — los clientes ven el inventario, crean su cuenta, guardan favoritos y envían consultas.
- **Panel de escritorio** — los administradores dan de alta vehículos, atienden consultas, registran clientes y ventas.

Lo que se cambia en un lado aparece en el otro: un auto nuevo en el escritorio sale en la web; una consulta o un registro en la web aparece en el escritorio; al reservar o cerrar una venta, el auto cambia de estado en la tienda.

## Estructura

```text
Proyecto_Auto/
├── base_datos/motorhaus.sql   ← tablas y datos de ejemplo (se ejecuta solo)
├── comun/                     ← código compartido
│   ├── config.py
│   ├── db.py                  ← conexión y consultas a la BD
│   └── ia.py                  ← Estudio IA (Ollama)
├── servidor/app.py            ← servidor web (Flask): páginas + API /api
├── web/                       ← HTML, CSS y JS de la tienda
├── escritorio/app.py          ← panel de escritorio (CustomTkinter)
├── tests/                     ← pruebas de integración (usan una BD aparte)
├── iniciar_web.bat
├── iniciar_escritorio.bat
└── requirements.txt
```

## Requisitos

- Windows con **SQL Server** encendido en `localhost` (autenticación de Windows).
- **ODBC Driver 17 o 18 for SQL Server**.
- **Python 3.10+**.

Si tu SQL Server tiene otro nombre o usa usuario y contraseña, copia `.env.example` como `.env` y ajústalo.

## Cómo usarlo

Doble clic en:

- `iniciar_web.bat` → abre la tienda en <http://127.0.0.1:5000>
- `iniciar_escritorio.bat` → abre el panel de administración

La primera vez crean el entorno de Python e instalan las dependencias. La base de datos `MOTORHAUS` y sus tablas se crean solas al arrancar cualquiera de las dos.

O desde PowerShell, en esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe servidor\app.py      # tienda web
.\.venv\Scripts\python.exe escritorio\app.py    # panel de escritorio
```

### Primer acceso al panel

Si todavía no hay administradores, el panel pide crear la primera cuenta. Después, desde **Configuración** se pueden agregar más administradores. El botón **Abrir tienda** enciende el servidor web si no está encendido.

### Contraseñas olvidadas

No se envían correos. Si un cliente pide recuperar su cuenta en la web, la solicitud aparece en **Clientes → Consultas por atender**; el administrador pulsa **Nueva clave**, se genera una contraseña temporal (se copia al portapapeles) y se la comparte al cliente, que puede cambiarla en «Mi cuenta».

## Base de datos

| Tabla | Para qué |
| --- | --- |
| `Marcas`, `Vehiculos`, `Fotos_Vehiculos` | Inventario |
| `Usuarios` | Cuentas (rol `cliente` desde la web, `admin` para el panel). Contraseñas con hash. |
| `Clientes` | Prospectos y clientes (de la web o del mostrador) |
| `Consultas` | Mensajes que llegan desde la web |
| `Favoritos` | Autos guardados por cada cliente |
| `Ventas` | Operaciones; su estado mueve el estado del vehículo |

`base_datos/motorhaus.sql` se puede ejecutar también en SQL Server Management Studio; no borra datos existentes. (`proyecto MOTORHAUS.SQLQuery2.sql` es el script original y ya no se usa.)

## Estudio IA

Usa **Ollama** instalado en esta computadora (por defecto el modelo `llama3.2:3b`; se puede cambiar desde la pantalla del Estudio IA o con `MOTORHAUS_IA_MODELO` en `.env`). Los datos se leen de la base de datos y solo se envían a Ollama local; nada sale a internet.

- **Análisis de inventario**: revisa precios, días en inventario, favoritos y consultas de cada auto.
- **Contenido para anuncios**: redacta el anuncio de un auto para la tienda web, redes sociales o marketplace. El botón **Usar como descripción en la tienda** lo publica como descripción del auto (también se llega desde **Inventario → ✦ Anuncio**).
- **Perspectivas de ventas**: revisa ventas, consultas de la web y clientes para sugerir oportunidades.

Ollama debe estar abierto. La primera generación tarda un poco más mientras se carga el modelo. Los modelos pequeños pueden equivocarse con algún dato: revisa el resultado antes de usarlo (se puede editar).

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover tests -v
```

Crean y borran una base `MOTORHAUS_PRUEBAS`, así que no tocan los datos reales.

## Pendiente

- Envío real de correos (recuperación de contraseña, avisos).
