"""Pruebas de integración: web y escritorio sobre la misma base de datos.

Usan una base de datos aparte (MOTORHAUS_PRUEBAS) que se crea y se borra
en cada ejecución, así nunca tocan los datos reales.

Ejecutar desde la carpeta del proyecto:  python -m unittest discover tests
"""

import os
import secrets
import unittest

os.environ["MOTORHAUS_DB_NOMBRE"] = "MOTORHAUS_PRUEBAS"

from comun import db  # noqa: E402
from servidor.app import app  # noqa: E402


def _borrar_bd():
    con = db._abrir("master", autocommit=True)
    try:
        con.cursor().execute(
            "IF DB_ID('MOTORHAUS_PRUEBAS') IS NOT NULL BEGIN "
            "ALTER DATABASE MOTORHAUS_PRUEBAS SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
            "DROP DATABASE MOTORHAUS_PRUEBAS; END"
        )
    finally:
        con.close()


def setUpModule():
    _borrar_bd()
    db.inicializar()


def tearDownModule():
    _borrar_bd()


VEHICULO = {
    "marca": "Mazda", "modelo": "CX-5", "version": "i Grand Touring", "tipo": "SUV", "anio": "2024",
    "color": "Rojo", "kilometraje": "1,200", "combustible": "Gasolina", "precio": "$650,000",
    "estado": "Disponible", "etiqueta": "OFERTA", "imagen": "https://example.com/cx5.jpg", "descripcion": "Prueba",
}


class WebYEscritorioTests(unittest.TestCase):
    def setUp(self):
        self.web = app.test_client()

    def test_inicializar_es_repetible(self):
        antes = len(db.listar_vehiculos())
        db.inicializar()
        self.assertEqual(len(db.listar_vehiculos()), antes)

    def test_vehiculo_del_escritorio_aparece_en_la_web(self):
        id_vehiculo = db.guardar_vehiculo(VEHICULO)
        publicos = {v["id"]: v for v in self.web.get("/api/vehiculos").get_json()["vehiculos"]}
        self.assertIn(id_vehiculo, publicos)
        self.assertEqual(publicos[id_vehiculo]["precio"], 650000)
        self.assertEqual(publicos[id_vehiculo]["kilometraje"], 1200)
        self.assertEqual(publicos[id_vehiculo]["imagen"], VEHICULO["imagen"])

        db.guardar_vehiculo({**VEHICULO, "estado": "Vendido"}, id_vehiculo)
        publicos = [v["id"] for v in self.web.get("/api/vehiculos").get_json()["vehiculos"]]
        self.assertNotIn(id_vehiculo, publicos)
        db.eliminar_vehiculo(id_vehiculo)
        self.assertIsNone(db.obtener_vehiculo(id_vehiculo))

    def test_validacion_de_vehiculo(self):
        with self.assertRaises(db.DatosInvalidos):
            db.guardar_vehiculo({**VEHICULO, "precio": "abc"})
        with self.assertRaises(db.DatosInvalidos):
            db.guardar_vehiculo({**VEHICULO, "imagen": "javascript:alert(1)"})

    def test_registro_web_crea_cliente_visible_en_escritorio(self):
        clave = secrets.token_urlsafe(12)
        respuesta = self.web.post("/api/registro", json={"nombre": "Ana Web", "correo": "ana@motorhaus.test", "clave": clave, "telefono": "6311112222"})
        self.assertEqual(respuesta.status_code, 201)
        cliente = next(c for c in db.listar_clientes() if c["correo"] == "ana@motorhaus.test")
        self.assertEqual(cliente["origen"], "Web")
        self.assertIsNotNone(cliente["id_usuario"])

        self.assertEqual(self.web.post("/api/registro", json={"nombre": "Ana", "correo": "ana@motorhaus.test", "clave": clave}).status_code, 400)
        self.assertEqual(self.web.post("/api/login", json={"correo": "ana@motorhaus.test", "clave": "mala-clave"}).status_code, 401)

        # El administrador restablece la clave desde el escritorio y el cliente entra con ella.
        temporal = db.restablecer_clave(cliente["id_usuario"])
        otra = app.test_client()
        self.assertEqual(otra.post("/api/login", json={"correo": "ana@motorhaus.test", "clave": temporal}).status_code, 200)

    def test_favoritos_requieren_sesion_y_se_guardan(self):
        id_vehiculo = db.listar_vehiculos()[0]["id"]
        self.assertEqual(self.web.put(f"/api/favoritos/{id_vehiculo}").status_code, 401)
        self.web.post("/api/registro", json={"nombre": "Fav", "correo": "fav@motorhaus.test", "clave": secrets.token_urlsafe(12)})
        self.assertEqual(self.web.put(f"/api/favoritos/{id_vehiculo}").get_json()["favoritos"], [id_vehiculo])
        self.assertEqual(self.web.get("/api/sesion").get_json()["favoritos"], [id_vehiculo])
        self.assertEqual(self.web.delete(f"/api/favoritos/{id_vehiculo}").get_json()["favoritos"], [])

    def test_consulta_web_llega_al_escritorio(self):
        id_vehiculo = db.listar_vehiculos()[0]["id"]
        respuesta = self.web.post("/api/consultas", json={"nombre": "Luis", "correo": "luis@motorhaus.test", "mensaje": "¿Sigue disponible?", "id_vehiculo": id_vehiculo})
        self.assertEqual(respuesta.status_code, 201)
        consulta = next(c for c in db.listar_consultas(solo_pendientes=True) if c["correo"] == "luis@motorhaus.test")
        self.assertEqual(consulta["tipo"], "Consulta de vehículo")
        db.marcar_consulta(consulta["id"])
        self.assertFalse(any(c["id"] == consulta["id"] for c in db.listar_consultas(solo_pendientes=True)))

    def test_api_exige_json(self):
        self.assertEqual(self.web.post("/api/login", data={"correo": "x"}).status_code, 415)

    def test_ventas_cambian_el_estado_del_vehiculo(self):
        id_vehiculo = db.guardar_vehiculo(VEHICULO)
        id_cliente = db.guardar_cliente({"nombre": "Mostrador", "estado": "Nuevo contacto"})
        venta = {"id_cliente": id_cliente, "id_vehiculo": id_vehiculo, "precio": "640000", "estado": "Reservado"}
        id_venta = db.guardar_venta(venta)
        self.assertEqual(db.obtener_vehiculo(id_vehiculo)["estado"], "Reservado")
        with self.assertRaises(db.DatosInvalidos):
            db.guardar_venta(venta)  # no se puede reservar dos veces
        db.guardar_venta({**venta, "estado": "Cerrada"}, id_venta)
        self.assertEqual(db.obtener_vehiculo(id_vehiculo)["estado"], "Vendido")
        with self.assertRaises(db.DatosInvalidos):
            db.eliminar_vehiculo(id_vehiculo)
        db.eliminar_venta(id_venta)
        self.assertEqual(db.obtener_vehiculo(id_vehiculo)["estado"], "Disponible")
        db.eliminar_vehiculo(id_vehiculo)
        db.eliminar_cliente(id_cliente)


