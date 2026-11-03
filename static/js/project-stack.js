(() => {
  "use strict";

  const section = document.getElementById("portfolio");
  if (!section) return;

  const slots = [...section.querySelectorAll("[data-stack-slot]")];
  const cards = slots.map((slot) => slot.querySelector("[data-stack-card]")).filter(Boolean);
  const progressBar = document.getElementById("stackProgress");
  const counterNumber = document.getElementById("stackCounterNumber");
  const counterTotal = section.querySelector(".stack-counter > span");
  const stackWork = document.getElementById("stackWork");
  const seeAllProjects = document.getElementById("seeAllStackProjects");
  const seeAllLabel = seeAllProjects?.querySelector("span");
  if (seeAllProjects) section.classList.add("has-project-expander");
  const dots = [...section.querySelectorAll(".stack-counter__dots i")];
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let frame = 0;

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
  const visibleSlots = () => slots.filter((slot) =>
    !slot.hidden && !slot.classList.contains("is-hidden") && getComputedStyle(slot).display !== "none"
  );

  function reveal(elements) {
    elements.forEach((element) => {
      element.classList.add("in");
      if (element.matches("[data-stack-card]")) element.classList.add("is-entered");
    });
  }

  function update() {
    frame = 0;
    const rect = section.getBoundingClientRect();
    const range = rect.height - window.innerHeight;
    const progress = range > 0 ? Math.min(1, Math.max(0, -rect.top / range)) : 0;
    if (progressBar) progressBar.style.width = `${progress * 100}%`;

    const heroTitle = document.querySelector("#hero .hero__brand");
    const hero = document.querySelector("#hero");
    if (!reduceMotion.matches && heroTitle && hero) {
      const fadeProgress = clamp((window.scrollY - hero.offsetTop) / Math.max(hero.offsetHeight * 0.78, 1), 0, 1);
      heroTitle.style.transform = `scale(${1 - fadeProgress * 0.12}) translateY(${-40 * fadeProgress}px)`;
      heroTitle.style.opacity = String(1 - fadeProgress * 0.82);
    }

    const visible = visibleSlots();
    let active = 0;
    visible.forEach((slot, index) => {
      if (slot.getBoundingClientRect().top <= window.innerHeight * 0.45) active = index;
    });
    if (counterNumber) counterNumber.textContent = String(visible.length ? active + 1 : 0).padStart(2, "0");
    if (counterTotal) counterTotal.textContent = `/ ${String(visible.length).padStart(2, "0")}`;
    dots.forEach((dot, index) => {
      dot.classList.toggle("is-active", index === active);
      dot.hidden = index >= visible.length;
    });

    visible.forEach((slot, index) => {
      const card = slot.querySelector("[data-stack-card]");
      if (!card) return;
      const depth = Math.max(0, active - index);
      const desktop = window.innerWidth > 899;
      card.style.setProperty("--s", desktop ? String(1 - Math.min(depth, 3) * 0.045) : "1");
      card.style.setProperty("--dim", desktop ? String(1 - Math.min(depth, 3) * 0.17) : "1");
    });

  }

  function scheduleUpdate() {
    if (!frame) frame = window.requestAnimationFrame(update);
  }

  function refreshLayout() {
    scheduleUpdate();
    if (window.ScrollTrigger && typeof window.ScrollTrigger.refresh === "function") window.ScrollTrigger.refresh();
  }

  seeAllProjects?.addEventListener("click", () => {
    const expanded = stackWork?.classList.toggle("is-expanded") || false;
    seeAllProjects.setAttribute("aria-expanded", String(expanded));
    seeAllProjects.classList.toggle("is-active", expanded);
    if (seeAllLabel) seeAllLabel.textContent = expanded ? "Show fewer projects" : "See all projects";
    refreshLayout();
  });

  if (reduceMotion.matches) {
    reveal([...section.querySelectorAll(".sp-reveal"), ...cards]);
  } else {
    section.classList.add("is-animated");
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("in");
          if (entry.target.matches("[data-stack-card]")) entry.target.classList.add("is-entered");
          observer.unobserve(entry.target);
        });
      }, { threshold: 0.18, rootMargin: "0px 0px -8% 0px" });
      section.querySelectorAll(".sp-reveal, [data-stack-card]").forEach((element) => observer.observe(element));
    } else {
      reveal([...section.querySelectorAll(".sp-reveal"), ...cards]);
    }

    section.querySelectorAll(".stack-card__picture").forEach((picture) => {
      const media = picture.querySelector(".stack-card__media");
      if (!media) return;
      picture.addEventListener("pointermove", (event) => {
        if (event.pointerType === "touch") return;
        const bounds = picture.getBoundingClientRect();
        const x = (event.clientX - bounds.left) / bounds.width - 0.5;
        const y = (event.clientY - bounds.top) / bounds.height - 0.5;
        media.style.setProperty("--ry", `${x * 8}deg`);
        media.style.setProperty("--rx", `${-y * 8}deg`);
      }, { passive: true });
      picture.addEventListener("pointerleave", () => {
        media.style.setProperty("--rx", "0deg");
        media.style.setProperty("--ry", "0deg");
      }, { passive: true });
    });
  }

  cards.forEach((card) => card.querySelectorAll("img").forEach((image) => {
    if (!image.complete) image.addEventListener("load", refreshLayout, { once: true });
  }));

  section.querySelectorAll(".stack-image-resizer").forEach((handle) => {
    const card = handle.closest(".stack-card");
    const panel = handle.closest(".stack-card__panel");
    if (!card || !panel) return;
    const snapMarkers = [...card.querySelectorAll(".stack-resize-snaps i")];
    let dragging = false;
    const maxImageWidth = () => {
      const panelWidth = panel.getBoundingClientRect().width;
      return Math.min(70, Math.max(0, ((panelWidth - 500) / Math.max(panelWidth, 1)) * 100));
    };
    const setWidth = (value) => {
      const maxWidth = maxImageWidth();
      const width = Math.min(maxWidth, Math.max(0, value));
      panel.style.setProperty("--image-width", `${width}%`);
      handle.setAttribute("aria-valuenow", String(Math.round(width)));
      handle.setAttribute("aria-valuemax", String(Math.floor(maxWidth)));
      handle.dataset.pct = String(Math.round(width));
      card.classList.toggle("is-image-hidden", width < 1);
      card.classList.toggle("is-details-wide", width < 28);
      card.classList.toggle("is-image-expanded", maxWidth > 0 && width >= maxWidth - 0.5);
      const snaps = [0, maxWidth * 0.36, maxWidth * 0.7, maxWidth];
      snapMarkers.forEach((marker, index) => {
        marker.style.left = `${snaps[index]}%`;
        marker.classList.toggle("is-active", Math.abs(snaps[index] - width) < 1.5);
      });
    };
    const move = (event) => {
      if (!dragging) return;
      const bounds = panel.getBoundingClientRect();
      if (bounds.width) setWidth(((event.clientX - bounds.left) / bounds.width) * 100);
    };
    const stop = () => {
      if (!dragging) return;
      const maxWidth = maxImageWidth();
      const width = Number(handle.getAttribute("aria-valuenow")) || 0;
      const snapPoints = [0, maxWidth * 0.36, maxWidth * 0.7, maxWidth];
      setWidth(snapPoints.reduce((best, point) => Math.abs(point - width) < Math.abs(best - width) ? point : best));
      dragging = false;
      card.classList.remove("is-resizing");
      if (handle.hasPointerCapture?.(eventPointerId)) handle.releasePointerCapture(eventPointerId);
      refreshLayout();
    };
    let eventPointerId = null;
    handle.addEventListener("pointerdown", (event) => {
      if (window.innerWidth < 900) return;
      event.preventDefault();
      dragging = true;
      eventPointerId = event.pointerId;
      card.classList.add("is-resizing");
      handle.setPointerCapture?.(event.pointerId);
      move(event);
    });
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", stop);
    handle.addEventListener("pointercancel", stop);
    handle.addEventListener("dblclick", () => {
      setWidth(Math.min(40, maxImageWidth() * 0.72));
      refreshLayout();
    });
    handle.addEventListener("keydown", (event) => {
      if (window.innerWidth < 900) return;
      const current = Number(handle.getAttribute("aria-valuenow")) || 40;
      if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
        event.preventDefault();
        setWidth(current + (event.key === "ArrowRight" ? 5 : -5));
        refreshLayout();
      } else if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        setWidth(event.key === "Home" ? 0 : maxImageWidth());
        refreshLayout();
      }
    });
    setWidth(Math.min(40, maxImageWidth() * 0.72));
  });

  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", scheduleUpdate, { passive: true });
  window.addEventListener("load", refreshLayout, { once: true });
  reduceMotion.addEventListener?.("change", scheduleUpdate);
  document.fonts?.ready.then(refreshLayout).catch(() => {});
  scheduleUpdate();
})();
