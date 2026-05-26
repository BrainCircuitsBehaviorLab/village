document.addEventListener("DOMContentLoaded", function () {
  const overlay = document.createElement("div");
  overlay.id = "lb-overlay";
  const img = document.createElement("img");
  overlay.appendChild(img);
  document.body.appendChild(overlay);

  document.querySelectorAll("img.zoomable").forEach(function (el) {
    el.addEventListener("click", function () {
      img.src = el.src;
      overlay.classList.add("lb-active");
    });
  });

  overlay.addEventListener("click", function () {
    overlay.classList.remove("lb-active");
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") overlay.classList.remove("lb-active");
  });
});
