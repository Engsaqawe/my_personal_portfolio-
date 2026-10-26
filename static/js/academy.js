(function () {
  "use strict";

  var themeKey = "engsaqawe-academy-theme";
  var classroom = document.querySelector(".academy-classroom");
  var publicPage = document.querySelector(".academy-public");
  var themeRoot = classroom || publicPage;

  function applyTheme(theme) {
    if (!themeRoot) return;
    themeRoot.classList.toggle("academy-dark", theme === "dark");
    document.querySelectorAll("[data-academy-theme]").forEach(function (button) {
      var icon = button.querySelector("i");
      button.setAttribute("aria-label", theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
      if (icon) icon.className = "fa-solid " + (theme === "dark" ? "fa-sun" : "fa-moon");
    });
  }

  var savedTheme = "light";
  try { savedTheme = localStorage.getItem(themeKey) || "light"; } catch (_) { /* storage may be disabled */ }
  applyTheme(savedTheme);

  document.querySelectorAll("[data-academy-theme]").forEach(function (button) {
    button.addEventListener("click", function () {
      var next = themeRoot && themeRoot.classList.contains("academy-dark") ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem(themeKey, next); } catch (_) { /* storage may be disabled */ }
    });
  });

  var theaterButton = document.querySelector("[data-theater]");
  if (theaterButton && classroom) {
    theaterButton.addEventListener("click", function () {
      var enabled = classroom.classList.toggle("is-theater");
      theaterButton.setAttribute("aria-pressed", enabled ? "true" : "false");
      theaterButton.innerHTML = '<i class="fa-solid fa-display"></i> ' + (enabled ? "Exit theater" : "Theater");
    });
  }

  var fullscreenButton = document.querySelector("[data-fullscreen]");
  var playerShell = document.getElementById("academyPlayerShell");
  if (fullscreenButton && playerShell) {
    fullscreenButton.addEventListener("click", function () {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else if (playerShell.requestFullscreen) {
        playerShell.requestFullscreen();
      }
    });
    document.addEventListener("fullscreenchange", function () {
      var active = document.fullscreenElement === playerShell;
      fullscreenButton.innerHTML = '<i class="fa-solid ' + (active ? "fa-compress" : "fa-expand") + '"></i> ' + (active ? "Exit full screen" : "Full screen");
    });
  }
})();
