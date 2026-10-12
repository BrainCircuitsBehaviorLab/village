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
    var filename = window.location.pathname.split("/").pop();
    if (filename === "" || filename === "index.html" || filename === "index") {
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

  // Every image in the page content can be enlarged, except those with the
  // no-zoom class and those inside a real link (one that doesn't just point to
  // the image file itself, which Sphinx adds to images with a set width).
  document.querySelectorAll("article.yue img").forEach(function (el) {
    if (el.classList.contains("no-zoom")) return;
    var link = el.closest("a");
    if (link && !link.classList.contains("image-reference")) return;
    el.classList.add("zoomable");
  });

  document.querySelectorAll("img.zoomable").forEach(function (el) {
    el.addEventListener("click", function (e) {
      // Images with a set width are wrapped by Sphinx in a link to the image
      // file: open the lightbox instead of following it.
      e.preventDefault();
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
