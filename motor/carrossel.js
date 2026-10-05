/* carrossel-engine — renderizador único do carrossel (sem marca; strings e fontes vêm de window.__TEMA = tema.json). JS puro, sem framework, sem build.
   API: window.Carrossel = { render(data, container, opts), validate(data) }
   Contrato dos dados: ver carrossel.schema.md. */
(function () {
  'use strict';

  // tema.json (injetado pelo render.py ou carregado pelo carrossel.html); defaults neutros se ausente
  function tema() {
    var t = window.__TEMA || {};
    return {
      nome_meta: t.nome_meta != null ? t.nome_meta : 'MARCA', handle: t.handle != null ? t.handle : '@marca',
      rodape_centro: t.rodape_centro != null ? t.rodape_centro : 'salva pra depois', fontes: t.fontes || [],
      // topo: lista de blocos do topo com {nome} {serie} {data}; padrão = 3 blocos
      topo: Array.isArray(t.topo) && t.topo.length ? t.topo : ['{nome}', '{serie}', '{data}']
    };
  }

  var TEMPLATES = ['T1', 'T1b', 'T2', 'T2c', 'T3', 'T4', 'T5'];
  var PAPEL = ['T2', 'T2c'];
  var INK = ['T3', 'T4'];
  var POSICOES = ['antes', 'depois', 'sobreposta', 'entre'];

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  // [palavra] -> <span class="hot">; a cor quente é do template (CSS), nunca do dado.
  // [palavra] = cor quente; {palavra} = marca-texto (caixa quente, texto ink). No máximo 1 dos dois por slide.
  function marcar(t) { return esc(t).replace(/\[([^\]]+)\]/g, '<span class="hot">$1</span>').replace(/\{([^}]+)\}/g, '<span class="hl">$1</span>'); }
  function marcadores(t) { return (String(t || '').match(/\[[^\]]*\]|\{[^}]*\}/g) || []).length; }
  function pad2(n) { return (n < 10 ? '0' : '') + n; }

  /* ---------- validação ---------- */
  function validate(data) {
    var errors = [], warnings = [];
    if (!data || !Array.isArray(data.slides) || !data.slides.length) {
      errors.push('slides: lista vazia ou ausente');
      return { errors: errors, warnings: warnings };
    }
    var sl = data.slides, n = sl.length, runFam = null, runLen = 0;
    sl.forEach(function (s, i) {
      var k = i + 1, p = 'slide ' + k + ': ', t = s.template;
      if (TEMPLATES.indexOf(t) < 0) { errors.push(p + 'template desconhecido "' + t + '"'); return; }
      // T5: display é opcional (headline pequena acima do card, até 2 linhas)
      if (t === 'T5') {
        if (s.display != null && (!Array.isArray(s.display) || s.display.length > 2)) errors.push(p + 'T5: display opcional, lista de até 2 linhas');
        var r = s.referencia || {};
        ['site', 'nome', 'descricao'].forEach(function (c) { if (!r[c]) errors.push(p + 'T5 exige referencia.' + c); });
        if (!('print' in r)) errors.push(p + 'T5 exige a chave referencia.print (caminho ou null)');
        else if (!r.print) warnings.push(p + 'T5 com print null (usando placeholder)');
        if (i === 0 || i === n - 1) errors.push(p + 'T5 não pode ser o primeiro nem o último slide');
        if (s.emocao || s.corpo || s.lista || s.diagrama || s.cta) errors.push(p + 'T5 não aceita emocao/corpo/lista/diagrama/cta');
      } else if (!Array.isArray(s.display) || !s.display.length) errors.push(p + 'display deve ser lista de linhas');
      var disp = Array.isArray(s.display) ? s.display : [];
      var m = disp.reduce(function (a, l) { return a + marcadores(l); }, 0) + marcadores(s.emocao && s.emocao.texto);
      if (m > 1) errors.push(p + 'mais de um marcador [ ] (' + m + ')');
      if (s.emocao) {
        if (!s.emocao.texto) errors.push(p + 'emocao.texto ausente');
        if (POSICOES.indexOf(s.emocao.posicao) < 0) errors.push(p + 'emocao.posicao inválida "' + s.emocao.posicao + '"');
        if (s.emocao.posicao === 'entre') {
          var a = s.emocao.apos_linha;
          if (!(Number.isInteger(a) && a >= 1 && a < disp.length)) errors.push(p + 'emocao "entre" exige apos_linha inteiro entre 1 e ' + (disp.length - 1));
        } else if (s.emocao.apos_linha != null) errors.push(p + 'apos_linha só vale com posicao "entre"');
      }
      if (s.lista && s.lista.length > 4) errors.push(p + 'lista com mais de 4 itens');
      if ((s.lista || s.diagrama) && t !== 'T3') errors.push(p + 'lista/diagrama só no T3');
      if (s.cta && t !== 'T4') errors.push(p + 'cta só no T4');
      if (s.referencia && t !== 'T5') errors.push(p + 'referencia só no T5');
      if (s.imagem != null && ['T1', 'T1b', 'T2', 'T4'].indexOf(t) < 0) errors.push(p + 'imagem só no T1/T1b/T2/T4');
      if ((i === 1 || i === n - 1) && !('imagem' in s)) errors.push(p + 'o ' + (i === 1 ? 'slide 2' : 'último slide') + ' exige a chave "imagem" (caminho ou null; só T1b/T2/T4 aceitam)');
      if ((t === 'T2' || t === 'T4') && s.imagem === null) warnings.push(p + t + ' com imagem null (usando placeholder)');
      if (s.recorte && ['T1', 'T1b', 'T2', 'T4'].indexOf(t) < 0) errors.push(p + 'recorte só no T1/T1b/T2/T4');
      if (s.bloco && (typeof s.bloco.y !== 'number' || (s.bloco.alinhar && ['esquerda', 'direita', 'centro'].indexOf(s.bloco.alinhar) < 0))) errors.push(p + 'bloco exige y numérico e alinhar esquerda|direita|centro');
      if (s.textura && (['led', 'grain'].indexOf(s.textura) < 0 || ['T2', 'T2c', 'T3'].indexOf(t) < 0)) errors.push(p + 'textura: só "led" ou "grain", em T2/T2c/T3');
      if (s.gancho && t !== 'T1' && t !== 'T1b') errors.push(p + 'gancho só no T1/T1b');
      if (s.diagrama && s.diagrama.tipo !== 'barra') errors.push(p + 'diagrama.tipo desconhecido "' + s.diagrama.tipo + '"');
      if (t === 'T1' && !s.imagem) warnings.push(p + 'T1 sem imagem (usando placeholder)');
      if (i === 0 && t !== 'T1' && t !== 'T1b') errors.push(p + 'o primeiro slide deve ser T1 ou T1b');
      if (i === n - 1 && t !== 'T4') errors.push(p + 'o último slide deve ser T4');
      var fam = PAPEL.indexOf(t) >= 0 ? 'papel' : INK.indexOf(t) >= 0 ? 'ink' : null;
      if (t === 'T5') return; // T5 não conta nem zera a regra de fundo repetido
      if (fam && fam === runFam) runLen++; else { runFam = fam; runLen = fam ? 1 : 0; }
      if (runLen === 4) errors.push(p + 'mais de 3 slides seguidos com o mesmo fundo (' + fam + ')');
    });
    // gancho: palavras do hook (slide 1), sem colchetes nem " / "
    var s0 = sl[0] || {};
    var txt = (Array.isArray(s0.display) ? s0.display.join(' ') : '') + ' ' + ((s0.emocao && s0.emocao.texto) || '');
    var palavras = txt.replace(/\[|\]/g, '').replace(/ \/ /g, ' ').split(/\s+/).filter(Boolean);
    if (palavras.length > 10) errors.push('slide 1: hook com ' + palavras.length + ' palavras (máx. 10)');
    return { errors: errors, warnings: warnings };
  }

  /* ---------- ícones fixos ---------- */
  var SVG_MARCADOR = '<svg viewBox="0 0 18 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3 2h12v20l-6-5-6 5z"/></svg>';

  // Placeholder de foto (T1): pôr do sol cinematográfico + figura humana pequena.
  var SVG_FOTO =
    '<svg viewBox="0 0 1080 1440" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">' +
    '<defs><linearGradient id="ceu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--ink)"/><stop offset=".45" style="stop-color:color-mix(in srgb, var(--ink) 88%, var(--detalhe))"/>' +
    '<stop offset=".62" style="stop-color:color-mix(in srgb, var(--quente-papel) 52%, var(--ink))"/><stop offset=".72" style="stop-color:var(--quente-papel)"/><stop offset=".76" style="stop-color:var(--quente)"/></linearGradient>' +
    '<radialGradient id="sol" cx="540" cy="1090" r="520" gradientUnits="userSpaceOnUse"><stop offset="0" style="stop-color:color-mix(in srgb, var(--quente) 76%, white)" stop-opacity=".85"/><stop offset=".35" style="stop-color:var(--quente)" stop-opacity=".4"/><stop offset="1" style="stop-color:var(--quente)" stop-opacity="0"/></radialGradient></defs>' +
    '<rect width="1080" height="1440" fill="url(#ceu)"/><rect width="1080" height="1440" fill="url(#sol)"/>' +
    '<path d="M0 1090 L120 1060 L260 1085 L420 1050 L560 1080 L720 1045 L880 1078 L1080 1050 L1080 1440 L0 1440Z" fill="#14100f"/>' +
    '<path d="M0 1130 L200 1112 L420 1135 L640 1108 L860 1130 L1080 1112 L1080 1440 L0 1440Z" fill="#0b0909"/>' +
    '<g fill="#050506"><circle cx="540" cy="1050" r="9"/><path d="M531 1060h18l4 36h-7l-1 22h-6v-18h-2v18h-6l-1-22h-7z"/></g></svg>';

  // Placeholder de foto para o bloco do T2 (936x500): recorte do mesmo pôr do sol (horizonte + figura).
  var SVG_FOTO_BLOCO = SVG_FOTO.replace('viewBox="0 0 1080 1440"', 'viewBox="0 850 1080 577"');

  // Placeholder de retrato (T1b): busto em silhueta.
  var SVG_RETRATO =
    '<svg viewBox="0 0 936 470" preserveAspectRatio="xMidYMax slice" xmlns="http://www.w3.org/2000/svg"><g fill="currentColor" opacity=".85">' +
    '<circle cx="468" cy="190" r="92"/><path d="M468 300c-130 0-230 60-250 170h500c-20-110-120-170-250-170z"/></g></svg>';

  /* ---------- montagem do HTML de cada slide ---------- */
  function linhasDisplay(arr) {
    return '<div class="display">' + arr.map(function (l, i) {
      // acento maiusculo com entrelinha 0.86 encosta na linha de cima: so essa linha ganha respiro
      var ac = i > 0 && /[ÁÀÂÃÉÊÍÓÔÕÚÜ]/.test(l) ? ' ac' : '';
      return '<div class="dl' + ac + '">' + marcar(l) + '</div>';
    }).join('') + '</div>';
  }
  function blocoEmocao(e) {
    var linhas = String(e.texto).split(' / ').map(function (l) { return '<span class="ln">' + marcar(l) + '</span>'; }).join('');
    // e.top (só T1b camadas): altura da serifada em u, para não cair no rosto
    var st = e.top != null ? ' style="--emo-top:' + Number(e.top) + '"' : '';
    return '<div class="emocao ' + e.posicao + '"' + st + '>' + linhas + '</div>';
  }
  function texto(s) {
    var d = s.display || [], e = s.emocao, h = '';
    if (e && e.posicao === 'antes') h += blocoEmocao(e);
    if (e && e.posicao === 'entre') {
      h += linhasDisplay(d.slice(0, e.apos_linha)) + blocoEmocao(e) + linhasDisplay(d.slice(e.apos_linha));
    } else h += linhasDisplay(d);
    if (e && (e.posicao === 'depois' || e.posicao === 'sobreposta')) h += blocoEmocao(e);
    return h;
  }
  function corpo(s) { return s.corpo ? '<div class="corpo">' + marcar(s.corpo) + '</div>' : ''; }

  function diagrama(g) {
    var total = g.partes.reduce(function (a, p) { return a + p.valor; }, 0) || 1;
    var w = function (p) { return 'style="width:' + (p.valor / total * 100) + '%"'; };
    var cls = function (p) { return p.destaque ? ' class="destaque"' : ''; };
    return '<div class="diagrama"><div class="barra-rotulos">' +
      g.partes.map(function (p) { return '<div' + cls(p) + ' ' + w(p) + '>' + esc(p.rotulo) + ' ' + p.valor + '%</div>'; }).join('') +
      '</div><div class="barra">' + g.partes.map(function (p) { return '<div' + cls(p) + ' ' + w(p) + '></div>'; }).join('') +
      '</div><div class="legenda">' +
      g.partes.map(function (p) { return '<div><i' + cls(p) + '></i><b>' + esc(p.rotulo) + '</b><span>' + esc(p.nota || '') + '</span></div>'; }).join('') +
      '</div></div>';
  }

  // camada do sujeito recortado (mesmo enquadramento da imagem); z-index no CSS (.camadas .recorte)
  function recorteDiv(s) { return s.recorte ? '<div class="recorte" style="background-image:url(\'' + esc(s.recorte) + '\')"></div>' : ''; }

  function corpoSlide(s) {
    var t = s.template;
    if (t === 'T1') {
      var foto = s.imagem
        ? '<div class="photo" style="background-image:url(\'' + esc(s.imagem) + '\')"></div>'
        : '<div class="photo">' + SVG_FOTO + '</div>';
      // tecido no T1 só quando pedido ("tecido": true); no T1b camadas é o padrão
      return foto + '<div class="scrim"></div>' + (s.tecido === true ? '<div class="tex-pano"></div>' : '') + '<div class="content">' + texto(s) + corpo(s) + '</div>' + recorteDiv(s) +
        (s.gancho ? '<div class="gancho">' + marcar(s.gancho) + '</div>' : '');
    }
    if (t === 'T1b' && s.recorte) {
      // modo camadas: foto sangrada > display > recorte do sujeito (rembg) > serifada na frente
      var fundo = s.imagem
        ? '<div class="photo" style="background-image:url(\'' + esc(s.imagem) + '\')"></div>'
        : '<div class="photo">' + SVG_FOTO + '</div>';
      // tecido só quando pedido (padrão sim); capas de banco usam "tecido": false
      return fundo + '<div class="scrim"></div>' + (s.tecido === false ? '' : '<div class="tex-pano"></div>') + '<div class="content">' + texto(s) + (s.bloco || s.sujeito ? corpo(s) : '') + '</div>' + recorteDiv(s) +
        (s.gancho ? '<div class="gancho">' + marcar(s.gancho) + '</div>' : '');
    }
    if (t === 'T1b') {
      var ret = s.imagem
        ? '<div class="portrait" style="background-image:url(\'' + esc(s.imagem) + '\')"></div>'
        : '<div class="portrait">' + SVG_RETRATO + '</div>';
      return '<div class="content">' + texto(s) + '</div>' + ret +
        (s.corpo ? '<div class="pill">' + marcar(s.corpo) + '</div>' : '') +
        (s.gancho ? '<div class="gancho">' + marcar(s.gancho) + '</div>' : '');
    }
    if (t === 'T2') {
      var fT2 = s.imagem === undefined ? '' : '<div class="foto"' + (s.imagem ? ' style="background-image:url(\'' + esc(s.imagem) + '\')">' : '>' + SVG_FOTO) + '</div>';
      // papel: textura de papel dobrado + halftone (só sem foto)
      var texP = s.imagem === undefined ? '<div class="tex-dobra"></div><div class="tex-ht"></div>' : '';
      return '<div class="vinheta"></div>' + texP + '<div class="content">' + texto(s) + corpo(s) + '</div>' + fT2 + recorteDiv(s);
    }
    if (t === 'T2c') return '<div class="grade"></div><div class="margem"></div><div class="jogo">#</div><div class="vinheta"></div><div class="tex-dobra"></div><div class="content">' + texto(s) + corpo(s) + '</div>';
    if (t === 'T3') {
      var extra = '';
      if (s.lista) extra += '<ol class="bloco-lista">' + s.lista.slice(0, 4).map(function (it, i) { return '<li><span class="n">' + pad2(i + 1) + '</span><span>' + marcar(it) + '</span></li>'; }).join('') + '</ol>';
      if (s.diagrama && s.diagrama.partes) extra += diagrama(s.diagrama);
      return '<div class="content">' + texto(s) + corpo(s) + extra + '</div>';
    }
    if (t === 'T5') {
      var r5 = s.referencia || {};
      var pr = r5.print ? '<img src="' + esc(r5.print) + '" alt="">' : '<div class="ph">' + esc(r5.site) + '</div>';
      return (s.display && s.display.length ? '<div class="ref-titulo">' + s.display.map(function (l) { return '<div>' + marcar(l) + '</div>'; }).join('') + '</div>' : '') +
        '<div class="chip">REFERÊNCIA</div><div class="navegador"><div class="barra-nav"><i class="d1"></i><i class="d2"></i><i class="d3"></i><span class="url">' + esc(r5.site) + '</span></div>' +
        '<div class="tela">' + pr + '</div><div class="info"><div class="nome">' + esc(r5.nome) + '</div><div class="desc">' + esc(r5.descricao) + '</div></div></div>';
    }
    // T4
    var c = s.cta ? '<div class="cta"><span class="pill">' + marcar(s.cta.acao) + '</span><div class="txt">' + marcar(s.cta.texto || '') + '</div></div>' : '';
    var bg = s.imagem === undefined ? '' : '<div class="photo"' + (s.imagem ? ' style="background-image:url(\'' + esc(s.imagem) + '\')">' : '>' + SVG_FOTO) + '</div><div class="veu"></div>';
    // T4 camadas: com `recorte`, o sujeito fica na frente do texto e fora do véu (aparece inteiro)
    return bg + '<div class="content">' + texto(s) + corpo(s) + c + '</div>' + recorteDiv(s);
  }

  function montarSlide(s, i, total, data) {
    var el = document.createElement('div');
    el.className = 'slide ' + String(s.template).toLowerCase() + (s.template === 'T2' && s.imagem !== undefined ? ' com-foto' : '') + (s.template === 'T4' && s.imagem !== undefined ? ' com-foto' : '') + (s.recorte && ['T1', 'T1b', 'T2', 'T4'].indexOf(s.template) >= 0 ? ' camadas' : '') + (s.template === 'T4' && s.recorte && s.texto === 'topo' ? ' texto-topo' : '') + (s.bloco || s.sujeito ? ' lay' : '') + (s.recorte && (s.template === 'T1' || s.template === 'T2' || s.bloco || s.sujeito) ? ' cam2' : '') + (s.template === 'T1b' ? ' fundo-' + (s.fundo === 'papel' ? 'papel' : 'ink') : '') + (s.rodape === 'claro' ? ' rodape-claro' : '') + (s.texto_frente ? ' texto-frente' : '');
    el.dataset.n = i + 1;
    var meta = data.meta || {}, tm = tema();
    // topo só com ano/mês; a posição no carrossel fica nas bolinhas do rodapé
    var dots = '';
    for (var k = 0; k < total; k++) dots += '<i' + (k === i ? ' class="on"' : '') + '></i>';
    var led = ['T2', 'T2c', 'T3'].indexOf(s.template) < 0 ? '' : s.textura === 'led' ? '<div class="tex-led"></div>' : s.textura === 'grain' ? '<div class="tex-grain"></div>' : '';
    if (s.textura === 'grain') el.classList.add('grain');
    el.innerHTML = '<div class="s">' + led + corpoSlide(s) +
      '<div class="meta">' + tm.topo.map(function (bl) {
        return '<span>' + esc(String(bl).replace('{nome}', tm.nome_meta).replace('{serie}', meta.serie || '').replace('{data}', meta.data || '')) + '</span>';
      }).join('') + '</div>' +
      '<div class="foot"><span class="handle">' + esc(tm.handle) + '</span>' +
      (tm.rodape_centro ? '<span class="centro">' + SVG_MARCADOR + '<span>' + esc(tm.rodape_centro) + '</span></span>' : '<span></span>') +
      '<span class="dots">' + dots + '</span></div></div>';
    return el;
  }

  /* ---------- bloco de texto (posição) e colisão com rostos (camadas) ---------- */
  // bloco {y, alinhar, largura}: posiciona o .content (topo y em u) à esquerda/direita/centro; vale em qualquer slide com foto
  function aplicarBloco(el, s) {
    var b = s.bloco; if (!b) return 936;
    var c = el.querySelector('.content'), w = b.largura || 936, al = b.alinhar || 'esquerda', st = c.style;
    st.top = 'calc(' + b.y + ' * var(--u))'; st.bottom = 'auto'; st.height = 'auto'; st.width = 'calc(' + w + ' * var(--u))';
    st.justifyContent = 'flex-start'; st.textAlign = al === 'direita' ? 'right' : al === 'centro' ? 'center' : 'left';
    var ai = al === 'direita' ? 'flex-end' : al === 'centro' ? 'center' : 'flex-start';
    st.alignItems = ai; st.setProperty('--al', ai);
    if (al === 'direita') { st.left = 'auto'; st.right = 'calc(72 * var(--u))'; }
    else if (al === 'centro') { st.left = 'calc(' + ((1080 - w) / 2) + ' * var(--u))'; st.right = 'auto'; }
    else { st.left = 'calc(72 * var(--u))'; st.right = 'auto'; }
    var d = c.querySelector('.display'); if (d) d.style.marginTop = '0';
    return w;
  }
  function caixa(els, base, u) {
    var r = null;
    els.forEach(function (x) {
      var q = x.getBoundingClientRect(); if (!q.width) return;
      var b = [(q.left - base.left) / u, (q.top - base.top) / u, (q.right - base.left) / u, (q.bottom - base.top) / u];
      r = r ? [Math.min(r[0], b[0]), Math.min(r[1], b[1]), Math.max(r[2], b[2]), Math.max(r[3], b[3])] : b;
    });
    return r;
  }
  function cruza(a, b, m) { m = m || 0; return a[0] < b[2] + m && a[2] > b[0] - m && a[1] < b[3] + m && a[3] > b[1] - m; }
  function arred(b) { return b && b.map(function (v) { return Math.round(v); }); }

  // Texto na frente (emocao, cta, corpo, gancho) nunca cobre cabeça nem rostos; display também não cobre rostos
  // (a cabeça do próprio sujeito recortado fica por cima do display, então só vale para texto à frente).
  // Determinístico, ≤ 20 tentativas por item: abaixo do display, abaixo da cabeça, acima da cabeça, acima do display,
  // cada uma no x atual e no lado com mais espaço; encolhe a emoção até 0.7× por último.
  function camadas(el, s, root, u, efs) {
    var base = el.getBoundingClientRect(), su = s.sujeito || {}, cab = su.cabeca || null, rostos = su.rostos || [];
    var propr = su.rostos_sujeito || [];  // rostos do próprio sujeito recortado: proibidos ao texto à frente; o display passa por trás
    var frente = (cab ? [cab] : []).concat(rostos, propr);
    var proibDisp = s.recorte ? rostos : rostos.concat(propr, cab ? [cab] : []);
    var disp = caixa(el.querySelectorAll('.dl'), base, u);
    var rep = { cabeca: cab, rostos: rostos, rostos_sujeito: propr, display: arred(disp), colisao: false, movidos: [] };
    var itens = [['emocao', '.emocao'], ['cta', '.cta'], ['corpo', '.corpo'], ['gancho', '.gancho']];
    var cur = {};  // caixa atual de cada item (os ainda não processados contam como obstáculo)
    itens.forEach(function (it) { var q = el.querySelector(it[1]); if (q) cur[it[0]] = caixa([q], base, u); });
    var fixos = [];
    itens.forEach(function (it) {
      var x = el.querySelector(it[1]); if (!x) return;
      fixos = Object.keys(cur).filter(function (k) { return k !== it[0]; }).map(function (k) { return cur[k]; });
      var m = 24, n = caixa([x], base, u), w = n[2] - n[0], h = n[3] - n[1];
      var livre = function (b) {
        return b[0] >= 71 && b[2] <= 1009 && b[1] >= 190 && b[3] <= 1280 &&
          !frente.some(function (f) { return cruza(b, f, m); }) && !cruza(b, disp, 0) && !fixos.some(function (f) { return cruza(b, f, 28); });
      };
      var final = n;
      if (frente.some(function (f) { return cruza(n, f, m); })) {
        var ok = null, tries = 0, escalas = it[0] === 'emocao' ? [1, 0.85, 0.7] : [1];
        for (var ei = 0; ei < escalas.length && !ok && tries < 20; ei++) {
          if (it[0] === 'emocao') { x.style.setProperty('--efsn', efs * escalas[ei]); x.style.transform = ''; }
          var nn = caixa([x], base, u); w = nn[2] - nn[0]; h = nn[3] - nn[1];
          var U = frente.reduce(function (a, f) { return [Math.min(a[0], f[0]), Math.min(a[1], f[1]), Math.max(a[2], f[2]), Math.max(a[3], f[3])]; }, [1e9, 1e9, -1e9, -1e9]);
          var ys = [disp[3] + 16, disp[1] - 16 - h, U[3] + m, U[1] - m - h];
          frente.forEach(function (f) { ys.push(f[3] + m, f[1] - m - h); });
          fixos.forEach(function (f) { ys.push(f[3] + 28, f[1] - 28 - h); });
          var ref = U;
          var esq = ref[0] - 72, dir = 1008 - ref[2];
          var xs = [nn[0], esq >= dir ? Math.max(72, ref[0] - m - w) : Math.min(1008 - w, ref[2] + m)];
          for (var yi = 0; yi < ys.length && !ok; yi++) for (var xi = 0; xi < xs.length && !ok; xi++) {
            if (++tries > 20) break;
            var cand = [xs[xi], ys[yi], xs[xi] + w, ys[yi] + h];
            if (livre(cand)) ok = [cand, nn];
          }
        }
        if (ok) {
          x.style.transform = 'translate(calc(' + (ok[0][0] - ok[1][0]) + ' * var(--u)), calc(' + (ok[0][1] - ok[1][1]) + ' * var(--u)))';
          final = ok[0]; rep.movidos.push(it[0]);
        } else { x.style.removeProperty('--efsn'); x.style.transform = ''; final = caixa([x], base, u); }
      }
      cur[it[0]] = final; rep[it[0]] = arred(final);
      if (frente.some(function (f) { return cruza(final, f, 0); })) rep.colisao = true;
    });
    if (disp && proibDisp.some(function (f) { return cruza(disp, f, 0); })) rep.colisao = true;
    return rep;
  }

  /* ---------- ajuste do display (determinístico, ≤ 20 iterações) ---------- */
  function ajustar(el, s) {
    var t = s.template, root = el.querySelector('.s'), u = el.getBoundingClientRect().width / 1080;
    if (t === 'T5') return { fs: 0, efs: 0 };
    var n = (s.display || []).length;
    var fs = (t === 'T1' || (t === 'T1b' && s.recorte)) ? 220 : n <= 2 ? 140 : n === 3 ? 120 : 100;
    if (t === 'T3' && (s.lista || s.diagrama)) fs = Math.min(fs, 120);
    var maxw = s.bloco ? aplicarBloco(el, s) : (t === 'T2c' ? 776 : 936);
    var maxe = t === 'T2c' && s.emocao && s.emocao.posicao === 'sobreposta' ? maxw + 90 : maxw;
    function medir(seletor) {
      var w = 0; el.querySelectorAll(seletor).forEach(function (x) { w = Math.max(w, x.getBoundingClientRect().width); }); return w / u;
    }
    for (var i = 0; i < 20; i++) {
      root.style.setProperty('--fsn', fs);
      var w = medir('.dl');
      if (w <= maxw) break;
      fs = Math.max(48, fs * maxw / w * 0.99);
    }
    var ef = fs * 1.1;
    for (i = 0; i < 20; i++) {
      root.style.setProperty('--efsn', ef);
      var we = medir('.emocao .ln');
      if (we <= maxe) break;
      ef = Math.max(40, ef * maxe / we * 0.99);
    }
    // T2 com foto: o bloco de texto (200u a 640u) não pode invadir a foto (começa em 700u).
    if (t === 'T2' && s.imagem !== undefined && !s.recorte && !s.bloco) {
      var ct = el.querySelector('.content');
      for (i = 0; i < 20; i++) {
        var top = ct.getBoundingClientRect().top, bot = top;
        ct.childNodes.forEach(function (x) { bot = Math.max(bot, x.getBoundingClientRect().bottom); });
        if ((bot - top) / u <= 440) break;
        fs = Math.max(48, fs * 0.93); ef = Math.max(40, ef * 0.93);
        root.style.setProperty('--fsn', fs); root.style.setProperty('--efsn', ef);
      }
    }
    var r = { fs: Math.round(fs), efs: Math.round(ef) };
    if (s.sujeito) r.camadas = camadas(el, s, root, u, ef);
    return r;
  }

  /* ---------- render ---------- */
  function render(data, container, opts) {
    opts = opts || {};
    var v = validate(data);
    container.innerHTML = '';
    if (!opts.only && v.errors.length) {
      var b = document.createElement('div'); b.className = 'erros'; b.textContent = 'ERROS DE VALIDAÇÃO\n' + v.errors.join('\n'); container.appendChild(b);
    }
    if (!opts.only && v.warnings.length) {
      var w = document.createElement('div'); w.className = 'avisos'; w.textContent = v.warnings.join('\n'); container.appendChild(w);
    }
    var slides = (data && data.slides) || [], els = [];
    slides.forEach(function (s, i) {
      if (opts.only && opts.only !== i + 1) return;
      if (TEMPLATES.indexOf(s.template) < 0) return;
      var el = montarSlide(s, i, slides.length, data); container.appendChild(el); els.push([el, s]);
    });
    var lista = tema().fontes;
    var fontes = document.fonts && lista.length ? Promise.all(lista.map(function (f) { return document.fonts.load(f); })) : Promise.resolve();
    return fontes.catch(function () {}).then(function () {
      var tamanhos = els.map(function (p) { return ajustar(p[0], p[1]); });
      var rel = { slides: slides.length, errors: v.errors, warnings: v.warnings, fit: tamanhos };
      var cams = tamanhos.map(function (x) { return x.camadas; }).filter(Boolean);
      window.__fitReport = { camadas: cams.length === 1 ? cams[0] : cams };
      document.title = 'READY:' + JSON.stringify(rel);
      return rel;
    });
  }

  window.Carrossel = { render: render, validate: validate };
})();
