(() => {
  "use strict";

  const section = document.querySelector(".stack-portfolio");
  if (!section) return;

  const cards = [...section.querySelectorAll("[data-stack-card]")];
  const slots = [...section.querySelectorAll("[data-stack-slot]")];
  const progressBar = document.getElementById("stackProgress");
  const counter = document.getElementById("stackCounterNumber");
  const dots = [...section.querySelectorAll(".stack-counter__dots i")];
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const desktop = window.matchMedia("(min-width: 900px)");
  let frame = 0;
  let activeIndex = 0;

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  function activate(index) {
    if (index === activeIndex) return;
    activeIndex = index;
    if (counter) counter.textContent = String(index + 1).padStart(2, "0");
    dots.forEach((dot, dotIndex) => dot.classList.toggle("is-active", dotIndex === index));
  }

  function update() {
    frame = 0;
    const viewport = window.innerHeight || 1;
    const scrollRange = document.documentElement.scrollHeight - viewport;
    if (progressBar) progressBar.style.transform = `scaleX(${scrollRange > 0 ? window.scrollY / scrollRange : 0})`;

    const heroTitle = document.querySelector("#hero .hero__brand");
    const hero = document.querySelector("#hero");
    if (!reducedMotion.matches && heroTitle && hero) {
      const fadeProgress = clamp((window.scrollY - hero.offsetTop) / Math.max(hero.offsetHeight * 0.78, 1), 0, 1);
      heroTitle.style.transform = `scale(${1 - fadeProgress * 0.12}) translateY(${-40 * fadeProgress}px)`;
      heroTitle.style.opacity = String(1 - fadeProgress * 0.82);
    } else if (heroTitle) {
      heroTitle.style.removeProperty("transform");
      heroTitle.style.removeProperty("opacity");
    }

    if (!reducedMotion.matches && desktop.matches) {
      slots.forEach((slot, index) => {
        const next = slots[index + 1];
        const card = slot.querySelector("[data-stack-card]");
        if (!next || !card) return;
        const top = next.getBoundingClientRect().top;
        const progress = clamp((viewport * 0.92 - top) / (viewport * 0.8), 0, 1);
        card.style.setProperty("--stack-progress", String(progress));
        card.style.transform = `scale(${1 - progress * 0.1}) rotateX(${progress * 5}deg)`;
        card.style.filter = `brightness(${1 - progress * 0.62})`;
      });
    } else {
      cards.forEach((card) => {
        card.style.removeProperty("--stack-progress");
        card.style.removeProperty("transform");
        card.style.removeProperty("filter");
      });
    }

    const candidates = cards.map((card, index) => {
      if (card.closest(".stack-slot")?.hidden) return null;
      const rect = card.getBoundingClientRect();
      return { index, top: Math.abs(rect.top + Math.min(rect.height, viewport) / 2 - viewport * 0.52) };
    }).filter(Boolean);
    if (candidates.length) activate(candidates.reduce((best, item) => item.top < best.top ? item : best).index);
  }

  function scheduleUpdate() {
    if (!frame) frame = requestAnimationFrame(update);
  }

  function refreshLayout() {
    scheduleUpdate();
    if (window.ScrollTrigger && typeof window.ScrollTrigger.refresh === "function") {
      window.ScrollTrigger.refresh();
    }
  }

  if (!reducedMotion.matches) {
    section.classList.add("is-animated");
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("is-entered");
        });
      }, { threshold: 0.18, rootMargin: "0px 0px -8% 0px" });
      cards.forEach((card) => observer.observe(card));
    } else {
      cards.forEach((card) => card.classList.add("is-entered"));
    }
  } else {
    cards.forEach((card) => card.classList.add("is-entered"));
  }

  cards.forEach((card) => {
    card.addEventListener("pointermove", (event) => {
      const bounds = card.getBoundingClientRect();
      card.style.setProperty("--mouse-x", `${event.clientX - bounds.left}px`);
      card.style.setProperty("--mouse-y", `${event.clientY - bounds.top}px`);
    }, { passive: true });
    card.querySelectorAll("img").forEach((image) => {
      if (!image.complete) image.addEventListener("load", refreshLayout, { once: true });
    });
  });

  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", scheduleUpdate, { passive: true });
  window.addEventListener("load", refreshLayout, { once: true });
  document.addEventListener("portfolio:filter", scheduleUpdate);
  reducedMotion.addEventListener?.("change", scheduleUpdate);
  desktop.addEventListener?.("change", scheduleUpdate);
  document.fonts?.ready.then(refreshLayout).catch(() => {});
  scheduleUpdate();
})();
