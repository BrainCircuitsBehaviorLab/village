document.addEventListener("DOMContentLoaded", function () {
  // Highlight the active top navbar link using the sidebar's current section
  var activeL1 = document.querySelector(".globaltoc .toctree-l1.current > a");
  if (activeL1) {
    var section = activeL1.textContent.trim().toLowerCase();
    document.querySelectorAll(".sy-head-links a").forEach(function (link) {
      if (link.textContent.trim().toLowerCase() === section) {
        link.classList.add("sy-nav-active");
      }
    });
  }

  // ── Logo src-swap (hover / active) ───────────────────────
  var brand = document.querySelector(".sy-head-brand");
  var isActive = false;

  if (brand) {
    brand.querySelectorAll("img").forEach(function (img) {
      var orig = img.getAttribute("src");
      img.dataset.orig = orig;
      img.dataset.purple = orig.replace(
        /logo_(light|dark)\.svg$/,
        "logo_$1_purple.svg"
      );
    });

    function applyLogoState(active) {
      brand.querySelectorAll("img").forEach(function (img) {
        img.src = active ? img.dataset.purple : img.dataset.orig;
      });
    }

    // Mark logo as active when on the landing page (index)
    var p = window.location.pathname.replace(/\/$/, "");
    if (p === "" || p.endsWith("/index") || p.endsWith("/index.html")) {
      isActive = true;
      brand.classList.add("sy-brand-active");
      applyLogoState(true);
    }

    brand.addEventListener("mouseenter", function () {
      applyLogoState(true);
    });
    brand.addEventListener("mouseleave", function () {
      applyLogoState(isActive);
    });
  }


  // ── Lightbox ─────────────────────────────────────────────
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
