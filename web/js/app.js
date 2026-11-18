// Tienda: inventario, favoritos y consultas, todo desde la base de datos MOTORHAUS.

const grid = document.querySelector("#vehiculos");
const tipo = document.querySelector("#tipo");
const orden = document.querySelector("#orden");
const busqueda = document.querySelector("#busqueda");
const tabs = document.querySelector("#tabs");
const dialogo = document.querySelector("#detalle");
const contenidoDetalle = document.querySelector("#detalle-contenido");

let autos = [];
let favoritos = new Set();
let usuario = null;
let filtro = "todos";

const SILUETA = `<svg class="car-silhouette" viewBox="0 0 120 48" aria-hidden="true"><path d="M8 34c0-5 3-8 9-9l14-3 13-10c3-2 6-3 10-3h20c4 0 7 1 10 4l9 9 13 2c5 1 8 4 8 9v4c0 2-1 3-3 3h-8a10 10 0 0 0-19 0H40a10 10 0 0 0-19 0h-10c-2 0-3-1-3-3z" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/><circle cx="30" cy="40" r="6" fill="none" stroke="currentColor" stroke-width="2.5"/><circle cx="94" cy="40" r="6" fill="none" stroke="currentColor" stroke-width="2.5"/><path d="M47 22l9-8h22l8 8z" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/></svg>`;

function imagenAuto(auto, clase) {
  if (auto.imagen) return `<div class="${clase}" style="background-image:url('${escapar(auto.imagen)}')">`;
  return `<div class="${clase} no-image">${SILUETA}<span class="no-image-brand">${escapar(auto.marca)}</span>`;
}

function etiquetaDe(auto) {
  if (auto.estado === "Reservado") return '<span class="car-tag reserved">RESERVADO</span>';
  return auto.etiqueta ? `<span class="car-tag">${escapar(auto.etiqueta)}</span>` : "";
}

function tarjeta(auto) {
  const favorito = favoritos.has(auto.id);
  return `
    <article class="car-card" data-details="${auto.id}" tabindex="0" role="button" aria-label="Ver detalles de ${escapar(auto.marca)} ${escapar(auto.modelo)}">
      ${imagenAuto(auto, "car-image")}
        ${etiquetaDe(auto)}
        <button type="button" class="favorite ${favorito ? "selected" : ""}" data-favorite="${auto.id}" aria-label="${favorito ? "Quitar de favoritos" : "Agregar a favoritos"}" aria-pressed="${favorito}">${favorito ? "♥" : "♡"}</button>
      </div>
      <div class="car-body">
        <div class="car-top"><div><span class="car-brand">${escapar(auto.marca)}</span><h3>${escapar(auto.modelo)}</h3><p class="car-subtitle">${escapar(auto.version || auto.tipo)}</p></div><span class="car-arrow" aria-hidden="true">↗</span></div>
        <div class="car-specs"><span>◷ &nbsp;${auto.anio}</span><span>◉ &nbsp;${numero.format(auto.kilometraje)} km</span><span>◇ &nbsp;${escapar(auto.combustible)}</span></div>
        <div class="car-bottom"><div><small>PRECIO</small><strong>${moneda.format(auto.precio)}</strong></div><span class="details-button">Ver detalles ↗</span></div>
      </div>
    </article>`;
}

function esqueleto() {
  return Array.from({ length: 6 }, () => `
    <div class="car-card skeleton" aria-hidden="true"><div class="car-image"></div><div class="car-body"><i></i><i></i><i class="short"></i></div></div>`).join("");
}

function pintarFiltros() {
  const presentes = [...new Set(autos.map(auto => auto.tipo))].sort();
  const opciones = ["todos", ...presentes];
  if (usuario) opciones.push("favoritos");
  tabs.innerHTML = opciones.map(t => {
    const nombre = t === "todos" ? "Todos" : t === "favoritos" ? `♥ Mis favoritos (${favoritos.size})` : escapar(t);
    return `<button type="button" class="tab" data-filter="${escapar(t)}">${nombre}</button>`;
  }).join("");
  tipo.innerHTML = `<option value="todos">Todos los modelos</option>` +
    presentes.map(t => `<option value="${escapar(t)}">${escapar(t)}</option>`).join("");
}

function pintarEstadisticas() {
  const disponibles = autos.filter(a => a.estado === "Disponible");
  const marcas = new Set(autos.map(a => a.marca)).size;
  const desde = Math.min(...autos.map(a => a.precio));
  document.querySelector("#hero-stats").textContent = autos.length
    ? `${disponibles.length} AUTOS DISPONIBLES · ${marcas} MARCAS · DESDE ${moneda.format(desde)}`
    : "";
}

