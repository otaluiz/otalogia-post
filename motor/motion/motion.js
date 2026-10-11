/* motion.js — animação dos slides do carrossel-engine (protótipo, 2026-10-11).
   Carregado pelo render_motion.py DEPOIS do READY do carrossel.html. Tudo é pausado e dirigido por Motion.seek(t)
   (segundos), então cada quadro sai igual em toda renderização (sem relógio real, sem Math.random).

   Por slide (lê o DOM que o carrossel.js montou):
   - foto (.photo/.foto): zoom lento 1.08 -> 1.00 em todo o slide; recorte com paralaxe leve (profundidade)
   - .meta/.foot: fade
   - display (.dl): cada linha sobe de trás de uma máscara, em cascata
   - emoção (handwritten): se "escreve" da esquerda pra direita
   - marca-texto (.hl): a caixa passa por trás da palavra
   - lista (li): cascata da esquerda
   - pílula do CTA: entra com overshoot e pulsa
   - partículas ASCII 3D (canvas): brasas em perspectiva nos slides com foto; esfera de caracteres girando nos de texto
*/
(function () {
  var EASE = 'cubic-bezier(.2,.8,.2,1)', BACK = 'cubic-bezier(.34,1.56,.64,1)';
  var anims = [], parts = null;

  function rng(seed) {  // mulberry32
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function anima(el, frames, delay, dur, easing, extra) {
    if (!el) return;
    var a = el.animate(frames, Object.assign({ delay: delay * 1000, duration: dur * 1000, easing: easing || EASE, fill: 'both' }, extra || {}));
    a.pause(); anims.push(a);
  }
  function todos(root, sel) { return Array.prototype.slice.call(root.querySelectorAll(sel)); }

  function particulas(slide, tipo, cor, u) {
    var cv = document.createElement('canvas'), W = 1080, H = 1440;
    cv.width = W; cv.height = H;
    cv.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:3;mix-blend-mode:screen;';
    var s = slide.querySelector('.s') || slide;
    s.appendChild(cv);
    var ctx = cv.getContext('2d'), r = rng(tipo === 'brasa' ? 7 : 11), pts = [], i;
    var RAMPA = ' .,:;-=+*#%@';
    if (tipo === 'brasa') {  // caixa 3D de brasas subindo
      for (i = 0; i < 520; i++) pts.push({ x: r() * 2 - 1, y: r() * 2 - 1, z: r() * 2 - 1, v: 0.04 + r() * 0.08, f: r() * 6.28 });
    } else {  // esfera de Fibonacci
      var N = 700, g = Math.PI * (3 - Math.sqrt(5));
      for (i = 0; i < N; i++) { var y = 1 - (i / (N - 1)) * 2, rad = Math.sqrt(1 - y * y), th = g * i; pts.push({ x: Math.cos(th) * rad, y: y, z: Math.sin(th) * rad }); }
    }
    var fonte = getComputedStyle(document.documentElement).getPropertyValue('--f-mono') || 'monospace';
    return function (t) {
      ctx.clearRect(0, 0, W, H);
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      var lista = [], k;
      if (tipo === 'brasa') {
        var ay = t * 0.12;
        for (k = 0; k < pts.length; k++) {
          var p = pts[k], yy = ((p.y - t * p.v + 3) % 2) - 1, xx = p.x + 0.04 * Math.sin(t * 1.3 + p.f);
          var X = xx * Math.cos(ay) - p.z * Math.sin(ay), Z = xx * Math.sin(ay) + p.z * Math.cos(ay) + 2.2;
          lista.push([X / Z * 900 + W / 2, yy / Z * 1300 + H * 0.55, Z, 0.5 + 0.5 * Math.sin(t * 2 + p.f)]);
        }
      } else {
        var a1 = t * 0.35, a2 = 0.45 + 0.1 * Math.sin(t * 0.4), cx = W * 0.72, cy = H * 0.74, R = 300;
        for (k = 0; k < pts.length; k++) {
          var q = pts[k], x1 = q.x * Math.cos(a1) + q.z * Math.sin(a1), z1 = -q.x * Math.sin(a1) + q.z * Math.cos(a1);
          var y2 = q.y * Math.cos(a2) - z1 * Math.sin(a2), z2 = q.y * Math.sin(a2) + z1 * Math.cos(a2) + 3;
          lista.push([cx + x1 / z2 * R * 3, cy + y2 / z2 * R * 3, z2, 1]);
        }
      }
      lista.sort(function (a, b) { return b[2] - a[2]; });  // fundo primeiro
      for (k = 0; k < lista.length; k++) {
        var e = lista[k], perto = Math.max(0, Math.min(1, (tipo === 'brasa' ? 3.2 - e[2] : 4 - e[2]) / 2));
        var ch = RAMPA[Math.min(RAMPA.length - 1, 1 + Math.floor(perto * (RAMPA.length - 1)))];
        ctx.font = (12 + 16 * perto) + 'px ' + fonte;
        ctx.fillStyle = cor;
        ctx.globalAlpha = (tipo === 'brasa' ? 0.18 + 0.55 * perto * e[3] : 0.10 + 0.45 * perto);
        ctx.fillText(ch, e[0], e[1]);
      }
      ctx.globalAlpha = 1;
    };
  }

  function init(opts) {
    opts = opts || {};
    var slide = document.querySelector('.slide'); if (!slide) return 0;
    var cs = getComputedStyle(slide), quente = (cs.getPropertyValue('--quente') || '#FF5A1F').trim();
    var dur = opts.duracao || 6, foto = slide.querySelector('.photo, .foto, .portrait');
    if (foto) {
      anima(foto, [{ transform: 'scale(1.08)', opacity: 0.3 }, { transform: 'scale(1.065)', opacity: 1, offset: 0.1 }, { transform: 'scale(1.0)', opacity: 1 }], 0, dur, 'linear');
    }
    var rec = slide.querySelector('.recorte');
    if (rec) anima(rec, [{ transform: 'translateY(18px) scale(1.06)' }, { transform: 'translateY(0) scale(1.0)' }], 0, dur, 'cubic-bezier(.3,0,.2,1)');
    todos(slide, '.meta, .foot').forEach(function (el) { anima(el, [{ opacity: 0 }, { opacity: 1 }], 0.1, 0.5, 'linear'); });

    var t0 = 0.3;
    todos(slide, '.ref-titulo div, .display .dl').forEach(function (el, i) {
      anima(el, [{ clipPath: 'inset(0 0 100% 0)', transform: 'translateY(45%)' }, { clipPath: 'inset(0 0 -20% 0)', transform: 'translateY(0)' }], t0 + i * 0.13, 0.75);
    });
    var nd = todos(slide, '.display .dl').length;
    var te = t0 + nd * 0.13 + 0.45;
    todos(slide, '.emocao .ln').forEach(function (el, i) {
      anima(el, [{ clipPath: 'inset(-30% 100% -30% 0)' }, { clipPath: 'inset(-30% -5% -30% 0)' }], te + i * 0.5, 0.9, 'cubic-bezier(.45,.05,.55,.95)');
    });
    todos(slide, '.hl').forEach(function (el) {  // a caixa quente varre por trás da palavra
      var c = getComputedStyle(el).backgroundColor;
      el.style.background = 'linear-gradient(' + c + ',' + c + ') no-repeat 0 0 / 0% 100%';
      anima(el, [{ backgroundSize: '0% 100%' }, { backgroundSize: '100% 100%' }], t0 + 0.55, 0.5);
    });
    todos(slide, '.bloco-lista li, .diagrama > *').forEach(function (el, i) {
      anima(el, [{ opacity: 0, transform: 'translateX(-28px)' }, { opacity: 1, transform: 'translateX(0)' }], te - 0.1 + i * 0.16, 0.55);
    });
    todos(slide, '.corpo, .chip, .navegador').forEach(function (el, i) {
      anima(el, [{ opacity: 0, transform: 'translateY(24px)' }, { opacity: 1, transform: 'translateY(0)' }], te + i * 0.15, 0.6);
    });
    var pill = slide.querySelector('.cta .pill'), txt = slide.querySelector('.cta .txt');
    if (pill) {
      var tp = te + 0.7;
      anima(pill, [{ transform: 'scale(0.6)', opacity: 0 }, { transform: 'scale(1)', opacity: 1 }], tp, 0.55, BACK);
      anima(pill, [{ transform: 'scale(1)' }, { transform: 'scale(1.06)' }, { transform: 'scale(1)' }], tp + 1.2, 1.1, 'ease-in-out', { iterations: 3, composite: 'replace' });
    }
    if (txt) anima(txt, [{ opacity: 0 }, { opacity: 1 }], te + 1.0, 0.5, 'linear');

    var claro = /\bt2c?\b/.test(slide.className) && !/com-foto/.test(slide.className);
    if (opts.particulas !== false && !claro) parts = particulas(slide, foto ? 'brasa' : 'esfera', quente, 1);
    return dur;
  }
  function seek(t) {
    for (var i = 0; i < anims.length; i++) anims[i].currentTime = t * 1000;
    if (parts) parts(t);
  }
  window.Motion = { init: init, seek: seek };
})();
