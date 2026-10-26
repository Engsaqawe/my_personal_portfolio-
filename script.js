/* =========================================================
   ENGSAQAWE — Interactions & Motion
   Loader · Lenis · GSAP · UI · Forms · A11y
   ========================================================= */

(() => {
  "use strict";

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* -------------------- Helpers -------------------- */
  const qs = (sel, ctx = document) => ctx.querySelector(sel);
  const qsa = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

  const clamp = (n, min, max) => Math.min(Math.max(n, min), max);

  /* -------------------- Year -------------------- */
  const yearEl = qs("#year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  /* -------------------- Loader -------------------- */
  const loader = qs(".loader");
  const loaderFill = qs(".loader__bar-fill");

  function finishLoader() {
    if (!loader) return;
    if (loaderFill) loaderFill.style.width = "100%";
    window.setTimeout(() => {
      loader.classList.add("is-done");
      document.body.classList.add("is-ready");
    }, prefersReducedMotion ? 0 : 320);
  }

  if (loaderFill && !prefersReducedMotion) {
    let progress = 0;
    const tick = () => {
      progress = Math.min(progress + Math.random() * 18 + 8, 92);
      loaderFill.style.width = `${progress}%`;
      if (progress < 92) window.setTimeout(tick, 120 + Math.random() * 160);
    };
    tick();
  }

  window.addEventListener("load", finishLoader);
  window.setTimeout(finishLoader, 2200);

  /* -------------------- Particles -------------------- */
  const particlesHost = qs(".bg-particles");
  if (particlesHost && !prefersReducedMotion) {
    const count = window.innerWidth < 720 ? 18 : 36;
    const frag = document.createDocumentFragment();
    for (let i = 0; i < count; i += 1) {
      const p = document.createElement("span");
      p.className = "particle";
      p.style.left = `${Math.random() * 100}%`;
      p.style.top = `${Math.random() * 100}%`;
      p.style.animationDuration = `${12 + Math.random() * 18}s`;
      p.style.animationDelay = `${Math.random() * 10}s`;
      p.style.opacity = String(0.2 + Math.random() * 0.6);
      frag.appendChild(p);
    }
    particlesHost.appendChild(frag);
  }

  /* -------------------- Cursor Glow -------------------- */
  const cursorGlow = qs(".cursor-glow");
  if (cursorGlow && window.matchMedia("(hover: hover)").matches && !prefersReducedMotion) {
    let x = window.innerWidth / 2;
    let y = window.innerHeight / 2;
    let tx = x;
    let ty = y;
    let rafId = 0;

    const render = () => {
      x += (tx - x) * 0.12;
      y += (ty - y) * 0.12;
      cursorGlow.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
      rafId = requestAnimationFrame(render);
    };

    window.addEventListener("pointermove", (e) => {
      tx = e.clientX;
      ty = e.clientY;
      cursorGlow.classList.add("is-active");
    }, { passive: true });

    window.addEventListener("pointerleave", () => {
      cursorGlow.classList.remove("is-active");
    });

    rafId = requestAnimationFrame(render);
  }

  /* -------------------- Navigation -------------------- */
  const nav = qs(".nav");
  const navToggle = qs(".nav__toggle");
  const navLinks = qsa(".nav__link");
  const mobileLinks = qsa(".nav__mobile-link");
  const sections = qsa("main section[id]");
  const activeIndicator = qs(".nav__active-indicator");

  function setNavScrolled() {
    if (!nav) return;
    nav.classList.toggle("is-scrolled", window.scrollY > 12);
  }

  setNavScrolled();
  window.addEventListener("scroll", setNavScrolled, { passive: true });

  if (navToggle && nav) {
    navToggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
  }

  function closeMobileNav() {
    if (!nav || !navToggle) return;
    nav.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
  }

  function updateActiveLink() {
    const scrollPos = window.scrollY + (nav?.offsetHeight || 80) + 40;
    let current = sections[0]?.id || "hero";

    sections.forEach((section) => {
      if (section.offsetTop <= scrollPos) current = section.id;
    });

    [...navLinks, ...mobileLinks].forEach((link) => {
      const href = link.getAttribute("href") || "";
      const id = href.replace("#", "");
      link.classList.toggle("is-active", id === current || (current === "hero" && href === "#hero"));
    });

    const active = navLinks.find((l) => l.classList.contains("is-active") && !l.classList.contains("nav__link--cta"));
    if (activeIndicator && active && window.innerWidth >= 960) {
      const parent = active.parentElement;
      if (!parent) return;
      const parentRect = parent.getBoundingClientRect();
      const linkRect = active.getBoundingClientRect();
      activeIndicator.style.opacity = "1";
      activeIndicator.style.width = `${linkRect.width}px`;
      activeIndicator.style.left = `${linkRect.left - parentRect.left}px`;
    } else if (activeIndicator) {
      activeIndicator.style.opacity = "0";
    }
  }

  window.addEventListener("scroll", updateActiveLink, { passive: true });
  window.addEventListener("resize", updateActiveLink);
  updateActiveLink();

  /* -------------------- Smooth Scroll Targets -------------------- */
  function scrollToTarget(hash) {
    const target = qs(hash);
    if (!target) return;

    const offset = (nav?.offsetHeight || 76) + 8;
    const top = target.getBoundingClientRect().top + window.scrollY - offset;

    if (window.__lenis) {
      window.__lenis.scrollTo(top, { offset: 0, duration: 1.1 });
    } else {
      window.scrollTo({ top, behavior: prefersReducedMotion ? "auto" : "smooth" });
    }
  }

  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-scroll-to], a[href^='#']");
    if (!trigger) return;

    const href = trigger.getAttribute("data-scroll-to") || trigger.getAttribute("href");
    if (!href || href === "#") return;

    const target = qs(href);
    if (!target) return;

    e.preventDefault();
    closeMobileNav();
    scrollToTarget(href);
    history.pushState(null, "", href);
  });

  /* -------------------- Lenis Smooth Scroll -------------------- */
  function initLenis() {
    if (prefersReducedMotion || typeof Lenis === "undefined") return null;

    const lenis = new Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });

    window.__lenis = lenis;

    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    if (typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined") {
      lenis.on("scroll", ScrollTrigger.update);
      gsap.ticker.add((time) => {
        lenis.raf(time * 1000);
      });
      gsap.ticker.lagSmoothing(0);
    }

    return lenis;
  }

  /* -------------------- GSAP / AOS / Tilt -------------------- */
  function initAOS() {
    if (typeof AOS === "undefined") return;
    AOS.init({
      duration: 800,
      easing: "ease-out-cubic",
      once: true,
      offset: 60,
      disable: prefersReducedMotion,
    });
  }

  function initTilt() {
    if (prefersReducedMotion || typeof VanillaTilt === "undefined") return;
    const cards = qsa(".tilt-card");
    if (!cards.length) return;
    VanillaTilt.init(cards, {
      max: 8,
      speed: 450,
      glare: true,
      "max-glare": 0.12,
      scale: 1.01,
    });
  }

  function initMagneticButtons() {
    if (prefersReducedMotion || !window.matchMedia("(hover: hover)").matches) return;

    qsa(".magnetic").forEach((btn) => {
      btn.addEventListener("pointermove", (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        btn.style.transform = `translate(${x * 0.18}px, ${y * 0.22}px)`;
      });

      btn.addEventListener("pointerleave", () => {
        btn.style.transform = "translate(0, 0)";
      });
    });
  }

  function animateStats() {
    const stats = qsa("[data-stat-target]");
    if (!stats.length) return;

    const run = (el) => {
      const target = Number(el.getAttribute("data-stat-target") || 0);
      if (prefersReducedMotion || typeof gsap === "undefined") {
        el.textContent = String(target);
        return;
      }
      const obj = { val: 0 };
      gsap.to(obj, {
        val: target,
        duration: 1.6,
        ease: "power2.out",
        onUpdate: () => {
          el.textContent = String(Math.round(obj.val));
        },
      });
    };

    if (typeof IntersectionObserver === "undefined") {
      stats.forEach(run);
      return;
    }

    const io = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        run(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.4 });

    stats.forEach((el) => io.observe(el));
  }

  function animateProgressBars() {
    const bars = qsa(".course-card__progress-bar");
    if (!bars.length) return;

    const reveal = (bar) => {
      const fill = qs(".course-card__progress-fill", bar);
      const value = Number(bar.getAttribute("data-progress") || 0);
      if (!fill) return;
      requestAnimationFrame(() => {
        fill.style.width = `${clamp(value, 0, 100)}%`;
      });
    };

    if (typeof IntersectionObserver === "undefined") {
      bars.forEach(reveal);
      return;
    }

    const io = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        reveal(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.35 });

    bars.forEach((bar) => io.observe(bar));
  }

  function initTypingEffect() {
    const line = qs(".hero__title-line--reveal");
    if (!line) return;

    const cursor = qs(".hero__title-cursor", line);
    const fullText = "breakthroughs";
    line.childNodes.forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) node.textContent = "";
    });

    // Keep structure: text + cursor
    let textNode = document.createTextNode("");
    line.insertBefore(textNode, cursor || null);

    if (prefersReducedMotion) {
      textNode.textContent = fullText;
      return;
    }

    let i = 0;
    const type = () => {
      textNode.textContent = fullText.slice(0, i);
      i += 1;
      if (i <= fullText.length) {
        window.setTimeout(type, 55 + Math.random() * 40);
      }
    };

    window.setTimeout(type, 700);
  }

  function initGsapScenes() {
    if (prefersReducedMotion || typeof gsap === "undefined") return;

    if (typeof ScrollTrigger !== "undefined") {
      gsap.registerPlugin(ScrollTrigger);
    }

    // Hero entrance
    const heroTl = gsap.timeline({ defaults: { ease: "power3.out" } });
    heroTl
      .from(".hero__content .eyebrow", { y: 20, opacity: 0, duration: 0.7 }, 0.15)
      .from(".hero__title-line", { y: 36, opacity: 0, duration: 0.85, stagger: 0.1 }, 0.25)
      .from(".hero__subtitle", { y: 24, opacity: 0, duration: 0.7 }, 0.55)
      .from(".hero__actions", { y: 20, opacity: 0, duration: 0.65 }, 0.7)
      .from(".hero__stats .stat-card", { y: 28, opacity: 0, duration: 0.7, stagger: 0.08 }, 0.85)
      .from(".hero__glass", { x: 40, opacity: 0, duration: 1 }, 0.4);

    // Section fades
    if (typeof ScrollTrigger !== "undefined") {
      qsa(".section__header").forEach((header) => {
        gsap.from(header, {
          scrollTrigger: {
            trigger: header,
            start: "top 85%",
          },
          y: 28,
          opacity: 0,
          duration: 0.8,
          ease: "power2.out",
        });
      });

      // Parallax soft motion on hero visual
      gsap.to(".hero__glass", {
        scrollTrigger: {
          trigger: ".hero",
          start: "top top",
          end: "bottom top",
          scrub: true,
        },
        y: 60,
        ease: "none",
      });
    }
  }

  /* -------------------- Portfolio Filters -------------------- */
  const filterBtns = qsa(".chip--filter");
  const projectCards = qsa(".project-card");

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const filter = btn.getAttribute("data-filter") || "all";
      filterBtns.forEach((b) => b.classList.toggle("chip--active", b === btn));

      projectCards.forEach((card) => {
        const category = card.getAttribute("data-category") || "";
        const show = filter === "all" || category === filter;
        card.classList.toggle("is-hidden", !show);

        if (show && typeof gsap !== "undefined" && !prefersReducedMotion) {
          gsap.fromTo(card, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" });
        }
      });
    });
  });

  /* -------------------- Certificate Modal -------------------- */
  const modal = qs("#certificate-modal");
  const modalTitle = qs("#certificate-modal-title");

  const certificateCopy = {
    architecture: {
      title: "Advanced Frontend Architecture",
      subtitle: "International Tech Institute · 2025",
    },
    ux: {
      title: "UX Strategy & Research",
      subtitle: "Digital Experience Academy · 2024",
    },
    cloud: {
      title: "Cloud-Native Systems",
      subtitle: "Cloud Engineering Institute · 2023",
    },
  };

  function openModal(key) {
    if (!modal) return;
    const data = certificateCopy[key] || {
      title: "Certificate Preview",
      subtitle: "High-resolution previews for verification available on request.",
    };
    if (modalTitle) modalTitle.textContent = data.title;
    const subtitle = qs(".modal__subtitle", modal);
    if (subtitle) subtitle.textContent = data.subtitle;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  qsa("[data-certificate-preview]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openModal(btn.getAttribute("data-certificate-preview") || "");
    });
  });

  qsa("[data-modal-close]").forEach((el) => {
    el.addEventListener("click", closeModal);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  /* -------------------- Contact Form Validation -------------------- */
  const form = qs("#contact-form");

  function setFieldError(field, message) {
    field.classList.toggle("is-invalid", Boolean(message));
    const error = qs(".field__error", field);
    if (error) error.textContent = message || "";
  }

  function validateEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();

      const nameField = qs("#name", form)?.closest(".field");
      const emailField = qs("#email", form)?.closest(".field");
      const typeField = qs("#projectType", form)?.closest(".field");
      const messageField = qs("#message", form)?.closest(".field");

      const name = qs("#name", form)?.value.trim() || "";
      const email = qs("#email", form)?.value.trim() || "";
      const projectType = qs("#projectType", form)?.value || "";
      const message = qs("#message", form)?.value.trim() || "";

      let valid = true;

      if (nameField) {
        if (name.length < 2) {
          setFieldError(nameField, "Please enter your name.");
          valid = false;
        } else setFieldError(nameField, "");
      }

      if (emailField) {
        if (!validateEmail(email)) {
          setFieldError(emailField, "Enter a valid email address.");
          valid = false;
        } else setFieldError(emailField, "");
      }

      if (typeField) {
        if (!projectType) {
          setFieldError(typeField, "Select a project type.");
          valid = false;
        } else setFieldError(typeField, "");
      }

      if (messageField) {
        if (message.length < 12) {
          setFieldError(messageField, "Share a bit more detail (12+ characters).");
          valid = false;
        } else setFieldError(messageField, "");
      }

      if (!valid) return;

      const subject = encodeURIComponent(`ENGSAQAWE inquiry — ${projectType}`);
      const body = encodeURIComponent(
        `Name: ${name}\nEmail: ${email}\nProject type: ${projectType}\n\n${message}`
      );

      window.location.href = `mailto:hello@engsaqawe.com?subject=${subject}&body=${body}`;
      form.reset();
    });

    // Live clear errors
    qsa("input, select, textarea", form).forEach((input) => {
      input.addEventListener("input", () => {
        const field = input.closest(".field");
        if (field) setFieldError(field, "");
      });
    });
  }

  /* -------------------- Boot -------------------- */
  function boot() {
    initLenis();
    initAOS();
    initTilt();
    initMagneticButtons();
    animateStats();
    animateProgressBars();
    initTypingEffect();
    initGsapScenes();

    // Recalc ScrollTrigger after fonts/images
    if (typeof ScrollTrigger !== "undefined") {
      window.setTimeout(() => ScrollTrigger.refresh(), 400);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
