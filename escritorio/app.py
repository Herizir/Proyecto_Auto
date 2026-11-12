"""Plantilla de interfaz de escritorio para Motorhaus."""

from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import webbrowser

import customtkinter as ctk


ROOT = Path(__file__).resolve().parent.parent
WEB_PAGE = ROOT / "web" / "index.html"

BG = "#f4f6ef"
WHITE = "#ffffff"
DARK = "#171d18"
SIDEBAR = "#111612"
MUTED = "#7e897c"
LINE = "#e7ebe3"
LIME = "#d8f65b"
SOFT = "#f0f3eb"

VEHICLES = [
    ("Porsche", "911 Carrera", "2023", "$2,450,000", "Disponible"),
    ("Mercedes-Benz", "Clase C", "2022", "$985,000", "Disponible"),
    ("BMW", "X5", "2023", "$1,490,000", "Reservado"),
    ("Audi", "Q5", "2022", "$895,000", "Disponible"),
    ("BMW", "Serie 3", "2023", "$920,000", "Disponible"),
    ("Porsche", "718 Cayman", "2022", "$1,750,000", "Disponible"),
]

NAV_ITEMS = [
    ("Resumen", "◫"),
    ("Inventario", "▦"),
    ("Clientes", "♙"),
    ("Ventas", "↗"),
    ("Estudio IA", "✦"),
    ("Lanzador", "◈"),
    ("Configuración", "⚙"),
]


class MotorhausApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Motorhaus | Panel de control")
        self.geometry("1440x900")
        self.minsize(1000, 680)
        self.configure(fg_color=BG)
        self.nav_buttons = {}
        self.current_page = "Resumen"
        self.access_container = None
        self._build_layout()
        self.show_page("Resumen")
        self.show_access()

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
        ctk.CTkLabel(bottom, text="●  MODO DEMOSTRACIÓN", text_color=LIME, font=ctk.CTkFont(size=9, weight="bold")).pack(anchor="w", padx=14, pady=(13, 3))
        ctk.CTkLabel(bottom, text="Datos de ejemplo, sin conexión", text_color="#a2aea0", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=14, pady=(0, 13))

        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main = main
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(main, height=70, fg_color=WHITE, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        ctk.CTkLabel(header, text="MOTORHAUS   /   PANEL DE CONTROL", text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=35)
        ctk.CTkButton(header, text="Salir de la demo", command=self.show_access, fg_color="transparent", hover_color=SOFT, text_color=DARK, width=120, height=32).pack(side="right", padx=25)
        ctk.CTkLabel(header, text="ADMINISTRACIÓN   ●", text_color="#6e7c6a", font=ctk.CTkFont(size=10, weight="bold")).pack(side="right")
        self.content = ctk.CTkScrollableFrame(main, fg_color=BG, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.content.grid_columnconfigure(0, weight=1)

    def show_page(self, page):
        self.current_page = page
        for name, button in self.nav_buttons.items():
            active = name == page
            button.configure(fg_color="#293525" if active else "transparent", text_color=LIME if active else "#a7b2a5")
        for widget in self.content.winfo_children():
            widget.destroy()
        pages = {
            "Resumen": self.dashboard,
            "Inventario": self.inventory,
            "Clientes": self.clients,
            "Ventas": self.sales,
            "Estudio IA": self.ai_studio,
            "Lanzador": self.launcher,
            "Configuración": self.settings,
            "Nuevo vehículo": lambda: self.record_form("Nuevo vehículo", "Inventario", [("Marca", "Ej. BMW"), ("Modelo", "Ej. X5"), ("Año", "Ej. 2023"), ("Precio (MXN)", "Ej. 1490000"), ("Kilometraje", "Ej. 12300"), ("Estado", "Ej. Disponible")]),
            "Nuevo cliente": lambda: self.record_form("Nuevo cliente", "Clientes", [("Nombre completo", "Nombre del cliente"), ("Correo electrónico", "correo@ejemplo.com"), ("Teléfono", "Número de contacto"), ("Vehículo de interés", "Ej. SUV"), ("Notas", "Información adicional")]),
            "Nueva venta": lambda: self.record_form("Nueva venta", "Ventas", [("Cliente", "Nombre del cliente"), ("Vehículo", "Modelo de interés"), ("Precio acordado (MXN)", "Importe"), ("Estado", "Ej. En seguimiento"), ("Notas", "Detalles de la oportunidad")]),
            "Análisis de inventario": lambda: self.ai_tool("Análisis de inventario", "Vehículos a considerar", "Selecciona la información que se analizará en una futura integración.", ["Inventario completo", "Disponibilidad", "Tiempo en inventario"]),
            "Contenido para anuncios": lambda: self.ai_tool("Contenido para anuncios", "Preparar un anuncio", "Define el vehículo y el estilo para una futura propuesta de contenido.", ["Vehículo de ejemplo", "Características destacadas", "Tono del anuncio"]),
            "Perspectivas de ventas": lambda: self.ai_tool("Perspectivas de ventas", "Explorar oportunidades", "Elige un periodo y el enfoque para un futuro análisis comercial.", ["Periodo de análisis", "Tipo de vehículo", "Objetivo comercial"]),
        }
        pages[page]()

    def show_access(self, recovery=False):
        self.sidebar.grid_remove()
        self.main.grid_remove()
        if self.access_container is not None:
            self.access_frame.destroy()
            self.access_container.destroy()
        self.access_container = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.access_container.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.access_container.grid_columnconfigure(0, weight=1)
        self.access_container.grid_rowconfigure(0, weight=1)
        self.access_frame = ctk.CTkScrollableFrame(self.access_container, fg_color=BG, corner_radius=0)
        self.access_frame.grid(row=0, column=0, sticky="nsew")
        card = self.panel(self.access_frame, width=460)
        card.pack(pady=60, padx=30)
        card.pack_propagate(True)
        self.label(card, "m.   MOTORHAUS", 22, DARK, True).pack(anchor="w", padx=35, pady=(30, 20))
        self.label(card, "●  ACCESO AL PANEL", 10, "#879582", True).pack(anchor="w", padx=35)
        title = "Recuperar acceso." if recovery else "Bienvenido de nuevo."
        self.label(card, title, 28, DARK, True).pack(anchor="w", padx=35, pady=(10, 4))
        description = "Solicita un enlace de recuperación en una versión futura." if recovery else "Tu espacio de trabajo, en un solo lugar."
        self.label(card, description, 12, MUTED, wraplength=380, justify="left").pack(anchor="w", padx=35)
        self.label(card, "Solo una interfaz: no ingreses credenciales reales.\nNo se autentica ni se envía información.", 11, "#637758", justify="left").pack(anchor="w", padx=35, pady=(18, 12))
        self.access_entry(card, "Correo electrónico", "correo@ejemplo.com")
        if not recovery:
            self.access_entry(card, "Contraseña", "Contraseña", password=True)
            ctk.CTkButton(card, text="¿Olvidaste tu contraseña?", command=lambda: self.show_access(True), fg_color="transparent", hover_color=SOFT, text_color=DARK, anchor="w", width=180).pack(anchor="w", padx=30)
        ctk.CTkButton(card, text="Enviar enlace · Próximamente" if recovery else "Iniciar sesión · Próximamente", state="disabled", width=340, height=42).pack(fill="x", padx=35, pady=(12, 8))
        if recovery:
            ctk.CTkButton(card, text="← Volver al acceso", command=self.show_access, fg_color="transparent", hover_color=SOFT, text_color=DARK, width=180).pack(anchor="w", padx=30, pady=(0, 30))
        else:
            ctk.CTkButton(card, text="Entrar en modo demostración  ↗", command=self.enter_demo, fg_color=DARK, hover_color="#334033", text_color="white", height=42).pack(fill="x", padx=35, pady=(0, 30))

    def access_entry(self, parent, title, placeholder, password=False):
        self.label(parent, title, 11, DARK, True).pack(anchor="w", padx=35, pady=(8, 4))
        ctk.CTkEntry(parent, placeholder_text=placeholder, show="*" if password else "", height=40, width=340, fg_color=WHITE, border_color=LINE).pack(fill="x", padx=35)

    def enter_demo(self):
        self.access_frame.destroy()
        self.access_container.destroy()
        self.access_container = None
        self.sidebar.grid()
        self.main.grid()
        self.show_page("Resumen")

    def heading(self, eyebrow, title, description, action=None):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.pack(fill="x", padx=27, pady=(29, 25))
        if action:
            ctk.CTkButton(frame, text="Abrir tienda   ↗", command=self.open_website, fg_color=DARK, hover_color="#334033", text_color="white", height=42, width=145, corner_radius=5).pack(side="right", anchor="s")
        text = ctk.CTkFrame(frame, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text, text=f"●  {eyebrow.upper()}", text_color="#879582", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(text, text=title, text_color=DARK, font=ctk.CTkFont(size=30, weight="bold")).pack(anchor="w", pady=(8, 2))
        ctk.CTkLabel(text, text=description, text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=650, justify="left").pack(anchor="w")

    def panel(self, parent, **kwargs):
        return ctk.CTkFrame(parent, fg_color=WHITE, corner_radius=8, **kwargs)

    def label(self, parent, text, size=12, color=DARK, bold=False, **kwargs):
        return ctk.CTkLabel(parent, text=text, text_color=color, font=ctk.CTkFont(size=size, weight="bold" if bold else "normal"), **kwargs)

    def dashboard(self):
        self.heading("Vista general", "Todo comienza aquí.", "Un vistazo a tu operación y a las oportunidades que vienen.", action=True)
        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=27)
        body.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stats")
        stats = [
            ("VEHÍCULOS EN INVENTARIO", "24", "↗  4 nuevos este mes"),
            ("CLIENTES POTENCIALES", "38", "↗  12 nuevos contactos"),
            ("VENTAS DEL MES", "08", "↗  2 más que el mes anterior"),
            ("VALOR DEL INVENTARIO", "$18.4M", "MXN  ·  valor estimado"),
        ]
        for column, (title, value, note) in enumerate(stats):
            card = self.panel(body)
            card.grid(row=0, column=column, sticky="nsew", padx=(0, 12) if column < 3 else 0)
            self.label(card, title, 9, MUTED, True).pack(anchor="w", padx=18, pady=(20, 12))
            self.label(card, value, 29, DARK, True).pack(anchor="w", padx=18)
            self.label(card, note, 10, "#799254").pack(anchor="w", padx=18, pady=(10, 20))

        middle = ctk.CTkFrame(body, fg_color="transparent")
        middle.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(18, 0))
        middle.grid_columnconfigure(0, weight=3)
        middle.grid_columnconfigure(1, weight=2)
        welcome = ctk.CTkFrame(middle, fg_color=DARK, corner_radius=8)
        welcome.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        self.label(welcome, "TU NEGOCIO, EN MOVIMIENTO  ↗", 10, LIME, True).pack(anchor="w", padx=25, pady=(24, 10))
        self.label(welcome, "Buenas decisiones.\nMejores caminos.", 25, "white", True, justify="left").pack(anchor="w", padx=25)
        self.label(welcome, "Todo lo que necesitas para gestionar tu tienda,\nen un solo lugar.", 12, "#abb8a8", justify="left").pack(anchor="w", padx=25, pady=(12, 18))
        ctk.CTkButton(welcome, text="Explorar inventario   ↗", command=lambda: self.show_page("Inventario"), fg_color=LIME, hover_color="#e5ff83", text_color=DARK, width=170, height=38, corner_radius=4).pack(anchor="w", padx=25, pady=(0, 24))

        ai = self.panel(middle)
        ai.grid(row=0, column=1, sticky="nsew")
        self.label(ai, "✦  ESTUDIO IA", 10, "#8ca259", True).pack(anchor="w", padx=23, pady=(24, 14))
        self.label(ai, "Ideas que impulsan.", 20, DARK, True).pack(anchor="w", padx=23)
        self.label(ai, "Un espacio para descubrir oportunidades,\ncrear contenido y analizar tu inventario.", 12, MUTED, justify="left").pack(anchor="w", padx=23, pady=(10, 18))
        ctk.CTkButton(ai, text="Explorar estudio IA   ↗", command=lambda: self.show_page("Estudio IA"), fg_color=SOFT, hover_color="#e5ebdf", text_color=DARK, height=38, width=170, corner_radius=4).pack(anchor="w", padx=23, pady=(0, 24))

        self.vehicle_table(body, row=2, title="Inventario reciente", limit=4)
        self.label(body, "Datos y métricas de ejemplo · Sin conexión a servicios ni almacenamiento", 10, MUTED).grid(row=3, column=0, columnspan=4, sticky="w", pady=(16, 25))

    def vehicle_table(self, parent, row=None, title="Vehículos", limit=None):
        card = self.panel(parent)
        if row is None:
            card.pack(fill="x", padx=27, pady=(0, 25))
        else:
            card.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(18, 0))
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(18, 12))
        self.label(top, title, 16, DARK, True).pack(side="left")
        if row is not None:
            ctk.CTkButton(top, text="Ver inventario  ↗", command=lambda: self.show_page("Inventario"), fg_color="transparent", hover_color=SOFT, text_color=DARK, width=125, height=28).pack(side="right")
        table = ctk.CTkFrame(card, fg_color="transparent")
        table.pack(fill="x", padx=20, pady=(0, 18))
        for col, weight in enumerate((3, 2, 1, 2, 2)):
            table.grid_columnconfigure(col, weight=weight, uniform="table")
        for col, text in enumerate(("VEHÍCULO", "MODELO", "AÑO", "PRECIO", "ESTADO")):
            self.label(table, text, 9, MUTED, True, anchor="w").grid(row=0, column=col, sticky="ew", pady=(0, 10))
        for index, vehicle in enumerate(VEHICLES[:limit] if limit else VEHICLES, start=1):
            for col, value in enumerate(vehicle):
                color = "#749052" if col == 4 and value == "Disponible" else ("#aa8d50" if col == 4 else DARK)
                self.label(table, value, 11, color, col == 0, anchor="w").grid(row=index, column=col, sticky="ew", pady=9)

    def inventory(self):
        self.heading("Gestión de vehículos", "Inventario.", "Una selección de vehículos de ejemplo para visualizar tu operación.", action=True)
        self.page_action("＋  Nuevo vehículo", "Nuevo vehículo")
        self.vehicle_table(self.content, title="Todos los vehículos · 6 ejemplos")
        self.notice("Vista de demostración", "El inventario es ilustrativo; todavía no permite guardar, editar ni publicar vehículos.")

    def clients(self):
        self.heading("Relaciones", "Clientes.", "Un espacio para acompañar cada relación de principio a fin.")
        self.page_action("＋  Nuevo cliente", "Nuevo cliente")
        self.example_list("Contactos recientes", [
            ("Andrea Martínez", "Interés: SUV", "Nuevo contacto"),
            ("Diego Rivera", "Interés: deportivo", "Seguimiento"),
            ("Sofía Torres", "Interés: sedán", "Nuevo contacto"),
        ])
        self.notice("Vista de demostración", "Estos contactos son ficticios y no se almacenan ni se envían a ningún servicio.")

    def sales(self):
        self.heading("Operación", "Ventas.", "Visualiza el recorrido de cada oportunidad en un solo lugar.")
        self.page_action("＋  Nueva venta", "Nueva venta")
        self.example_list("Oportunidades recientes", [
            ("Porsche 911 Carrera", "Cotización de ejemplo", "En seguimiento"),
            ("BMW X5", "Cotización de ejemplo", "Reservado"),
            ("Mercedes-Benz Clase C", "Cotización de ejemplo", "Nueva oportunidad"),
        ])
        self.notice("Vista de demostración", "Esta pantalla es una plantilla; no registra ventas ni procesa pagos.")

    def example_list(self, title, rows):
        card = self.panel(self.content)
        card.pack(fill="x", padx=27, pady=(0, 20))
        self.label(card, title, 16, DARK, True).pack(anchor="w", padx=22, pady=(20, 10))
        for name, detail, status in rows:
            line = ctk.CTkFrame(card, fg_color="transparent")
            line.pack(fill="x", padx=22, pady=10)
            self.label(line, name, 12, DARK, True).pack(side="left")
            self.label(line, status, 11, "#799254").pack(side="right")
            self.label(line, detail, 11, MUTED).pack(side="right", padx=35)

    def notice(self, title, description):
        card = ctk.CTkFrame(self.content, fg_color="#eaf0df", corner_radius=8)
        card.pack(fill="x", padx=27, pady=(0, 25))
        self.label(card, title, 12, DARK, True).pack(anchor="w", padx=20, pady=(15, 2))
        self.label(card, description, 11, MUTED, wraplength=700, justify="left").pack(anchor="w", padx=20, pady=(0, 15))

    def page_action(self, text, page):
        ctk.CTkButton(self.content, text=text, command=lambda: self.show_page(page), fg_color=DARK, hover_color="#334033", height=40, width=170).pack(anchor="w", padx=27, pady=(0, 18))

    def record_form(self, title, back, fields):
        self.heading("Plantilla de formulario", f"{title}.", "Completa los campos para visualizar el formulario. Los datos no se guardan.")
        self.page_action(f"←  Volver a {back}", back)
        card = self.panel(self.content)
        card.pack(fill="x", padx=27, pady=(0, 20))
        self.label(card, "Información general", 16, DARK, True).pack(anchor="w", padx=24, pady=(20, 10))
        for title, placeholder in fields:
            self.label(card, title, 11, DARK, True).pack(anchor="w", padx=24, pady=(8, 4))
            ctk.CTkEntry(card, placeholder_text=placeholder, height=40, fg_color=WHITE, border_color=LINE).pack(fill="x", padx=24)
        ctk.CTkButton(card, text="Guardar · Próximamente", state="disabled", height=40).pack(anchor="w", padx=24, pady=24)
        self.notice("Sin almacenamiento", "Este formulario es una maqueta. Los datos se descartan al cambiar de pantalla.")

    def settings(self):
        self.heading("Espacio de trabajo", "Configuración.", "Plantillas para el perfil y las preferencias de tu tienda.")
        card = self.panel(self.content)
        card.pack(fill="x", padx=27, pady=(0, 20))
        self.label(card, "Perfil de administración", 16, DARK, True).pack(anchor="w", padx=24, pady=(20, 10))
        for title, placeholder in [("Nombre", "Administrador de ejemplo"), ("Correo electrónico", "correo@ejemplo.com"), ("Nombre de la tienda", "Motorhaus")]:
            self.label(card, title, 11, DARK, True).pack(anchor="w", padx=24, pady=(8, 4))
            ctk.CTkEntry(card, placeholder_text=placeholder, height=40, fg_color=WHITE, border_color=LINE).pack(fill="x", padx=24)
        ctk.CTkButton(card, text="Guardar cambios · Próximamente", state="disabled", height=40).pack(anchor="w", padx=24, pady=24)
        self.notice("Configuración de muestra", "Los cambios no se guardan y no hay cuentas ni permisos conectados.")

    def ai_tool(self, title, subtitle, description, fields):
        self.heading("Estudio IA · plantilla", f"{title}.", description)
        self.page_action("←  Volver al estudio IA", "Estudio IA")
        card = self.panel(self.content)
        card.pack(fill="x", padx=27, pady=(0, 20))
        self.label(card, subtitle, 16, DARK, True).pack(anchor="w", padx=24, pady=(20, 10))
        for field in fields:
            self.label(card, field, 11, DARK, True).pack(anchor="w", padx=24, pady=(8, 4))
            ctk.CTkEntry(card, placeholder_text="Dato de ejemplo", height=40, fg_color=WHITE, border_color=LINE).pack(fill="x", padx=24)
        ctk.CTkButton(card, text="Generar · Próximamente", state="disabled", height=40).pack(anchor="w", padx=24, pady=24)
        self.notice("Resultado futuro", "Aquí aparecerá el resultado cuando exista una integración. No hay modelo ni datos conectados.")

    def ai_studio(self):
        self.heading("Próximamente · sin conexión", "Estudio IA.", "Herramientas pensadas para ayudarte a tomar mejores decisiones. Solo interfaces.")
        intro = ctk.CTkFrame(self.content, fg_color=DARK, corner_radius=8)
        intro.pack(fill="x", padx=27, pady=(0, 18))
        self.label(intro, "✦   UN NUEVO COPILOTO PARA TU NEGOCIO", 10, LIME, True).pack(anchor="w", padx=25, pady=(22, 8))
        self.label(intro, "Más ideas. Mejores oportunidades.", 22, "white", True).pack(anchor="w", padx=25)
        self.label(intro, "La futura integración con Ollama vivirá aquí. Por ahora, estas herramientas son solo visuales.", 12, "#abb8a8", wraplength=700, justify="left").pack(anchor="w", padx=25, pady=(8, 22))
        cards = ctk.CTkFrame(self.content, fg_color="transparent")
        cards.pack(fill="x", padx=27, pady=(0, 18))
        cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="ai")
        tools = [
            ("◇", "Análisis de inventario", "Detecta oportunidades y vehículos que necesitan atención.", "Ver plantilla"),
            ("✎", "Contenido para anuncios", "Prepara descripciones para presentar cada vehículo.", "Ver plantilla"),
            ("↗", "Perspectivas de ventas", "Explora tendencias y posibles oportunidades comerciales.", "Ver plantilla"),
        ]
        for col, (icon, title, description, action) in enumerate(tools):
            card = self.panel(cards)
            card.grid(row=0, column=col, sticky="nsew", padx=(0, 14) if col < 2 else 0)
            self.label(card, icon, 25, "#87a341").pack(anchor="w", padx=20, pady=(20, 8))
            self.label(card, title, 15, DARK, True).pack(anchor="w", padx=20)
            self.label(card, description, 11, MUTED, wraplength=210, justify="left").pack(anchor="w", padx=20, pady=(10, 15))
            ctk.CTkButton(card, text=f"{action}  ↗", command=lambda page=title: self.show_page(page), fg_color=SOFT, hover_color="#e5ebdf", text_color=DARK, height=35, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=20, pady=(0, 20))
        self.notice("Sin modelo conectado", "No se ejecutan modelos, no se envían datos y no hay integración con Ollama en esta plantilla.")

    def launcher(self):
        self.heading("Centro de aplicaciones", "Tu lanzador.", "Accede a las interfaces de Motorhaus desde un mismo lugar.")
        card = self.panel(self.content)
        card.pack(fill="x", padx=27, pady=(0, 20))
        self.label(card, "◈   TIENDA WEB", 10, "#8ca259", True).pack(anchor="w", padx=25, pady=(24, 10))
        self.label(card, "Tu escaparate digital.", 21, DARK, True).pack(anchor="w", padx=25)
        self.label(card, "Abre la plantilla de la tienda en tu navegador predeterminado.", 12, MUTED).pack(anchor="w", padx=25, pady=(8, 18))
        ctk.CTkButton(card, text="Abrir tienda web   ↗", command=self.open_website, fg_color=DARK, hover_color="#334033", height=42, width=180).pack(anchor="w", padx=25, pady=(0, 24))
        self.notice("Modo local", "El lanzador abre el archivo HTML local. No inicia servidores ni administra servicios.")

    def open_website(self):
        if not WEB_PAGE.is_file():
            messagebox.showerror("Tienda no encontrada", f"No se encontró la plantilla web:\n{WEB_PAGE}", parent=self)
            return
        try:
            opened = webbrowser.open(WEB_PAGE.as_uri())
        except webbrowser.Error as error:
            messagebox.showerror("No se pudo abrir la tienda", str(error), parent=self)
            return
        if not opened:
            messagebox.showerror("No se pudo abrir la tienda", "No hay un navegador disponible para abrir la plantilla.", parent=self)


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    MotorhausApp().mainloop()
