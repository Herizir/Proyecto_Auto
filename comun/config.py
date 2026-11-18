"""Configuración de conexión.

Lee variables de entorno y, si existe, el archivo ``.env`` en la carpeta
del proyecto (ver ``.env.example``).
"""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _cargar_env():
    archivo = RAIZ / ".env"
    if not archivo.is_file():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env()

DB_SERVIDOR = os.environ.get("MOTORHAUS_DB_SERVIDOR", "localhost")
DB_NOMBRE = os.environ.get("MOTORHAUS_DB_NOMBRE", "MOTORHAUS")
# Si se dejan vacíos se usa la autenticación de Windows.
DB_USUARIO = os.environ.get("MOTORHAUS_DB_USUARIO", "")
DB_CLAVE = os.environ.get("MOTORHAUS_DB_CLAVE", "")
DB_DRIVER = os.environ.get("MOTORHAUS_DB_DRIVER", "")

WEB_PUERTO = int(os.environ.get("MOTORHAUS_WEB_PUERTO", "5000"))
WEB_URL = f"http://127.0.0.1:{WEB_PUERTO}"
# Clave para firmar las cookies de sesión de la web.
WEB_SECRETO = os.environ.get("MOTORHAUS_SECRETO", "")

# Estudio IA: Ollama corriendo en esta computadora.
IA_URL = os.environ.get("MOTORHAUS_IA_URL", "http://127.0.0.1:11434").rstrip("/")
IA_MODELO = os.environ.get("MOTORHAUS_IA_MODELO", "llama3.2:3b")
