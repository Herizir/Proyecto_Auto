# Motorhaus

Plantillas de interfaz para una tienda de autos y su panel de escritorio. Ambos comparten la misma identidad visual. Los vehículos, clientes, precios y métricas son ejemplos ficticios.

## Estructura

```text
Proyecto_Auto/
├── web/
│   ├── index.html
│   ├── cuenta.html
│   ├── css/styles.css
│   ├── css/cuenta.css
│   ├── js/app.js
│   └── js/cuenta.js
├── escritorio/
│   ├── app.py
│   └── requirements.txt
└── README.md
```

## Tienda web

Abre `web/index.html` en un navegador moderno. Puedes filtrar y ordenar los vehículos, marcar favoritos durante la sesión y abrir fichas de muestra. La opción «Mi cuenta» muestra las plantillas de acceso, registro y recuperación: no introduzcas credenciales reales, ya que no existe autenticación. Las imágenes y fuentes se cargan desde Internet; sin conexión se utilizan los colores y fuentes de respaldo. El correo de contacto es un marcador de ejemplo y debe reemplazarse antes de publicar.

## Escritorio

Con Python instalado, ejecuta desde la carpeta del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r escritorio\requirements.txt
python escritorio\app.py
```

Si la política de ejecución de PowerShell no permite activar el entorno, utiliza directamente `.\.venv\Scripts\python.exe -m pip install -r escritorio\requirements.txt` y `.\.venv\Scripts\python.exe escritorio\app.py`.

Para entrar al ERP usa «Entrar en modo demostración» en la pantalla de acceso. El lanzador abre el archivo local de la tienda en el navegador predeterminado. Los formularios de vehículos, clientes, ventas y configuración son demostraciones visuales: no guardan datos ni realizan operaciones comerciales. El inicio de sesión y la recuperación están desactivados.

## IA

El Estudio IA incluye plantillas navegables para análisis de inventario, contenido de anuncios y perspectivas de ventas. La generación está desactivada: **no hay integración con Ollama**, ejecución de modelos ni envío de información. No se ha implementado backend.
