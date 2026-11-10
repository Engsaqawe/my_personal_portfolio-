/* Campaign Popup — matches campaign.html exactly, wide on desktop, responsive on mobile */
(function () {
  "use strict";

  /* ---- URL parameter helpers ---- */
  var params;
  try { params = new URLSearchParams(window.location.search); } catch (e) { params = { get: function () { return null; } }; }
  if (params.get("popup") === "off") return;                 // never show
  var fromWall = params.get("from") === "wall";              // always show (skip hide-hours)

  /* ---- storage helpers (safe try/catch) ---- */
  function storageGet(key) {
    try { var v = localStorage.getItem(key); if (v !== null) return v; } catch (e) {}
    try { return sessionStorage.getItem(key); } catch (e) {}
    return null;
  }
  function storageSet(key, value) {
    try { localStorage.setItem(key, value); } catch (e) {}
    try { sessionStorage.setItem(key, value); } catch (e) {}
  }

  /* ---- fetch campaign settings ---- */
  var CACHE_KEY = "engsaqawe_campaign_cfg";
  var cachedRaw = storageGet(CACHE_KEY);
  var cached = null;
  try { cached = cachedRaw ? JSON.parse(cachedRaw) : null; } catch (e) { cached = null; }

  function todayMogadishu() {
    try {
      return new Intl.DateTimeFormat("en-CA", { timeZone: "Africa/Mogadishu", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    } catch (e) {
      return new Date().toISOString().slice(0, 10);
    }
  }

  function shouldShow(cfg) {
    if (!cfg || !cfg.enabled) return false;
    if (cfg.endDate) {
      var today = todayMogadishu();
      if (today > cfg.endDate) return false;
    } else {
      return false;                                           // no end date = do not show
    }
    return true;                                              // shows whenever page is refreshed/visited
  }

  /* fast decision from cache */
  if (cached && cached._ts && (Date.now() - cached._ts < 60000)) {
    if (shouldShow(cached)) initPopup();
    return;                                                   // fresh cache, skip fetch
  }

  /* if we have stale cache, decide immediately but also refresh */
  var showedFromCache = false;
  if (cached && shouldShow(cached)) {
    showedFromCache = true;
    initPopup();
  }

  /* fetch fresh settings (timeout 2 s) */
  var controller;
  try { controller = new AbortController(); setTimeout(function () { controller.abort(); }, 2000); } catch (e) { controller = null; }
  var fetchOpts = { cache: "no-store" };
  if (controller) fetchOpts.signal = controller.signal;

  try {
    fetch("/api/campaign-settings", fetchOpts)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (cfg) {
        cfg._ts = Date.now();
        storageSet(CACHE_KEY, JSON.stringify(cfg));
        if (!showedFromCache && shouldShow(cfg)) initPopup();
        if (showedFromCache && !shouldShow(cfg)) removePopup();
      })
      .catch(function () { /* silently fail; popup stays based on cache decision */ });
  } catch (e) { /* fetch not available */ }

  /* ---- build popup DOM & Interactivity ---- */
  function initPopup() {
    var overlay = document.getElementById("cpop-overlay");
    if (!overlay) return;
    overlay.style.display = "flex";
    document.body.style.overflow = "hidden";
    document.body.classList.add("cpop-active");

    /* focus trap */
    var dialog = overlay.querySelector('[role="dialog"]');
    if (dialog) dialog.focus();

    /* ESC key */
    overlay._escHandler = function (e) { if (e.key === "Escape") closePopup(); };
    document.addEventListener("keydown", overlay._escHandler);

    /* close buttons */
    var xBtn = overlay.querySelector(".cpop-x-btn");
    if (xBtn) xBtn.addEventListener("click", closePopup);
    var closeBtn = overlay.querySelector(".cpop-close-btn");
    if (closeBtn) closeBtn.addEventListener("click", closePopup);

    /* Smooth scroll inside dialog for anchor links */
    var ctaHero = overlay.querySelector(".cpop-hero__cta");
    if (ctaHero) {
      ctaHero.addEventListener("click", function (e) {
        e.preventDefault();
        var target = document.getElementById("cpop-ku-dooro");
        if (target && target.scrollIntoView) {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    }

    /* ---- 8 Promises & 7 Stickers (identical to campaign.html) ---- */
    var POINTS = [
      { so: ["Hagidda Ardayda", "Arday kasta oo cusub waa inuu qof hago helaa.", "Hage waxbarasho iyo mentoring ah oo ardayda hoose ka caawiya inay gaaraan hadafkooda."],
        en: ["Student Guidance", "Every new student gets a guide.", "Academic guidance and mentoring so junior students reach their goals."] },
      { so: ["Communities Xirfadeed", "Ardayda kugu xirfadaha iyo kugu xiisaha ah hel.", "la caqabadaha recources-ka , fikradaha iyo shaqada intaba, si ay isoo baxaan natiijooyin dhab ah."],
        en: ["Skills-Based Community", "Find students who share your skills.", "Connect students by interest, skill, and field, so they learn and work together."] },
      { so: ["Wadaagidda Aqoonta", "Waxa mid baro, dhammaan way baran karaan.", "Ardayda ku dhiirri geli inay wadaagaan aqoon, fikrado iyo kheyraad waxbarasho."],
        en: ["Knowledge Sharing", "What one student learns, all can learn.", "Share ideas, notes, and learning resources."] },
      { so: ["Wada Shaqayn", "Mashaariic waaweyn waxaa dhisa kooxo.", "Taageer kooxaha, mashaariicda ardayda iyo isbarashada ardayda dhexdooda."],
        en: ["Collaboration", "Big projects are built by teams.", "Support teamwork, student projects, and peer-to-peer learning."] },
      { so: ["Horumarinta Xirfadaha", "Shahaado iyo xirfad dhab ah.", "Workshops, tababar gacan-ku-hay ah iyo tartamo teknoolajiyadeed oo u diyaariya ardayda suuqa shaqada."],
        en: ["Skills Development", "A degree plus real skills.", "Workshops, hands-on training, and technology competitions."] },
      { so: ["Matalaadda Ardayda", "Codkaaga wuxuu gaaraa maamulka.", "Waxaan abaabuli doonaa mashaariic ururinta fikrado-celin (feedback), kadibna natiijada u gudbin doonaa maamulka, anigoo ardayda u soo sheegaya waxa go'aansaday."],
        en: ["Student Representation", "Your voice reaches management.", "I will run feedback projects such as surveys and suggestion forms, present the results to management, and report back to students."] },
      { so: ["Agab iyo Goobo Waxbarasho", "Kulliyad diyaar u ah waxbarasho tayo leh.", "Waxaan soo jeedin doonaa maktabad wanaagsan, shaybaarro la qalabeeyey, agab gargaar degdeg ah iyo qolal waxbarasho oo habboon."],
        en: ["Facilities and Equipment", "A faculty ready for quality learning.", "I will propose a better library, equipped labs, first aid tools, and proper study rooms."] },
      { so: ["Hoggaan Muddo Dheer", "Ballanqaadku waa inuu dhammaado.", "Sannad saddexaad ayaan jiraa, markaa waan joogi doonaa sannadaha soo socda si shaqooyinka aan bilaabo aan u dhammaystiro."],
        en: ["Long-Term Leadership", "A promise must be finished.", "I am in my third year, so I will be here in the coming years to finish what I start."] }
    ];

    var STICKERS = [
      { L: "S", p: 1, so: "Saaxiibo xirfaddaada la mid ah ma haysaa?", en: "Do you have friends who share your skills?" },
      { L: "U", p: 0, so: "Ujeeddadaada ma cadahay?", en: "Is your goal clear?" },
      { L: "C", p: 3, so: "Cidda kula shaqayn lahayd mashruucaaga?", en: "Who would you work with on your project?" },
      { L: "C", p: 2, so: "Cilmigaaga ma la wadaagtaa?", en: "Do you share your knowledge?" },
      { L: "E", p: 5, so: "Ereyadaada ma gaadhaan maamulka?", en: "Do your words reach management?" },
      { L: "S", p: 4, so: "Sidee xirfaddaada u kobcin lahayd?", en: "How would you grow your skills?" },
      { L: "S", p: null, so: "Si kaligaa ah guul ma gaadhi kartaa?", en: "Can you reach success alone?" }
    ];

    var UI = {
      so: { n: "Sticker-ka", of: "ee", arrow: "Raac falaarta \u2192", ans: "Jawaabta:", see: "Eeg ballanka", next: "Sticker-ka xiga \u2192", together: "Wadajir", togetherP: "Guul waa wadajir." },
      en: { n: "Sticker", of: "of", arrow: "Follow the arrow \u2192", ans: "The answer:", see: "See the promise", next: "Next sticker \u2192", together: "Together", togetherP: "Success is togetherness." }
    };

    var lang = "so";
    try { var s = localStorage.getItem("campaign-lang"); if (s === "en" || s === "so") lang = s; } catch (e) {}

    var idx = 0;
    var pointsEl = document.getElementById("cpop-points");
    var lettersEl = document.getElementById("cpop-letters");

    function buildPoints() {
      if (!pointsEl) return;
      pointsEl.innerHTML = "";
      POINTS.forEach(function (p, i) {
        var d = p[lang];
        var el = document.createElement("div");
        el.className = "cpop-point";
        el.id = "cpop-p" + (i + 1);
        el.innerHTML = "<h3>" + (i + 1) + ". " + d[0] + "</h3><b>" + d[1] + "</b><p>" + d[2] + "</p>";
        pointsEl.appendChild(el);
      });
    }

    function buildLetters() {
      if (!lettersEl) return;
      lettersEl.innerHTML = "";
      STICKERS.forEach(function (s, i) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "cpop-ltr";
        b.textContent = s.L;
        b.setAttribute("aria-label", UI[lang].n + " " + (i + 1) + ": " + s.L);
        b.addEventListener("click", function () { idx = i; renderTrail(); });
        lettersEl.appendChild(b);
      });
    }

    function renderTrail() {
      var u = UI[lang], s = STICKERS[idx];
      if (lettersEl) {
        Array.prototype.forEach.call(lettersEl.children, function (b, i) {
          b.setAttribute("aria-pressed", i === idx ? "true" : "false");
        });
      }
      var sn = document.getElementById("cpop-sn");
      if (sn) sn.textContent = u.n + " " + (idx + 1) + " " + u.of + " " + STICKERS.length;
      var sq = document.getElementById("cpop-sq");
      if (sq) sq.textContent = s[lang];
      var sa = document.getElementById("cpop-sa");
      if (sa) sa.textContent = u.arrow;
      var rl = document.getElementById("cpop-rl");
      if (rl) rl.textContent = u.ans;
      var nextBtn = document.getElementById("cpop-next");
      if (nextBtn) nextBtn.textContent = u.next;

      if (pointsEl) {
        Array.prototype.forEach.call(pointsEl.children, function (c) { c.classList.remove("on"); });
      }

      var ra = document.getElementById("cpop-ra");
      var rp = document.getElementById("cpop-rp");
      var rk = document.getElementById("cpop-rk");

      if (s.p === null) {
        if (ra) ra.textContent = u.together;
        if (rp) rp.textContent = u.togetherP;
        if (rk) rk.style.display = "none";
      } else {
        var d = POINTS[s.p][lang];
        if (ra) ra.textContent = d[0];
        if (rp) rp.textContent = d[1];
        if (rk) {
          rk.style.display = "";
          rk.textContent = u.see;
        }
        if (pointsEl && pointsEl.children[s.p]) {
          pointsEl.children[s.p].classList.add("on");
        }
      }
    }

    function applyLang() {
      Array.prototype.forEach.call(overlay.querySelectorAll("[data-so]"), function (el) {
        el.innerHTML = el.getAttribute("data-" + lang);
      });
      Array.prototype.forEach.call(overlay.querySelectorAll(".cpop-lang button"), function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-lang") === lang ? "true" : "false");
      });
      buildPoints();
      buildLetters();
      renderTrail();
    }

    Array.prototype.forEach.call(overlay.querySelectorAll(".cpop-lang button"), function (b) {
      b.addEventListener("click", function () {
        lang = b.getAttribute("data-lang");
        try { localStorage.setItem("campaign-lang", lang); } catch (e) {}
        applyLang();
      });
    });

    var nextEl = document.getElementById("cpop-next");
    if (nextEl) {
      nextEl.addEventListener("click", function () {
        idx = (idx + 1) % STICKERS.length;
        renderTrail();
      });
    }

    var rkEl = document.getElementById("cpop-rk");
    if (rkEl) {
      rkEl.addEventListener("click", function () {
        var s = STICKERS[idx];
        if (s && s.p !== null) {
          var target = document.getElementById("cpop-p" + (s.p + 1));
          if (target && target.scrollIntoView) {
            target.scrollIntoView({ behavior: "smooth", block: "center" });
            target.classList.add("on");
          }
        }
      });
    }

    applyLang();
  }

  function closePopup() {
    var overlay = document.getElementById("cpop-overlay");
    if (!overlay) return;
    overlay.style.display = "none";
    document.body.style.overflow = "";
    document.body.classList.remove("cpop-active");
    try { localStorage.removeItem("engsaqawe_campaign_closed"); } catch (e) {}
    try { sessionStorage.removeItem("engsaqawe_campaign_closed"); } catch (e) {}
    if (overlay._escHandler) document.removeEventListener("keydown", overlay._escHandler);
  }

  function removePopup() {
    var overlay = document.getElementById("cpop-overlay");
    if (overlay) {
      overlay.style.display = "none";
      document.body.style.overflow = "";
      document.body.classList.remove("cpop-active");
    }
  }
})();
