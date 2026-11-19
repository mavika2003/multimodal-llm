(function () {
  const badge = document.createElement("div");
  badge.textContent = "AIRLOCK active";
  badge.style.cssText =
    "position:fixed;bottom:12px;right:12px;z-index:99999;background:#0b1220;color:#93c5fd;padding:6px 10px;font:12px system-ui;border-radius:6px;";
  document.documentElement.appendChild(badge);
})();