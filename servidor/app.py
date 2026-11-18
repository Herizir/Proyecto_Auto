"""Servidor de la tienda web Motorhaus.

Sirve las páginas de ``web/`` y una API JSON en ``/api`` que lee y escribe
en la misma base de datos que usa la app de escritorio.

Ejecutar desde la carpeta del proyecto:  python servidor/app.py
"""

from datetime import timedelta
from functools import wraps
from pathlib import Path
import secrets
import sys

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from flask import Flask, abort, jsonify, request, send_from_directory, session  # noqa: E402

from comun import config, db  # noqa: E402

WEB = RAIZ / "web"


def _secreto():
    if config.WEB_SECRETO:
        return config.WEB_SECRETO
    archivo = RAIZ / ".secreto"
    if not archivo.is_file():
        archivo.write_text(secrets.token_hex(32), encoding="utf-8")
    return archivo.read_text(encoding="utf-8").strip()


app = Flask(__name__, static_folder=None)
app.config.update(
    SECRET_KEY=_secreto(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    JSON_AS_ASCII=False,
)


# ------------------------------------------------------------------ utilidades

def _json():
    """Lee el cuerpo JSON. Exigir JSON evita que otros sitios envíen formularios a la API."""
    if not request.is_json:
        abort(415)
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        abort(400)
    return datos


def _usuario_actual():
    id_usuario = session.get("usuario")
    if not id_usuario:
        return None
    usuario = db.obtener_usuario(id_usuario)
    if not usuario:
        session.clear()
    return usuario


def requiere_sesion(funcion):
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        usuario = _usuario_actual()
        if not usuario:
            return jsonify(error="Inicia sesión para continuar."), 401
        return funcion(usuario, *args, **kwargs)
    return envoltura


def _publico(vehiculo):
    """Solo los campos que la tienda necesita mostrar."""
    campos = ("id", "marca", "modelo", "version", "tipo", "anio", "color", "kilometraje",
              "combustible", "precio", "descripcion", "estado", "etiqueta", "imagen")
    return {campo: vehiculo[campo] for campo in campos}


def _usuario_json(usuario):
    return {"id": usuario["id"], "nombre": usuario["nombre"], "correo": usuario["correo"],
            "telefono": usuario.get("telefono"), "rol": usuario["rol"]}


@app.errorhandler(db.DatosInvalidos)
def _datos_invalidos(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(db.SinConexion)
def _sin_conexion(error):
    app.logger.error("Sin conexión a la base de datos: %s", error)
    return jsonify(error="La tienda no puede conectarse a la base de datos en este momento."), 503


@app.errorhandler(415)
def _no_json(_error):
    return jsonify(error="La solicitud debe enviarse como JSON."), 415


@app.errorhandler(400)
def _peticion_mala(_error):
    return jsonify(error="Solicitud no válida."), 400


# ------------------------------------------------------------------ páginas

@app.get("/")
def inicio():
    return send_from_directory(WEB, "index.html")


@app.get("/<path:ruta>")
def archivos(ruta):
    if ruta.startswith("api/"):
        abort(404)
    return send_from_directory(WEB, ruta)


# ------------------------------------------------------------------ catálogo

@app.get("/api/vehiculos")
def api_vehiculos():
    tipo = request.args.get("tipo") or None
    if tipo == "todos":
        tipo = None
    orden = request.args.get("orden")
    vehiculos = db.listar_vehiculos(solo_publicos=True, tipo=tipo, orden=orden)
    return jsonify(vehiculos=[_publico(v) for v in vehiculos], tipos=db.TIPOS)


@app.get("/api/vehiculos/<int:id_vehiculo>")
def api_vehiculo(id_vehiculo):
    vehiculo = db.obtener_vehiculo(id_vehiculo)
    if not vehiculo or vehiculo["estado"] == "Vendido":
        return jsonify(error="Vehículo no encontrado."), 404
    return jsonify(_publico(vehiculo))


# ------------------------------------------------------------------ cuentas

@app.get("/api/sesion")
def api_sesion():
    usuario = _usuario_actual()
    if not usuario:
        return jsonify(usuario=None, favoritos=[])
    return jsonify(usuario=_usuario_json(usuario), favoritos=db.listar_favoritos(usuario["id"]))


@app.post("/api/registro")
def api_registro():
    datos = _json()
    usuario = db.crear_usuario(datos.get("nombre"), datos.get("correo"), datos.get("clave"),
                               rol="cliente", telefono=datos.get("telefono"))
    session.clear()
    session.permanent = True
    session["usuario"] = usuario["id"]
    return jsonify(usuario=_usuario_json(usuario)), 201


@app.post("/api/login")
def api_login():
    datos = _json()
    usuario = db.autenticar(datos.get("correo"), datos.get("clave"))
    if not usuario:
        return jsonify(error="Correo o contraseña incorrectos."), 401
    session.clear()
    session.permanent = True
    session["usuario"] = usuario["id"]
    return jsonify(usuario=_usuario_json(usuario))


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)


@app.post("/api/recuperar")
def api_recuperar():
    datos = _json()
    db.solicitar_recuperacion(datos.get("correo"))
    # Misma respuesta exista o no la cuenta, para no revelar qué correos están registrados.
    return jsonify(mensaje="Si el correo tiene una cuenta, el equipo de Motorhaus te contactará para restablecer tu acceso.")


@app.get("/api/cuenta")
@requiere_sesion
def api_cuenta(usuario):
    favoritos = db.listar_favoritos(usuario["id"])
    vehiculos = [db.obtener_vehiculo(i) for i in favoritos]
    return jsonify(
        usuario=_usuario_json(usuario),
        favoritos=[_publico(v) for v in vehiculos if v],
        consultas=[{"tipo": c["tipo"], "vehiculo": c["vehiculo"], "mensaje": c["mensaje"],
                    "atendida": bool(c["atendida"]), "fecha": c["fecha"].isoformat()}
                   for c in db.listar_consultas(id_usuario=usuario["id"])],
    )


@app.post("/api/cuenta/clave")
@requiere_sesion
def api_cambiar_clave(usuario):
    datos = _json()
    db.cambiar_clave(usuario["id"], datos.get("actual"), datos.get("nueva"))
    return jsonify(mensaje="Contraseña actualizada.")


# ------------------------------------------------------------------ favoritos

@app.put("/api/favoritos/<int:id_vehiculo>")
@requiere_sesion
def api_agregar_favorito(usuario, id_vehiculo):
    db.cambiar_favorito(usuario["id"], id_vehiculo, True)
    return jsonify(favoritos=db.listar_favoritos(usuario["id"]))


@app.delete("/api/favoritos/<int:id_vehiculo>")
@requiere_sesion
def api_quitar_favorito(usuario, id_vehiculo):
    db.cambiar_favorito(usuario["id"], id_vehiculo, False)
    return jsonify(favoritos=db.listar_favoritos(usuario["id"]))


# ------------------------------------------------------------------ contacto

@app.post("/api/consultas")
def api_consulta():
    datos = _json()
    id_vehiculo = datos.get("id_vehiculo")
    if id_vehiculo is not None:
        try:
            id_vehiculo = int(id_vehiculo)
        except (TypeError, ValueError):
            raise db.DatosInvalidos("Vehículo no válido.") from None
    db.registrar_consulta(
        nombre=datos.get("nombre"), correo=datos.get("correo"), telefono=datos.get("telefono"),
        mensaje=datos.get("mensaje"), id_vehiculo=id_vehiculo,
        tipo="Consulta de vehículo" if id_vehiculo else "Contacto",
    )
    return jsonify(mensaje="¡Gracias! Recibimos tu mensaje y te contactaremos pronto."), 201


def main():
    try:
        db.inicializar()
    except db.SinConexion as error:
        print(f"\nNo se pudo iniciar la tienda.\n{error}\n")
        sys.exit(1)
    print(f"Motorhaus web en {config.WEB_URL}  (Ctrl+C para detener)")
    app.run(host="127.0.0.1", port=config.WEB_PUERTO, debug=False, threaded=True)


if __name__ == "__main__":
    main()
