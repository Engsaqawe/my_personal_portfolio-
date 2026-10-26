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

  /* -------------------- Custom Cursor -------------------- */
  const customCursor = qs(".custom-cursor");
  const cursorDot = qs(".custom-cursor__dot", customCursor);
  const cursorRing = qs(".custom-cursor__ring", customCursor);
  const cursorGlow = qs(".cursor-glow");

  if (customCursor && window.matchMedia("(hover: hover)").matches && !prefersReducedMotion) {
    document.body.classList.add("has-custom-cursor");

    let cx = window.innerWidth / 2;
    let cy = window.innerHeight / 2;
    let tx = cx;
    let ty = cy;
    let rx = cx;
    let ry = cy;

    const moveCursor = () => {
      cx += (tx - cx) * 0.22;
      cy += (ty - cy) * 0.22;
      rx += (tx - rx) * 0.1;
      ry += (ty - ry) * 0.1;

      customCursor.style.transform = `translate(${cx}px, ${cy}px)`;
      if (cursorRing) cursorRing.style.transform = `translate(${rx - cx}px, ${ry - cy}px)`;

      if (cursorGlow) {
        cursorGlow.style.transform = `translate(${rx}px, ${ry}px) translate(-50%, -50%)`;
        cursorGlow.classList.add("is-active");
      }
      requestAnimationFrame(moveCursor);
    };
    requestAnimationFrame(moveCursor);

    window.addEventListener("pointermove", (e) => {
      tx = e.clientX;
      ty = e.clientY;
    }, { passive: true });

    const hoverTargets = "a, button, .btn, .chip, .showcase-card, .project-card, .project-card__link, .about__thumb, input, textarea, select";
    document.addEventListener("mouseover", (e) => {
      if (e.target.closest(hoverTargets)) customCursor.classList.add("is-hovering");
    });
    document.addEventListener("mouseout", (e) => {
      if (e.target.closest(hoverTargets)) customCursor.classList.remove("is-hovering");
    });
    document.addEventListener("mousedown", () => customCursor.classList.add("is-clicking"));
    document.addEventListener("mouseup", () => customCursor.classList.remove("is-clicking"));
  } else if (cursorGlow && window.matchMedia("(hover: hover)").matches && !prefersReducedMotion) {
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
  function scrollToTop() {
    if (window.__lenis) {
      window.__lenis.scrollTo(0, { duration: 1.1 });
    } else {
      window.scrollTo({ top: 0, behavior: prefersReducedMotion ? "auto" : "smooth" });
    }
  }

  function scrollToTarget(hash) {
    if (!hash || hash === "#top" || hash === "#hero") {
      scrollToTop();
      return;
    }

    const target = qs(hash);
    if (!target) return;

    const offset = (nav?.offsetHeight || 76) + 8;
    const top = target.getBoundingClientRect().top + window.scrollY - offset;

    if (window.__lenis) {
      window.__lenis.scrollTo(top, { duration: 1.1 });
    } else {
      window.scrollTo({ top, behavior: prefersReducedMotion ? "auto" : "smooth" });
    }
  }

  document.addEventListener("click", (e) => {
    const scrollBtn = e.target.closest("#scrollTop, #scrollTopFab, .scroll-top-btn, .scroll-top-fab");
    if (scrollBtn) {
      e.preventDefault();
      closeMobileNav();
      scrollToTop();
      history.pushState(null, "", "#hero");
      return;
    }

    const trigger = e.target.closest("[data-scroll-to], a[href^='#']");
    if (!trigger) return;

    const href = trigger.getAttribute("data-scroll-to") || trigger.getAttribute("href");
    if (!href || href === "#") return;

    if (href === "#top" || href === "#hero") {
      e.preventDefault();
      closeMobileNav();
      scrollToTop();
      history.pushState(null, "", href);
      return;
    }

    const target = qs(href);
    if (!target) return;

    e.preventDefault();
    closeMobileNav();
    scrollToTarget(href);
    history.pushState(null, "", href);
  });

  /* -------------------- Floating scroll-top button -------------------- */
  const scrollFab = qs("#scrollTopFab");
  const progressRing = qs("#scrollProgressRing");
  const progressRingTop = qs("#scrollProgressRingTop");
  const portfolioProgress = qs("#portfolioProgress");

  function setupProgressRing(circle) {
    if (!circle) return 0;
    const r = Number(circle.getAttribute("r") || 24);
    const len = 2 * Math.PI * r;
    circle.style.strokeDasharray = String(len);
    circle.style.strokeDashoffset = String(len);
    return len;
  }

  const ringLen = setupProgressRing(progressRing);
  const ringLenTop = setupProgressRing(progressRingTop);

  function updateScrollProgress() {
    const doc = document.documentElement;
    const max = Math.max(doc.scrollHeight - window.innerHeight, 1);
    const scrollY = window.__lenis?.scroll ?? window.scrollY;
    const pct = Math.min(Math.max(scrollY / max, 0), 1);
    const offset = ringLen * (1 - pct);

    if (progressRing && ringLen) {
      progressRing.style.strokeDashoffset = String(offset);
    }
    if (progressRingTop && ringLenTop) {
      progressRingTop.style.strokeDashoffset = String(ringLenTop * (1 - pct));
    }
    if (scrollFab) {
      scrollFab.classList.toggle("is-visible", scrollY > 400);
    }
  }

  window.addEventListener("scroll", updateScrollProgress, { passive: true });
  updateScrollProgress();

  /* -------------------- Horizontal portfolio scroll -------------------- */
  function initHorizontalPortfolio() {
    const pinEl = qs("#portfolioPin");
    const spacer = qs("#portfolioPinSpacer");
    const track = qs("#portfolioTrack");
    const wrap = qs(".portfolio__track-wrap");
    if (!pinEl || !track) return;
    const section = pinEl.closest(".portfolio");
    const progressBar = qs("#portfolioProgress");
    // The horizontal movement is directly controlled by the user's page scroll,
    // so keep the portfolio journey available even when reduced motion is on.
    const isDesktop = () => window.matchMedia("(min-width: 900px)").matches;
    let pinStart = 0;
    let distance = 0;
    let frame = 0;

    function setPinFixed(fixed) {
      if (!spacer) return;
      if (fixed) {
        if (spacer.hidden) {
          spacer.style.height = `${pinEl.offsetHeight}px`;
          spacer.hidden = false;
        }
        const bounds = section.getBoundingClientRect();
        pinEl.style.position = "fixed";
        pinEl.style.top = `${nav?.offsetHeight || 76}px`;
        pinEl.style.left = `${bounds.left}px`;
        pinEl.style.width = `${bounds.width}px`;
      } else {
        spacer.hidden = true;
        spacer.style.removeProperty("height");
        pinEl.style.removeProperty("position");
        pinEl.style.removeProperty("top");
        pinEl.style.removeProperty("left");
        pinEl.style.removeProperty("width");
      }
    }

    function measure(preserveStart = false) {
      if (!isDesktop() || !wrap || !section) {
        setPinFixed(false);
        track.style.transform = "";
        section?.style.removeProperty("padding-bottom");
        section?.style.removeProperty("--portfolio-scroll-distance");
        if (progressBar) progressBar.style.width = "0%";
        return;
      }
      distance = Math.max(track.scrollWidth - wrap.clientWidth, 0);
      // Move the next section beneath the fixed rail for its full height, so
      // it starts just below the header when the final project releases.
      const nextSectionReveal = Math.min(pinEl.offsetHeight, distance);
      const anchor = spacer && !spacer.hidden ? spacer : pinEl;
      if (!preserveStart || !pinStart) {
        pinStart = section.getBoundingClientRect().top + window.scrollY + anchor.offsetTop;
      }
      section.style.paddingBottom = `${distance - nextSectionReveal}px`;
      section.style.setProperty("--portfolio-scroll-distance", `${distance}px`);
      update();
    }

    function update() {
      if (!isDesktop()) return;
      if (!distance) {
        setPinFixed(false);
        return;
      }
      const navHeight = nav?.offsetHeight || 76;
      const scrollY = window.__lenis?.scroll ?? window.scrollY;
      const start = pinStart - navHeight;
      const progress = clamp((scrollY - start) / distance, 0, 1);
      // Release as soon as the final project reaches its final position.
      setPinFixed(scrollY >= start && scrollY < start + distance);
      track.style.transform = `translate3d(${-distance * progress}px, 0, 0)`;
      if (progressBar) progressBar.style.width = `${progress * 100}%`;
    }

    function scheduleUpdate() {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        update();
      });
    }

    document.addEventListener("portfolio:filter", () => measure(true));
    window.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("resize", measure);
    // Recalculate the pin start after fonts and images have settled; otherwise
    // a layout shift above the portfolio can make the cards jump past view.
    window.addEventListener("load", () => measure(false), { once: true });
    if (document.fonts?.ready) document.fonts.ready.then(() => measure(false));
    measure();
  }

  function initPortfolioMobileCue() {
    const trackWrap = qs("#portfolioTrackWrap");
    const arrows = qs("#portfolioScrollArrows");
    const cue = qs("#portfolioSwipeCue");
    if (!trackWrap) return;

    const hideCue = () => {
      arrows?.classList.add("is-hidden");
      cue?.classList.add("is-hidden");
    };

    const scrollProjects = (direction) => {
      const card = trackWrap.querySelector(".project-card--slide");
      const gap = 28;
      const amount = card ? card.offsetWidth + gap : trackWrap.clientWidth * 0.85;
      trackWrap.scrollBy({ left: direction * amount, behavior: "smooth" });
    };

    const bindScrollBtn = (el, direction) => {
      if (!el) return;
      el.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        scrollProjects(direction);
      });
    };

    bindScrollBtn(qs("#portfolioArrowLeft"), -1);
    bindScrollBtn(qs("#portfolioArrowRight"), 1);
    bindScrollBtn(qs("#portfolioSwipeLeft"), -1);
    bindScrollBtn(qs("#portfolioSwipeRight"), 1);

    trackWrap.addEventListener(
      "scroll",
      () => {
        if (trackWrap.scrollLeft > 24) hideCue();
      },
      { passive: true }
    );

    window.setTimeout(() => {
      if (trackWrap.scrollWidth <= trackWrap.clientWidth + 8) {
        hideCue();
      }
    }, 800);
  }

  function initMobileProjectList() {
    const track = qs("#portfolioTrack");
    const button = qs("#seeAllProjects");
    if (!track || !button) return;

    const isMobile = () => window.matchMedia("(max-width: 899px)").matches;
    const showAllLabel = button.textContent.trim() || "See all projects";
    const showLessLabel = button.getAttribute("data-show-less") || "Show fewer projects";
    let expanded = false;
    let wasMobile = isMobile();

    function update({ reset = false } = {}) {
      const mobile = isMobile();
      if (reset || mobile !== wasMobile) expanded = false;
      wasMobile = mobile;

      const cards = qsa(".project-card--slide", track);
      cards.forEach((card) => card.classList.remove("is-mobile-extra"));
      const visibleCards = cards.filter((card) => !card.classList.contains("is-hidden"));

      if (mobile) {
        visibleCards.slice(1).forEach((card) => card.classList.add("is-mobile-extra"));
        track.classList.toggle("is-mobile-expanded", expanded);
      } else {
        track.classList.remove("is-mobile-expanded");
      }

      button.hidden = !mobile || visibleCards.length < 2;
      button.setAttribute("aria-expanded", String(mobile && expanded));
      button.textContent = expanded ? showLessLabel : showAllLabel;
    }

    button.addEventListener("click", () => {
      expanded = !expanded;
      update();
      if (!expanded) qs("#portfolio")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    document.addEventListener("portfolio:filter", () => update({ reset: true }));
    window.addEventListener("resize", () => update());
    update();
  }

  function initPortfolioReveal() {
    const cards = qsa("#portfolioTrack .project-card--slide");
    if (!cards.length) return;
    document.documentElement.classList.add("portfolio-reveal-enabled");
    if (prefersReducedMotion || typeof IntersectionObserver === "undefined") {
      cards.forEach((card) => card.classList.add("is-entered"));
      return;
    }
    const observer = new IntersectionObserver((entries, activeObserver) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-entered");
        activeObserver.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -5% 0px" });
    cards.forEach((card, index) => {
      card.style.setProperty("--project-reveal-delay", `${(index % 2) * 90}ms`);
      observer.observe(card);
    });
  }

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
      lenis.on("scroll", updateScrollProgress);
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
    const cards = qsa(".tilt-card:not(.project-card--slide)");
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

  function initTypewriter() {
    const el = qs("#typewriter-text");
    if (!el) return;

    const fromData = (el.getAttribute("data-phrases") || "")
      .split("||")
      .map((s) => s.trim())
      .filter(Boolean);
    const phrases = fromData.length
      ? fromData
      : ["websites.", "web apps.", "clean UI.", "MySQL systems.", "digital tools."];

    let phraseIndex = 0;
    let charIndex = 0;
    let deleting = false;

    const tick = () => {
      const current = phrases[phraseIndex];
      if (!deleting) {
        el.textContent = current.slice(0, charIndex + 1);
        charIndex += 1;
        if (charIndex === current.length) {
          deleting = true;
          window.setTimeout(tick, 2200);
          return;
        }
        window.setTimeout(tick, prefersReducedMotion ? 0 : 55 + Math.random() * 35);
      } else {
        el.textContent = current.slice(0, charIndex - 1);
        charIndex -= 1;
        if (charIndex === 0) {
          deleting = false;
          phraseIndex = (phraseIndex + 1) % phrases.length;
          window.setTimeout(tick, 500);
          return;
        }
        window.setTimeout(tick, prefersReducedMotion ? 0 : 28);
      }
    };

    if (prefersReducedMotion) {
      el.textContent = phrases[0];
      return;
    }
    window.setTimeout(tick, 900);
  }

  function initPopUpText() {
    if (prefersReducedMotion || typeof gsap === "undefined") return;

    qsa(".pop-up-text").forEach((el) => {
      if (el.closest(".hero")) return;
      gsap.set(el, { opacity: 0, y: 50, scale: 0.88 });

      gsap.to(el, {
        scrollTrigger: {
          trigger: el,
          start: "top 92%",
          toggleActions: "play none none none",
        },
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.85,
        ease: "back.out(1.4)",
      });
    });

    // Hero pop-ups play immediately on load
    const heroPops = qsa(".hero .pop-up-text");
    if (heroPops.length) {
      gsap.set(heroPops, { opacity: 0, y: 40, scale: 0.9 });
      gsap.to(heroPops, {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 1,
        stagger: 0.12,
        ease: "back.out(1.6)",
        delay: 0.3,
      });
    }
  }

  function initTypingEffect() {
    initTypewriter();
  }

  function initGsapScenes() {
    if (prefersReducedMotion || typeof gsap === "undefined") return;

    if (typeof ScrollTrigger !== "undefined") {
      gsap.registerPlugin(ScrollTrigger);
    }

    // Hero entrance
    const heroTl = gsap.timeline({ defaults: { ease: "power3.out" } });
    heroTl
      .from(".hero__brand", { y: 60, opacity: 0, scale: 0.85, duration: 1.1, ease: "back.out(1.7)" }, 0.2)
      .from(".hero__typewriter", { y: 24, opacity: 0, duration: 0.7 }, 0.5)
      .from(".hero__portrait-wrap", { x: 40, opacity: 0, scale: 0.96, duration: 1.1 }, 0.35);

    initSplitTitles();
    initScrollReveals();
    initPopUpText();

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

      gsap.to(".hero__portrait-wrap", {
        scrollTrigger: {
          trigger: ".hero",
          start: "top top",
          end: "bottom top",
          scrub: true,
        },
        y: 50,
        ease: "none",
      });

      gsap.to(".light-wave", {
        scrollTrigger: {
          trigger: ".hero",
          start: "top top",
          end: "bottom top",
          scrub: true,
        },
        y: 80,
        opacity: 0.25,
        ease: "none",
      });
    }
  }

  function initSplitTitles() {
    if (prefersReducedMotion || typeof gsap === "undefined") return;

    qsa(".split-title").forEach((title) => {
      const text = title.textContent.trim();
      title.textContent = "";
      const words = text.split(/\s+/);

      words.forEach((word, wi) => {
        const wordSpan = document.createElement("span");
        wordSpan.className = "word";
        wordSpan.style.display = "inline-block";
        wordSpan.style.marginRight = "0.28em";

        word.split("").forEach((char) => {
          const charSpan = document.createElement("span");
          charSpan.className = "char";
          charSpan.textContent = char;
          wordSpan.appendChild(charSpan);
        });

        title.appendChild(wordSpan);
        if (wi < words.length - 1) title.appendChild(document.createTextNode(" "));
      });

      const chars = title.querySelectorAll(".char");
      gsap.set(chars, { y: "110%", opacity: 0, rotateX: -40, scale: 0.5 });

      gsap.to(chars, {
        scrollTrigger: {
          trigger: title,
          start: "top 88%",
        },
        y: "0%",
        opacity: 1,
        rotateX: 0,
        scale: 1,
        duration: 0.75,
        stagger: 0.025,
        ease: "back.out(1.6)",
      });
    });
  }

  function initScrollReveals() {
    if (prefersReducedMotion || typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") return;

    qsa(".reveal-text").forEach((el) => {
      gsap.from(el, {
        scrollTrigger: { trigger: el, start: "top 90%" },
        y: 24,
        opacity: 0,
        duration: 0.75,
        ease: "power2.out",
      });
    });

    qsa(".reveal-card").forEach((el, i) => {
      if (el.classList.contains("project-card--slide")) return;
      gsap.from(el, {
        scrollTrigger: { trigger: el, start: "top 92%" },
        y: 36,
        opacity: 0,
        duration: 0.8,
        delay: (i % 3) * 0.06,
        ease: "power2.out",
      });
    });
  }

  function initPhotoGallery() {
    const mainPhoto = qs(".about__photo--main");
    const thumbs = qsa(".about__thumb");
    if (!mainPhoto || !thumbs.length) return;

    thumbs.forEach((thumb) => {
      thumb.addEventListener("click", () => {
        const src = thumb.getAttribute("data-photo");
        if (!src) return;

        thumbs.forEach((t) => t.classList.remove("is-active"));
        thumb.classList.add("is-active");

        mainPhoto.classList.add("is-switching");
        window.setTimeout(() => {
          mainPhoto.src = src;
          mainPhoto.classList.remove("is-switching");
        }, 220);

        if (typeof gsap !== "undefined" && !prefersReducedMotion) {
          gsap.fromTo(mainPhoto, { scale: 1.04 }, { scale: 1, duration: 0.7, ease: "power2.out" });
        }
      });
    });
  }

  /* -------------------- Portfolio Filters -------------------- */
  const filterBtns = qsa(".chip--filter");
  const projectCards = qsa(".project-card, .stack-card");

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const filter = btn.getAttribute("data-filter") || "all";
      filterBtns.forEach((b) => b.classList.toggle("chip--active", b === btn));

      projectCards.forEach((card) => {
        const category = card.getAttribute("data-category") || "";
        const show = filter === "all" || category === filter;
        card.classList.toggle("is-hidden", !show);
        const stackSlot = card.closest(".stack-slot");
        if (stackSlot) stackSlot.hidden = !show;

        if (show && typeof gsap !== "undefined" && !prefersReducedMotion) {
          gsap.fromTo(card, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" });
        }
      });

      document.dispatchEvent(new Event("portfolio:filter"));

      if (typeof ScrollTrigger !== "undefined") {
        window.setTimeout(() => ScrollTrigger.refresh(), 120);
      }
    });
  });

  /* -------------------- Certificate Modal -------------------- */
  const modal = qs("#cert-modal") || qs("#certificate-modal");
  const modalTitle = qs("#cert-modal-title") || qs("#certificate-modal-title");

  qsa("[data-cert-preview]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!modal) return;
      const title = btn.getAttribute("data-cert-preview") || "Certificate";
      if (modalTitle) modalTitle.textContent = title;
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    });
  });

  const seeAllCerts = qs("#seeAllCerts");
  const certsGrid = qs("#certificatesGrid");
  const seeAllCertsLabel = qs("#seeAllCertsLabel");
  const certExtras = qsa(".certificate-card--extra");

  if (seeAllCerts && certsGrid && certExtras.length) {
    seeAllCerts.addEventListener("click", () => {
      const expanded = certsGrid.classList.toggle("is-expanded");
      seeAllCerts.setAttribute("aria-expanded", String(expanded));
      seeAllCerts.classList.toggle("is-active", expanded);
      if (seeAllCertsLabel) {
        seeAllCertsLabel.textContent = expanded ? "Show less" : "See all";
      }
    });
  } else if (seeAllCerts) {
    seeAllCerts.style.display = "none";
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  qsa("[data-certificate-preview]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (modalTitle) modalTitle.textContent = btn.getAttribute("data-certificate-preview") || "Certificate";
      if (modal) {
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
      }
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
      const messageField = qs("#message", form)?.closest(".field");

      const name = qs("#name", form)?.value.trim() || "";
      const email = qs("#email", form)?.value.trim() || "";
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

      if (messageField) {
        if (!message) {
          setFieldError(messageField, "Please enter a message.");
          valid = false;
        } else setFieldError(messageField, "");
      }

      if (!valid) return;

      // Valid — submit to Flask/MySQL
      form.submit();
    });

    // Live clear errors
    qsa("input, select, textarea", form).forEach((input) => {
      input.addEventListener("input", () => {
        const field = input.closest(".field");
        if (field) setFieldError(field, "");
      });
    });
  }

  const messageInput = qs("#message");
  const messageCount = qs("#messageCount");
  if (messageInput && messageCount) {
    const updateMessageCount = () => { messageCount.textContent = String(messageInput.value.length); };
    messageInput.addEventListener("input", updateMessageCount);
    updateMessageCount();
  }

  /* Scroll-led word emphasis, using the mission and vision copy already in the CMS. */
  const emphasisNodes = qsa(".scroll-emphasis");
  emphasisNodes.forEach((node) => {
    const words = node.textContent.trim().split(/\s+/);
    node.replaceChildren(...words.map((word, index) => {
      const span = document.createElement("span");
      span.className = "scroll-emphasis__word";
      span.textContent = `${word}${index < words.length - 1 ? " " : ""}`;
      return span;
    }));
  });
  let emphasisFrame = 0;
  const paintEmphasis = () => {
    if (!emphasisNodes.length || emphasisFrame) return;
    emphasisFrame = requestAnimationFrame(() => {
      emphasisNodes.forEach((node) => {
        const rect = node.getBoundingClientRect();
        const progress = clamp((window.innerHeight * 0.82 - rect.top) / (window.innerHeight * 0.72), 0, 1);
        const words = qsa(".scroll-emphasis__word", node);
        const active = progress * (words.length + 4);
        words.forEach((word, index) => word.style.setProperty("--word-progress", String(clamp(active - index, 0, 1))));
      });
      emphasisFrame = 0;
    });
  };
  window.addEventListener("scroll", paintEmphasis, { passive: true });
  window.addEventListener("resize", paintEmphasis);
  paintEmphasis();

  /* -------------------- Boot -------------------- */
  function initThemeToggle() {
    const btn = qs("#themeToggle");
    const root = document.documentElement;
    if (!btn) return;

    const applyTheme = (theme) => {
      root.setAttribute("data-theme", theme);
      try {
        localStorage.setItem("engsaqawe-theme", theme);
      } catch (_) {}
      const meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute("content", theme === "light" ? "#F3F6F1" : "#0A101F");
      btn.setAttribute("aria-label", theme === "light" ? "Switch to dark theme" : "Switch to light theme");
    };

    applyTheme(root.getAttribute("data-theme") || "light");

    btn.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      applyTheme(next);
    });
  }

  function boot() {
    initThemeToggle();
    initLenis();
    initAOS();
    initTilt();
    initMagneticButtons();
    animateStats();
    animateProgressBars();
    initTypingEffect();
    initGsapScenes();
    initPortfolioReveal();
    initMobileProjectList();
    initPhotoGallery();

    // Recalc ScrollTrigger after fonts/images load
    if (typeof ScrollTrigger !== "undefined") {
      window.setTimeout(() => ScrollTrigger.refresh(), 400);
      window.setTimeout(() => ScrollTrigger.refresh(), 1200);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
