// Variante neon (tema-gta): soma ao otaMotion os efeitos aprovados na aidealab. Determinístico (sem Math.random).
// - pôr do sol varre de baixo pra cima na entrada; scanlines
// - linhas do título entram com aberração cromática magenta/teal que assenta no contorno ink
// - 1ª linha do título pisca como letreiro de neon e fica acesa
// - pílula do CTA pulsa em glow teal
window.otaNeon = (tl, S, m) => {
  const $$ = (s) => [...document.querySelectorAll(s)];
  const FLICK = [1, .15, 1, .35, 1, .05, .9, 1];  // fixo: mesmo quadro em todo render
  return (sl, t0) => {
    const sec = document.getElementById(sl), papel = sec.classList.contains("papel"), foto = !!sec.querySelector(".foto");
    if (!papel) {
      sec.insertAdjacentHTML("beforeend", '<div class="sol"></div><div class="scan"></div>');
      tl.fromTo(`#${sl} .sol`, { scaleY: 0, opacity: 1 }, { scaleY: 1, duration: 0.9, ease: "power2.out" }, t0);
      tl.to(`#${sl} .sol`, { opacity: 0, duration: 1.2, ease: "power1.out" }, t0 + 0.8);
      if (foto) tl.fromTo(`#${sl} .foto`, { x: -6 }, { x: 0, duration: 0.4, ease: "steps(4)" }, t0);
    }
    const base = papel ? "none" : foto ? "0 3px 0 #1A0B2E, 0 0 18px rgba(26,11,46,.85)" : "0 0 14px rgba(255,46,136,.35)";
    $$(`#${sl} .display .linha`).forEach((ln, i) => {
      const ti = t0 + 0.45 + i * 0.13;
      tl.fromTo(ln, { textShadow: "-8px 0 0 rgba(255,46,136,.9), 8px 0 0 rgba(25,211,197,.9)" }, { textShadow: base === "none" ? "0 0 0 rgba(0,0,0,0)" : base, duration: 0.7, ease: "power3.out" }, ti);
    });
    const um = sec.querySelector(".display .linha");
    if (um && !papel) {
      FLICK.forEach((o, k) => tl.to(um, { opacity: o, duration: 0.06, ease: "none" }, t0 + 1.3 + k * 0.08));
      tl.to(um, { textShadow: "0 0 22px rgba(255,46,136,.9), 0 3px 0 #1A0B2E", duration: 0.4 }, t0 + 2);
    }
    const pill = sec.querySelector(".pill");
    if (pill) {
      tl.to(pill, { boxShadow: "0 0 36px rgba(25,211,197,.95)", duration: 0.7, ease: "sine.inOut", yoyo: true, repeat: 5 }, t0 + 2.2);
    }
  };
};