function normalizar(texto) {
  return String(texto ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function seleccionActual() {
  const texto = normalizar(busqueda.value.trim());
  const seleccion = autos.filter(auto =>
    (filtro === "todos" || (filtro === "favoritos" ? favoritos.has(auto.id) : auto.tipo === filtro)) &&
    (!texto || normalizar(`${auto.marca} ${auto.modelo} ${auto.version} ${auto.tipo} ${auto.anio}`).includes(texto)));
  const criterios = {
    menor: (a, b) => a.precio - b.precio,
    mayor: (a, b) => b.precio - a.precio,
    nuevo: (a, b) => b.anio - a.anio,
    km: (a, b) => a.kilometraje - b.kilometraje,
  };
  if (criterios[orden.value]) seleccion.sort(criterios[orden.value]);
  return seleccion;
}

function mostrarAutos() {
  const seleccion = seleccionActual();
  document.querySelector("#resultados").textContent = `${seleccion.length} vehículo${seleccion.length === 1 ? "" : "s"}`;
  tabs.querySelectorAll(".tab").forEach(tab => {
    const activa = tab.dataset.filter === filtro;
    tab.classList.toggle("active", activa);
    tab.setAttribute("aria-pressed", String(activa));
  });
  if (filtro !== "favoritos") tipo.value = filtro;
  grid.setAttribute("aria-busy", "false");
  if (seleccion.length) {
    grid.innerHTML = seleccion.map(tarjeta).join("");
    return;
  }
  const mensaje = filtro === "favoritos" && !busqueda.value
    ? "Aún no tienes favoritos. Toca el ♡ de cualquier auto para guardarlo."
    : "No encontramos autos con esos filtros.";
  grid.innerHTML = `<div class="empty"><p>${mensaje}</p><button type="button" class="details-button" id="limpiar">Ver todo el inventario</button></div>`;
}

async function cargar() {
  grid.innerHTML = esqueleto();
  try {
    const [catalogo, sesion] = await Promise.all([api("/api/vehiculos"), api("/api/sesion")]);
    autos = catalogo.vehiculos;
    usuario = sesion.usuario;
    favoritos = new Set(sesion.favoritos);
    etiquetaCuenta(usuario);
    if (usuario) document.querySelector("#nota-inventario").textContent = "Precios en pesos mexicanos. Tus favoritos se guardan en tu cuenta.";
    prellenar(document.querySelector("#form-contacto"));
    pintarFiltros();
    pintarEstadisticas();
    mostrarAutos();
    // El inventario cambia la altura de la página: si se entró con #seccion, volver a ubicarla.
    const destino = location.hash && document.querySelector(location.hash);
    if (destino) destino.scrollIntoView({ behavior: "instant" });
    actualizarEncabezado();
  } catch (error) {
    grid.setAttribute("aria-busy", "false");
    grid.innerHTML = `<div class="empty"><p>${escapar(error.message)}</p><button type="button" class="details-button" id="reintentar">Reintentar</button></div>`;
  }
}

function prellenar(formulario) {
  if (!usuario || !formulario) return;
  formulario.nombre.value ||= usuario.nombre;
  formulario.correo.value ||= usuario.correo;
  if (usuario.telefono) formulario.telefono.value ||= usuario.telefono;
}

async function alternarFavorito(id) {
  if (!usuario) {
    aviso("Inicia sesión en «Mi cuenta» para guardar tus favoritos.", "error");
    return;
  }
  const quitar = favoritos.has(id);
  try {
    const respuesta = await api(`/api/favoritos/${id}`, { metodo: quitar ? "DELETE" : "PUT" });
    favoritos = new Set(respuesta.favoritos);
    pintarFiltros();
    mostrarAutos();
    aviso(quitar ? "Quitado de favoritos." : "Guardado en tus favoritos.");
  } catch (error) {
    aviso(error.message, "error");
  }
}

function formularioConsulta(auto) {
  return `
    <form class="lead-form" id="form-consulta">
      <h3>¿Te interesa este auto?</h3>
      <p class="lead-help">Déjanos tus datos y un asesor te contacta para resolver tus dudas o agendar una visita.</p>
      <div class="form-grid">
        <label>Nombre<input name="nombre" required maxlength="100" autocomplete="name"></label>
        <label>Correo<input name="correo" type="email" required maxlength="150" autocomplete="email"></label>
        <label>Teléfono<input name="telefono" type="tel" maxlength="20" autocomplete="tel"></label>
      </div>
      <label>Mensaje<textarea name="mensaje" rows="3" maxlength="1000">Hola, me interesa el ${escapar(auto.marca)} ${escapar(auto.modelo)} ${auto.anio}.</textarea></label>
      <p class="form-message" aria-live="polite"></p>
      <button class="button button-dark" type="submit">Enviar consulta <span>↗</span></button>
    </form>`;
}

function abrirDetalle(auto) {
  const favorito = favoritos.has(auto.id);
  const ficha = [
    ["Año", auto.anio], ["Kilometraje", `${numero.format(auto.kilometraje)} km`],
    ["Combustible", auto.combustible], ["Tipo", auto.tipo], ["Color", auto.color || "—"], ["Estado", auto.estado],
  ];
  contenidoDetalle.innerHTML = `
    ${imagenAuto(auto, "modal-image")}${etiquetaDe(auto)}</div>
    <span class="car-brand">${escapar(auto.marca)}</span>
    <h2 id="detalle-titulo">${escapar(auto.modelo)}</h2>
    ${auto.version ? `<p class="modal-version">${escapar(auto.version)}</p>` : ""}
    <div class="modal-price"><div><small>PRECIO</small><strong>${moneda.format(auto.precio)}</strong></div>
      <button type="button" class="details-button modal-fav" data-favorite="${auto.id}" aria-pressed="${favorito}">${favorito ? "♥ En favoritos" : "♡ Guardar"}</button></div>
    <dl class="spec-grid">${ficha.map(([k, v]) => `<div><dt>${k}</dt><dd>${escapar(v)}</dd></div>`).join("")}</dl>
    ${auto.descripcion ? `<p class="modal-description">${escapar(auto.descripcion)}</p>` : ""}
    ${formularioConsulta(auto)}`;
  const formulario = contenidoDetalle.querySelector("#form-consulta");
  prellenar(formulario);
  formulario.addEventListener("submit", async event => {
    event.preventDefault();
    const respuesta = await enviarFormulario(formulario, datos => api("/api/consultas", { metodo: "POST", datos: { ...datos, id_vehiculo: auto.id } }));
    if (respuesta) {
      dialogo.close();
      aviso(respuesta.mensaje);
    }
  });
  contenidoDetalle.querySelector(".modal-fav").addEventListener("click", async () => {
    await alternarFavorito(auto.id);
    if (usuario && dialogo.open) {
      const boton = contenidoDetalle.querySelector(".modal-fav");
      const activo = favoritos.has(auto.id);
      boton.textContent = activo ? "♥ En favoritos" : "♡ Guardar";
      boton.setAttribute("aria-pressed", String(activo));
    }
  });
  dialogo.showModal();
  dialogo.querySelector(".modal-content").scrollTop = 0;
}

// ---------- eventos

tabs.addEventListener("click", event => {
  const tab = event.target.closest(".tab");
  if (!tab) return;
  filtro = tab.dataset.filter;
  mostrarAutos();
});
orden.addEventListener("change", mostrarAutos);
tipo.addEventListener("change", () => { filtro = tipo.value; mostrarAutos(); });
busqueda.addEventListener("input", mostrarAutos);
document.querySelector("#buscador").addEventListener("submit", event => {
  event.preventDefault();
  filtro = tipo.value;
  mostrarAutos();
  document.querySelector("#inventario").scrollIntoView({ behavior: "smooth" });
});

function abrirDesde(elemento) {
  const auto = autos.find(item => item.id === Number(elemento.dataset.details));
  if (auto) abrirDetalle(auto);
}
grid.addEventListener("click", event => {
  if (event.target.closest("#limpiar")) {
    filtro = "todos";
    busqueda.value = "";
    mostrarAutos();
    return;
  }
  if (event.target.closest("#reintentar")) { cargar(); return; }
  const favorito = event.target.closest("[data-favorite]");
  if (favorito) { alternarFavorito(Number(favorito.dataset.favorite)); return; }
  const tarjetaAuto = event.target.closest("[data-details]");
  if (tarjetaAuto) abrirDesde(tarjetaAuto);
});
grid.addEventListener("keydown", event => {
  if ((event.key === "Enter" || event.key === " ") && event.target.matches(".car-card")) {
    event.preventDefault();
    abrirDesde(event.target);
  }
});
document.querySelector(".modal-close").addEventListener("click", () => dialogo.close());
dialogo.addEventListener("click", event => { if (event.target === dialogo) dialogo.close(); });

const formContacto = document.querySelector("#form-contacto");
formContacto.addEventListener("submit", async event => {
  event.preventDefault();
  const respuesta = await enviarFormulario(formContacto, datos => api("/api/consultas", { metodo: "POST", datos }));
  if (respuesta) {
    formContacto.mensaje.value = "";
    const mensaje = formContacto.querySelector(".form-message");
    mensaje.textContent = respuesta.mensaje;
    mensaje.dataset.tipo = "ok";
  }
});

// Encabezado: sombra al desplazarse y enlace activo según la sección visible.
const header = document.querySelector(".header");
const enlaces = [...document.querySelectorAll(".nav-links a")];
const secciones = enlaces.map(a => document.querySelector(a.getAttribute("href")));
function actualizarEncabezado() {
  header.classList.toggle("scrolled", window.scrollY > 10);
  const limite = window.scrollY + window.innerHeight * 0.35;
  let actual = 0;
  secciones.forEach((seccion, i) => { if (seccion && seccion.offsetTop <= limite) actual = i; });
  if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) actual = secciones.length - 1;
  enlaces.forEach((a, i) => a.classList.toggle("active", i === actual));
}
window.addEventListener("scroll", actualizarEncabezado, { passive: true });
actualizarEncabezado();

cargar();
