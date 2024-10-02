var swiper = new Swiper(".swiper", {
  effect: "cards",
  grabCursor: true,
  initialSlide: 2,
  speed: 500,
  loop: true,
  rotate: true,
  mousewheel: {
    invert: false,
    forceToAxis: true,
    sensitivity: 0.5,
  },
  lazy: {
    loadPrevNext: true,
    loadPrevNextAmount: 2,
  },
});