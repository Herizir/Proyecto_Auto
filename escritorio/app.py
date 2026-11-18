"""Panel de escritorio de Motorhaus.

Trabaja sobre la misma base de datos SQL Server que la tienda web: lo que
se registra aquí aparece en la web y viceversa.

Ejecutar desde la carpeta del proyecto:  python escritorio/app.py
"""

from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from tkinter import messagebox
import urllib.request
import webbrowser

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import customtkinter as ctk  # noqa: E402

from comun import config, db, ia  # noqa: E402

BG = "#f4f6ef"
WHITE = "#ffffff"
DARK = "#171d18"
SIDEBAR = "#111612"
MUTED = "#7e897c"
LINE = "#e7ebe3"
LIME = "#d8f65b"
SOFT = "#f0f3eb"
GREEN = "#749052"
AMBER = "#aa8d50"
RED = "#a33a2a"

# Colores de las etiquetas de estado: (fondo, texto).
ESTADOS = {
    "Disponible": ("#e6f0d3", "#4d6d12"), "Reservado": ("#f6e9c6", "#7a5d17"), "Vendido": ("#e9ebe6", "#5f685d"),
    "Nuevo contacto": ("#e6f0d3", "#4d6d12"), "Seguimiento": ("#f6e9c6", "#7a5d17"),
    "Cliente": ("#dfe8f5", "#2f4f7a"), "Descartado": ("#e9ebe6", "#5f685d"),
    "En seguimiento": ("#e6f0d3", "#4d6d12"), "Cerrada": ("#dfe8f5", "#2f4f7a"), "Cancelada": ("#f6dedb", "#8a3326"),
    "Contacto": ("#eef0ea", "#3f4a3d"), "Consulta de vehículo": ("#e6f0d3", "#4d6d12"), "Recuperación": ("#f6dedb", "#8a3326"),
}

NAV_ITEMS = [
    ("Resumen", "◫"),
    ("Inventario", "▦"),
    ("Clientes", "♙"),
    ("Ventas", "↗"),
    ("Estudio IA", "✦"),
    ("Lanzador", "◈"),
    ("Configuración", "⚙"),
]


def dinero(valor):
    return f"${valor:,.0f}"


def fecha(valor):
    return valor.strftime("%d/%m/%Y") if valor else ""


class MotorhausApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Motorhaus | Panel de control")
        self.geometry("1440x900")
        self.minsize(1000, 680)
        self.configure(fg_color=BG)
        self.nav_buttons = {}
        self.current_page = "Resumen"
        self.page_args = ()
        self.access_container = None
        self.usuario = None
        self.servidor = None
        self.ia_modelo = config.IA_MODELO
        self.generacion = None
        self.protocol("WM_DELETE_WINDOW", self.cerrar)
        self._build_layout()
        self.arrancar()

    # ------------------------------------------------------------ arranque

    def arrancar(self):
        try:
            db.inicializar()
        except db.SinConexion as error:
            self.show_error_conexion(str(error))
            return
        self.show_access()

    def cerrar(self):
        self.detener_generacion()
        if self.servidor and self.servidor.poll() is None:
            self.servidor.terminate()
        self.destroy()

    def intentar(self, funcion, *args, **kwargs):
        """Ejecuta una operación de base de datos mostrando los errores al usuario."""
        try:
            return funcion(*args, **kwargs), True
        except db.DatosInvalidos as error:
            messagebox.showwarning("Revisa los datos", str(error), parent=self)
        except db.SinConexion as error:
            messagebox.showerror("Sin conexión", str(error), parent=self)
        return None, False

    # ------------------------------------------------------------ estructura

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=228, fg_color=SIDEBAR, corner_radius=0)
        self.sidebar = sidebar
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(3, weight=1)

        logo = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew", padx=25, pady=(30, 43))
        ctk.CTkLabel(logo, text="m.", text_color=LIME, font=ctk.CTkFont(size=36, weight="bold")).pack(side="left")
        brand = ctk.CTkFrame(logo, fg_color="transparent")
        brand.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(brand, text="MOTORHAUS", text_color="white", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(brand, text="AUTOMOTIVE CLUB", text_color="#7d897d", font=ctk.CTkFont(size=9)).pack(anchor="w")

        ctk.CTkLabel(sidebar, text="ESPACIO DE TRABAJO", text_color="#697569", font=ctk.CTkFont(size=10, weight="bold")).grid(row=1, column=0, sticky="w", padx=25, pady=(0, 12))
        navigation = ctk.CTkFrame(sidebar, fg_color="transparent")
        navigation.grid(row=2, column=0, sticky="ew", padx=12)
        for name, icon in NAV_ITEMS:
            button = ctk.CTkButton(
                navigation, text=f"  {icon}     {name}", anchor="w", height=43,
                fg_color="transparent", hover_color="#242e24", text_color="#a7b2a5",
                font=ctk.CTkFont(size=13), corner_radius=6,
                command=lambda page=name: self.show_page(page),
            )
            button.pack(fill="x", pady=2)
            self.nav_buttons[name] = button

        bottom = ctk.CTkFrame(sidebar, fg_color="#202920", corner_radius=8)
        bottom.grid(row=4, column=0, sticky="ew", padx=16, pady=20)
        ctk.CTkLabel(bottom, text="●  CONECTADO", text_color=LIME, font=ctk.CTkFont(size=9, weight="bold")).pack(anchor="w", padx=14, pady=(13, 3))
        ctk.CTkLabel(bottom, text=f"Base de datos {config.DB_NOMBRE}\ncompartida con la tienda web", text_color="#a2aea0", font=ctk.CTkFont(size=10), justify="left").pack(anchor="w", padx=14, pady=(0, 13))

        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main = main
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(main, height=70, fg_color=WHITE, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        self.breadcrumb = ctk.CTkLabel(header, text="MOTORHAUS   /   RESUMEN", text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold"))
        self.breadcrumb.pack(side="left", padx=35)
        ctk.CTkButton(header, text="Cerrar sesión", command=self.logout, fg_color="transparent", hover_color=SOFT, text_color=DARK, width=110, height=32).pack(side="right", padx=(5, 25))
        ctk.CTkButton(header, text="↻  Actualizar", command=self.refrescar, fg_color="transparent", hover_color=SOFT, text_color=DARK, width=110, height=32).pack(side="right")
        self.header_user = ctk.CTkLabel(header, text="", text_color="#6e7c6a", font=ctk.CTkFont(size=10, weight="bold"))
        self.header_user.pack(side="right", padx=15)
        self.content = ctk.CTkScrollableFrame(main, fg_color=BG, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.content.grid_columnconfigure(0, weight=1)

    def show_page(self, page, *args):
        self.detener_generacion()
        self.current_page = page
        self.page_args = args
        seccion = {"Vehículo": "Inventario", "Cliente": "Clientes", "Venta": "Ventas",
                   "Análisis de inventario": "Estudio IA", "Contenido para anuncios": "Estudio IA",
                   "Perspectivas de ventas": "Estudio IA"}.get(page, page)
        ruta = f"{seccion}   /   {page}" if seccion != page else page
        self.breadcrumb.configure(text=f"MOTORHAUS   /   {ruta.upper()}")
        try:
            pendientes = db.contar_consultas_pendientes()
        except db.SinConexion:
            pendientes = 0
        for (name, icon), button in zip(NAV_ITEMS, self.nav_buttons.values()):
            active = name == seccion
            texto = f"  {icon}     {name}" + (f"   ({pendientes})" if name == "Clientes" and pendientes else "")
            button.configure(text=texto, fg_color="#293525" if active else "transparent", text_color=LIME if active else "#a7b2a5")
        for widget in self.content.winfo_children():
            widget.destroy()
        self.content._parent_canvas.yview_moveto(0)
        pages = {
            "Resumen": self.dashboard,
            "Inventario": self.inventory,
            "Clientes": self.clients,
            "Ventas": self.sales,
            "Estudio IA": self.ai_studio,
            "Lanzador": self.launcher,
            "Configuración": self.settings,
            "Vehículo": self.vehicle_form,
            "Cliente": self.client_form,
            "Venta": self.sale_form,
            "Análisis de inventario": self.ai_inventory,
            "Contenido para anuncios": self.ai_ad,
            "Perspectivas de ventas": self.ai_sales,
        }
        try:
            pages[page](*args)
        except db.SinConexion as error:
            self.notice("Sin conexión con la base de datos", str(error))

    def refrescar(self):
        self.show_page(self.current_page, *self.page_args)

    # ------------------------------------------------------------ acceso

    def _limpiar_acceso(self):
        if self.access_container is not None:
            self.access_container.destroy()
            self.access_container = None

    def _pantalla_acceso(self):
        self.sidebar.grid_remove()
        self.main.grid_remove()
        self._limpiar_acceso()
        self.access_container = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.access_container.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.access_container.grid_columnconfigure((0, 1), weight=1, uniform="acceso")
        self.access_container.grid_rowconfigure(0, weight=1)

        # Panel de marca
        marca = ctk.CTkFrame(self.access_container, fg_color=SIDEBAR, corner_radius=0)
        marca.grid(row=0, column=0, sticky="nsew")
        logo = ctk.CTkFrame(marca, fg_color="transparent")
        logo.pack(anchor="w", padx=60, pady=(50, 0))
        self.label(logo, "m.", 40, LIME, True).pack(side="left")
        textos = ctk.CTkFrame(logo, fg_color="transparent")
        textos.pack(side="left", padx=(12, 0))
        self.label(textos, "MOTORHAUS", 14, "white", True).pack(anchor="w")
        self.label(textos, "AUTOMOTIVE CLUB", 9, "#7d897d").pack(anchor="w")
        pie = ctk.CTkFrame(marca, fg_color="transparent")
        pie.pack(side="bottom", anchor="w", padx=60, pady=50)
        self.label(pie, "●  PANEL DE ADMINISTRACIÓN", 10, LIME, True).pack(anchor="w", pady=(0, 14))
        self.label(pie, "Tu tienda,\nen un solo lugar.", 38, "white", True, justify="left").pack(anchor="w")
        self.label(pie, "Inventario, clientes, ventas y tienda web\nconectados a la misma base de datos.", 13, "#a2aea0", justify="left").pack(anchor="w", pady=(16, 0))

        # Formulario
        lado = ctk.CTkFrame(self.access_container, fg_color=BG, corner_radius=0)
        lado.grid(row=0, column=1, sticky="nsew")
        card = ctk.CTkFrame(lado, fg_color="transparent", width=380)
        card.place(relx=0.5, rely=0.5, anchor="center")
        return card

    def show_error_conexion(self, mensaje):
        card = self._pantalla_acceso()
        self.label(card, "●  SIN CONEXIÓN", 10, RED, True).pack(anchor="w", padx=35)
        self.label(card, "No se encontró la base de datos.", 22, DARK, True).pack(anchor="w", padx=35, pady=(10, 8))
        self.label(card, mensaje, 11, MUTED, wraplength=380, justify="left").pack(anchor="w", padx=35)
        ctk.CTkButton(card, text="Reintentar", command=self.arrancar, fg_color=DARK, hover_color="#334033", height=42).pack(fill="x", padx=35, pady=30)

    def show_access(self):
        try:
            primera_vez = not db.hay_administradores()
        except db.SinConexion as error:
            self.show_error_conexion(str(error))
            return
        card = self._pantalla_acceso()
        self.label(card, "●  ACCESO AL PANEL", 10, "#879582", True).pack(anchor="w", padx=35)
        if primera_vez:
            self.label(card, "Crea tu cuenta.", 28, DARK, True).pack(anchor="w", padx=35, pady=(10, 4))
            self.label(card, "Aún no hay administradores. Crea la primera cuenta para entrar al panel.", 12, MUTED, wraplength=380, justify="left").pack(anchor="w", padx=35, pady=(0, 12))
            nombre = self.access_entry(card, "Nombre", "Tu nombre")
        else:
            self.label(card, "Bienvenido de nuevo.", 28, DARK, True).pack(anchor="w", padx=35, pady=(10, 4))
            self.label(card, "Entra con tu cuenta de administrador.", 12, MUTED).pack(anchor="w", padx=35, pady=(0, 12))
        correo = self.access_entry(card, "Correo electrónico", "correo@ejemplo.com")
        clave = self.access_entry(card, "Contraseña", "Contraseña", password=True)
        confirmar = self.access_entry(card, "Confirmar contraseña", "Repite la contraseña", password=True) if primera_vez else None
        error = self.label(card, "", 11, RED, wraplength=380, justify="left")
        error.pack(anchor="w", padx=35, pady=(10, 0))

        def entrar(_event=None):
            if primera_vez:
                if clave.get() != confirmar.get():
                    error.configure(text="Las contraseñas no coinciden.")
                    return
                usuario, ok = self.intentar(db.crear_usuario, nombre.get(), correo.get(), clave.get(), rol="admin")
                if not ok:
                    return
            else:
                usuario, ok = self.intentar(db.autenticar, correo.get(), clave.get(), rol="admin")
                if not ok:
                    return
                if not usuario:
                    error.configure(text="Correo o contraseña incorrectos.")
                    return
            self.login(usuario)

        ctk.CTkButton(card, text="Crear cuenta y entrar  ↗" if primera_vez else "Iniciar sesión  ↗", command=entrar, fg_color=DARK, hover_color="#334033", text_color="white", height=42).pack(fill="x", padx=35, pady=(12, 30))
        for campo in (correo, clave, confirmar):
            if campo is not None:
                campo.bind("<Return>", entrar)
        (nombre if primera_vez else correo).focus_set()

    def access_entry(self, parent, title, placeholder, password=False):
        self.label(parent, title, 11, DARK, True).pack(anchor="w", padx=35, pady=(8, 4))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, show="•" if password else "", height=40, width=340, fg_color=WHITE, border_color=LINE)
        entry.pack(fill="x", padx=35)
        return entry

    def login(self, usuario):
        self.usuario = usuario
        self._limpiar_acceso()
        self.header_user.configure(text=f"{usuario['nombre'].upper()}   ●")
        self.sidebar.grid()
        self.main.grid()
        self.show_page("Resumen")

    def logout(self):
        self.usuario = None
        self.show_access()

    # ------------------------------------------------------------ componentes

    def heading(self, eyebrow, title, description, actions=(), back=None):
        """Encabezado de página. actions: [(texto, comando, estilo)] con estilo primary|secondary.
        back: (texto, página) para un enlace de regreso."""
        if back:
            ctk.CTkButton(self.content, text=f"←  {back[0]}", command=lambda: self.show_page(back[1]), anchor="w",
                          fg_color="transparent", hover_color="#e9ede4", text_color=MUTED, height=28, width=10,
                          font=ctk.CTkFont(size=12)).pack(anchor="w", padx=21, pady=(22, 0))
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.pack(fill="x", padx=27, pady=(8 if back else 29, 25))
        for text, command, style in reversed(list(actions)):
            primary = style == "primary"
            ctk.CTkButton(frame, text=text, command=command, height=42, corner_radius=5,
                          fg_color=DARK if primary else WHITE, hover_color="#334033" if primary else SOFT,
                          text_color="white" if primary else DARK, border_width=0 if primary else 1, border_color=LINE,
                          font=ctk.CTkFont(size=13, weight="bold" if primary else "normal")).pack(side="right", anchor="s", padx=(10, 0))
        text = ctk.CTkFrame(frame, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text, text=f"●  {eyebrow.upper()}", text_color="#879582", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(text, text=title, text_color=DARK, font=ctk.CTkFont(size=30, weight="bold")).pack(anchor="w", pady=(8, 2))
        ctk.CTkLabel(text, text=description, text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=650, justify="left").pack(anchor="w")

    def panel(self, parent, **kwargs):
        return ctk.CTkFrame(parent, fg_color=WHITE, corner_radius=8, **kwargs)

    def label(self, parent, text, size=12, color=DARK, bold=False, **kwargs):
        return ctk.CTkLabel(parent, text=text, text_color=color, font=ctk.CTkFont(size=size, weight="bold" if bold else "normal"), **kwargs)

    def small_button(self, parent, text, command, danger=False):
        return ctk.CTkButton(parent, text=text, command=command, width=10, height=26, corner_radius=4,
                             fg_color=SOFT, hover_color="#f3d9d4" if danger else "#e5ebdf",
                             text_color=RED if danger else DARK, font=ctk.CTkFont(size=11))

    def pill(self, parent, text):
        fondo, color = ESTADOS.get(text, ("#eef0ea", "#3f4a3d"))
        return ctk.CTkLabel(parent, text=f"  {text}  ", fg_color=fondo, text_color=color, corner_radius=10, height=22,
                            font=ctk.CTkFont(size=10, weight="bold"))

    def toast(self, mensaje, error=False):
        """Aviso breve en la esquina inferior; desaparece solo. Un aviso nuevo reemplaza al anterior."""
        anterior = getattr(self, "_aviso", None)
        if anterior is not None and anterior.winfo_exists():
            anterior.destroy()
        aviso = self._aviso = ctk.CTkLabel(self, text=f"   {'✕' if error else '✓'}   {mensaje}   ", fg_color="#7c2a1f" if error else DARK,
                             text_color="white", corner_radius=6, height=40, font=ctk.CTkFont(size=12, weight="bold"))
        aviso.place(relx=1.0, rely=1.0, x=-28, y=-28, anchor="se")
        aviso.lift()
        self.after(2800, lambda: aviso.winfo_exists() and aviso.destroy())

    def table(self, parent, title, columns, rows, actions=None, empty="Sin registros todavía.", more=None,
              search=None, filtro=None):
        """Tabla con encabezado, separadores y, opcionalmente, búsqueda y filtro.

        columns: [(título, peso)] o [(título, peso, "pill")] para mostrar el valor como etiqueta de estado.
        rows: [(item, [valores])]. search: texto de ayuda del buscador (busca en todos los valores).
        filtro: (opciones, función(fila_valores, opción) -> bool); la primera opción muestra todo.
        """
        card = self.panel(parent)
        card.pack(fill="x", padx=27, pady=(0, 20))
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(18, 12))
        titulo = self.label(top, title, 16, DARK, True)
        titulo.pack(side="left")
        if more:
            ctk.CTkButton(top, text=f"{more[0]}  ↗", command=more[1], fg_color="transparent", hover_color=SOFT, text_color=DARK, width=125, height=28).pack(side="right")
        selector = buscador = None
        if filtro:
            selector = ctk.CTkOptionMenu(top, values=filtro[0], width=150, height=32, fg_color=SOFT, button_color="#e1e7da",
                                         button_hover_color="#d5ddcd", text_color=DARK, dropdown_fg_color=WHITE, dropdown_text_color=DARK)
            selector.pack(side="right", padx=(8, 0))
        if search:
            buscador = ctk.CTkEntry(top, placeholder_text=f"⌕   {search}", width=240, height=32, fg_color=SOFT, border_width=0, text_color=DARK)
            buscador.pack(side="right")

        table = ctk.CTkFrame(card, fg_color="transparent")
        table.pack(fill="x", padx=20, pady=(0, 14))
        all_columns = [(c[0], c[1], c[2] if len(c) > 2 else "") for c in columns] + ([("", 3, "")] if actions else [])
        for col, (_, weight, _) in enumerate(all_columns):
            table.grid_columnconfigure(col, weight=weight, uniform="table")

        def pintar(*_):
            for widget in table.winfo_children():
                widget.destroy()
            for col, (text, _, _) in enumerate(all_columns):
                self.label(table, text, 9, MUTED, True, anchor="w").grid(row=0, column=col, sticky="ew", pady=(0, 8))
            texto = buscador.get().strip().lower() if buscador else ""
            opcion = selector.get() if selector else None
            visibles = [
                (item, values) for item, values in rows
                if (not texto or texto in " ".join(str(v or "") for v in values).lower())
                and (not filtro or opcion == filtro[0][0] or filtro[1](values, opcion))
            ]
            if search or filtro:
                titulo.configure(text=f"{title} · {len(visibles)}" if len(visibles) == len(rows) else f"{title} · {len(visibles)} de {len(rows)}")
            if not visibles:
                mensaje = empty if not rows else "Ningún resultado con esa búsqueda."
                self.label(table, mensaje, 11, MUTED, anchor="w").grid(row=2, column=0, columnspan=len(all_columns), sticky="ew", pady=14)
            for index, (item, values) in enumerate(visibles):
                fila = index * 2 + 2
                ctk.CTkFrame(table, height=1, corner_radius=0, fg_color="#eceee8").grid(row=fila - 1, column=0, columnspan=len(all_columns), sticky="ew")
                for col, value in enumerate(values):
                    texto_celda = str(value if value not in (None, "") else "—")
                    if all_columns[col][2] == "pill" and value:
                        self.pill(table, texto_celda).grid(row=fila, column=col, sticky="w", pady=9)
                    else:
                        self.label(table, texto_celda, 11, DARK if value not in (None, "") else MUTED, col == 0,
                                   anchor="w", wraplength=170, justify="left").grid(row=fila, column=col, sticky="ew", pady=9)
                if actions:
                    box = ctk.CTkFrame(table, fg_color="transparent")
                    box.grid(row=fila, column=len(values), sticky="e", pady=4)
                    for text, command, danger in actions(item):
                        self.small_button(box, text, command, danger).pack(side="left", padx=(6, 0))

        pendiente = {"id": None}

        def programar(*_):
            if pendiente["id"]:
                self.after_cancel(pendiente["id"])
            pendiente["id"] = self.after(180, pintar)

        if buscador:
            buscador.bind("<KeyRelease>", programar)
        if selector:
            selector.configure(command=lambda _opcion: pintar())
        pintar()
        return card

    def notice(self, title, description):
        card = ctk.CTkFrame(self.content, fg_color="#eaf0df", corner_radius=8)
        card.pack(fill="x", padx=27, pady=(0, 25))
        self.label(card, title, 12, DARK, True).pack(anchor="w", padx=20, pady=(15, 2))
        self.label(card, description, 11, MUTED, wraplength=700, justify="left").pack(anchor="w", padx=20, pady=(0, 15))

    def form(self, title, fields, values=None, columns=2):
        """Crea un formulario. fields: [(clave, etiqueta, tipo, opciones)].
        tipo: entry | combo (editable) | option (lista fija) | text. Devuelve {clave: lector}."""
        values = values or {}
        card = self.panel(self.content)
        card.pack(fill="x", padx=27, pady=(0, 20))
        self.label(card, title, 16, DARK, True).pack(anchor="w", padx=24, pady=(20, 6))
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=24, pady=(0, 10))
        for col in range(columns):
            grid.grid_columnconfigure(col, weight=1, uniform="form")
        readers, position = {}, 0
        for key, text, kind, options in fields:
            wide = kind == "text"
            if wide and position % columns:
                position += columns - position % columns
            row, col = divmod(position, columns)
            box = ctk.CTkFrame(grid, fg_color="transparent")
            box.grid(row=row, column=col, columnspan=columns if wide else 1, sticky="ew", padx=(0, 16), pady=6)
            self.label(box, text, 11, DARK, True).pack(anchor="w", pady=(0, 4))
            current = values.get(key)
            current = "" if current is None else str(current)
            if kind == "text":
                widget = ctk.CTkTextbox(box, height=80, fg_color=WHITE, border_color=LINE, border_width=2, text_color=DARK)
                widget.insert("1.0", current)
                readers[key] = lambda w=widget: w.get("1.0", "end").strip()
            elif kind in ("combo", "option"):
                cls = ctk.CTkComboBox if kind == "combo" else ctk.CTkOptionMenu
                extra = dict(fg_color=WHITE, border_color=LINE, button_color=LINE) if kind == "combo" else dict(fg_color=SOFT, button_color="#e1e7da", button_hover_color="#d5ddcd", dropdown_fg_color=WHITE)
                widget = cls(box, values=options or [""], height=38, text_color=DARK, dropdown_text_color=DARK, **extra)
                widget.set(current if current or kind == "combo" else (options[0] if options else ""))
                readers[key] = widget.get
            else:
                widget = ctk.CTkEntry(box, height=38, fg_color=WHITE, border_color=LINE, text_color=DARK)
                widget.insert(0, current)
                readers[key] = widget.get
            widget.pack(fill="x")
            readers[f"_{key}"] = widget
            position += columns if wide else 1
        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(6, 22))
        readers["_footer"] = footer
        return readers

    @staticmethod
    def leer(readers):
        return {key: read() for key, read in readers.items() if not key.startswith("_")}

    def confirmar(self, titulo, mensaje):
        return messagebox.askyesno(titulo, mensaje, parent=self)

    # ------------------------------------------------------------ resumen

    def dashboard(self):
        datos = db.resumen()
        nombre = (self.usuario or {}).get("nombre", "").split(" ")[0]
        self.heading("Vista general", f"Hola, {nombre}." if nombre else "Todo comienza aquí.",
                     "Un vistazo a tu operación con datos en vivo de la base de datos.",
                     actions=[("Abrir tienda   ↗", self.open_website, "secondary"),
                              ("＋  Nuevo vehículo", lambda: self.show_page("Vehículo"), "primary")])
        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.pack(fill="x", padx=27)
        body.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stats")
        diferencia = datos["ventas_mes"] - datos["ventas_mes_anterior"]
        stats = [
            ("VEHÍCULOS EN INVENTARIO", f"{datos['inventario']:02d}", f"↗  {datos['inventario_mes']} nuevos este mes"),
            ("CLIENTES", f"{datos['clientes']:02d}", f"↗  {datos['clientes_mes']} nuevos · {datos['cuentas_web']} con cuenta web"),
            ("VENTAS DEL MES", f"{datos['ventas_mes']:02d}", f"{'↗' if diferencia >= 0 else '↘'}  {abs(diferencia)} {'más' if diferencia >= 0 else 'menos'} que el mes anterior"),
            ("VALOR DEL INVENTARIO", self._millones(datos["valor_inventario"]), "MXN  ·  vehículos no vendidos"),
        ]
        for column, (title, value, note) in enumerate(stats):
            card = self.panel(body)
            card.grid(row=0, column=column, sticky="nsew", padx=(0, 12) if column < 3 else 0)
            self.label(card, title, 9, MUTED, True).pack(anchor="w", padx=18, pady=(20, 12))
            self.label(card, value, 29, DARK, True).pack(anchor="w", padx=18)
            self.label(card, note, 10, "#799254").pack(anchor="w", padx=18, pady=(10, 20))

        middle = ctk.CTkFrame(self.content, fg_color="transparent")
        middle.pack(fill="x", padx=27, pady=18)
        middle.grid_columnconfigure(0, weight=3, uniform="medio")
        middle.grid_columnconfigure(1, weight=2, uniform="medio")

        # Consultas recientes desde la web
        pendientes = self.panel(middle)
        pendientes.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        top = ctk.CTkFrame(pendientes, fg_color="transparent")
        top.pack(fill="x", padx=23, pady=(22, 6))
        self.label(top, "✉  DESDE LA TIENDA WEB", 10, "#8ca259", True).pack(side="left")
        ctk.CTkButton(top, text="Ver todas  ↗", command=lambda: self.show_page("Clientes"), fg_color="transparent", hover_color=SOFT, text_color=DARK, width=90, height=26).pack(side="right")
        total = datos["consultas_pendientes"]
        self.label(pendientes, f"{total} consulta{'s' if total != 1 else ''} por atender" if total else "Todo al día ✓", 20, DARK, True).pack(anchor="w", padx=23, pady=(0, 10))
        recientes = db.listar_consultas(solo_pendientes=True, limite=4)
        if not recientes:
            self.label(pendientes, "Cuando alguien escriba desde la tienda web, aparecerá aquí.", 12, MUTED).pack(anchor="w", padx=23, pady=(0, 22))
        for consulta in recientes:
            ctk.CTkFrame(pendientes, height=1, corner_radius=0, fg_color="#eceee8").pack(fill="x", padx=23)
            fila = ctk.CTkFrame(pendientes, fg_color="transparent")
            fila.pack(fill="x", padx=23, pady=8)
            self.label(fila, consulta["cliente"], 12, DARK, True).pack(side="left")
            self.label(fila, f"  ·  {consulta['vehiculo'] or consulta['tipo']}", 11, MUTED).pack(side="left")
            self.label(fila, fecha(consulta["fecha"]), 10, MUTED).pack(side="right")
        if recientes:
            ctk.CTkFrame(pendientes, height=14, fg_color="transparent").pack()

        # Accesos rápidos
        rapido = ctk.CTkFrame(middle, fg_color=DARK, corner_radius=8)
        rapido.grid(row=0, column=1, sticky="nsew")
        self.label(rapido, "ACCESOS RÁPIDOS  ↗", 10, LIME, True).pack(anchor="w", padx=25, pady=(22, 8))
        self.label(rapido, "Lo que cambias aquí se ve\nal instante en la tienda web.", 15, "white", True, justify="left").pack(anchor="w", padx=25, pady=(0, 14))
        for texto, pagina in [("＋  Registrar una venta", "Venta"), ("＋  Agregar un cliente", "Cliente"), ("✦  Escribir un anuncio con IA", "Contenido para anuncios")]:
            ctk.CTkButton(rapido, text=texto, command=lambda p=pagina: self.show_page(p), anchor="w", fg_color="#232c24",
                          hover_color="#2f3b2f", text_color="#dfe7da", height=36, corner_radius=5).pack(fill="x", padx=25, pady=3)
        ctk.CTkFrame(rapido, height=16, fg_color="transparent").pack()

        self.vehicle_table("Inventario reciente", limit=5, more=("Ver inventario", lambda: self.show_page("Inventario")))

    @staticmethod
    def _millones(valor):
        return f"${valor / 1_000_000:.1f}M" if valor >= 1_000_000 else dinero(valor)

    # ------------------------------------------------------------ inventario

    def vehicle_table(self, title, limit=None, more=None, actions=None, buscar=False):
        vehiculos = db.listar_vehiculos()
        if limit:
            vehiculos = sorted(vehiculos, key=lambda v: v["fecha_alta"], reverse=True)[:limit]
        rows = [(v, [v["marca"], v["modelo"], v["tipo"], v["anio"], dinero(v["precio"]), v["estado"]]) for v in vehiculos]
        columns = [("MARCA", 2), ("MODELO", 3), ("TIPO", 2), ("AÑO", 1), ("PRECIO", 2), ("ESTADO", 2, "pill")]
        return self.table(self.content, title, columns, rows, actions=actions, more=more,
                          empty="No hay vehículos. Agrega el primero con «Nuevo vehículo».",
                          search="Buscar marca o modelo" if buscar else None,
                          filtro=(["Todos los estados"] + db.ESTADOS_VEHICULO, lambda fila, op: fila[5] == op) if buscar else None)

    def inventory(self):
        self.heading("Gestión de vehículos", "Inventario.", "Los vehículos que no estén vendidos se publican automáticamente en la tienda web.",
                     actions=[("Abrir tienda   ↗", self.open_website, "secondary"),
                              ("＋  Nuevo vehículo", lambda: self.show_page("Vehículo"), "primary")])
        self.vehicle_table("Vehículos", buscar=True, actions=lambda v: [
            ("Editar", lambda: self.show_page("Vehículo", v["id"]), False),
            *([("$ Vender", lambda: self.show_page("Venta", None, v["id"], "Cerrada"), False)] if v["estado"] == "Disponible" else []),
            ("✦ Anuncio", lambda: self.show_page("Contenido para anuncios", v["id"]), False),
            ("Eliminar", lambda: self.delete_vehicle(v), True),
        ])

    def delete_vehicle(self, vehiculo):
        if self.confirmar("Eliminar vehículo", f"¿Eliminar {vehiculo['marca']} {vehiculo['modelo']}? Dejará de aparecer en la tienda."):
            _, ok = self.intentar(db.eliminar_vehiculo, vehiculo["id"])
            if ok:
                self.show_page("Inventario")
                self.toast("Vehículo eliminado")

    def vehicle_form(self, id_vehiculo=None):
        vehiculo = db.obtener_vehiculo(id_vehiculo) if id_vehiculo else None
        if id_vehiculo and not vehiculo:
            messagebox.showwarning("No encontrado", "El vehículo ya no existe.", parent=self)
            self.show_page("Inventario")
            return
        nuevo = vehiculo is None
        self.heading("Inventario", "Nuevo vehículo." if nuevo else f"{vehiculo['marca']} {vehiculo['modelo']}.",
                     "Completa la ficha. Al guardar, el cambio se ve en la tienda web.", back=("Volver a Inventario", "Inventario"))
        valores = vehiculo or {"tipo": "Sedán", "combustible": "Gasolina", "estado": "Disponible", "etiqueta": ""}
        campos = self.form("Ficha del vehículo", [
            ("marca", "Marca", "combo", db.listar_marcas()),
            ("modelo", "Modelo", "entry", None),
            ("version", "Versión", "entry", None),
            ("tipo", "Tipo", "option", db.TIPOS),
            ("anio", "Año", "entry", None),
            ("color", "Color", "entry", None),
            ("kilometraje", "Kilometraje", "entry", None),
            ("combustible", "Combustible", "option", db.COMBUSTIBLES),
            ("precio", "Precio (MXN)", "entry", None),
            ("estado", "Estado", "option", db.ESTADOS_VEHICULO),
            ("etiqueta", "Etiqueta en la tienda", "option", db.ETIQUETAS),
            ("imagen", "URL de la imagen (https://…)", "entry", None),
            ("descripcion", "Descripción", "text", None),
        ], valores)

        segun_ventas = db.estado_por_ventas(id_vehiculo) if id_vehiculo else None

        def guardar():
            datos = self.leer(campos)
            deseado = datos["estado"]
            # Vender o apartar un auto se hace registrando la venta, para que aparezca en «Ventas».
            pedir_venta = deseado in ("Vendido", "Reservado") and not segun_ventas and \
                (not vehiculo or deseado != vehiculo["estado"])
            if pedir_venta:
                datos["estado"] = vehiculo["estado"] if vehiculo else "Disponible"
            guardado, ok = self.intentar(db.guardar_vehiculo, datos, id_vehiculo)
            if not ok:
                return
            if pedir_venta:
                self.show_page("Venta", None, guardado, "Cerrada" if deseado == "Vendido" else "Reservado")
                self.toast("Ahora elige al cliente y guarda la venta")
            else:
                self.show_page("Inventario")
                self.toast("Vehículo guardado")

        ctk.CTkButton(campos["_footer"], text="Guardar vehículo", command=guardar, fg_color=DARK, hover_color="#334033", height=40, width=170).pack(side="left")
        if segun_ventas:
            nota = f"El estado lo controla su venta ({'cerrada' if segun_ventas == 'Vendido' else 'reservada'}). Para cambiarlo, ve a «Ventas»."
        else:
            nota = "Si eliges «Vendido» o «Reservado», al guardar te pedirá registrar la venta."
        self.label(campos["_footer"], nota, 11, MUTED).pack(side="left", padx=16)
        if segun_ventas:
            campos["_estado"].configure(state="disabled")

    # ------------------------------------------------------------ clientes

    def clients(self):
        self.heading("Relaciones", "Clientes.", "Prospectos y clientes de la tienda web y del mostrador, en un solo lugar.",
                     actions=[("＋  Nuevo cliente", lambda: self.show_page("Cliente"), "primary")])

        consultas = db.listar_consultas(solo_pendientes=True)
        self.table(self.content, f"Consultas por atender · {len(consultas)}",
                   [("CLIENTE", 2), ("TIPO", 2, "pill"), ("VEHÍCULO", 2), ("MENSAJE", 4), ("CONTACTO", 3), ("FECHA", 2)],
                   [(c, [c["cliente"], c["tipo"], c["vehiculo"], c["mensaje"], "\n".join(filter(None, [c["correo"], c["telefono"]])), fecha(c["fecha"])])
                    for c in consultas],
                   actions=self._acciones_consulta, empty="No hay consultas pendientes. ¡Todo al día! ✓")

        clientes = db.listar_clientes()
        self.table(self.content, "Clientes",
                   [("NOMBRE", 3), ("CORREO", 3), ("TELÉFONO", 2), ("INTERÉS", 2), ("ORIGEN", 2), ("ESTADO", 2, "pill")],
                   [(c, [c["nombre"], c["correo"], c["telefono"], c["interes"],
                         c["origen"] + (" · cuenta" if c["id_usuario"] else ""), c["estado"]]) for c in clientes],
                   actions=self._acciones_cliente, empty="Aún no hay clientes registrados.",
                   search="Buscar nombre, correo o teléfono",
                   filtro=(["Todos los estados"] + db.ESTADOS_CLIENTE, lambda fila, op: fila[5] == op))

    def _acciones_consulta(self, consulta):
        acciones = [("Atendida ✓", lambda: self._atender(consulta["id"]), False)]
        if consulta["tipo"] == "Recuperación" and consulta["id_usuario"]:
            acciones.insert(0, ("Nueva clave", lambda: self.reset_password(consulta["id_usuario"], consulta["cliente"]), False))
        return acciones

    def _atender(self, id_consulta):
        _, ok = self.intentar(db.marcar_consulta, id_consulta, True)
        if ok:
            self.show_page("Clientes")
            self.toast("Consulta marcada como atendida")

    def _acciones_cliente(self, cliente):
        acciones = [("Editar", lambda: self.show_page("Cliente", cliente["id"]), False)]
        if cliente["id_usuario"]:
            acciones.append(("Nueva clave", lambda: self.reset_password(cliente["id_usuario"], cliente["nombre"]), False))
        acciones.append(("Eliminar", lambda: self.delete_client(cliente), True))
        return acciones

    def reset_password(self, id_usuario, nombre):
        if not self.confirmar("Restablecer contraseña", f"¿Generar una contraseña temporal para {nombre}? La actual dejará de funcionar."):
            return
        temporal, ok = self.intentar(db.restablecer_clave, id_usuario)
        if ok:
            self.clipboard_clear()
            self.clipboard_append(temporal)
            messagebox.showinfo("Contraseña temporal",
                                f"Nueva contraseña para {nombre}:\n\n{temporal}\n\nSe copió al portapapeles. "
                                "Compártela con el cliente; podrá cambiarla en «Mi cuenta».", parent=self)

    def delete_client(self, cliente):
        if self.confirmar("Eliminar cliente", f"¿Eliminar a {cliente['nombre']} y sus consultas?"):
            _, ok = self.intentar(db.eliminar_cliente, cliente["id"])
            if ok:
                self.show_page("Clientes")
                self.toast("Cliente eliminado")

    def client_form(self, id_cliente=None):
        cliente = db.obtener_cliente(id_cliente) if id_cliente else None
        if id_cliente and not cliente:
            self.show_page("Clientes")
            self.toast("Ese cliente ya no existe", error=True)
            return
        self.heading("Clientes", "Nuevo cliente." if not cliente else f"{cliente['nombre']}.", "Datos de contacto y seguimiento.",
                     back=("Volver a Clientes", "Clientes"))
        if cliente:
            origen = f"Registrado desde: {cliente['origen']}  ·  Alta: {fecha(cliente['fecha_alta'])}"
            if cliente["id_usuario"]:
                origen += "  ·  Tiene cuenta en la tienda web"
            self.label(self.content, origen, 11, MUTED).pack(anchor="w", padx=29, pady=(0, 12))
        campos = self.form("Información general", [
            ("nombre", "Nombre completo", "entry", None),
            ("correo", "Correo electrónico", "entry", None),
            ("telefono", "Teléfono", "entry", None),
            ("interes", "Vehículo de interés", "entry", None),
            ("estado", "Estado", "option", db.ESTADOS_CLIENTE),
            ("notas", "Notas", "text", None),
        ], cliente or {"estado": "Nuevo contacto"})

        def guardar():
            _, ok = self.intentar(db.guardar_cliente, self.leer(campos), id_cliente)
            if ok:
                self.show_page("Clientes")
                self.toast("Cliente guardado")

        ctk.CTkButton(campos["_footer"], text="Guardar cliente", command=guardar, fg_color=DARK, hover_color="#334033", height=40, width=170).pack(side="left")

    # ------------------------------------------------------------ ventas

    def sales(self):
        self.heading("Operación", "Ventas.", "Al reservar o cerrar una venta, el vehículo cambia de estado en la tienda web.",
                     actions=[("＋  Nueva venta", lambda: self.show_page("Venta"), "primary")])
        ventas = db.listar_ventas()
        cerradas = [s for s in ventas if s["estado"] == "Cerrada"]
        resumen = ctk.CTkFrame(self.content, fg_color="transparent")
        resumen.pack(fill="x", padx=27, pady=(0, 18))
        resumen.grid_columnconfigure((0, 1, 2), weight=1, uniform="ventas")
        for col, (titulo, valor) in enumerate([
            ("EN PROCESO", str(sum(1 for s in ventas if s["estado"] in ("En seguimiento", "Reservado")))),
            ("CERRADAS", str(len(cerradas))),
            ("MONTO CERRADO", dinero(sum(s["precio"] for s in cerradas))),
        ]):
            card = self.panel(resumen)
            card.grid(row=0, column=col, sticky="nsew", padx=(0, 12) if col < 2 else 0)
            self.label(card, titulo, 9, MUTED, True).pack(anchor="w", padx=18, pady=(16, 6))
            self.label(card, valor, 22, DARK, True).pack(anchor="w", padx=18, pady=(0, 16))

        sin_venta = db.vehiculos_sin_venta()
        if sin_venta:
            aviso = ctk.CTkFrame(self.content, fg_color="#f6e9c6", corner_radius=8)
            aviso.pack(fill="x", padx=27, pady=(0, 18))
            self.label(aviso, f"⚠  {len(sin_venta)} auto{'s' if len(sin_venta) != 1 else ''} marcado{'s' if len(sin_venta) != 1 else ''} "
                              "como vendido o reservado sin venta registrada", 12, "#5c4510", True).pack(anchor="w", padx=20, pady=(14, 2))
            self.label(aviso, "Registra la venta para que cuente en tus números y quede ligada a un cliente.", 11, "#7a5d17").pack(anchor="w", padx=20, pady=(0, 8))
            for v in sin_venta:
                fila = ctk.CTkFrame(aviso, fg_color="transparent")
                fila.pack(fill="x", padx=20, pady=(0, 6))
                self.label(fila, f"{v['marca']} {v['modelo']} {v['anio']}", 12, DARK, True).pack(side="left")
                self.label(fila, f"   {v['estado']}  ·  {dinero(v['precio'])}", 11, "#7a5d17").pack(side="left")
                ctk.CTkButton(fila, text="Registrar venta  ↗", height=28, width=140, fg_color=DARK, hover_color="#334033",
                              command=lambda v=v: self.show_page("Venta", None, v["id"], "Cerrada" if v["estado"] == "Vendido" else "Reservado")
                              ).pack(side="right")
            ctk.CTkFrame(aviso, height=8, fg_color="transparent").pack()

        self.table(self.content, "Operaciones",
                   [("VEHÍCULO", 3), ("CLIENTE", 3), ("PRECIO", 2), ("ESTADO", 2, "pill"), ("FECHA", 2)],
                   [(s, [s["vehiculo"], s["cliente"], dinero(s["precio"]), s["estado"], fecha(s["fecha"])]) for s in ventas],
                   actions=lambda s: [
                       ("Editar", lambda: self.show_page("Venta", s["id"]), False),
                       ("Eliminar", lambda: self.delete_sale(s), True),
                   ], empty="Aún no hay ventas. Registra la primera con «Nueva venta».",
                   search="Buscar auto o cliente",
                   filtro=(["Todos los estados"] + db.ESTADOS_VENTA, lambda fila, op: fila[3] == op))

    def delete_sale(self, venta):
        if self.confirmar("Eliminar venta", f"¿Eliminar la operación de {venta['vehiculo']} con {venta['cliente']}?"):
            _, ok = self.intentar(db.eliminar_venta, venta["id"])
            if ok:
                self.show_page("Ventas")
                self.toast("Venta eliminada")

    def sale_form(self, id_venta=None, id_vehiculo=None, estado=None):
        """Formulario de venta. id_vehiculo y estado llegan ya elegidos desde «Vender» o «Registrar venta»."""
        venta = next((s for s in db.listar_ventas() if s["id"] == id_venta), None) if id_venta else None
        clientes = db.listar_clientes()
        # Se pueden vender los autos no vendidos y los marcados «Vendido» a mano que aún no tienen venta.
        pendientes = {v["id"] for v in db.vehiculos_sin_venta()}
        vehiculos = [v for v in db.listar_vehiculos()
                     if v["estado"] != "Vendido" or v["id"] in pendientes or (venta and v["id"] == venta["id_vehiculo"])]
        if id_venta and not venta:
            self.show_page("Ventas")
            self.toast("Esa venta ya no existe", error=True)
            return
        if not clientes or not vehiculos:
            falta = [("＋  Nuevo cliente", lambda: self.show_page("Cliente"), "primary")] if not clientes else \
                    [("＋  Nuevo vehículo", lambda: self.show_page("Vehículo"), "primary")]
            self.heading("Ventas", "Nueva venta.", "Para registrar una venta necesitas al menos un cliente y un vehículo sin vender.",
                         actions=falta, back=("Volver a Ventas", "Ventas"))
            return
        op_clientes = {f"{c['nombre']}  (#{c['id']})": c["id"] for c in clientes}
        op_vehiculos = {f"{v['marca']} {v['modelo']} {v['anio']}  (#{v['id']})": v for v in vehiculos}
        valores = {"estado": "En seguimiento"}
        if venta:
            valores = dict(venta)
            valores["cliente"] = next(k for k, i in op_clientes.items() if i == venta["id_cliente"])
            valores["vehiculo"] = next(k for k, v in op_vehiculos.items() if v["id"] == venta["id_vehiculo"])
        else:
            primero = next((k for k, v in op_vehiculos.items() if v["id"] == id_vehiculo), next(iter(op_vehiculos)))
            valores.update(cliente=next(iter(op_clientes)), vehiculo=primero, precio=op_vehiculos[primero]["precio"])
            if estado in db.ESTADOS_VENTA:
                valores["estado"] = estado
        self.heading("Ventas", "Nueva venta." if not venta else f"Venta #{venta['id']}.",
                     "Relaciona un cliente con un vehículo. «Reservado» y «Cerrada» cambian el estado del auto en la tienda.",
                     back=("Volver a Ventas", "Ventas"))
        campos = self.form("Detalle de la operación", [
            ("cliente", "Cliente", "option", list(op_clientes)),
            ("vehiculo", "Vehículo", "option", list(op_vehiculos)),
            ("precio", "Precio acordado (MXN)", "entry", None),
            ("estado", "Estado", "option", db.ESTADOS_VENTA),
            ("notas", "Notas", "text", None),
        ], valores)

        def al_cambiar_vehiculo(opcion):
            campo = campos["_precio"]
            campo.delete(0, "end")
            campo.insert(0, str(op_vehiculos[opcion]["precio"]))

        campos["_vehiculo"].configure(command=al_cambiar_vehiculo)

        def guardar():
            datos = self.leer(campos)
            datos["id_cliente"] = op_clientes[datos.pop("cliente")]
            datos["id_vehiculo"] = op_vehiculos[datos.pop("vehiculo")]["id"]
            _, ok = self.intentar(db.guardar_venta, datos, id_venta)
            if ok:
                self.show_page("Ventas")
                self.toast("Venta guardada")

        ctk.CTkButton(campos["_footer"], text="Guardar venta", command=guardar, fg_color=DARK, hover_color="#334033", height=40, width=170).pack(side="left")

    # ------------------------------------------------------------ configuración

    def settings(self):
        self.heading("Espacio de trabajo", "Configuración.", "Tu perfil de administración.")
        perfil = self.form("Perfil de administración", [
            ("nombre", "Nombre", "entry", None),
        ], self.usuario, columns=1)
        self.label(perfil["_footer"], f"Correo: {self.usuario['correo']}", 11, MUTED).pack(side="right")

        def guardar_perfil():
            nombre = perfil["nombre"]()
            _, ok = self.intentar(db.actualizar_perfil, self.usuario["id"], nombre)
            if ok:
                self.usuario["nombre"] = nombre.strip()
                self.header_user.configure(text=f"{self.usuario['nombre'].upper()}   ●")
                self.toast("Perfil actualizado")

        ctk.CTkButton(perfil["_footer"], text="Guardar perfil", command=guardar_perfil, fg_color=DARK, hover_color="#334033", height=40, width=170).pack(side="left")

        clave = self.form("Cambiar contraseña", [
            ("actual", "Contraseña actual", "entry", None),
            ("nueva", "Nueva contraseña", "entry", None),
        ])
        clave["_actual"].configure(show="•")
        clave["_nueva"].configure(show="•")

        def guardar_clave():
            _, ok = self.intentar(db.cambiar_clave, self.usuario["id"], clave["actual"](), clave["nueva"]())
            if ok:
                clave["_actual"].delete(0, "end")
                clave["_nueva"].delete(0, "end")
                self.toast("Contraseña actualizada")

        ctk.CTkButton(clave["_footer"], text="Cambiar contraseña", command=guardar_clave, fg_color=DARK, hover_color="#334033", height=40, width=170).pack(side="left")

        nuevo = self.form("Agregar otro administrador", [
            ("nombre", "Nombre", "entry", None),
            ("correo", "Correo electrónico", "entry", None),
            ("clave", "Contraseña inicial", "entry", None),
        ], columns=3)
        nuevo["_clave"].configure(show="•")

        def crear_admin():
            datos = self.leer(nuevo)
            _, ok = self.intentar(db.crear_usuario, datos["nombre"], datos["correo"], datos["clave"], rol="admin")
            if ok:
                self.show_page("Configuración")
                self.toast(f"Se creó la cuenta de {datos['nombre'].strip()}")

        ctk.CTkButton(nuevo["_footer"], text="Crear administrador", command=crear_admin, fg_color=DARK, hover_color="#334033", height=40, width=170).pack(side="left")

    # ------------------------------------------------------------ estudio IA

    def ia_estado(self):
        """Consulta Ollama. Devuelve (modelos instalados, mensaje de error o None)."""
        try:
            modelos = ia.modelos()
        except ia.IANoDisponible as error:
            return [], str(error)
        if not modelos:
            return [], "Ollama está encendido pero no tiene modelos. Instala uno con «ollama pull llama3.2:3b»."
        if self.ia_modelo not in modelos:
            self.ia_modelo = modelos[0]
        return modelos, None

    def ai_studio(self):
        self.heading("Asistente local", "Estudio IA.", "Analiza tu inventario, redacta anuncios y descubre oportunidades con un modelo que corre en esta computadora.")
        modelos, error = self.ia_estado()
        intro = ctk.CTkFrame(self.content, fg_color=DARK, corner_radius=8)
        intro.pack(fill="x", padx=27, pady=(0, 18))
        self.label(intro, "✦   UN NUEVO COPILOTO PARA TU NEGOCIO", 10, LIME, True).pack(anchor="w", padx=25, pady=(22, 8))
        self.label(intro, "Más ideas. Mejores oportunidades.", 22, "white", True).pack(anchor="w", padx=25)
        if error:
            self.label(intro, f"●  OLLAMA NO DISPONIBLE\n{error}", 12, "#f0b3a8", wraplength=760, justify="left").pack(anchor="w", padx=25, pady=(10, 12))
            ctk.CTkButton(intro, text="Reintentar", command=self.refrescar, fg_color=LIME, hover_color="#e5ff83", text_color=DARK, width=140, height=36).pack(anchor="w", padx=25, pady=(0, 22))
        else:
            fila = ctk.CTkFrame(intro, fg_color="transparent")
            fila.pack(anchor="w", padx=25, pady=(12, 6))
            self.label(fila, "●  OLLAMA CONECTADO   ·   Modelo", 11, LIME, True).pack(side="left", padx=(0, 10))
            selector = ctk.CTkOptionMenu(fila, values=modelos, command=self._elegir_modelo, width=200, height=32,
                                         fg_color="#2a352a", button_color="#334033", button_hover_color="#3d4c3d", text_color="white")
            selector.set(self.ia_modelo)
            selector.pack(side="left")
            self.label(intro, "Los datos se leen de la base MOTORHAUS y solo se envían a Ollama en esta computadora; nada sale a internet.", 12, "#abb8a8", wraplength=760, justify="left").pack(anchor="w", padx=25, pady=(6, 22))
        cards = ctk.CTkFrame(self.content, fg_color="transparent")
        cards.pack(fill="x", padx=27, pady=(0, 18))
        cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="ai")
        tools = [
            ("◇", "Análisis de inventario", "Detecta los autos que necesitan atención y revisa precios con tus datos reales."),
            ("✎", "Contenido para anuncios", "Redacta el anuncio de un auto y publícalo como su descripción en la tienda."),
            ("↗", "Perspectivas de ventas", "Revisa ventas, consultas y clientes para encontrar oportunidades."),
        ]
        for col, (icon, title, description) in enumerate(tools):
            card = self.panel(cards)
            card.grid(row=0, column=col, sticky="nsew", padx=(0, 14) if col < 2 else 0)
            self.label(card, icon, 25, "#87a341").pack(anchor="w", padx=20, pady=(20, 8))
            self.label(card, title, 15, DARK, True).pack(anchor="w", padx=20)
            self.label(card, description, 11, MUTED, wraplength=210, justify="left").pack(anchor="w", padx=20, pady=(10, 15))
            ctk.CTkButton(card, text="Abrir  ↗", command=lambda page=title: self.show_page(page), fg_color=SOFT, hover_color="#e5ebdf", text_color=DARK, height=35, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=20, pady=(0, 20))

    def _elegir_modelo(self, modelo):
        self.ia_modelo = modelo

    def ai_layout(self, title, description, fields, values):
        """Pantalla común de las herramientas: parámetros arriba, resultado abajo."""
        self.heading("Estudio IA", f"{title}.", description, back=("Volver al Estudio IA", "Estudio IA"))
        _, error = self.ia_estado()
        if error:
            self.notice("Ollama no está disponible", error)
        campos = self.form("Parámetros", fields, values)
        generar = ctk.CTkButton(campos["_footer"], text="✦  Generar", fg_color=DARK, hover_color="#334033", height=40, width=170,
                                state="disabled" if error else "normal")
        generar.pack(side="left")
        self.label(campos["_footer"], f"Modelo: {self.ia_modelo}", 11, MUTED).pack(side="right")

        card = self.panel(self.content)
        card.pack(fill="x", padx=27, pady=(0, 25))
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 10))
        self.label(top, "Resultado", 16, DARK, True).pack(side="left")
        estado = self.label(top, "", 11, MUTED)
        estado.pack(side="left", padx=14)
        copiar = self.small_button(top, "Copiar", lambda: self._copiar(texto))
        copiar.pack(side="right", padx=(6, 0))
        detener = self.small_button(top, "Detener", self.detener_generacion, danger=True)
        detener.configure(state="disabled")
        detener.pack(side="right")
        texto = ctk.CTkTextbox(card, height=340, wrap="word", fg_color=SOFT, text_color=DARK, font=ctk.CTkFont(size=13), border_width=0)
        texto.pack(fill="x", padx=24)
        texto.insert("1.0", "Elige los parámetros y pulsa «Generar». Puedes editar el resultado antes de copiarlo.")
        extra = ctk.CTkFrame(card, fg_color="transparent")
        extra.pack(fill="x", padx=24, pady=(12, 22))
        return campos, {"generar": generar, "detener": detener, "estado": estado, "texto": texto, "extra": extra}

    def _copiar(self, texto):
        self.clipboard_clear()
        self.clipboard_append(texto.get("1.0", "end").strip())

    def detener_generacion(self):
        if self.generacion:
            self.generacion["detener"] = True
            self.generacion = None

    def ejecutar_ia(self, crear_prompt, ui, al_terminar=None):
        """Arma el prompt con datos de la BD y genera en segundo plano, mostrando el texto en vivo."""
        prompt, ok = self.intentar(crear_prompt)
        if not ok:
            return
        self.detener_generacion()
        estado = {"detener": False, "cola": queue.Queue()}
        self.generacion = estado
        modelo = self.ia_modelo

        def trabajar():
            try:
                for parte in ia.generar(prompt, modelo, detener=lambda: estado["detener"]):
                    estado["cola"].put(("texto", parte))
                estado["cola"].put(("fin", None))
            except ia.IANoDisponible as error:
                estado["cola"].put(("error", str(error)))
            except Exception as error:  # noqa: BLE001 — se muestra al usuario
                estado["cola"].put(("error", f"Error inesperado: {error}"))

        ui["texto"].delete("1.0", "end")
        ui["estado"].configure(text="Pensando… (la primera vez puede tardar mientras se carga el modelo)", text_color=MUTED)
        ui["generar"].configure(state="disabled")
        ui["detener"].configure(state="normal")
        threading.Thread(target=trabajar, daemon=True).start()
        self.after(60, self._leer_generacion, estado, ui, al_terminar)

    def _leer_generacion(self, estado, ui, al_terminar):
        if not ui["texto"].winfo_exists():
            return
        final = None
        try:
            while final is None:
                tipo, valor = estado["cola"].get_nowait()
                if tipo == "texto":
                    ui["texto"].insert("end", valor)
                    ui["texto"].see("end")
                    ui["estado"].configure(text="Escribiendo…")
                else:
                    final = (tipo, valor)
        except queue.Empty:
            pass
        if final is None and not estado["detener"]:
            self.after(60, self._leer_generacion, estado, ui, al_terminar)
            return
        if self.generacion is estado:
            self.generacion = None
        ui["generar"].configure(state="normal")
        ui["detener"].configure(state="disabled")
        if final and final[0] == "error":
            ui["estado"].configure(text="No se pudo generar", text_color=RED)
            ui["texto"].insert("end", ("\n\n" if ui["texto"].get("1.0", "end").strip() else "") + final[1])
        elif estado["detener"]:
            ui["estado"].configure(text="Detenido", text_color=AMBER)
        else:
            limpio = ia.limpiar_markdown(ui["texto"].get("1.0", "end"))
            ui["texto"].delete("1.0", "end")
            ui["texto"].insert("1.0", limpio)
            ui["estado"].configure(text="Listo ✓  ·  Revisa los datos: la IA puede equivocarse", text_color=GREEN)
            if al_terminar:
                al_terminar()

    def ai_inventory(self):
        campos, ui = self.ai_layout(
            "Análisis de inventario",
            "La IA revisa precios, días en inventario, favoritos y consultas de cada auto.",
            [("enfoque", "Enfoque", "option", ia.ENFOQUES_INVENTARIO),
             ("notas", "Indicaciones adicionales (opcional)", "text", None)],
            {"enfoque": ia.ENFOQUES_INVENTARIO[0]},
        )
        ui["generar"].configure(command=lambda: self.ejecutar_ia(
            lambda: ia.prompt_inventario(campos["enfoque"](), campos["notas"]()), ui))

    def ai_ad(self, id_vehiculo=None):
        vehiculos = [v for v in db.listar_vehiculos() if v["estado"] != "Vendido"]
        if not vehiculos:
            self.heading("Estudio IA", "Contenido para anuncios.", "Agrega un vehículo al inventario para poder redactar su anuncio.",
                         actions=[("＋  Nuevo vehículo", lambda: self.show_page("Vehículo"), "primary")],
                         back=("Volver al Estudio IA", "Estudio IA"))
            return
        opciones = {f"{v['marca']} {v['modelo']} {v['anio']}  (#{v['id']})": v["id"] for v in vehiculos}
        inicial = next((k for k, i in opciones.items() if i == id_vehiculo), next(iter(opciones)))
        campos, ui = self.ai_layout(
            "Contenido para anuncios",
            "Redacta el anuncio de un auto. Si te gusta, publícalo como su descripción en la tienda web.",
            [("vehiculo", "Vehículo", "option", list(opciones)),
             ("tono", "Tono", "option", ia.TONOS),
             ("canal", "Dónde se publicará", "option", ia.CANALES),
             ("destacar", "Qué destacar (opcional)", "text", None)],
            {"vehiculo": inicial, "tono": ia.TONOS[0], "canal": ia.CANALES[0]},
        )
        usar = ctk.CTkButton(ui["extra"], text="Usar como descripción en la tienda  ↗", fg_color=LIME, hover_color="#e5ff83",
                             text_color=DARK, height=38, width=260, state="disabled")
        usar.pack(side="left")
        self.label(ui["extra"], "Máximo 500 caracteres. Puedes editar el texto antes de publicarlo.", 11, MUTED).pack(side="left", padx=14)

        def publicar():
            id_elegido = opciones[campos["vehiculo"]()]
            texto = ui["texto"].get("1.0", "end").strip()
            if len(texto) > 500:
                messagebox.showwarning("Texto muy largo", f"La descripción tiene {len(texto)} caracteres; recórtala a 500 o menos.", parent=self)
                return
            _, ok = self.intentar(db.actualizar_descripcion, id_elegido, texto)
            if ok:
                self.toast("Publicado · la descripción ya aparece en la tienda web")

        usar.configure(command=publicar)
        ui["generar"].configure(command=lambda: self.ejecutar_ia(
            lambda: ia.prompt_anuncio(opciones[campos["vehiculo"]()], campos["tono"](), campos["canal"](), campos["destacar"]()),
            ui, al_terminar=lambda: usar.configure(state="normal")))

    def ai_sales(self):
        campos, ui = self.ai_layout(
            "Perspectivas de ventas",
            "La IA revisa ventas, consultas de la web, clientes y los autos con más interés.",
            [("periodo", "Periodo", "option", list(ia.PERIODOS)),
             ("objetivo", "Objetivo comercial (opcional)", "text", None)],
            {"periodo": next(iter(ia.PERIODOS))},
        )
        ui["generar"].configure(command=lambda: self.ejecutar_ia(
            lambda: ia.prompt_ventas(campos["periodo"](), campos["objetivo"]()), ui))

    # ------------------------------------------------------------ lanzador / web

    def launcher(self):
        self.heading("Centro de aplicaciones", "Tu lanzador.", "Abre la tienda web conectada a esta misma base de datos.")
        card = self.panel(self.content)
        card.pack(fill="x", padx=27, pady=(0, 20))
        self.label(card, "◈   TIENDA WEB", 10, "#8ca259", True).pack(anchor="w", padx=25, pady=(24, 10))
        self.label(card, "Tu escaparate digital.", 21, DARK, True).pack(anchor="w", padx=25)
        estado = "encendido" if self.servidor_activo() else "apagado"
        self.label(card, f"Servidor web: {estado}  ·  {config.WEB_URL}", 12, MUTED).pack(anchor="w", padx=25, pady=(8, 18))
        ctk.CTkButton(card, text="Abrir tienda web   ↗", command=self.open_website, fg_color=DARK, hover_color="#334033", height=42, width=180).pack(anchor="w", padx=25, pady=(0, 24))
        self.notice("Cómo funciona", "Si el servidor no está encendido, el panel lo inicia en segundo plano y lo detiene al cerrar la aplicación. "
                                     "También puedes encenderlo por separado con «python servidor/app.py».")

    @staticmethod
    def servidor_activo():
        try:
            with urllib.request.urlopen(f"{config.WEB_URL}/api/sesion", timeout=1):
                return True
        except OSError:
            return False

    def open_website(self):
        if self.servidor_activo():
            self._abrir_navegador()
            return
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            self.servidor = subprocess.Popen([sys.executable, str(RAIZ / "servidor" / "app.py")], cwd=RAIZ, creationflags=flags)
        except OSError as error:
            messagebox.showerror("No se pudo iniciar la tienda", str(error), parent=self)
            return
        self.toast("Encendiendo la tienda web…")
        self._esperar_servidor(time.time())

    def _esperar_servidor(self, inicio):
        """Revisa cada 300 ms si el servidor ya responde, sin congelar la ventana."""
        if self.servidor_activo():
            self._abrir_navegador()
        elif self.servidor and self.servidor.poll() is not None or time.time() - inicio > 10:
            messagebox.showerror("No se pudo iniciar la tienda",
                                 "El servidor web no respondió. Ejecuta «iniciar_web.bat» para ver el error.", parent=self)
        else:
            self.after(300, self._esperar_servidor, inicio)

    def _abrir_navegador(self):
        if not webbrowser.open(config.WEB_URL):
            messagebox.showerror("No se pudo abrir la tienda", f"Abre manualmente {config.WEB_URL} en tu navegador.", parent=self)
        if self.current_page == "Lanzador":
            self.refrescar()


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    MotorhausApp().mainloop()
