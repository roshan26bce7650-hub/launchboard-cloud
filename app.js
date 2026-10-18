document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-modal-open]").forEach(button => {
    button.addEventListener("click", () => {
      const modal = document.getElementById(button.dataset.modalOpen);
      if (modal) {
        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        const input = modal.querySelector("input");
        if (input) setTimeout(() => input.focus(), 80);
      }
    });
  });
  document.querySelectorAll("[data-modal-close]").forEach(button => {
    button.addEventListener("click", () => {
      const modal = button.closest(".modal-backdrop");
      modal?.classList.remove("open");
      modal?.setAttribute("aria-hidden", "true");
    });
  });
  document.querySelectorAll(".modal-backdrop").forEach(modal => {
    modal.addEventListener("click", event => {
      if (event.target === modal) {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
      }
    });
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      document.querySelectorAll(".modal-backdrop.open").forEach(modal => {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
      });
    }
  });
  document.querySelectorAll("form[data-confirm]").forEach(form => {
    form.addEventListener("submit", event => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
  document.querySelectorAll(".flash").forEach(flash => {
    setTimeout(() => {
      flash.style.transition = "opacity .35s";
      flash.style.opacity = "0";
      setTimeout(() => flash.remove(), 400);
    }, 5000);
  });
});
