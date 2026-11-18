"""Estudio IA: herramientas que usan un modelo local de Ollama.

Los datos se leen de la base MOTORHAUS y se envían únicamente al Ollama
configurado (por defecto, el de esta misma computadora).
"""

from datetime import datetime, timedelta
import json
import re
import urllib.error
import urllib.request

from comun import config, db

SISTEMA = (
    "Eres el asistente comercial de Motorhaus, una agencia de autos seminuevos premium en México. "
    "Respondes siempre en español de México, con frases claras y concretas. "
    "Los precios están en pesos mexicanos (MXN). Usa solo los datos que se te dan; "
    "si algo no se puede saber con esos datos, dilo en lugar de inventarlo. "
    "No uses tablas ni Markdown complejo: usa títulos cortos y viñetas con guion (-)."
)

ENFOQUES_INVENTARIO = ["Inventario completo", "Vehículos que necesitan atención", "Precios y valor del inventario"]
TONOS = ["Elegante", "Deportivo", "Familiar", "Directo y breve"]
CANALES = ["Tienda web", "Redes sociales", "Marketplace"]
PERIODOS = {"Últimos 30 días": 30, "Últimos 90 días": 90, "Todo el historial": None}


class IANoDisponible(RuntimeError):
    """No se pudo hablar con Ollama."""


# ------------------------------------------------------------------ Ollama

def _peticion(ruta, datos=None, timeout=10):
    cuerpo = json.dumps(datos).encode("utf-8") if datos is not None else None
    req = urllib.request.Request(f"{config.IA_URL}{ruta}", data=cuerpo,
                                 headers={"Content-Type": "application/json"} if cuerpo else {})
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", "replace")
        try:
            detalle = json.loads(detalle).get("error", detalle)
        except ValueError:
            pass
        raise IANoDisponible(f"Ollama respondió con un error: {detalle}") from error
    except OSError as error:
        raise IANoDisponible(
            f"No se pudo conectar con Ollama en {config.IA_URL}. "
            "Abre la aplicación Ollama (o ejecuta «ollama serve») y vuelve a intentar."
        ) from error


def modelos():
    """Nombres de los modelos instalados en Ollama."""
    with _peticion("/api/tags", timeout=3) as respuesta:
        datos = json.load(respuesta)
    return sorted(m["name"] for m in datos.get("models", []))


def generar(prompt, modelo=None, detener=None):
    """Genera texto con streaming: devuelve un iterador de fragmentos.

    ``detener`` es una función opcional; si devuelve True se corta la generación.
    """
    datos = {
        "model": modelo or config.IA_MODELO,
        "stream": True,
        "think": False,
        "options": {"temperature": 0.6, "num_ctx": 4096},
        "messages": [{"role": "system", "content": SISTEMA}, {"role": "user", "content": prompt}],
    }
    with _peticion("/api/chat", datos, timeout=300) as respuesta:
        for linea in respuesta:
            if detener and detener():
                return
            if not linea.strip():
                continue
            parte = json.loads(linea)
            if parte.get("error"):
                raise IANoDisponible(parte["error"])
            texto = parte.get("message", {}).get("content", "")
            if texto:
                yield texto
            if parte.get("done"):
                return


def limpiar_markdown(texto):
    """Quita negritas, encabezados y viñetas de Markdown para mostrar texto plano."""
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"__(.+?)__", r"\1", texto)
    texto = re.sub(r"^#{1,6}\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^(\s*)[*•]\s+", r"\1- ", texto, flags=re.MULTILINE)
    return texto.strip()


# ------------------------------------------------------------------ prompts

def _dias(fecha):
    return max((datetime.now() - fecha).days, 0) if fecha else 0


def _linea_vehiculo(v):
    return (f"- #{v['id']} {v['marca']} {v['modelo']} {v['version'] or ''} {v['anio']} · {v['tipo']} · "
            f"{v['kilometraje']:,} km · ${v['precio']:,} · {v['estado']} · {_dias(v['fecha_alta'])} días en inventario · "
            f"{v['favoritos']} favoritos · {v['consultas']} consultas").replace("  ", " ")


