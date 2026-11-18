// Mi cuenta: acceso, registro, recuperación y panel del cliente.

const sinSesion = document.querySelector("#sin-sesion");
const conSesion = document.querySelector("#con-sesion");
const accountViews = document.querySelectorAll(".account-view");
const accountTabs = document.querySelectorAll(".account-tab");

function mostrarVista(view) {
  accountViews.forEach(section => { section.hidden = section.id !== view; });
  accountTabs.forEach(tab => {
    const active = tab.dataset.view === view;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-pressed", String(active));
  });
}

document.querySelectorAll("[data-view]").forEach(button => {
  button.addEventListener("click", () => mostrarVista(button.dataset.view));
});

function fecha(iso) {
  return new Date(iso).toLocaleDateString("es-MX", { day: "numeric", month: "short", year: "numeric" });
}

async function cargarPanel() {
  const datos = await api("/api/cuenta");
  document.querySelector("#panel-nombre").textContent = datos.usuario.nombre.split(" ")[0];
  document.querySelector("#panel-correo").textContent = datos.usuario.correo;

  document.querySelector("#panel-favoritos").innerHTML = datos.favoritos.length
    ? datos.favoritos.map(auto => `
        <div class="panel-item">
          <div><strong>${escapar(auto.marca)} ${escapar(auto.modelo)}</strong><small>${auto.anio} · ${escapar(auto.tipo)}${auto.estado !== "Disponible" ? " · " + escapar(auto.estado) : ""}</small></div>
          <div class="panel-item-side"><span>${moneda.format(auto.precio)}</span><button type="button" class="account-link" data-quitar="${auto.id}">Quitar</button></div>
        </div>`).join("")
    : '<p class="panel-empty">Aún no guardas autos. Toca el ♡ en el inventario para agregarlos.</p>';

  document.querySelector("#panel-consultas").innerHTML = datos.consultas.length
    ? datos.consultas.map(c => `
        <div class="panel-item">
          <div><strong>${escapar(c.vehiculo || c.tipo)}</strong><small>${fecha(c.fecha)}</small></div>
          <span class="panel-badge ${c.atendida ? "done" : ""}">${c.atendida ? "Atendida" : "En revisión"}</span>
        </div>`).join("")
    : '<p class="panel-empty">No has enviado consultas todavía.</p>';
}

async function iniciar() {
  try {
    const { usuario } = await api("/api/sesion");
    if (usuario) {
      await cargarPanel();
      sinSesion.hidden = true;
      conSesion.hidden = false;
    } else {
      conSesion.hidden = true;
      sinSesion.hidden = false;
      if (location.hash === "#registro") mostrarVista("registro");
    }
  } catch (error) {
    sinSesion.hidden = false;
    aviso(error.message, "error");
  }
}

const formAcceso = document.querySelector("#form-acceso");
formAcceso.addEventListener("submit", async event => {
  event.preventDefault();
  if (await enviarFormulario(formAcceso, datos => api("/api/login", { metodo: "POST", datos }))) {
    formAcceso.reset();
    iniciar();
  }
});

const formRegistro = document.querySelector("#form-registro");
formRegistro.addEventListener("submit", async event => {
  event.preventDefault();
  if (await enviarFormulario(formRegistro, datos => api("/api/registro", { metodo: "POST", datos }))) {
    formRegistro.reset();
    aviso("¡Cuenta creada! Bienvenido a Motorhaus.");
    iniciar();
  }
});

const formRecuperacion = document.querySelector("#form-recuperacion");
formRecuperacion.addEventListener("submit", async event => {
  event.preventDefault();
  const respuesta = await enviarFormulario(formRecuperacion, datos => api("/api/recuperar", { metodo: "POST", datos }));
  if (respuesta) {
    const mensaje = formRecuperacion.querySelector(".form-message");
    mensaje.textContent = respuesta.mensaje;
    mensaje.dataset.tipo = "ok";
    formRecuperacion.reset();
  }
});

const formClave = document.querySelector("#form-clave");
formClave.addEventListener("submit", async event => {
  event.preventDefault();
  const respuesta = await enviarFormulario(formClave, datos => api("/api/cuenta/clave", { metodo: "POST", datos }));
  if (respuesta) {
    formClave.reset();
    formClave.closest("details").open = false;
    aviso(respuesta.mensaje);
  }
});

document.querySelector("#panel-favoritos").addEventListener("click", async event => {
  const boton = event.target.closest("[data-quitar]");
  if (!boton) return;
  try {
    await api(`/api/favoritos/${boton.dataset.quitar}`, { metodo: "DELETE" });
    await cargarPanel();
  } catch (error) {
    aviso(error.message, "error");
  }
});

document.querySelector("#cerrar-sesion").addEventListener("click", async () => {
  await api("/api/logout", { metodo: "POST" }).catch(() => {});
  iniciar();
});

iniciar();
