(() => {
  "use strict";

  const section = document.querySelector(".affiliate-section");
  if (!section) return;

  const reveals = [...section.querySelectorAll("[data-reveal]")];
  const cards = [...section.querySelectorAll(".affiliate-card")];
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  if (!reduceMotion.matches && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.15, rootMargin: "0px 0px -6% 0px" });

    section.classList.add("affiliate-section--motion");
    reveals.forEach((element) => observer.observe(element));
  } else {
    reveals.forEach((element) => element.classList.add("is-visible"));
  }

  cards.forEach((card) => {
    card.addEventListener("pointermove", (event) => {
      const bounds = card.getBoundingClientRect();
      card.style.setProperty("--mx", `${event.clientX - bounds.left}px`);
      card.style.setProperty("--my", `${event.clientY - bounds.top}px`);
    }, { passive: true });
  });
})();
