"""Acceso a la base de datos MOTORHAUS (SQL Server).

La tienda web (``servidor/app.py``) y la app de escritorio
(``escritorio/app.py``) usan exclusivamente estas funciones, así ambas
leen y escriben en la misma base de datos.
"""

from contextlib import contextmanager
from decimal import Decimal
import re
import secrets

import pyodbc
from werkzeug.security import check_password_hash, generate_password_hash

from comun import config

SCRIPT_SQL = config.RAIZ / "base_datos" / "motorhaus.sql"

TIPOS = ["Sedán", "SUV", "Deportivo", "Pickup", "Hatchback"]
COMBUSTIBLES = ["Gasolina", "Diésel", "Híbrido", "Eléctrico"]
ESTADOS_VEHICULO = ["Disponible", "Reservado", "Vendido"]
ETIQUETAS = ["", "DESTACADO", "RECIÉN LLEGADO", "SELECCIÓN", "OFERTA"]
ESTADOS_CLIENTE = ["Nuevo contacto", "Seguimiento", "Cliente", "Descartado"]
ESTADOS_VENTA = ["En seguimiento", "Reservado", "Cerrada", "Cancelada"]

CORREO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DatosInvalidos(ValueError):
    """Error de validación con un mensaje apto para mostrar al usuario."""


class SinConexion(RuntimeError):
    """No se pudo conectar con SQL Server."""


# ------------------------------------------------------------------ conexión

def _driver():
    if config.DB_DRIVER:
        return config.DB_DRIVER
    disponibles = pyodbc.drivers()
    for nombre in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"):
        if nombre in disponibles:
            return nombre
    raise SinConexion("No hay un driver ODBC de SQL Server instalado.")


def _cadena(base):
    partes = [
        f"DRIVER={{{_driver()}}}",
        f"SERVER={config.DB_SERVIDOR}",
        f"DATABASE={base}",
        "TrustServerCertificate=yes",
    ]
    if config.DB_USUARIO:
        partes += [f"UID={config.DB_USUARIO}", f"PWD={config.DB_CLAVE}"]
    else:
        partes.append("Trusted_Connection=yes")
    return ";".join(partes)


def _abrir(base=None, autocommit=False):
    try:
        return pyodbc.connect(_cadena(base or config.DB_NOMBRE), autocommit=autocommit, timeout=5)
    except pyodbc.Error as error:
        raise SinConexion(
            f"No se pudo conectar a SQL Server en «{config.DB_SERVIDOR}». "
            f"Revisa que el servicio esté encendido y la configuración en .env.\n\n{error}"
        ) from error


@contextmanager
def conexion():
    """Abre una conexión con transacción: confirma al salir o deshace si hay error."""
    con = _abrir()
    try:
        yield con.cursor()
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def inicializar():
    """Crea la base de datos, las tablas y los datos de ejemplo si faltan."""
    script = SCRIPT_SQL.read_text(encoding="utf-8")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", config.DB_NOMBRE):
        raise SinConexion("El nombre de la base de datos solo puede tener letras, números y guiones bajos.")
    script = re.sub(r"\bMOTORHAUS\b", config.DB_NOMBRE, script)
    lotes = [lote.strip() for lote in re.split(r"^\s*GO\s*$", script, flags=re.MULTILINE | re.IGNORECASE)]
    con = _abrir("master", autocommit=True)
    try:
        cursor = con.cursor()
        for lote in lotes:
            if lote:
                cursor.execute(lote)
    finally:
        con.close()


def _filas(cursor):
    columnas = [c[0] for c in cursor.description]
    return [{col: _valor(v) for col, v in zip(columnas, fila)} for fila in cursor.fetchall()]


def _fila(cursor):
    filas = _filas(cursor)
    return filas[0] if filas else None


def _valor(valor):
    if isinstance(valor, Decimal):
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    return valor


# ------------------------------------------------------------------ validación

def _texto(datos, campo, nombre, maximo, obligatorio=True):
    valor = str(datos.get(campo) or "").strip()
    if obligatorio and not valor:
        raise DatosInvalidos(f"El campo «{nombre}» es obligatorio.")
    if len(valor) > maximo:
        raise DatosInvalidos(f"«{nombre}» admite como máximo {maximo} caracteres.")
    return valor or None