class VentaYEstadoTests(unittest.TestCase):
    def test_auto_marcado_vendido_a_mano_se_detecta_y_se_registra(self):
        # Caso reportado: el auto se marcó «Vendido» en Inventario y no aparecía en Ventas.
        id_vehiculo = db.guardar_vehiculo({**VEHICULO, "estado": "Vendido"})
        self.assertIn(id_vehiculo, [v["id"] for v in db.vehiculos_sin_venta()])
        id_cliente = db.guardar_cliente({"nombre": "Comprador", "estado": "Nuevo contacto"})
        id_venta = db.guardar_venta({"id_cliente": id_cliente, "id_vehiculo": id_vehiculo, "precio": "650000", "estado": "Cerrada"})
        self.assertIn(id_venta, [s["id"] for s in db.listar_ventas()])
        self.assertNotIn(id_vehiculo, [v["id"] for v in db.vehiculos_sin_venta()])
        self.assertEqual(db.obtener_vehiculo(id_vehiculo)["estado"], "Vendido")
        db.eliminar_venta(id_venta)
        db.eliminar_vehiculo(id_vehiculo)
        db.eliminar_cliente(id_cliente)

    def test_estado_con_venta_no_se_cambia_a_mano(self):
        id_vehiculo = db.guardar_vehiculo(VEHICULO)
        id_cliente = db.guardar_cliente({"nombre": "Apartado", "estado": "Nuevo contacto"})
        id_venta = db.guardar_venta({"id_cliente": id_cliente, "id_vehiculo": id_vehiculo, "precio": "640000", "estado": "Reservado"})
        self.assertEqual(db.estado_por_ventas(id_vehiculo), "Reservado")
        with self.assertRaises(db.DatosInvalidos):
            db.guardar_vehiculo({**VEHICULO, "estado": "Disponible"}, id_vehiculo)
        db.guardar_vehiculo({**VEHICULO, "estado": "Reservado", "precio": "660000"}, id_vehiculo)  # otros cambios sí
        self.assertEqual(db.obtener_vehiculo(id_vehiculo)["precio"], 660000)
        db.eliminar_venta(id_venta)
        self.assertIsNone(db.estado_por_ventas(id_vehiculo))
        db.eliminar_vehiculo(id_vehiculo)
        db.eliminar_cliente(id_cliente)