def prompt_inventario(enfoque, notas=""):
    vehiculos = db.metricas_vehiculos()
    activos = [v for v in vehiculos if v["estado"] != "Vendido"]
    if not activos:
        raise db.DatosInvalidos("No hay vehículos en inventario para analizar.")
    instrucciones = {
        "Inventario completo": "Haz un diagnóstico general del inventario: mezcla de tipos y precios, qué autos generan más interés y cuáles menos, y 3 a 5 acciones recomendadas.",
        "Vehículos que necesitan atención": "Identifica los vehículos que necesitan atención (muchos días en inventario, poco interés, reservados sin cerrar) y para cada uno propone una acción concreta.",
        "Precios y valor del inventario": "Analiza los precios: rango, valor total, autos que parecen caros o baratos para su año y kilometraje en comparación con el resto, y sugerencias de ajuste prudentes.",
    }[enfoque]
    valor = sum(v["precio"] for v in activos)
    return (
        f"{instrucciones}\n\n"
        f"Inventario actual ({len(activos)} vehículos, valor total ${valor:,} MXN):\n"
        + "\n".join(_linea_vehiculo(v) for v in activos)
        + (f"\n\nIndicaciones adicionales del administrador: {notas}" if notas.strip() else "")
    )


def prompt_anuncio(id_vehiculo, tono, canal, destacar=""):
    v = db.obtener_vehiculo(id_vehiculo)
    if not v:
        raise db.DatosInvalidos("El vehículo ya no existe.")
    extension = {
        "Tienda web": "un párrafo de 60 a 90 palabras, sin emojis ni hashtags",
        "Redes sociales": "un texto de 40 a 70 palabras con 2 o 3 emojis y 3 hashtags al final",
        "Marketplace": "un título de una línea y debajo 4 viñetas con los datos clave",
    }[canal]
    return (
        f"Escribe el anuncio de venta de este vehículo para {canal.lower()}: {extension}. "
        f"Tono: {tono.lower()}. Escribe solo el anuncio, sin explicaciones ni comillas.\n\n"
        f"Vehículo: {v['marca']} {v['modelo']} {v['version'] or ''} {v['anio']}\n"
        f"Tipo: {v['tipo']} · Color: {v['color'] or 'no indicado'} · {v['kilometraje']:,} km · {v['combustible']}\n"
        f"Precio: ${v['precio']:,} MXN\n"
        f"Descripción actual: {v['descripcion'] or 'sin descripción'}"
        + (f"\nDestacar: {destacar}" if destacar.strip() else "")
    )


def prompt_ventas(periodo, objetivo=""):
    dias = PERIODOS[periodo]
    desde = datetime.now() - timedelta(days=dias) if dias else None
    en_periodo = (lambda f: desde is None or f >= desde)
    ventas = [s for s in db.listar_ventas() if en_periodo(s["fecha"])]
    consultas = [c for c in db.listar_consultas() if en_periodo(c["fecha"])]
    clientes = db.listar_clientes()
    vehiculos = db.metricas_vehiculos()

    def conteo(items, clave):
        resultado = {}
        for item in items:
            resultado[item[clave] or "sin dato"] = resultado.get(item[clave] or "sin dato", 0) + 1
        return ", ".join(f"{k}: {n}" for k, n in sorted(resultado.items(), key=lambda x: -x[1])) or "ninguno"

    interes = sorted((v for v in vehiculos if v["estado"] != "Vendido"), key=lambda v: -(v["favoritos"] + v["consultas"]))[:5]
    cerradas = [s for s in ventas if s["estado"] == "Cerrada"]
    return (
        f"Analiza el desempeño comercial de Motorhaus ({periodo.lower()}) y da: un resumen de 2 o 3 frases, "
        "3 a 5 oportunidades concretas de venta (menciona clientes o autos cuando aplique) y 2 riesgos a vigilar.\n\n"
        f"Ventas registradas: {len(ventas)} ({conteo(ventas, 'estado')}). "
        f"Monto cerrado: ${sum(s['precio'] for s in cerradas):,} MXN.\n"
        + "".join(f"- {s['vehiculo']} con {s['cliente']}: ${s['precio']:,}, {s['estado']}\n" for s in ventas[:15])
        + f"\nConsultas desde la web: {len(consultas)} ({conteo(consultas, 'tipo')}); "
        f"sin atender: {sum(1 for c in consultas if not c['atendida'])}.\n"
        + "".join(f"- {c['cliente']} preguntó por {c['vehiculo'] or 'información general'} ({'atendida' if c['atendida'] else 'pendiente'})\n" for c in consultas[:10])
        + f"\nClientes por estado: {conteo(clientes, 'estado')}. Por origen: {conteo(clientes, 'origen')}.\n"
        "Autos con más interés (favoritos + consultas):\n"
        + "\n".join(_linea_vehiculo(v) for v in interes)
        + (f"\n\nObjetivo del administrador: {objetivo}" if objetivo.strip() else "")
    )