def _entero(datos, campo, nombre, minimo=0, maximo=None, obligatorio=True):
    crudo = str(datos.get(campo) or "").replace(",", "").replace("$", "").replace(" ", "").strip()
    if not crudo:
        if obligatorio:
            raise DatosInvalidos(f"El campo «{nombre}» es obligatorio.")
        return None
    try:
        valor = int(float(crudo))
    except ValueError:
        raise DatosInvalidos(f"«{nombre}» debe ser un número.") from None
    if valor < minimo or (maximo is not None and valor > maximo):
        raise DatosInvalidos(f"«{nombre}» está fuera del rango permitido.")
    return valor


def _opcion(datos, campo, nombre, opciones):
    valor = str(datos.get(campo) or "").strip()
    if valor not in opciones:
        raise DatosInvalidos(f"Elige un valor válido para «{nombre}».")
    return valor


def _correo(valor, obligatorio=True):
    valor = str(valor or "").strip().lower()
    if not valor:
        if obligatorio:
            raise DatosInvalidos("El correo electrónico es obligatorio.")
        return None
    if len(valor) > 150 or not CORREO_RE.match(valor):
        raise DatosInvalidos("Escribe un correo electrónico válido.")
    return valor


def _url(valor):
    valor = str(valor or "").strip()
    if not valor:
        return None
    if not re.match(r"^https?://[^\s'\"()<>]+$", valor) or len(valor) > 500:
        raise DatosInvalidos("La imagen debe ser una dirección http(s) válida.")
    return valor


# ------------------------------------------------------------------ vehículos

_SQL_VEHICULOS = """
SELECT V.ID_Vehiculo AS id, M.Nombre_Marca AS marca, V.Modelo AS modelo, V.Version AS version,
       V.Tipo AS tipo, V.Anio AS anio, V.Color AS color, V.Kilometraje AS kilometraje,
       V.Combustible AS combustible, V.Precio AS precio, V.Descripcion AS descripcion,
       V.Estado AS estado, V.Etiqueta AS etiqueta, V.Fecha_Alta AS fecha_alta,
       (SELECT TOP 1 F.Foto_URL FROM dbo.Fotos_Vehiculos F
         WHERE F.ID_Vehiculo = V.ID_Vehiculo ORDER BY F.ID_Foto) AS imagen
FROM dbo.Vehiculos V
INNER JOIN dbo.Marcas M ON M.ID_Marca = V.ID_Marca
"""


def listar_vehiculos(solo_publicos=False, tipo=None, orden=None):
    condiciones, parametros = [], []
    if solo_publicos:
        condiciones.append("V.Estado <> 'Vendido'")
    if tipo:
        condiciones.append("V.Tipo = ?")
        parametros.append(tipo)
    sql = _SQL_VEHICULOS + (" WHERE " + " AND ".join(condiciones) if condiciones else "")
    sql += {
        "menor": " ORDER BY V.Precio ASC",
        "mayor": " ORDER BY V.Precio DESC",
    }.get(orden, " ORDER BY CASE V.Etiqueta WHEN 'DESTACADO' THEN 0 ELSE 1 END, V.Fecha_Alta DESC, V.ID_Vehiculo DESC")
    with conexion() as cur:
        cur.execute(sql, parametros)
        return _filas(cur)


def obtener_vehiculo(id_vehiculo):
    with conexion() as cur:
        cur.execute(_SQL_VEHICULOS + " WHERE V.ID_Vehiculo = ?", id_vehiculo)
        return _fila(cur)


def listar_marcas():
    with conexion() as cur:
        cur.execute("SELECT Nombre_Marca FROM dbo.Marcas ORDER BY Nombre_Marca")
        return [fila[0] for fila in cur.fetchall()]


