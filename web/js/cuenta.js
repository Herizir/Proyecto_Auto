const accountViews = document.querySelectorAll(".account-view");
const accountTabs = document.querySelectorAll(".account-tab");

document.querySelectorAll(".account-view form").forEach(form => {
  form.addEventListener("submit", event => event.preventDefault());
});

document.querySelectorAll("[data-view]").forEach(button => {
  button.addEventListener("click", () => {
    const view = button.dataset.view;
    accountViews.forEach(section => { section.hidden = section.id !== view; });
    accountTabs.forEach(tab => {
      const active = tab.dataset.view === view;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-pressed", String(active));
    });
  });
});
