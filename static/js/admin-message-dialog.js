(() => {
  "use strict";
  const dialog = document.getElementById("adminMessageDialog");
  if (!dialog) return;
  const title = document.getElementById("adminMessageTitle");
  const email = document.getElementById("adminMessageEmail");
  const body = document.getElementById("adminMessageBody");
  const reply = document.getElementById("adminMessageReply");
  document.querySelectorAll("[data-message-open]").forEach((button) => {
    button.addEventListener("click", () => {
      title.textContent = button.dataset.person || "Visitor";
      email.textContent = button.dataset.email || "";
      email.href = `mailto:${button.dataset.email || ""}`;
      body.textContent = button.dataset.message || "";
      reply.href = button.dataset.replyUrl || "#";
      dialog.showModal();
    });
  });
  dialog.querySelectorAll("[data-message-close]").forEach((button) => button.addEventListener("click", () => dialog.close()));
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
})();