def guardar_vehiculo(datos, id_vehiculo=None):
    """Crea (sin id) o actualiza un vehículo. Devuelve su id."""
    marca = _texto(datos, "marca", "Marca", 50)
    valores = (
        _texto(datos, "modelo", "Modelo", 100),
        _texto(datos, "version", "Versión", 100, obligatorio=False),
        _opcion(datos, "tipo", "Tipo", TIPOS),
        _entero(datos, "anio", "Año", 1950, 2100),
        _texto(datos, "color", "Color", 30, obligatorio=False),
        _entero(datos, "kilometraje", "Kilometraje", 0, 2_000_000, obligatorio=False) or 0,
        _opcion(datos, "combustible", "Combustible", COMBUSTIBLES),
        _entero(datos, "precio", "Precio", 1, 999_999_999),
        _texto(datos, "descripcion", "Descripción", 500, obligatorio=False),
        _opcion(datos, "estado", "Estado", ESTADOS_VEHICULO),
        _texto(datos, "etiqueta", "Etiqueta", 30, obligatorio=False),
    )
    imagen = _url(datos.get("imagen"))
    with conexion() as cur:
        if id_vehiculo is not None:
            # Si el auto tiene una venta reservada o cerrada, su estado lo manda esa venta.
            segun_ventas = _estado_por_ventas(cur, id_vehiculo)
            if segun_ventas and valores[9] != segun_ventas:
                raise DatosInvalidos(
                    f"Este auto tiene una venta en estado «{'Cerrada' if segun_ventas == 'Vendido' else 'Reservado'}», "
                    f"así que debe quedar como «{segun_ventas}». Para cambiarlo, edita o cancela la venta en «Ventas»."
                )
        cur.execute("SELECT ID_Marca FROM dbo.Marcas WHERE Nombre_Marca = ?", marca)
        fila = cur.fetchone()
        if fila:
            id_marca = fila[0]
        else:
            cur.execute("INSERT INTO dbo.Marcas (Nombre_Marca) OUTPUT INSERTED.ID_Marca VALUES (?)", marca)
            id_marca = cur.fetchone()[0]
        if id_vehiculo is None:
            cur.execute(
                """INSERT INTO dbo.Vehiculos (ID_Marca, Modelo, Version, Tipo, Anio, Color, Kilometraje,
                       Combustible, Precio, Descripcion, Estado, Etiqueta)
                   OUTPUT INSERTED.ID_Vehiculo VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                id_marca, *valores,
            )
            id_vehiculo = cur.fetchone()[0]
        else:
            cur.execute(
                """UPDATE dbo.Vehiculos SET ID_Marca=?, Modelo=?, Version=?, Tipo=?, Anio=?, Color=?,
                       Kilometraje=?, Combustible=?, Precio=?, Descripcion=?, Estado=?, Etiqueta=?
                   WHERE ID_Vehiculo=?""",
                id_marca, *valores, id_vehiculo,
            )
            if cur.rowcount == 0:
                raise DatosInvalidos("El vehículo ya no existe.")
        cur.execute("SELECT TOP 1 ID_Foto FROM dbo.Fotos_Vehiculos WHERE ID_Vehiculo=? ORDER BY ID_Foto", id_vehiculo)
        foto = cur.fetchone()
        if imagen and foto:
            cur.execute("UPDATE dbo.Fotos_Vehiculos SET Foto_URL=? WHERE ID_Foto=?", imagen, foto[0])
        elif imagen:
            cur.execute(
                "INSERT INTO dbo.Fotos_Vehiculos (ID_Vehiculo, Foto_URL, Descripcion) VALUES (?,?,?)",
                id_vehiculo, imagen, f"Fotografía {valores[0]}"[:150],
            )
        elif foto:
            cur.execute("DELETE FROM dbo.Fotos_Vehiculos WHERE ID_Vehiculo=?", id_vehiculo)
    return id_vehiculo


def metricas_vehiculos():
    """Vehículos con cuántos favoritos y consultas ha recibido cada uno (para el Estudio IA)."""
    sql = _SQL_VEHICULOS.replace(
        "AS imagen\n",
        """AS imagen,
       (SELECT COUNT(*) FROM dbo.Favoritos F WHERE F.ID_Vehiculo = V.ID_Vehiculo) AS favoritos,
       (SELECT COUNT(*) FROM dbo.Consultas Q WHERE Q.ID_Vehiculo = V.ID_Vehiculo) AS consultas
""",
    )
    with conexion() as cur:
        cur.execute(sql + " ORDER BY V.Fecha_Alta")
        return _filas(cur)


def actualizar_descripcion(id_vehiculo, descripcion):
    descripcion = _texto({"d": descripcion}, "d", "Descripción", 500)
    with conexion() as cur:
        cur.execute("UPDATE dbo.Vehiculos SET Descripcion=? WHERE ID_Vehiculo=?", descripcion, id_vehiculo)
        if cur.rowcount == 0:
            raise DatosInvalidos("El vehículo ya no existe.")


def eliminar_vehiculo(id_vehiculo):
    with conexion() as cur:
        cur.execute("SELECT COUNT(*) FROM dbo.Ventas WHERE ID_Vehiculo=?", id_vehiculo)
        if cur.fetchone()[0]:
            raise DatosInvalidos("Este vehículo tiene ventas registradas. Márcalo como «Vendido» en lugar de eliminarlo.")
        cur.execute("DELETE FROM dbo.Vehiculos WHERE ID_Vehiculo=?", id_vehiculo)


# ------------------------------------------------------------------ usuarios

def _clave(valor):
    valor = str(valor or "")
    if len(valor) < 8:
        raise DatosInvalidos("La contraseña debe tener al menos 8 caracteres.")
    if len(valor) > 128:
        raise DatosInvalidos("La contraseña es demasiado larga.")
    return generate_password_hash(valor)


def hay_administradores():
    with conexion() as cur:
        cur.execute("SELECT COUNT(*) FROM dbo.Usuarios WHERE Rol='admin'")
        return cur.fetchone()[0] > 0


def crear_usuario(nombre, correo, clave, rol="cliente", telefono=None):
    """Crea una cuenta. Los clientes también quedan registrados en la tabla Clientes."""
    nombre = _texto({"n": nombre}, "n", "Nombre", 100)
    correo = _correo(correo)
    telefono = _texto({"t": telefono}, "t", "Teléfono", 20, obligatorio=False)
    clave_hash = _clave(clave)
    if rol not in ("cliente", "admin"):
        raise DatosInvalidos("Rol no válido.")
    with conexion() as cur:
        cur.execute("SELECT 1 FROM dbo.Usuarios WHERE Correo=?", correo)
        if cur.fetchone():
            raise DatosInvalidos("Ya existe una cuenta con ese correo.")
        cur.execute(
            "INSERT INTO dbo.Usuarios (Nombre, Correo, Clave_Hash, Rol) OUTPUT INSERTED.ID_Usuario VALUES (?,?,?,?)",
            nombre, correo, clave_hash, rol,
        )
        id_usuario = cur.fetchone()[0]
        if rol == "cliente":
            id_cliente = _cliente_por_correo(cur, nombre, correo, telefono, origen="Web")
            cur.execute("UPDATE dbo.Clientes SET ID_Usuario=? WHERE ID_Cliente=?", id_usuario, id_cliente)
    return obtener_usuario(id_usuario)


def obtener_usuario(id_usuario):
    with conexion() as cur:
        cur.execute(
            """SELECT U.ID_Usuario AS id, U.Nombre AS nombre, U.Correo AS correo, U.Rol AS rol,
                      U.Fecha_Registro AS fecha_registro, C.Telefono AS telefono
               FROM dbo.Usuarios U LEFT JOIN dbo.Clientes C ON C.ID_Usuario = U.ID_Usuario
               WHERE U.ID_Usuario=?""",
            id_usuario,
        )
        return _fila(cur)


def autenticar(correo, clave, rol=None):
    """Devuelve el usuario si correo y contraseña coinciden; si no, None."""
    correo = str(correo or "").strip().lower()
    with conexion() as cur:
        cur.execute("SELECT ID_Usuario, Clave_Hash, Rol FROM dbo.Usuarios WHERE Correo=?", correo)
        fila = cur.fetchone()
    if not fila or not check_password_hash(fila.Clave_Hash, str(clave or "")):
        return None
    if rol and fila.Rol != rol:
        return None
    return obtener_usuario(fila.ID_Usuario)


def actualizar_perfil(id_usuario, nombre):
    nombre = _texto({"n": nombre}, "n", "Nombre", 100)
    with conexion() as cur:
        cur.execute("UPDATE dbo.Usuarios SET Nombre=? WHERE ID_Usuario=?", nombre, id_usuario)


def cambiar_clave(id_usuario, actual, nueva):
    with conexion() as cur:
        cur.execute("SELECT Clave_Hash FROM dbo.Usuarios WHERE ID_Usuario=?", id_usuario)
        fila = cur.fetchone()
        if not fila or not check_password_hash(fila[0], str(actual or "")):
            raise DatosInvalidos("La contraseña actual no es correcta.")
        cur.execute("UPDATE dbo.Usuarios SET Clave_Hash=? WHERE ID_Usuario=?", _clave(nueva), id_usuario)


def restablecer_clave(id_usuario):
    """Genera una contraseña temporal (para que el administrador se la dé al cliente)."""
    temporal = secrets.token_urlsafe(8)
    with conexion() as cur:
        cur.execute("UPDATE dbo.Usuarios SET Clave_Hash=? WHERE ID_Usuario=?", _clave(temporal), id_usuario)
        if cur.rowcount == 0:
            raise DatosInvalidos("La cuenta ya no existe.")
    return temporal


# ------------------------------------------------------------------ clientes

def _cliente_por_correo(cur, nombre, correo, telefono, origen):
    """Busca un cliente por correo o lo crea. Devuelve su id."""
    cur.execute("SELECT ID_Cliente FROM dbo.Clientes WHERE Correo=?", correo)
    fila = cur.fetchone()
    if fila:
        id_cliente = fila[0]
        if telefono:
            cur.execute("UPDATE dbo.Clientes SET Telefono=? WHERE ID_Cliente=? AND Telefono IS NULL", telefono, id_cliente)
    else:
        cur.execute(
            "INSERT INTO dbo.Clientes (Nombre, Correo, Telefono, Origen) OUTPUT INSERTED.ID_Cliente VALUES (?,?,?,?)",
            nombre, correo, telefono, origen,
        )
        id_cliente = cur.fetchone()[0]
    # Si existe una cuenta web con ese correo, se enlaza (así ve sus consultas en «Mi cuenta»).
    cur.execute(
        """UPDATE dbo.Clientes SET ID_Usuario = (SELECT ID_Usuario FROM dbo.Usuarios WHERE Correo=? AND Rol='cliente')
           WHERE ID_Cliente=? AND ID_Usuario IS NULL""",
        correo, id_cliente,
    )
    return id_cliente


def listar_clientes():
    with conexion() as cur:
        cur.execute(
            """SELECT C.ID_Cliente AS id, C.Nombre AS nombre, C.Correo AS correo, C.Telefono AS telefono,
                      C.Interes AS interes, C.Notas AS notas, C.Estado AS estado, C.Origen AS origen,
                      C.ID_Usuario AS id_usuario, C.Fecha_Alta AS fecha_alta,
                      (SELECT COUNT(*) FROM dbo.Consultas Q WHERE Q.ID_Cliente=C.ID_Cliente AND Q.Atendida=0) AS pendientes
               FROM dbo.Clientes C ORDER BY C.Fecha_Alta DESC, C.ID_Cliente DESC"""
        )
        return _filas(cur)


def guardar_cliente(datos, id_cliente=None):
    valores = (
        _texto(datos, "nombre", "Nombre", 100),
        _correo(datos.get("correo"), obligatorio=False),
        _texto(datos, "telefono", "Teléfono", 20, obligatorio=False),
        _texto(datos, "interes", "Vehículo de interés", 100, obligatorio=False),
        _texto(datos, "notas", "Notas", 500, obligatorio=False),
        _opcion(datos, "estado", "Estado", ESTADOS_CLIENTE),
    )
    with conexion() as cur:
        if valores[1]:
            cur.execute("SELECT ID_Cliente FROM dbo.Clientes WHERE Correo=?", valores[1])
            otro = cur.fetchone()
            if otro and otro[0] != id_cliente:
                raise DatosInvalidos("Ya hay otro cliente con ese correo.")
        if id_cliente is None:
            cur.execute(
                """INSERT INTO dbo.Clientes (Nombre, Correo, Telefono, Interes, Notas, Estado, Origen)
                   OUTPUT INSERTED.ID_Cliente VALUES (?,?,?,?,?,?,'Escritorio')""",
                *valores,
            )
            return cur.fetchone()[0]
        cur.execute(
            "UPDATE dbo.Clientes SET Nombre=?, Correo=?, Telefono=?, Interes=?, Notas=?, Estado=? WHERE ID_Cliente=?",
            *valores, id_cliente,
        )
        if cur.rowcount == 0:
            raise DatosInvalidos("El cliente ya no existe.")
        return id_cliente


def obtener_cliente(id_cliente):
    return next((c for c in listar_clientes() if c["id"] == id_cliente), None)


def eliminar_cliente(id_cliente):
    with conexion() as cur:
        cur.execute("SELECT COUNT(*) FROM dbo.Ventas WHERE ID_Cliente=?", id_cliente)
        if cur.fetchone()[0]:
            raise DatosInvalidos("Este cliente tiene ventas registradas y no se puede eliminar.")
        cur.execute("DELETE FROM dbo.Clientes WHERE ID_Cliente=?", id_cliente)


# ------------------------------------------------------------------ consultas

def registrar_consulta(nombre, correo, telefono=None, mensaje=None, id_vehiculo=None, tipo="Contacto"):
    nombre = _texto({"n": nombre}, "n", "Nombre", 100)
    correo = _correo(correo)
    telefono = _texto({"t": telefono}, "t", "Teléfono", 20, obligatorio=False)
    mensaje = _texto({"m": mensaje}, "m", "Mensaje", 1000, obligatorio=False)
    with conexion() as cur:
        if id_vehiculo is not None:
            cur.execute("SELECT Modelo FROM dbo.Vehiculos WHERE ID_Vehiculo=?", id_vehiculo)
            vehiculo = cur.fetchone()
            if not vehiculo:
                raise DatosInvalidos("El vehículo ya no está disponible.")
        id_cliente = _cliente_por_correo(cur, nombre, correo, telefono, origen="Web")
        if id_vehiculo is not None:
            cur.execute("UPDATE dbo.Clientes SET Interes=? WHERE ID_Cliente=?", vehiculo[0][:100], id_cliente)
        cur.execute(
            "INSERT INTO dbo.Consultas (ID_Cliente, ID_Vehiculo, Tipo, Mensaje) VALUES (?,?,?,?)",
            id_cliente, id_vehiculo, tipo, mensaje,
        )


def solicitar_recuperacion(correo):
    """Deja una solicitud para el administrador si existe una cuenta con ese correo."""
    correo = _correo(correo)
    with conexion() as cur:
        cur.execute(
            "SELECT C.ID_Cliente FROM dbo.Clientes C INNER JOIN dbo.Usuarios U ON U.ID_Usuario=C.ID_Usuario WHERE U.Correo=?",
            correo,
        )
        fila = cur.fetchone()
        if fila:
            cur.execute(
                "INSERT INTO dbo.Consultas (ID_Cliente, Tipo, Mensaje) VALUES (?, 'Recuperación', ?)",
                fila[0], "El cliente solicitó restablecer su contraseña desde la web.",
            )


def listar_consultas(solo_pendientes=False, id_usuario=None, limite=None):
    condiciones, parametros = [], []
    if solo_pendientes:
        condiciones.append("Q.Atendida = 0")
    if id_usuario is not None:
        condiciones.append("C.ID_Usuario = ?")
        parametros.append(id_usuario)
    top = f"TOP {int(limite)} " if limite else ""
    sql = f"""SELECT {top}Q.ID_Consulta AS id, Q.Tipo AS tipo, Q.Mensaje AS mensaje, Q.Atendida AS atendida,
                     Q.Fecha AS fecha, C.ID_Cliente AS id_cliente, C.Nombre AS cliente, C.Correo AS correo,
                     C.Telefono AS telefono, C.ID_Usuario AS id_usuario,
                     CASE WHEN V.ID_Vehiculo IS NULL THEN NULL ELSE CONCAT(M.Nombre_Marca, ' ', V.Modelo) END AS vehiculo
              FROM dbo.Consultas Q
              INNER JOIN dbo.Clientes C ON C.ID_Cliente = Q.ID_Cliente
              LEFT JOIN dbo.Vehiculos V ON V.ID_Vehiculo = Q.ID_Vehiculo
              LEFT JOIN dbo.Marcas M ON M.ID_Marca = V.ID_Marca"""
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY Q.Atendida, Q.Fecha DESC"
    with conexion() as cur:
        cur.execute(sql, parametros)
        return _filas(cur)


def contar_consultas_pendientes():
    with conexion() as cur:
        cur.execute("SELECT COUNT(*) FROM dbo.Consultas WHERE Atendida = 0")
        return cur.fetchone()[0]


def marcar_consulta(id_consulta, atendida=True):
    with conexion() as cur:
        cur.execute("UPDATE dbo.Consultas SET Atendida=? WHERE ID_Consulta=?", 1 if atendida else 0, id_consulta)


# ------------------------------------------------------------------ favoritos

def listar_favoritos(id_usuario):
    with conexion() as cur:
        cur.execute("SELECT ID_Vehiculo FROM dbo.Favoritos WHERE ID_Usuario=? ORDER BY Fecha DESC", id_usuario)
        return [fila[0] for fila in cur.fetchall()]


def cambiar_favorito(id_usuario, id_vehiculo, agregar):
    with conexion() as cur:
        if agregar:
            cur.execute("SELECT 1 FROM dbo.Vehiculos WHERE ID_Vehiculo=?", id_vehiculo)
            if not cur.fetchone():
                raise DatosInvalidos("El vehículo no existe.")
            cur.execute(
                """IF NOT EXISTS (SELECT 1 FROM dbo.Favoritos WHERE ID_Usuario=? AND ID_Vehiculo=?)
                   INSERT INTO dbo.Favoritos (ID_Usuario, ID_Vehiculo) VALUES (?, ?)""",
                id_usuario, id_vehiculo, id_usuario, id_vehiculo,
            )
        else:
            cur.execute("DELETE FROM dbo.Favoritos WHERE ID_Usuario=? AND ID_Vehiculo=?", id_usuario, id_vehiculo)


# ------------------------------------------------------------------ ventas

def listar_ventas():
    with conexion() as cur:
        cur.execute(
            """SELECT S.ID_Venta AS id, S.ID_Cliente AS id_cliente, C.Nombre AS cliente,
                      S.ID_Vehiculo AS id_vehiculo, CONCAT(M.Nombre_Marca, ' ', V.Modelo) AS vehiculo,
                      S.Precio_Acordado AS precio, S.Estado AS estado, S.Notas AS notas, S.Fecha AS fecha
               FROM dbo.Ventas S
               INNER JOIN dbo.Clientes C ON C.ID_Cliente = S.ID_Cliente
               INNER JOIN dbo.Vehiculos V ON V.ID_Vehiculo = S.ID_Vehiculo
               INNER JOIN dbo.Marcas M ON M.ID_Marca = V.ID_Marca
               ORDER BY S.Fecha DESC, S.ID_Venta DESC"""
        )
        return _filas(cur)


def _estado_por_ventas(cur, id_vehiculo):
    """'Vendido' si tiene una venta cerrada, 'Reservado' si tiene una reservada; si no, None."""
    cur.execute(
        """SELECT CASE WHEN EXISTS (SELECT 1 FROM dbo.Ventas WHERE ID_Vehiculo=? AND Estado='Cerrada') THEN 'Vendido'
                       WHEN EXISTS (SELECT 1 FROM dbo.Ventas WHERE ID_Vehiculo=? AND Estado='Reservado') THEN 'Reservado'
                  END""",
        id_vehiculo, id_vehiculo,
    )
    return cur.fetchone()[0]


def estado_por_ventas(id_vehiculo):
    with conexion() as cur:
        return _estado_por_ventas(cur, id_vehiculo)


def vehiculos_sin_venta():
    """Autos marcados como Vendido o Reservado que no tienen una venta que lo respalde."""
    with conexion() as cur:
        cur.execute(
            _SQL_VEHICULOS + """ WHERE (V.Estado = 'Vendido' AND NOT EXISTS
                                   (SELECT 1 FROM dbo.Ventas S WHERE S.ID_Vehiculo = V.ID_Vehiculo AND S.Estado = 'Cerrada'))
                                OR (V.Estado = 'Reservado' AND NOT EXISTS
                                   (SELECT 1 FROM dbo.Ventas S WHERE S.ID_Vehiculo = V.ID_Vehiculo AND S.Estado IN ('Reservado', 'Cerrada')))
                              ORDER BY V.ID_Vehiculo"""
        )
        return _filas(cur)


def _sincronizar_estado_vehiculo(cur, id_vehiculo):
    """El estado del vehículo sigue a sus ventas: cerrada → Vendido, reservada → Reservado."""
    cur.execute(
        """UPDATE dbo.Vehiculos SET Estado =
             CASE WHEN EXISTS (SELECT 1 FROM dbo.Ventas WHERE ID_Vehiculo=? AND Estado='Cerrada') THEN 'Vendido'
                  WHEN EXISTS (SELECT 1 FROM dbo.Ventas WHERE ID_Vehiculo=? AND Estado='Reservado') THEN 'Reservado'
                  ELSE 'Disponible' END
           WHERE ID_Vehiculo=?""",
        id_vehiculo, id_vehiculo, id_vehiculo,
    )


def guardar_venta(datos, id_venta=None):
    id_cliente = _entero(datos, "id_cliente", "Cliente", 1)
    id_vehiculo = _entero(datos, "id_vehiculo", "Vehículo", 1)
    precio = _entero(datos, "precio", "Precio acordado", 1, 999_999_999)
    estado = _opcion(datos, "estado", "Estado", ESTADOS_VENTA)
    notas = _texto(datos, "notas", "Notas", 500, obligatorio=False)
    with conexion() as cur:
        if estado in ("Reservado", "Cerrada"):
            cur.execute(
                """SELECT 1 FROM dbo.Ventas WHERE ID_Vehiculo=? AND Estado IN ('Reservado','Cerrada')
                   AND ID_Venta <> ISNULL(?, 0)""",
                id_vehiculo, id_venta,
            )
            if cur.fetchone():
                raise DatosInvalidos("Ese vehículo ya está reservado o vendido en otra operación.")
        anterior = None
        if id_venta is None:
            cur.execute(
                """INSERT INTO dbo.Ventas (ID_Cliente, ID_Vehiculo, Precio_Acordado, Estado, Notas)
                   OUTPUT INSERTED.ID_Venta VALUES (?,?,?,?,?)""",
                id_cliente, id_vehiculo, precio, estado, notas,
            )
            id_venta = cur.fetchone()[0]
        else:
            cur.execute("SELECT ID_Vehiculo FROM dbo.Ventas WHERE ID_Venta=?", id_venta)
            fila = cur.fetchone()
            if not fila:
                raise DatosInvalidos("La venta ya no existe.")
            anterior = fila[0]
            cur.execute(
                "UPDATE dbo.Ventas SET ID_Cliente=?, ID_Vehiculo=?, Precio_Acordado=?, Estado=?, Notas=? WHERE ID_Venta=?",
                id_cliente, id_vehiculo, precio, estado, notas, id_venta,
            )
        _sincronizar_estado_vehiculo(cur, id_vehiculo)
        if anterior and anterior != id_vehiculo:
            _sincronizar_estado_vehiculo(cur, anterior)
        if estado == "Cerrada":
            cur.execute("UPDATE dbo.Clientes SET Estado='Cliente' WHERE ID_Cliente=?", id_cliente)
    return id_venta


def eliminar_venta(id_venta):
    with conexion() as cur:
        cur.execute("SELECT ID_Vehiculo FROM dbo.Ventas WHERE ID_Venta=?", id_venta)
        fila = cur.fetchone()
        if not fila:
            return
        cur.execute("DELETE FROM dbo.Ventas WHERE ID_Venta=?", id_venta)
        _sincronizar_estado_vehiculo(cur, fila[0])


# ------------------------------------------------------------------ resumen

def resumen():
    with conexion() as cur:
        cur.execute(
            """SELECT
                 (SELECT COUNT(*) FROM dbo.Vehiculos WHERE Estado <> 'Vendido') AS inventario,
                 (SELECT COUNT(*) FROM dbo.Vehiculos WHERE Estado <> 'Vendido'
                    AND Fecha_Alta >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) AS inventario_mes,
                 (SELECT ISNULL(SUM(Precio), 0) FROM dbo.Vehiculos WHERE Estado <> 'Vendido') AS valor_inventario,
                 (SELECT COUNT(*) FROM dbo.Clientes) AS clientes,
                 (SELECT COUNT(*) FROM dbo.Clientes
                    WHERE Fecha_Alta >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) AS clientes_mes,
                 (SELECT COUNT(*) FROM dbo.Ventas WHERE Estado='Cerrada'
                    AND Fecha >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) AS ventas_mes,
                 (SELECT COUNT(*) FROM dbo.Ventas WHERE Estado='Cerrada'
                    AND Fecha >= DATEADD(MONTH, -1, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1))
                    AND Fecha <  DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) AS ventas_mes_anterior,
                 (SELECT COUNT(*) FROM dbo.Consultas WHERE Atendida = 0) AS consultas_pendientes,
                 (SELECT COUNT(*) FROM dbo.Usuarios WHERE Rol='cliente') AS cuentas_web"""
        )
        return _fila(cur)