class EstudioIATests(unittest.TestCase):
    def test_prompts_usan_datos_reales(self):
        from comun import ia

        vehiculo = db.listar_vehiculos()[0]
        for enfoque in ia.ENFOQUES_INVENTARIO:
            self.assertIn(vehiculo["modelo"], ia.prompt_inventario(enfoque, "Priorizar SUV"))
        anuncio = ia.prompt_anuncio(vehiculo["id"], ia.TONOS[0], "Redes sociales", "Garantía de agencia")
        self.assertIn(f"{vehiculo['precio']:,}", anuncio)
        self.assertIn("Garantía de agencia", anuncio)
        for periodo in ia.PERIODOS:
            self.assertIn("Clientes por estado", ia.prompt_ventas(periodo))
        with self.assertRaises(db.DatosInvalidos):
            ia.prompt_anuncio(999999, ia.TONOS[0], ia.CANALES[0])

    def test_limpiar_markdown(self):
        from comun import ia

        self.assertEqual(ia.limpiar_markdown("## Título\n**Hola** mundo\n* uno"), "Título\nHola mundo\n- uno")

    def test_error_claro_si_ollama_no_responde(self):
        from comun import config, ia

        original = config.IA_URL
        config.IA_URL = "http://127.0.0.1:9"
        self.addCleanup(setattr, config, "IA_URL", original)
        with self.assertRaises(ia.IANoDisponible):
            ia.modelos()
        with self.assertRaises(ia.IANoDisponible):
            list(ia.generar("hola"))

    def test_anuncio_publicado_aparece_en_la_web(self):
        id_vehiculo = db.listar_vehiculos()[0]["id"]
        db.actualizar_descripcion(id_vehiculo, "Anuncio generado por IA")
        self.assertEqual(app.test_client().get(f"/api/vehiculos/{id_vehiculo}").get_json()["descripcion"], "Anuncio generado por IA")
        with self.assertRaises(db.DatosInvalidos):
            db.actualizar_descripcion(id_vehiculo, "x" * 501)


class EscritorioTests(unittest.TestCase):
    def test_acceso_y_todas_las_pantallas(self):
        import customtkinter as ctk
        from escritorio.app import MotorhausApp

        ctk.set_appearance_mode("light")
        clave = secrets.token_urlsafe(12)
        if not db.autenticar("admin@motorhaus.test", clave, rol="admin"):
            try:
                db.crear_usuario("Admin Pruebas", "admin@motorhaus.test", clave, rol="admin")
            except db.DatosInvalidos:
                pass
        usuario = db.autenticar("admin@motorhaus.test", clave, rol="admin")
        self.assertIsNotNone(usuario)

        ventana = MotorhausApp()
        self.addCleanup(ventana.destroy)
        ventana.update()
        self.assertIsNotNone(ventana.access_container)
        self.assertFalse(ventana.sidebar.winfo_ismapped())

        ventana.login(usuario)
        ventana.update()
        self.assertIsNone(ventana.access_container)
        self.assertTrue(ventana.sidebar.winfo_ismapped())

        id_vehiculo = db.listar_vehiculos()[0]["id"]
        id_cliente = db.guardar_cliente({"nombre": "Pantallas", "estado": "Nuevo contacto"})
        id_venta = db.guardar_venta({"id_cliente": id_cliente, "id_vehiculo": id_vehiculo, "precio": "1", "estado": "En seguimiento"})
        pantallas = [("Resumen",), ("Inventario",), ("Vehículo",), ("Vehículo", id_vehiculo), ("Clientes",),
                     ("Cliente",), ("Cliente", id_cliente), ("Ventas",), ("Venta",), ("Venta", id_venta),
                     ("Venta", None, id_vehiculo, "Cerrada"),
                     ("Estudio IA",), ("Análisis de inventario",), ("Contenido para anuncios",),
                     ("Contenido para anuncios", id_vehiculo), ("Perspectivas de ventas",),
                     ("Lanzador",), ("Configuración",)]
        for pantalla in pantallas:
            with self.subTest(pantalla=pantalla):
                ventana.show_page(*pantalla)
                ventana.update()
                self.assertEqual(ventana.current_page, pantalla[0])
        db.eliminar_venta(id_venta)
        db.eliminar_cliente(id_cliente)

        ventana.logout()
        ventana.update()
        self.assertFalse(ventana.sidebar.winfo_ismapped())


if __name__ == "__main__":
    unittest.main()
