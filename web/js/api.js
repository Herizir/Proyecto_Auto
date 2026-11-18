// Utilidades compartidas por las páginas de la tienda.

async function api(ruta, { metodo = "GET", datos } = {}) {
  const opciones = { method: metodo, headers: {}, credentials: "same-origin" };
  if (datos !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(datos);
  }
  let respuesta;
  try {
    respuesta = await fetch(ruta, opciones);
  } catch {
    throw new Error("No se pudo conectar con la tienda. ¿Está encendido el servidor?");
  }
  const cuerpo = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    const error = new Error(cuerpo.error || "Ocurrió un error inesperado.");
    error.estado = respuesta.status;
    throw error;
  }
  return cuerpo;
}

function escapar(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

const moneda = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });
const numero = new Intl.NumberFormat("es-MX");

function aviso(texto, tipo = "ok") {
  let caja = document.querySelector(".toast");
  if (!caja) {
    caja = document.createElement("div");
    caja.className = "toast";
    caja.setAttribute("role", "status");
    document.body.append(caja);
  }
  caja.textContent = texto;
  caja.dataset.tipo = tipo;
  caja.classList.add("visible");
  clearTimeout(aviso.temporizador);
  aviso.temporizador = setTimeout(() => caja.classList.remove("visible"), 4200);
}

function datosFormulario(formulario) {
  return Object.fromEntries(new FormData(formulario).entries());
}

// Deshabilita el botón mientras se envía y muestra el error en el formulario.
async function enviarFormulario(formulario, accion) {
  const boton = formulario.querySelector("[type=submit]");
  const mensaje = formulario.querySelector(".form-message");
  if (mensaje) { mensaje.textContent = ""; mensaje.dataset.tipo = ""; }
  boton.disabled = true;
  try {
    return await accion(datosFormulario(formulario));
  } catch (error) {
    if (mensaje) { mensaje.textContent = error.message; mensaje.dataset.tipo = "error"; }
    else aviso(error.message, "error");
  } finally {
    boton.disabled = false;
  }
}

function etiquetaCuenta(usuario) {
  const enlace = document.querySelector(".nav-account");
  if (enlace) enlace.textContent = usuario ? `Hola, ${usuario.nombre.split(" ")[0]}` : "Mi cuenta";
}

if (location.protocol === "file:") {
  document.addEventListener("DOMContentLoaded", () => {
    document.body.insertAdjacentHTML("afterbegin", '<div class="file-warning">Abre la tienda desde el servidor: ejecuta <code>python servidor/app.py</code> y entra a <a href="http://127.0.0.1:5000">http://127.0.0.1:5000</a>.</div>');
  });
}
