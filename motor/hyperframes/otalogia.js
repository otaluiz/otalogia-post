// Helpers de motion do tema otalogia (GSAP). Tudo entra com expo/power3.out e assenta até ~3,5 s;
// depois só o ambiente respira até o fim do slide (loop limpo no Instagram). Determinístico: sem Math.random.
window.otaMotion = (tl, S = 6) => {
  const E = "expo.out";
  let seed = 11; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const $ = (s) => document.querySelector(s);

  const m = {
    // linhas do display sobem de trás da máscara, em cascata
    // título letra por letra: cada linha sobe de trás da máscara com leve rotação, em cascata
    linhas: (sl, t0) => document.querySelectorAll(`#${sl} .display .linha > span`).forEach((ln, i) => {
      const cs = m.letras(ln);
      tl.fromTo(cs, { yPercent: 115, rotate: 8, opacity: 0 }, { yPercent: 0, rotate: 0, opacity: 1, duration: 0.95, ease: E, stagger: 0.022 }, t0 + i * 0.14);
    }),
    // quebra os nós de texto em letras (palavra inteira num inline-block para não partir a linha), mantendo .hl/.hot
    letras: (el) => {
      const nos = [], w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      while (w.nextNode()) nos.push(w.currentNode);
      nos.forEach((n) => {
        const f = document.createDocumentFragment();
        n.textContent.split(/(\s+)/).forEach((p) => {
          if (!p) return;
          if (/^\s+$/.test(p)) return f.append(p);
          const pal = document.createElement("span");
          pal.style.cssText = "display:inline-block;white-space:nowrap";
          [...p].forEach((ch) => { const c = document.createElement("span"); c.className = "ch-a"; c.style.display = "inline-block"; c.textContent = ch; pal.append(c); });
          f.append(pal);
        });
        n.replaceWith(f);
      });
      return el.querySelectorAll(".ch-a");
    },
    // câmera que desliza: cada camada anda numa velocidade (fundo devagar, texto no meio, personagem e partículas na frente)
    parallax: (sl, t0) => {
      const sec = $(`#${sl}`), camadas = [
        [".foto, .bloom, .led, .dobra, .grade-fundo", 14],
        [".margem, .jogo", 18],
        [".conteudo", 24],
        [".emocao, .lista, .cta, .busca", 10],
        [".base, .chip, .ref-titulo", 20],
        [".recorte", 52],
        [".brasas", 90],
      ];
      camadas.forEach(([sel, d]) => {
        const els = [...sec.querySelectorAll(sel)];
        if (els.length) tl.fromTo(els, { x: d }, { x: -d, duration: S, ease: "sine.inOut" }, t0);
      });
      const rec = sec.querySelectorAll(".recorte");
      if (rec.length) tl.fromTo(rec, { rotation: 0.6 }, { rotation: -0.6, duration: S, ease: "sine.inOut" }, t0);
      const nav = sec.querySelector(".navegador");
      if (nav) {
        gsap.set(sec, { perspective: 1400 });
        tl.fromTo(nav, { rotationY: 5, rotationX: 2, x: 12 }, { rotationY: -5, rotationX: -1, x: -12, duration: S, ease: "sine.inOut" }, t0);
      }
    },
    parallaxTodos: () => document.querySelectorAll("section[data-start]").forEach((s) => m.parallax(s.id, +s.dataset.start)),
    sobe: (sel, t, d = 0.9) => tl.fromTo(sel, { y: 30, opacity: 0, filter: "blur(10px)" }, { y: 0, opacity: 1, filter: "blur(0px)", duration: d, ease: "power3.out" }, t),
    // frase manuscrita se escreve da esquerda pra direita
    escreve: (sel, t, d = 1.2) => tl.fromTo(sel, { clipPath: "inset(-30% 100% -30% -5%)" }, { clipPath: "inset(-30% -5% -30% -5%)", duration: d, ease: "power2.inOut" }, t),
    // caixa laranja varre por trás da palavra; a letra troca de cor junto
    marca: (sel, t, fg) => tl.fromTo(sel, { backgroundSize: "0% 100%", color: fg }, { backgroundSize: "100% 100%", color: "#0B0B12", duration: 0.7, ease: "power3.inOut" }, t),
    // todos os marca-texto do seletor, cada um partindo da cor do texto em volta
    marcas: (sel, t) => document.querySelectorAll(sel).forEach((el, i) => m.marca(el, t + i * 0.15, getComputedStyle(el.parentElement).color)),
    // reduz o display e a frase manuscrita até a linha mais larga caber no bloco (o PNG estático faz o mesmo)
    ajusta: () => document.querySelectorAll(".conteudo").forEach((c) => {
      const w = c.clientWidth;
      c.querySelectorAll(".display, .emocao").forEach((el) => {
        const linhas = el.classList.contains("display") ? [...el.querySelectorAll(".linha > span")] : [el];
        const larg = Math.max(...linhas.map((l) => l.scrollWidth));
        if (larg > w) el.style.fontSize = parseFloat(getComputedStyle(el).fontSize) * (w / larg) * 0.98 + "px";
      });
    }),
    respira: (sel, t0) => tl.fromTo(sel, { scale: 1 }, { scale: 1.06, duration: S, ease: "none" }, t0),
    lista: (sl, t0, passo = 0.35) => document.querySelectorAll(`#${sl} .lista li`).forEach((li, i, all) => {
      const t = t0 + i * passo;
      // a linha de baixo da lista entra junto com o último item
      if (i === all.length - 1 && !li.querySelector(".fim")) li.insertAdjacentHTML("beforeend", '<i class="fio fim"></i>');
      tl.fromTo(li.querySelectorAll(".fio"), { scaleX: 0 }, { scaleX: 1, duration: 1.1, ease: E }, t);
      tl.fromTo(li.querySelector(".n"), { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.7, ease: "power3.out" }, t + 0.05);
      tl.fromTo(li.querySelector(".t"), { opacity: 0, x: 40, filter: "blur(8px)" }, { opacity: 1, x: 0, filter: "blur(0px)", duration: 0.9, ease: E }, t + 0.1);
    }),
    // foto: acende do escuro com push-in lento, bloom respira, recorte com paralaxe, brasas sobem
    foto: (sl, t0, { z = 1.12, brasas = 40 } = {}) => {
      const rec = $(`#${sl} .recorte`);
      tl.fromTo(`#${sl} .foto`, { scale: z, filter: "brightness(.3)" }, { scale: 1, filter: "brightness(1)", duration: S, ease: "power2.out" }, t0);
      if (rec) tl.fromTo(rec, { scale: z * 1.02, y: 18, filter: "brightness(.3)" }, { scale: 1, y: 0, filter: "brightness(1)", duration: S, ease: "power2.out" }, t0);
      tl.fromTo(`#${sl} .bloom`, { scale: z, opacity: 0 }, { scale: 1, opacity: 0.3, duration: S, ease: "power2.out" }, t0);
      tl.to(`#${sl} .bloom`, { opacity: 0.16, duration: 1.1, ease: "sine.inOut", yoyo: true, repeat: 3 }, t0 + 1.4);
      [.9, .55, 1, .7, .95, .6, 1, .8].forEach((o, i) => tl.to(`#${sl} .luz`, { opacity: o, duration: 0.25, ease: "sine.inOut" }, t0 + 0.6 + i * 0.65));
      const p = $(`#${sl} .brasas`);
      for (let i = 0; p && i < brasas; i++) {
        const d = document.createElement("i"), r = 2 + rnd() * 4;
        Object.assign(d.style, { width: r + "px", height: r + "px", left: rnd() * 1080 + "px", top: 600 + rnd() * 840 + "px" });
        p.appendChild(d);
        tl.fromTo(d, { y: 0, x: 0, opacity: 0 }, { y: -(120 + rnd() * 320), x: (rnd() - 0.5) * 90, opacity: 0.25 + rnd() * 0.6, duration: S, ease: "sine.out" }, t0);
        tl.to(d, { opacity: 0, duration: 1.2, ease: "power1.in" }, t0 + S - 1.2 - rnd());
      }
    },
    chrome: (sl, t0) => tl.fromTo([`#${sl} .topo`, `#${sl} .rodape`], { opacity: 0 }, { opacity: 1, duration: 0.6, ease: "power2.out" }, t0 + 0.05),
    // pílula do CTA: overshoot e pulsa até o fim
    pill: (sel, t) => {
      tl.fromTo(sel, { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.9, ease: "back.out(1.7)" }, t);
      tl.to(sel, { scale: 1.04, duration: 0.7, ease: "sine.inOut", yoyo: true, repeat: Math.max(1, Math.floor((S - (t % S) - 1.2) / 0.7)) }, t + 1);
    },
    // print do site: navegador sobe, a página aproxima devagar a partir do topo, info entra
    referencia: (sl, t0) => {
      m.sobe(`#${sl} .chip`, t0 + 0.15, 0.7);
      m.sobe(`#${sl} .ref-titulo`, t0 + 0.3, 0.7);
      tl.fromTo(`#${sl} .navegador`, { y: 80, opacity: 0, scale: 0.96 }, { y: 0, opacity: 1, scale: 1, duration: 1.1, ease: E }, t0 + 0.35);
      tl.fromTo(`#${sl} .tela img`, { scale: 1 }, { scale: 1.12, duration: S - 1.4, ease: "sine.inOut" }, t0 + 1.4);
      m.sobe(`#${sl} .info .nome`, t0 + 0.9);
      m.sobe(`#${sl} .info .desc`, t0 + 1.15);
    },
  };
  return m;
};
