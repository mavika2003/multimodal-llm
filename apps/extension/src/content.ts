(function () {
  if (document.documentElement.dataset.airlockExtension === "1") return;
  document.documentElement.dataset.airlockExtension = "1";

  const badge = document.createElement("div");
  badge.textContent = "AIRLOCK extension";
  badge.setAttribute("role", "status");
  badge.style.cssText =
    "position:fixed;bottom:12px;right:12px;z-index:99999;background:#15191f;color:#6ee7b7;padding:6px 10px;font:12px system-ui;border-radius:6px;border:1px solid #1f6b50;pointer-events:none;";
  document.documentElement.appendChild(badge);

  window.addEventListener("airlock:last-scan", ((e: CustomEvent) => {
    const d = e.detail as { decision?: string };
    if (d?.decision) badge.textContent = `AIRLOCK · ${d.decision}`;
  }) as EventListener);
})();