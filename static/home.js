/**
 * Scroll reveal for repo sections (IntersectionObserver).
 * No dependencies; skips work if user prefers reduced motion (CSS handles basics).
 */
(function () {
  "use strict";

  var slides = document.querySelectorAll("[data-repo-slide]");
  if (!slides.length || !("IntersectionObserver" in window)) {
    slides.forEach(function (el) {
      el.classList.add("is-visible");
    });
    return;
  }

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion) {
    slides.forEach(function (el) {
      el.classList.add("is-visible");
    });
    return;
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
        }
      });
    },
    {
      root: null,
      rootMargin: "0px 0px -12% 0px",
      threshold: [0, 0.15, 0.35],
    }
  );

  slides.forEach(function (el) {
    observer.observe(el);
  });
})();
