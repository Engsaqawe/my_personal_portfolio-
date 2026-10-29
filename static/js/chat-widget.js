(() => {
  "use strict";
  const widget = document.getElementById("chat-widget");
  const toggle = document.getElementById("chatToggle");
  const close = document.getElementById("chatClose");
  const panel = document.getElementById("chatPanel");
  const messagesBox = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const chatStatus = document.getElementById("chatStatus");
  if (!widget || !toggle || !panel) return;

  const setOpen = (open) => {
    widget.dataset.open = String(open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close chat" : "Open chat");
    panel.setAttribute("aria-hidden", String(!open));
    if (open) {
      if (messagesBox) messagesBox.scrollTop = messagesBox.scrollHeight;
      panel.querySelector("textarea")?.focus({ preventScroll: true });
    }
  };

  toggle.addEventListener("click", () => setOpen(widget.dataset.open !== "true"));
  close?.addEventListener("click", () => setOpen(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && widget.dataset.open === "true") setOpen(false);
  });
  if (window.location.hash === "#chat-widget") setOpen(true);

  let refreshMessages = async () => {};
  chatForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = chatForm.querySelector("button");
    const input = chatForm.querySelector("textarea");
    if (button) button.disabled = true;
    if (chatStatus) chatStatus.textContent = "Sending…";
    try {
      const response = await fetch(chatForm.action, {
        method: "POST",
        body: new FormData(chatForm),
        headers: { "X-Requested-With": "XMLHttpRequest", Accept: "application/json" },
        credentials: "same-origin",
      });
      const result = await response.json();
      if (!response.ok) {
        if (response.status === 401) {
          window.location.assign(`/account/login?next=${encodeURIComponent("/#chat-widget")}`);
          return;
        }
        throw new Error(result.message || "The message could not be sent.");
      }
      if (input) input.value = "";
      if (chatStatus) chatStatus.textContent = "Sent. I’ll reply here.";
      await refreshMessages();
    } catch (error) {
      if (chatStatus) chatStatus.textContent = error.message || "Could not send. Please try again.";
    } finally {
      if (button) button.disabled = false;
    }
  });

  if (messagesBox) {
    let previousCount = messagesBox.querySelectorAll(".site-chat__message").length;
    refreshMessages = async () => {
      try {
        const response = await fetch("/chat/messages", { credentials: "same-origin", headers: { Accept: "application/json" } });
        if (!response.ok) return;
        const messages = await response.json();
        if (messages.length === previousCount) return;
        const wasAtBottom = messagesBox.scrollHeight - messagesBox.scrollTop - messagesBox.clientHeight < 48;
        messagesBox.replaceChildren();
        messages.forEach((message) => {
          const article = document.createElement("article");
          article.className = `site-chat__message site-chat__message--${message.sender === "admin" ? "admin" : "user"}`;
          const sender = document.createElement("span");
          sender.textContent = message.sender === "admin" ? "ENGSAQAWE" : "Me";
          const body = document.createElement("p");
          body.textContent = message.body;
          const time = document.createElement("time");
          time.textContent = message.created_at;
          article.append(sender, body, time);
          messagesBox.append(article);
        });
        previousCount = messages.length;
        if (wasAtBottom || widget.dataset.open === "true") messagesBox.scrollTop = messagesBox.scrollHeight;
      } catch (_) { /* Keep the last messages visible if the network is briefly unavailable. */ }
    };
    window.setInterval(() => {
      if (widget.dataset.open === "true") refreshMessages();
    }, 12000);
  }
})();
