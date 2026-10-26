(() => {
  "use strict";

  const body = document.body;
  const sidebar = document.getElementById("adminSidebar");
  const overlay = document.getElementById("adminOverlay");
  const openBtn = document.getElementById("adminMenuBtn");
  const closeBtn = document.getElementById("adminMenuClose");

  if (!sidebar || !openBtn) return;

  const openMenu = () => {
    body.classList.add("admin-menu-open");
    body.style.overflow = "hidden";
    openBtn.setAttribute("aria-expanded", "true");
    if (overlay) overlay.setAttribute("aria-hidden", "false");
  };

  const closeMenu = () => {
    body.classList.remove("admin-menu-open");
    body.style.overflow = "";
    openBtn.setAttribute("aria-expanded", "false");
    if (overlay) overlay.setAttribute("aria-hidden", "true");
  };

  openBtn.addEventListener("click", openMenu);
  closeBtn?.addEventListener("click", closeMenu);
  overlay?.addEventListener("click", closeMenu);

  sidebar.querySelectorAll(".admin-nav a, .admin-sidebar__foot a").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth < 1024) closeMenu();
    });
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth >= 1024) closeMenu();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });
})();
