const autos = [
  { id: 1, marca: "Porsche", modelo: "911 Carrera", version: "3.0 Turbo · Coupé", tipo: "Deportivo", ano: "2023", kilometros: "8,200 km", combustible: "Gasolina", precio: 2450000, etiqueta: "DESTACADO", imagen: "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=900&q=80" },
  { id: 2, marca: "Mercedes-Benz", modelo: "Clase C", version: "C 300 · AMG Line", tipo: "Sedán", ano: "2022", kilometros: "18,500 km", combustible: "Gasolina", precio: 985000, etiqueta: "RECIÉN LLEGADO", imagen: "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=900&q=80" },
  { id: 3, marca: "BMW", modelo: "X5", version: "xDrive40i · M Sport", tipo: "SUV", ano: "2023", kilometros: "12,300 km", combustible: "Gasolina", precio: 1490000, etiqueta: "DESTACADO", imagen: "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=900&q=80" },
  { id: 4, marca: "Audi", modelo: "Q5", version: "45 TFSI · S line", tipo: "SUV", ano: "2022", kilometros: "21,000 km", combustible: "Gasolina", precio: 895000, etiqueta: "SELECCIÓN", imagen: "https://images.unsplash.com/photo-1606152421802-db97b9c7a11b?auto=format&fit=crop&w=900&q=80" },
  { id: 5, marca: "BMW", modelo: "Serie 3", version: "330i · Sport Line", tipo: "Sedán", ano: "2023", kilometros: "14,600 km", combustible: "Gasolina", precio: 920000, etiqueta: "SELECCIÓN", imagen: "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=900&q=80" },
  { id: 6, marca: "Porsche", modelo: "718 Cayman", version: "2.0 Turbo · Coupé", tipo: "Deportivo", ano: "2022", kilometros: "10,800 km", combustible: "Gasolina", precio: 1750000, etiqueta: "DESTACADO", imagen: "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=900&q=80" }
];

const grid = document.querySelector("#vehiculos");
const tipo = document.querySelector("#tipo");
const orden = document.querySelector("#orden");
const dialogo = document.querySelector("#detalle");
const favoritos = new Set();
const moneda = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });
let filtro = "todos";

function mostrarAutos() {
  const seleccion = autos.filter(auto => filtro === "todos" || auto.tipo === filtro);
  if (orden.value === "menor") seleccion.sort ( (a, b) => a.precio - b.precio );
  if (orden.value === "mayor") seleccion.sort ( (a, b) => b.precio - a.precio );
  document.querySelector("#resultados").textContent = `${seleccion.length} vehículos`;
  document.querySelectorAll(".tab").forEach(tab => tab.classList.toggle("active", tab.dataset.filter === filtro));
  tipo.value = filtro;
  grid.innerHTML = seleccion.map(auto => `
    <article class="car-card">
      <div class="car-image" style="background-image:url('${auto.imagen}')">
        <span class="car-tag">${auto.etiqueta}</span>
        <button class="favorite ${favoritos.has(auto.id) ? "selected" : ""}" data-favorite="${auto.id}" aria-label="${favoritos.has(auto.id) ? "Quitar de favoritos" : "Agregar a favoritos"}" aria-pressed="${favoritos.has(auto.id)}">${favoritos.has(auto.id) ? "♥" : "♡"}</button>
      </div>
      <div class="car-body">
        <div class="car-top"><div><span class="car-brand">${auto.marca}</span><h3>${auto.modelo}</h3><p class="car-subtitle">${auto.version}</p></div><span class="car-arrow">↗</span></div>
        <div class="car-specs"><span>◷ &nbsp;${auto.ano}</span><span>◉ &nbsp;${auto.kilometros}</span><span>◇ &nbsp;${auto.combustible}</span></div>
        <div class="car-bottom"><div><small>PRECIO DE MUESTRA</small><strong>${moneda.format(auto.precio)}</strong></div><button class="details-button" data-details="${auto.id}">Ver detalles ↗</button></div>
      </div>
    </article>`).join("") || '<p class="empty">No hay vehículos en esta categoría.</p>';
}

document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => {
  filtro = tab.dataset.filter;
  mostrarAutos();
}));
document.querySelector("#buscar").addEventListener("click", () => {
  filtro = tipo.value;
  mostrarAutos();
  document.querySelector("#inventario").scrollIntoView({ behavior: "smooth" });
});
grid.addEventListener("click", event => {
  const favorito = event.target.closest("[data-favorite]");
  const detalle = event.target.closest("[data-details]");
  if (favorito) {
    const id = Number(favorito.dataset.favorite);
    if (favoritos.has(id)) favoritos.delete(id); else favoritos.add(id);
    mostrarAutos();
  }
  if (detalle) {
    const auto = autos.find(item => item.id === Number(detalle.dataset.details));
    if (!auto) return;
    document.querySelector("#detalle-contenido").innerHTML = `<span class="car-brand">${auto.marca} · ${auto.tipo}</span><h2>${auto.modelo}</h2><p>${auto.version}<br>${auto.ano} · ${auto.kilometros} · ${auto.combustible}</p><small>PRECIO DE MUESTRA</small><br><strong>${moneda.format(auto.precio)}</strong><p>Esta ficha es una demostración visual. Los datos no corresponden a un vehículo disponible.</p><a class="button button-dark" href="mailto:hola@motorhaus.example?subject=Consulta%20de%20veh%C3%ADculo">Consultar vehículo <span>↗</span></a>`;
    dialogo.showModal();
  }
});
document.querySelector(".modal-close").addEventListener("click", () => dialogo.close());
mostrarAutos();
