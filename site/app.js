/* Radar da Câmara de Teresópolis — interface.
   Lê window.DADOS (gerado por coletor/processar.py) e window.CONFIG (config.js). */
(() => {
  "use strict";
  const D = window.DADOS || {vereadores: [], proposicoes: [], noticias: []};
  const CFG = Object.assign({siteUrl: "", repoUrl: "", erroUrl: "", contatoEmail: "", goatcounter: ""}, window.CONFIG || {});
  const main = document.getElementById("conteudo");
  const noticia = Object.fromEntries(D.noticias.map(n => [n.id, n]));
  const vereador = Object.fromEntries(D.vereadores.map(v => [v.slug, v]));
  const prop = Object.fromEntries(D.proposicoes.map(p => [p.chave, p]));
  const reduzir = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ================= utilidades ================= */
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  const sem = t => String(t).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const slug = t => sem(t).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const data = iso => iso ? new Date(iso + "T12:00:00").toLocaleDateString("pt-BR", {day: "numeric", month: "short", year: "numeric"}) : "";
  const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  const nomeMes = ym => { const [a, m] = ym.split("-"); return `${MESES[+m - 1]} ${a}`; };
  const slugProp = k => k.replace(/[ /]/g, "-");
  const chaveDeSlug = s => { const m = decodeURIComponent(s || "").match(/^([A-Z]+)-(\d+)-(\d+)$/); return m ? `${m[1]} ${m[2]}/${m[3]}` : null; };
  const classe = (pre, s) => pre + slug(s);
  const plural = (n, um, varios) => `<b class="num">${n}</b> ${n === 1 ? um : varios}`;
  const contador = n => `<b class="num contador" data-alvo="${n}">${reduzir ? n : 0}</b>`;
  const nomeAutor = a => vereador[a] ? `<a href="#/vereador/${a}">${esc(vereador[a].nome)}</a>` : esc(a);
  const deAutor = a => (a === "Executivo" ? "do " : a === "Mesa Diretora" ? "da " : "de ") + nomeAutor(a);
  const SIT_ORDEM = ["aprovado", "rejeitado", "vetado", "em comissão", "lido em plenário", "apresentado", "adiado", "citado", "revogada", "lei citada"];
  const ehLei = p => p.tipo === "LEI" || p.tipo === "LC";
  const tituloProp = p => p.ementa || (ehLei(p) ? `${p.tipo_nome} nº ${p.numero}/${p.ano}` : "");
  const aprovadosDe = v => v.autoria.filter(k => prop[k]?.situacao === "aprovado").length;
  const TEMAS = [...new Set([...D.proposicoes.flatMap(p => p.temas || []), ...D.noticias.flatMap(n => n.temas || [])])].sort();
  const temaDeSlug = s => TEMAS.find(t => slug(t) === s);
  const ICON = {
    voltar: `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>`,
    zap: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.7-1.2s.2-1.1.2-1.2-.2-.2-.5-.3z"/></svg>`,
    link: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></svg>`,
    erro: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 21V4h12l-1.5 4L16 12H4"/></svg>`,
    estrela: `<svg viewBox="0 0 24 24"><path d="M12 3.2l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 17l-5.4 2.9 1.1-6.1-4.5-4.2 6.1-.8z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>`,
    baixar: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11m0 0l-4-4m4 4l4-4M5 20h14"/></svg>`,
  };

  /* ================= glossário ================= */
  const GLOSSARIO = {
    "PL": ["Projeto de Lei", "Proposta de lei comum. Pode ser apresentada por vereadores, pelo prefeito ou pela população. Se aprovada e sancionada, vira lei municipal."],
    "PLC": ["Projeto de Lei Complementar", "Trata de temas que a Lei Orgânica exige em lei complementar, como código tributário, estrutura da prefeitura e plano diretor. Precisa de maioria absoluta para passar."],
    "PR": ["Projeto de Resolução", "Decide assuntos internos da própria Câmara, como o regimento e o horário das sessões. Não vai para o prefeito."],
    "PDL": ["Projeto de Decreto Legislativo", "Decisões da Câmara com efeito fora dela, como aprovar as contas do prefeito ou conceder títulos de cidadão."],
    "PELO": ["Emenda à Lei Orgânica", "Muda a Lei Orgânica, a “constituição” do município. Exige votação em dois turnos e dois terços dos vereadores."],
    "LEI": ["Lei municipal", "Uma lei que já está em vigor (ou esteve). Aparece aqui quando é citada nas notícias."],
    "LC": ["Lei complementar", "Uma lei complementar já em vigor (ou revogada), citada nas notícias."],
    "apresentado": ["Apresentado", "O projeto foi protocolado na Câmara. Ainda vai ser lido em plenário e analisado pelas comissões."],
    "lido em plenário": ["Lido em plenário", "O projeto foi lido numa sessão, o que inicia oficialmente a tramitação. Em seguida vai para as comissões."],
    "em comissão": ["Nas comissões", "Grupos de 3 vereadores especializados (Justiça, Finanças, Saúde etc.) analisam e dão parecer antes da votação."],
    "adiado": ["Adiado", "A votação foi adiada, retirada de pauta ou houve pedido de vista (mais tempo para analisar)."],
    "aprovado": ["Aprovado", "O plenário aprovou. Projetos de lei ainda vão para o prefeito, que pode sancionar (virar lei) ou vetar."],
    "rejeitado": ["Rejeitado", "O plenário votou contra, ou o projeto foi arquivado."],
    "vetado": ["Vetado", "O prefeito recusou o projeto aprovado. A Câmara pode derrubar o veto em nova votação."],
    "citado": ["Só citado", "A notícia menciona o projeto, mas não diz em que etapa ele está."],
    "revogada": ["Revogada", "A lei deixou de valer porque outra lei a cancelou."],
    "lei citada": ["Lei citada", "Uma lei existente mencionada na notícia, não um projeto em tramitação."],
    "Executivo": ["Executivo", "A Prefeitura. Projetos “do Executivo” são enviados pelo prefeito."],
    "Mesa Diretora": ["Mesa Diretora", "Presidente, vice e secretários da Câmara, que administram a Casa."],
  };
  const termo = (chave, texto) => GLOSSARIO[chave] ? `<button type="button" class="termo" data-termo="${esc(chave)}">${texto ?? esc(chave)}</button>` : (texto ?? esc(chave));
  const pilula = s => `<button type="button" class="situacao ${classe("s-", s)}" data-termo="${esc(s)}" aria-label="${esc(s)}: o que significa">${esc(s)}</button>`;

  /* ================= preferências do leitor ================= */
  const CHAVE = "radar-tere-v1";
  const ler = () => { try { return JSON.parse(localStorage.getItem(CHAVE)) || {}; } catch { return {}; } };
  const pref = Object.assign({seguindo: [], ultimaVisita: null}, ler());
  const salvar = () => { try { localStorage.setItem(CHAVE, JSON.stringify(pref)); } catch {} };
  const visitaAnterior = pref.ultimaVisita;
  pref.ultimaVisita = new Date().toISOString().slice(0, 10); salvar();
  const segue = s => pref.seguindo.includes(s);
  const alternarSeguir = s => { pref.seguindo = segue(s) ? pref.seguindo.filter(x => x !== s) : [...pref.seguindo, s]; salvar(); };
  const novidade = v => visitaAnterior && v.mencoes.some(m => (noticia[m.noticia]?.data || "") > visitaAnterior);
  let comparar = [];
  const estado = {ordem: "nome", partido: "", soSeguindo: false, busca: "", tipo: "", sit: "", ano: "", tema: "", mostrar: 20, leis: false};

  /* ================= avatar ================= */
  const CORES = ["#3E6E8E", "#8A5A44", "#5B6F2E", "#7A4E7E", "#2F7A74", "#9A6B1F", "#6B5B95", "#A0475B", "#4F6D5A", "#56708A", "#8C5E3C", "#3F7F5F"];
  const partidos = [...new Set(D.vereadores.map(v => v.partido))].sort();
  const corPartido = p => CORES[partidos.indexOf(p) % CORES.length] || "var(--mata)";
  const iniciais = nome => {
    const p = nome.replace(/\b(Dr|Dra|Pr|Prof|Profa|Professora|Professor|Pastor|Vereador|Vereadora)\.?\s+/gi, "").split(/\s+/).filter(Boolean);
    return ((p[0]?.[0] || "") + (p.length > 1 ? p[p.length - 1][0] : (p[0]?.[1] || ""))).toUpperCase();
  };
  const avatar = (v, grande = false) => `<span class="avatar${grande ? " grande" : ""}" style="--cor:${corPartido(v.partido)}" aria-hidden="true">${v.foto
    ? `<img src="fotos/${esc(v.foto)}" alt="" loading="lazy" onerror="this.replaceWith(document.createTextNode('${iniciais(v.nome)}'))">` : iniciais(v.nome)}</span>`;

  /* ================= compartilhar e reportar ================= */
  const urlAtual = () => (CFG.siteUrl ? CFG.siteUrl.replace(/\/$/, "/") + location.hash : location.href);
  const linkZap = texto => `https://wa.me/?text=${encodeURIComponent(texto + "\n" + urlAtual())}`;
  const linkErro = contexto => {
    if (CFG.erroUrl) return CFG.erroUrl;
    if (!CFG.repoUrl) return "#/sobre";
    const corpo = `Página: ${urlAtual()}\n\nO que está errado:\n\nOnde está a informação correta (link, se tiver):\n`;
    return `${CFG.repoUrl.replace(/\/$/, "")}/issues/new?title=${encodeURIComponent("Erro: " + contexto)}&body=${encodeURIComponent(corpo)}`;
  };
  const botoesAcao = (textoZap, contexto) => `
    <a class="botao zap" href="${esc(linkZap(textoZap))}" target="_blank" rel="noopener">${ICON.zap}WhatsApp</a>
    <button type="button" class="botao secundario" data-acao="copiar">${ICON.link}Copiar link</button>
    <a class="botao secundario" href="${esc(linkErro(contexto))}" target="_blank" rel="noopener">${ICON.erro}Encontrou um erro?</a>`;

  function toast(msg) {
    document.querySelector(".toast")?.remove();
    const t = document.createElement("div"); t.className = "toast"; t.textContent = msg; t.setAttribute("role", "status");
    document.body.appendChild(t); setTimeout(() => t.remove(), 2100);
  }
  function copiarLink() {
    const url = urlAtual();
    const falhou = () => toast("Copie o endereço na barra do navegador");
    try { navigator.clipboard.writeText(url).then(() => toast("Link copiado"), falhou); } catch { falhou(); }
  }

  const avisoDemo = D.demo ? `<p class="aviso entra">Demonstração com notícias e vereadores fictícios. Os dados reais aparecem quando o coletor roda.</p>` : "";

  /* ================= cabeçalho vivo ================= */
  (function cabecalho() {
    const el = document.querySelector("#vivo span");
    if (!D.gerado_em) { el.textContent = "Aguardando a primeira coleta de notícias"; return; }
    const g = new Date(D.gerado_em), hoje = new Date();
    const dia = g.toDateString() === hoje.toDateString() ? "hoje" : g.toDateString() === new Date(hoje - 864e5).toDateString() ? "ontem" : g.toLocaleDateString("pt-BR", {day: "numeric", month: "long"});
    el.textContent = `Atualizado ${dia} às ${g.toLocaleTimeString("pt-BR", {hour: "2-digit", minute: "2-digit"})}. ${D.noticias.length} notícias analisadas.`;
    document.getElementById("atualizado").textContent = `Última atualização: ${g.toLocaleString("pt-BR")}.`;
    document.getElementById("link-codigo").href = CFG.repoUrl || "#/sobre";
    document.getElementById("link-erro-rodape").href = linkErro("geral");
    if (!reduzir) {
      const fundo = document.querySelector(".serra.fundo"), nevoa = document.querySelector(".nevoa");
      let pedido = false;
      addEventListener("scroll", () => {
        if (pedido) return; pedido = true;
        requestAnimationFrame(() => { const y = Math.min(scrollY, 400); fundo.style.transform = `translateY(${y * .18}px)`; nevoa.style.translate = `0 ${y * .3}px`; pedido = false; });
      }, {passive: true});
    }
  })();

  /* ================= gráficos ================= */
  function contarPorMes(noticias) {
    if (!D.noticias.length) return [];
    const c = {};
    noticias.forEach(n => { const k = n.data.slice(0, 7); c[k] = (c[k] || 0) + 1; });
    const datas = D.noticias.map(n => n.data.slice(0, 7)).sort();
    let [a, m] = datas[0].split("-").map(Number); const [af, mf] = datas[datas.length - 1].split("-").map(Number);
    const out = [];
    while (a < af || (a === af && m <= mf)) { const k = `${a}-${String(m).padStart(2, "0")}`; out.push([k, c[k] || 0]); m++; if (m > 12) { m = 1; a++; } }
    return out.length > 18 ? out.slice(-18) : out;
  }
  function graficoMensal(serie, {altura = 150, rotulo = "notícias", link = k => `#/sessoes/mes/${k}`, destaque = null} = {}) {
    if (!serie.length) return `<p class="vazio">Sem dados ainda.</p>`;
    const max = Math.max(1, ...serie.map(s => s[1]));
    const passo = Math.max(1, Math.ceil(max / 3)), teto = passo * Math.ceil(max / passo);
    const ticks = []; for (let t = 0; t <= teto; t += passo) ticks.push(t);
    const ano = k => serie.length > 12 || serie[0][0].slice(0, 4) !== serie[serie.length - 1][0].slice(0, 4) ? (k.endsWith("-01") || k === serie[0][0] ? `<br>${k.slice(2, 4)}` : "") : "";
    return `<div class="mensal" style="--h:${altura}px" role="group" aria-label="${rotulo} por mês">
      <div class="area">${ticks.map(t => `<span class="grade" style="bottom:${t / teto * 100}%"><em>${t}</em></span>`).join("")}
        <div class="cols">${serie.map(([k, v], i) => `<a href="${link(k)}" class="${destaque && destaque !== k ? "mudo" : ""}${destaque === k ? " atual" : ""}" aria-label="${nomeMes(k)}: ${v} ${rotulo}" data-dica="${nomeMes(k)}: ${v} ${rotulo}"><span class="v" style="height:${v / teto * 100}%;--i:${i}"></span></a>`).join("")}</div>
      </div>
      <div class="rotulos">${serie.map(([k]) => `<span>${MESES[+k.slice(5) - 1]}${ano(k)}</span>`).join("")}</div></div>`;
  }
  function barraSituacao(lista, link = s => `#/projetos/situacao/${slug(s)}`) {
    const c = {}; lista.forEach(p => c[p.situacao] = (c[p.situacao] || 0) + 1);
    const ord = SIT_ORDEM.filter(s => c[s]);
    if (!ord.length) return `<p class="vazio">Nenhum projeto.</p>`;
    return `<div class="empilhada" role="list">${ord.map(s => `<a role="listitem" data-sit="${esc(s)}" class="${classe("c-", s)}" style="flex:${c[s]}" href="${link(s)}" data-dica="${esc(s)}: ${c[s]}" aria-label="${esc(s)}: ${c[s]}"></a>`).join("")}</div>
      <div class="legenda">${ord.map(s => `<a data-sit="${esc(s)}" href="${link(s)}"><i class="${classe("c-", s)}"></i>${esc(s)} <b class="num">${c[s]}</b></a>`).join("")}</div>`;
  }
  function barrasTemas(contagem, link = t => `#/projetos/tema/${slug(t)}`, limite = 12) {
    const itens = Object.entries(contagem).filter(e => e[1]).sort((a, b) => b[1] - a[1]).slice(0, limite);
    if (!itens.length) return `<p class="leg">Nenhum tema identificado ainda.</p>`;
    const max = itens[0][1];
    return `<div class="hbarras">${itens.map(([t, n], i) => `<a href="${link(t)}"><span class="t">${esc(t)}</span><span class="b"><span style="width:${(n / max * 100).toFixed(1)}%;--i:${i}"></span></span><span class="n">${n}</span></a>`).join("")}</div>`;
  }
  const dica = document.getElementById("dica");
  document.addEventListener("pointerover", e => { const d = e.target.closest?.("[data-dica]"); if (d && e.pointerType === "mouse") { dica.textContent = d.dataset.dica; dica.hidden = false; } });
  document.addEventListener("pointermove", e => { if (!dica.hidden) { dica.style.left = Math.min(e.clientX + 12, innerWidth - dica.offsetWidth - 8) + "px"; dica.style.top = (e.clientY - 38) + "px"; } });
  document.addEventListener("pointerout", e => { if (e.target.closest?.("[data-dica]")) dica.hidden = true; });

  /* ================= etapas da lei ================= */
  const ETAPAS = ["Apresentado", "Lido em plenário", "Comissões", "Votação", "Prefeito"];
  function etapas(p) {
    if (ehLei(p)) return "";
    const pos = {"apresentado": 0, "lido em plenário": 1, "em comissão": 2, "adiado": 3, "aprovado": 3, "rejeitado": 3, "vetado": 4}[p.situacao];
    if (pos === undefined) return `<p class="nota">As notícias citam este projeto, mas não dizem em que etapa ele está.</p>`;
    const falhou = p.situacao === "rejeitado" || p.situacao === "vetado";
    const concluida = p.situacao === "aprovado" ? 3 : falhou ? pos - 1 : pos - 1;
    const prog = Math.max(0, Math.min(1, (p.situacao === "aprovado" ? 3 : pos) / 4)) * 80;
    const explica = {
      "aprovado": p.tipo === "PR" || p.tipo === "PDL" ? "Aprovado pela Câmara. Este tipo de projeto não vai para o prefeito." : "Aprovado pela Câmara. A próxima etapa é a sanção ou o veto do prefeito, que o Radar ainda não acompanha.",
      "rejeitado": "O plenário rejeitou o projeto.", "vetado": "O prefeito vetou o projeto. A Câmara ainda pode derrubar o veto.",
      "adiado": "A votação foi adiada.", "em comissão": "O projeto está sendo analisado pelas comissões.",
      "lido em plenário": "O projeto foi lido em sessão e deve seguir para as comissões.", "apresentado": "O projeto acabou de ser apresentado.",
    }[p.situacao];
    return `<div class="cartao entra" style="--i:2"><h3>Em que etapa está</h3><p class="leg">${esc(explica)}</p>
      <ol class="etapas" style="--progresso:0%" data-progresso="${prog}%"><span class="trilha" aria-hidden="true"></span>
      ${ETAPAS.map((e, i) => `<li class="${i <= concluida ? "feita" : ""}${i === pos && !(p.situacao === "aprovado") ? (falhou ? " falhou" : " atual") : ""}${p.situacao === "aprovado" && i === 4 && p.tipo !== "PR" && p.tipo !== "PDL" ? " atual" : ""}"><i>${i <= concluida ? "✓" : falhou && i === pos ? "✕" : i + 1}</i>${e}</li>`).join("")}</ol></div>`;
  }

  /* ================= itens ================= */
  function cartaoProp(p, i = 0) {
    const autores = p.autores.length ? p.autores.map(deAutor).join(", ") : "autoria não informada";
    const t = tituloProp(p);
    return `<li class="prop entra" style="--i:${Math.min(i, 12)}">
      <div class="topo"><button type="button" class="codigo" data-termo="${p.tipo}" title="${esc(p.tipo_nome)}">${esc(p.chave)}</button>${pilula(p.situacao)}</div>
      <a class="titulo${t ? "" : " sem"}" href="#/projeto/${slugProp(p.chave)}">${esc(t || "A notícia não descreve este projeto")}</a>
      <div class="meta">${autores}, ${data(p.data_situacao)}</div>
      ${(p.temas || []).length ? `<div class="temas-mini">${p.temas.map(x => `<a href="#/projetos/tema/${slug(x)}">${esc(x)}</a>`).join("")}</div>` : ""}</li>`;
  }
  const botaoSeguir = v => `<button type="button" class="seguir" data-seguir="${v.slug}" aria-pressed="${segue(v.slug)}" aria-label="${segue(v.slug) ? "Deixar de seguir" : "Seguir"} ${esc(v.nome)}" title="${segue(v.slug) ? "Seguindo" : "Seguir"}">${ICON.estrela}</button>`;
  function itemNoticia(n, i = 0) {
    return `<li class="entra" style="--i:${Math.min(i, 10)}"><time>${data(n.data)}</time><a class="tit" href="${esc(n.link)}" target="_blank" rel="noopener">${esc(n.titulo)}</a>
      <div class="etiquetas">${n.proposicoes.map(k => `<a href="#/projeto/${slugProp(k)}">${esc(k)}</a>`).join("")}
      ${n.vereadores.map(s => `<a href="#/vereador/${s}">${segue(s) ? "★ " : ""}${esc(vereador[s]?.nome)}</a>`).join("")}</div></li>`;
  }

  /* ================= INÍCIO ================= */
  function inicio() {
    if (!D.noticias.length) return avisoDemo + `<div class="vazio">Ainda não há notícias carregadas. O coletor roda automaticamente todo dia; depois da primeira execução, o painel aparece aqui.</div>`;
    const sessoes = D.noticias.filter(n => n.sessao).length;
    const projetos = D.proposicoes.filter(p => !ehLei(p));
    const aprov = projetos.filter(p => p.situacao === "aprovado");
    const contTemas = {}; projetos.forEach(p => (p.temas || []).forEach(t => contTemas[t] = (contTemas[t] || 0) + 1));
    const recentes = [...aprov].sort((a, b) => b.data_situacao.localeCompare(a.data_situacao)).slice(0, 4);
    const seguidos = pref.seguindo.map(s => vereador[s]).filter(Boolean);
    let blocoSeguidos;
    if (seguidos.length) {
      const novas = D.noticias.filter(n => n.vereadores.some(segue) && (!visitaAnterior || n.data > visitaAnterior)).slice(0, 5);
      blocoSeguidos = `<h2 class="secao">Quem você segue</h2>
        <div class="chips" style="margin-bottom:14px">${seguidos.map(v => `<a class="chip" href="#/vereador/${v.slug}">★ ${esc(v.nome)}</a>`).join("")}</div>
        ${novas.length ? `<p class="intro">${visitaAnterior ? `Desde sua última visita (${data(visitaAnterior)}):` : "Mais recentes:"}</p><ol class="linha-tempo">${novas.map(itemNoticia).join("")}</ol>`
          : `<p class="intro">Nenhuma notícia nova sobre eles desde ${data(visitaAnterior)}.</p>`}`;
    } else {
      blocoSeguidos = `<p class="nota entra" style="margin-top:16px;--i:4">Toque na ★ ao lado de um vereador para segui-lo. Na próxima visita, esta página mostra o que saiu sobre ele.</p>`;
    }
    return avisoDemo + `
      <div class="painel">
        <a class="cifra entra" style="--i:0" href="#/sessoes">${contador(sessoes)}<span>sessões noticiadas</span></a>
        <a class="cifra entra" style="--i:1" href="#/projetos">${contador(projetos.length)}<span>projetos acompanhados</span></a>
        <a class="cifra entra" style="--i:2" href="#/projetos/situacao/aprovado">${contador(aprov.length)}<span>aprovados</span></a>
        <a class="cifra entra" style="--i:3" href="#/vereadores">${contador(D.vereadores.length)}<span>vereadores</span></a>
      </div>
      ${blocoSeguidos}
      ${recentes.length ? `<h2 class="secao">Aprovados recentemente</h2><ul class="lista">${recentes.map(cartaoProp).join("")}</ul>` : ""}
      <h2 class="secao">Atividade da Câmara</h2>
      <div class="cartao entra"><h3>Notícias por mês</h3><p class="leg">Toque em um mês para ver o que aconteceu.</p>${graficoMensal(contarPorMes(D.noticias))}</div>
      <div class="dupla" style="margin-top:14px">
        <div class="cartao entra" style="--i:1"><h3>Assuntos dos projetos</h3><p class="leg">Toque em um tema para ver os projetos.</p>${barrasTemas(contTemas)}</div>
        <div class="cartao entra" style="--i:2"><h3>Em que pé estão</h3><p class="leg">Toque numa cor para ver os projetos. Toque no nome para entender a etapa.</p>${barraSituacao(projetos)}</div>
      </div>
      <h2 class="secao">Últimas notícias da Câmara</h2>
      <ol class="linha-tempo">${D.noticias.slice(0, 5).map(itemNoticia).join("")}</ol>
      <a class="botao secundario" href="#/sessoes">Ver todas as notícias</a>`;
  }

  /* ================= VEREADORES ================= */
  function vereadores() {
    return avisoDemo + `
      <p class="nota entra" style="margin-bottom:18px">Os números mostram quantas notícias da Câmara citam cada vereador e quantos projetos as notícias atribuem a ele. Não medem desempenho: o presidente, por exemplo, aparece em quase todas as sessões porque as conduz.</p>
      <div class="ferramentas"><div class="chips" id="f-partido" role="group" aria-label="Filtrar por partido">
        <button type="button" class="chip" data-partido="" aria-pressed="${!estado.partido}">Todos</button>
        ${partidos.map(p => `<button type="button" class="chip" data-partido="${esc(p)}" aria-pressed="${estado.partido === p}"><i class="avatar" style="--cor:${corPartido(p)};width:10px;height:10px;align-self:center"></i>${esc(p)} <small>${D.vereadores.filter(v => v.partido === p).length}</small></button>`).join("")}
      </div></div>
      <div class="ferramentas">
        <label>Ordenar por <select id="ordem"><option value="nome">nome</option><option value="mencoes">mais citados</option><option value="projetos">mais projetos</option><option value="aprovados">mais aprovados</option></select></label>
        <label><input type="checkbox" id="so-seguindo" ${estado.soSeguindo ? "checked" : ""}> Só quem eu sigo</label>
      </div>
      <div class="grade-ver" id="lista-ver"></div>`;
  }
  function desenharVereadores(animar = true) {
    let lista = D.vereadores.filter(v => (!estado.partido || v.partido === estado.partido) && (!estado.soSeguindo || segue(v.slug)));
    const chave = {mencoes: v => v.mencoes.length, projetos: v => v.autoria.length, aprovados: aprovadosDe}[estado.ordem];
    lista = [...lista].sort((a, b) => chave ? (chave(b) - chave(a) || a.nome.localeCompare(b.nome)) : a.nome.localeCompare(b.nome, "pt-BR"));
    const el = document.getElementById("lista-ver");
    el.innerHTML = lista.length ? lista.map((v, i) => `<div class="ver${novidade(v) ? " novo" : ""}${animar ? " entra" : ""}" style="--i:${Math.min(i, 14)}">
        ${avatar(v)}
        <a class="nome" href="#/vereador/${v.slug}">${esc(v.nome)}</a>
        <span class="partido">${esc(v.partido)}${v.cargo ? ", " + esc(v.cargo) : ""}</span>
        <div class="canto">${botaoSeguir(v)}<label class="comparar-cx"><input type="checkbox" data-comparar="${v.slug}" ${comparar.includes(v.slug) ? "checked" : ""}> comparar</label></div>
        <div class="numeros"><span>aparece em ${plural(v.mencoes.length, "notícia", "notícias")}</span><span>${plural(v.autoria.length, "projeto", "projetos")}</span><span>${plural(aprovadosDe(v), "aprovado", "aprovados")}</span></div>
      </div>`).join("") : `<div class="vazio">${estado.soSeguindo ? "Você ainda não segue ninguém. Toque na ★ de um vereador." : "Nenhum vereador com esse filtro."}</div>`;
    document.getElementById("ordem").value = estado.ordem;
  }
  function desenharBarraComparar() {
    const b = document.getElementById("barra-comparar");
    if (!comparar.length) { b.hidden = true; return; }
    b.hidden = false;
    b.innerHTML = comparar.length === 1
      ? `<span>${esc(vereador[comparar[0]].nome)}: escolha mais um</span><button type="button" class="fechar" aria-label="Limpar seleção">×</button>`
      : `<span>${esc(vereador[comparar[0]].nome)} e ${esc(vereador[comparar[1]].nome)}</span><a class="botao primario" href="#/comparar/${comparar[0]}/${comparar[1]}">Comparar</a><button type="button" class="fechar" aria-label="Limpar seleção">×</button>`;
  }

  /* ================= PERFIL ================= */
  function perfil(s) {
    const v = vereador[s];
    if (!v) return `<div class="vazio">Vereador não encontrado. <a href="#/vereadores">Ver a lista completa</a>.</div>`;
    const props = v.autoria.map(k => prop[k]).filter(Boolean);
    const mens = v.mencoes.map(m => noticia[m.noticia]).filter(Boolean);
    const mencoes = [...v.mencoes].sort((a, b) => (noticia[b.noticia]?.data || "").localeCompare(noticia[a.noticia]?.data || ""));
    const andamento = props.filter(p => !["aprovado", "rejeitado", "vetado", "citado"].includes(p.situacao)).length;
    return avisoDemo + `<a class="voltar" href="#/vereadores">${ICON.voltar}Todos os vereadores</a>
      <section>
        <div class="perfil-topo entra">${avatar(v, true)}
          <div class="quem"><h2 class="nome-grande">${esc(v.nome)}</h2>
          <p class="sub">${esc(v.partido)}${v.cargo ? `, ${esc(v.cargo)}` : ""}${v.url && v.url !== "#" ? `. <a href="${esc(v.url)}" target="_blank" rel="noopener">Página na Câmara</a>` : ""}</p></div>
          <button type="button" class="botao ${segue(v.slug) ? "primario" : "secundario"}" data-seguir="${v.slug}" aria-pressed="${segue(v.slug)}">${segue(v.slug) ? "★ Seguindo" : "☆ Seguir"}</button>
        </div>
        <div class="resumo entra" style="--i:1">
          <div>${contador(v.mencoes.length)}notícias citam</div><div>${contador(props.length)}projetos de autoria</div>
          <div>${contador(aprovadosDe(v))}aprovados</div><div>${contador(andamento)}em andamento</div>
        </div>
        <div class="acoes entra" style="--i:2;margin-bottom:22px">${botoesAcao(`${v.nome} (${v.partido}) no Radar da Câmara de Teresópolis: ${props.length} projetos de autoria, ${aprovadosDe(v)} aprovados.`, v.nome)}</div>
        <div class="dupla">
          <div class="cartao entra" style="--i:3"><h3>Presença nas notícias</h3><p class="leg">Notícias que citam ${esc(v.nome)}, por mês.</p>${graficoMensal(contarPorMes(mens), {altura: 130})}</div>
          <div class="cartao entra" style="--i:4"><h3>Assuntos em que aparece</h3><p class="leg">Por quantidade de notícias.</p>${barrasTemas(v.temas || {}, t => `#/projetos/tema/${slug(t)}`, 6)}</div>
        </div>
        <h2 class="secao">Projetos de autoria</h2>
        ${props.length ? `<ul class="lista">${props.map(cartaoProp).join("")}</ul>`
          : `<div class="vazio">Nenhum projeto atribuído a este vereador nas notícias. Isso não quer dizer que ele não tenha apresentado projetos: muitas notícias não informam o autor.</div>`}
        <h2 class="secao">O que as notícias registram</h2>
        ${mencoes.length ? `<ol class="linha-tempo">${mencoes.map((m, i) => { const n = noticia[m.noticia]; return n ? `<li class="entra" style="--i:${Math.min(i, 10)}"><time>${data(n.data)}</time>
          <a class="tit" href="${esc(n.link)}" target="_blank" rel="noopener">${esc(n.titulo)}</a>${m.trechos.map(t => `<p class="trecho">${esc(t)}</p>`).join("")}</li>` : ""; }).join("")}</ol>`
          : `<div class="vazio">Nenhuma notícia cita este vereador ainda.</div>`}
      </section>`;
  }

  /* ================= COMPARAR ================= */
  function compararVer(a, b) {
    const A = vereador[a], B = vereador[b];
    if (!A || !B) return `<div class="vazio">Escolha dois vereadores na <a href="#/vereadores">lista</a> para comparar.</div>`;
    const met = [["Notícias que citam", v => v.mencoes.length], ["Projetos de autoria", v => v.autoria.length], ["Projetos aprovados", aprovadosDe]];
    const serie = v => contarPorMes(v.mencoes.map(m => noticia[m.noticia]).filter(Boolean));
    const temas = [...new Set([...Object.keys(A.temas || {}), ...Object.keys(B.temas || {})])];
    const maxT = Math.max(1, ...temas.flatMap(t => [A.temas?.[t] || 0, B.temas?.[t] || 0]));
    const corB = "var(--estrela)";
    return avisoDemo + `<a class="voltar" href="#/vereadores">${ICON.voltar}Todos os vereadores</a>
      <div class="comparacao entra" style="margin-bottom:14px">${[A, B].map(v => `<div class="cabeca">${avatar(v)}<div><h2 style="font-size:clamp(20px,3vw,28px)"><a href="#/vereador/${v.slug}" style="color:inherit">${esc(v.nome)}</a></h2><span class="leg">${esc(v.partido)}</span></div></div>`).join("")}</div>
      ${met.map(([rot, f], i) => { const x = f(A), y = f(B); return `<div class="par entra" style="--i:${i + 1}">
        <div class="cartao"><span class="leg">${rot}</span><br><b class="${x > y ? "vence" : ""}">${x}</b></div>
        <div class="cartao"><span class="leg">${rot}</span><br><b class="${y > x ? "vence" : ""}">${y}</b></div></div>`; }).join("")}
      <div class="comparacao">${[A, B].map((v, i) => `<div class="cartao entra" style="--i:${i + 4}"><h3>${esc(v.nome)}</h3><p class="leg">Notícias por mês</p>${graficoMensal(serie(v), {altura: 120})}</div>`).join("")}</div>
      <h2 class="secao">Assuntos</h2>
      <div class="cartao entra">${temas.length ? `<div class="hbarras">${temas.map((t, i) => `
        <div class="linha" style="grid-template-columns:minmax(0,12em) 1fr"><span class="t">${esc(t)}</span>
        <span style="display:flex;flex-direction:column;gap:3px">
          <span class="b" title="${esc(A.nome)}: ${A.temas?.[t] || 0}"><span style="width:${((A.temas?.[t] || 0) / maxT * 100).toFixed(1)}%;--i:${i}"></span></span>
          <span class="b" title="${esc(B.nome)}: ${B.temas?.[t] || 0}"><span style="width:${((B.temas?.[t] || 0) / maxT * 100).toFixed(1)}%;background:${corB};--i:${i}"></span></span>
        </span></div>`).join("")}</div>` : "<p class=\"leg\">Nenhum tema identificado.</p>"}
        <div class="legenda"><span><i style="background:var(--mata)"></i>${esc(A.nome)}</span><span><i style="background:${corB}"></i>${esc(B.nome)}</span></div></div>`;
  }

  /* ================= PROJETOS ================= */
  function projetos() {
    if (!D.proposicoes.length) return avisoDemo + `<div class="vazio">Nenhum projeto encontrado nas notícias carregadas.</div>`;
    const base = D.proposicoes.filter(p => !ehLei(p));
    const anos = [...new Set(base.map(p => p.ano))].sort((a, b) => b - a);
    const tipos = [...new Map(base.map(p => [p.tipo, p.tipo_nome])).entries()];
    const sits = SIT_ORDEM.filter(s => base.some(p => p.situacao === s));
    const contTema = t => base.filter(p => (p.temas || []).includes(t)).length;
    const temas = TEMAS.filter(contTema);
    return avisoDemo + `
      <div class="ferramentas">
        <input type="search" id="busca" placeholder="Buscar por assunto, número ou autor" aria-label="Buscar projetos" value="${esc(estado.busca)}" style="flex:1 1 240px">
        <select id="f-tipo" aria-label="Tipo"><option value="">Todos os tipos</option>${tipos.map(([s, n]) => `<option value="${s}">${esc(n)}</option>`).join("")}</select>
        <select id="f-sit" aria-label="Situação"><option value="">Qualquer situação</option>${sits.map(s => `<option>${esc(s)}</option>`).join("")}</select>
        <select id="f-ano" aria-label="Ano"><option value="">Todos os anos</option>${anos.map(a => `<option>${a}</option>`).join("")}</select>
      </div>
      <div class="chips" id="f-tema" role="group" aria-label="Filtrar por tema" style="margin-bottom:16px">
        <button type="button" class="chip" data-tema="" aria-pressed="${!estado.tema}">Todos os temas</button>
        ${temas.map(t => `<button type="button" class="chip" data-tema="${esc(t)}" aria-pressed="${estado.tema === t}">${esc(t)} <small>${contTema(t)}</small></button>`).join("")}
      </div>
      <div class="cartao" style="margin-bottom:16px"><div id="resumo-filtro"></div></div>
      <ul class="lista" id="lista-projetos"></ul>
      <div class="ferramentas" style="margin-top:18px"><label><input type="checkbox" id="mostrar-leis" ${estado.leis ? "checked" : ""}> Mostrar também leis antigas citadas nas notícias</label></div>`;
  }
  function filtrados() {
    const q = sem(estado.busca.trim());
    return D.proposicoes.filter(p => (estado.leis || !ehLei(p)) && (!estado.tipo || p.tipo === estado.tipo) && (!estado.sit || p.situacao === estado.sit) &&
      (!estado.ano || String(p.ano) === estado.ano) && (!estado.tema || (p.temas || []).includes(estado.tema)) &&
      (!q || sem([p.chave, p.tipo_nome, p.ementa, ...p.autores.map(x => vereador[x]?.nome || x), ...p.mencoes.map(m => m.trecho), ...(p.temas || [])].join(" ")).includes(q)));
  }
  function desenharProjetos() {
    const itens = filtrados();
    ["f-tipo", "f-sit", "f-ano"].forEach((id, i) => { const el = document.getElementById(id); el.value = [estado.tipo, estado.sit, estado.ano][i]; });
    document.querySelectorAll("#f-tema .chip").forEach(c => c.setAttribute("aria-pressed", c.dataset.tema === estado.tema));
    const total = D.proposicoes.filter(p => estado.leis || !ehLei(p)).length;
    document.getElementById("resumo-filtro").innerHTML = `<p class="leg" style="margin:0 0 10px"><b class="num" style="color:var(--granito);font-size:18px">${itens.length}</b> de ${total} projetos. Toque numa cor para filtrar.</p>` + barraSituacao(itens, () => "#");
    document.querySelectorAll("#resumo-filtro [data-sit]").forEach(a => a.addEventListener("click", e => {
      e.preventDefault(); estado.sit = estado.sit === a.dataset.sit ? "" : a.dataset.sit; estado.mostrar = 20; desenharProjetos();
    }));
    const lista = document.getElementById("lista-projetos");
    lista.innerHTML = itens.length ? itens.slice(0, estado.mostrar).map(cartaoProp).join("") +
      (itens.length > estado.mostrar ? `<li><button type="button" class="mais" id="mais">Mostrar mais ${Math.min(20, itens.length - estado.mostrar)} de ${itens.length - estado.mostrar}</button></li>` : "")
      : `<li class="vazio">Nenhum projeto com esses filtros. <button type="button" class="botao secundario" id="limpar">Limpar filtros</button></li>`;
    document.getElementById("mais")?.addEventListener("click", () => { estado.mostrar += 20; desenharProjetos(); });
    document.getElementById("limpar")?.addEventListener("click", () => { Object.assign(estado, {busca: "", tipo: "", sit: "", ano: "", tema: ""}); document.getElementById("busca").value = ""; desenharProjetos(); });
  }
  function projeto(s) {
    const p = prop[chaveDeSlug(s)];
    if (!p) return `<div class="vazio">Projeto não encontrado. <a href="#/projetos">Ver todos</a>.</div>`;
    const t = tituloProp(p);
    const textoZap = `${p.chave}${t ? `: ${t}` : ""}. Situação: ${p.situacao}.`;
    return avisoDemo + `<a class="voltar" href="#/projetos">${ICON.voltar}Todos os projetos</a>
      <section>
        <div class="topo entra" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px">
          <button type="button" class="codigo" data-termo="${p.tipo}">${esc(p.chave)}</button>${pilula(p.situacao)}<span class="leg" style="margin:0">desde ${data(p.data_situacao)}</span></div>
        <h2 class="titulo-projeto entra" style="--i:1">${esc(t || `${p.tipo_nome} ${p.chave}`)}</h2>
        ${t ? "" : `<p class="leg">As notícias não descrevem o conteúdo deste projeto.</p>`}
        <p class="sub entra" style="--i:1;margin-bottom:18px">${termo(p.tipo, esc(p.tipo_nome))}. Autoria: ${p.autores.length ? p.autores.map(a => GLOSSARIO[a] ? termo(a) : nomeAutor(a)).join(", ") : "não informada nas notícias"}.</p>
        ${(p.temas || []).length ? `<div class="temas-mini entra" style="--i:2;margin-bottom:18px">${p.temas.map(x => `<a href="#/projetos/tema/${slug(x)}">${esc(x)}</a>`).join("")}</div>` : ""}
        ${etapas(p)}
        <div class="acoes entra" style="--i:3;margin:18px 0 0">${botoesAcao(textoZap, p.chave)}</div>
        <h2 class="secao">O caminho nas notícias</h2>
        <ol class="linha-tempo">${p.mencoes.map((m, i) => { const n = noticia[m.noticia]; return `<li class="entra" style="--i:${i}"><time>${data(m.data)}</time> ${pilula(m.situacao)}
          <a class="tit" href="${esc(n?.link)}" target="_blank" rel="noopener">${esc(n?.titulo)}</a><p class="trecho">${esc(m.trecho)}</p></li>`; }).join("")}</ol>
      </section>`;
  }

  /* ================= SESSÕES ================= */
  function sessoes(mes) {
    if (!D.noticias.length) return avisoDemo + `<div class="vazio">Ainda não há notícias carregadas.</div>`;
    return avisoDemo + `
      <div class="cartao entra" style="margin-bottom:16px"><h3>${mes ? nomeMes(mes) : "Todas as notícias"}</h3><p class="leg">${mes ? `<a href="#/sessoes">Ver todos os meses</a> ou toque em outro mês.` : "Toque em um mês para filtrar."}</p>
      ${graficoMensal(contarPorMes(D.noticias), {destaque: mes, link: k => k === mes ? "#/sessoes" : `#/sessoes/mes/${k}`})}</div>
      <div class="ferramentas"><label><input type="checkbox" id="so-sessoes"> Só relatos de sessões</label><label><input type="checkbox" id="so-seguidos"> Só com quem eu sigo</label></div>
      <ol class="linha-tempo" id="lista-noticias"></ol>`;
  }
  function desenharSessoes(mes) {
    const so = document.getElementById("so-sessoes").checked, seg = document.getElementById("so-seguidos").checked;
    const itens = D.noticias.filter(n => (!so || n.sessao) && (!seg || n.vereadores.some(segue)) && (!mes || n.data.startsWith(mes)));
    document.getElementById("lista-noticias").innerHTML = itens.length ? itens.map(itemNoticia).join("") : `<li>Nenhuma notícia com esses filtros.</li>`;
  }

  /* ================= COMO FUNCIONA ================= */
  function sobre() {
    const glos = ["PL", "PLC", "PR", "PDL", "PELO", "em comissão", "aprovado", "vetado", "Executivo", "Mesa Diretora"];
    return `<section class="prosa">
      <h2 class="nome-grande entra">Como o Radar funciona</h2>
      <p class="sub entra" style="--i:1;margin-bottom:24px">Um projeto independente e sem fins lucrativos para tornar a Câmara de Teresópolis mais fácil de acompanhar.</p></section>
      <div class="dupla">
        <div class="cartao entra" style="--i:2"><h3>De onde vêm os dados</h3><div class="prosa" style="margin-top:8px">
          <p>Todo dia, às 6h17, um programa lê as notícias publicadas no site oficial da Câmara (camarateresopolis.com.br) e identifica quais vereadores e quais projetos aparecem em cada uma, em que etapa o projeto está e quem é o autor.</p>
          <p>Nada é escrito à mão: tudo vem do texto das notícias, e cada informação tem link para a notícia original.</p></div></div>
        <div class="cartao entra" style="--i:3"><h3>O que o Radar não sabe</h3><div class="prosa" style="margin-top:8px">
          <p>Se a Câmara não noticiou uma votação, o Radar não fica sabendo. Votos individuais de cada vereador quase nunca aparecem nas notícias.</p>
          <p>A identificação é automática e pode errar. Os temas são atribuídos por palavras-chave. Por isso há um botão "Encontrou um erro?" em cada página.</p></div></div>
      </div>
      <h2 class="secao">Como uma lei nasce em Teresópolis</h2>
      <ol class="passos-lei cartao">
        <li class="entra"><div><b>Apresentação</b><p>Um vereador, o prefeito, a Mesa Diretora ou a população (com assinaturas) protocola o projeto.</p></div></li>
        <li class="entra" style="--i:1"><div><b>Leitura em plenário</b><p>O projeto é lido numa sessão e começa a tramitar oficialmente.</p></div></li>
        <li class="entra" style="--i:2"><div><b>Comissões</b><p>Comissões de 3 vereadores (Justiça, Finanças, Saúde e outras) analisam e dão parecer.</p></div></li>
        <li class="entra" style="--i:3"><div><b>Votação</b><p>O plenário, com os 21 vereadores, aprova ou rejeita. Alguns projetos exigem maioria qualificada.</p></div></li>
        <li class="entra" style="--i:4"><div><b>Prefeito</b><p>Projetos de lei aprovados vão para o prefeito, que sanciona (vira lei) ou veta. A Câmara pode derrubar o veto.</p></div></li>
      </ol>
      <h2 class="secao">Palavras que aparecem por aqui</h2>
      <dl class="glossario">${glos.map((k, i) => `<div class="cartao entra" style="--i:${i}"><dt>${esc(GLOSSARIO[k][0])}${k.length <= 4 && k === k.toUpperCase() ? ` (${k})` : ""}</dt><dd>${esc(GLOSSARIO[k][1])}</dd></div>`).join("")}</dl>
      <h2 class="secao" id="dados">Dados abertos</h2>
      <div class="cartao"><p class="leg">Use à vontade, citando o Radar da Câmara de Teresópolis como fonte (licença CC BY 4.0). Os arquivos CSV abrem no Excel e no Google Planilhas.</p>
        <div class="downloads">
          <a class="botao secundario" href="dados/projetos.csv" download>${ICON.baixar}Projetos (CSV)</a>
          <a class="botao secundario" href="dados/vereadores.csv" download>${ICON.baixar}Vereadores (CSV)</a>
          <a class="botao secundario" href="dados/noticias.csv" download>${ICON.baixar}Notícias (CSV)</a>
          <a class="botao secundario" href="dados/radar.json" download>${ICON.baixar}Tudo (JSON)</a>
        </div></div>
      <h2 class="secao">Compromissos</h2>
      <div class="prosa cartao">
        <p><b>Neutralidade.</b> O Radar não dá notas, não faz ranking de melhores ou piores e não tem lado político. Não aceita dinheiro de políticos, partidos ou candidatos.</p>
        <p><b>Correções.</b> Erros apontados são corrigidos e o histórico de mudanças fica público no código do projeto.</p>
        <p><b>Direito de resposta.</b> Vereadores e assessorias podem pedir correções ou esclarecimentos pelo mesmo canal.</p>
        <p><b>Privacidade.</b> O site não usa cookies nem pede cadastro. Os vereadores que você segue ficam salvos apenas no seu navegador.</p>
        ${CFG.contatoEmail ? `<p><b>Contato.</b> <span style="user-select:all">${esc(CFG.contatoEmail)}</span></p>` : ""}
        <div class="acoes" style="margin-top:12px"><a class="botao primario" href="${esc(linkErro("geral"))}" target="_blank" rel="noopener">${ICON.erro}Reportar um erro</a>${CFG.repoUrl ? `<a class="botao secundario" href="${esc(CFG.repoUrl)}" target="_blank" rel="noopener">Ver o código</a>` : ""}</div>
      </div>`;
  }

  /* ================= busca geral ================= */
  const campo = document.getElementById("busca-geral"), caixa = document.getElementById("resultados");
  let ativo = -1;
  function buscar() {
    const q = sem(campo.value.trim());
    if (q.length < 2) { caixa.hidden = true; campo.setAttribute("aria-expanded", "false"); return; }
    const vs = D.vereadores.filter(v => sem(v.nome + " " + v.partido).includes(q)).slice(0, 5);
    const ts = TEMAS.filter(t => sem(t).includes(q)).slice(0, 3);
    const ps = D.proposicoes.filter(p => sem(p.chave + " " + p.ementa + " " + p.mencoes.map(m => m.trecho).join(" ")).includes(q)).slice(0, 6);
    const ns = D.noticias.filter(n => sem(n.titulo).includes(q)).slice(0, 4);
    let html = "";
    if (vs.length) html += `<h4>Vereadores</h4>` + vs.map(v => `<a href="#/vereador/${v.slug}">${esc(v.nome)}<small>${esc(v.partido)}</small></a>`).join("");
    if (ts.length) html += `<h4>Temas</h4>` + ts.map(t => `<a href="#/projetos/tema/${slug(t)}">${esc(t)}</a>`).join("");
    if (ps.length) html += `<h4>Projetos</h4>` + ps.map(p => `<a href="#/projeto/${slugProp(p.chave)}">${esc(tituloProp(p) || p.chave)}<small>${esc(p.chave)}, ${esc(p.situacao)}</small></a>`).join("");
    if (ns.length) html += `<h4>Notícias</h4>` + ns.map(n => `<a href="${esc(n.link)}" target="_blank" rel="noopener">${esc(n.titulo)}<small>${data(n.data)}</small></a>`).join("");
    caixa.innerHTML = html || `<p>Nada encontrado para "${esc(campo.value)}". Tente outra palavra, como "saúde" ou o nome de um vereador.</p>`;
    caixa.hidden = false; campo.setAttribute("aria-expanded", "true"); ativo = -1;
  }
  campo.addEventListener("input", buscar);
  campo.addEventListener("keydown", e => {
    const links = [...caixa.querySelectorAll("a")];
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); if (!links.length) return;
      ativo = (ativo + (e.key === "ArrowDown" ? 1 : -1) + links.length) % links.length;
      links.forEach((l, i) => l.classList.toggle("ativo", i === ativo)); links[ativo].scrollIntoView({block: "nearest"});
    } else if (e.key === "Enter") { const l = links[ativo] || links[0]; if (l) l.click(); }
    else if (e.key === "Escape") { caixa.hidden = true; campo.blur(); }
  });
  caixa.addEventListener("click", e => { if (e.target.closest("a")) { caixa.hidden = true; campo.value = ""; } });

  /* ================= explicações (glossário) ================= */
  const pop = document.getElementById("pop");
  let popDe = null;
  function mostrarPop(alvo) {
    const g = GLOSSARIO[alvo.dataset.termo];
    if (!g) return;
    if (popDe === alvo && !pop.hidden) { pop.hidden = true; popDe = null; return; }
    pop.innerHTML = `<b>${esc(g[0])}</b>${esc(g[1])}`;
    pop.hidden = false; popDe = alvo;
    const r = alvo.getBoundingClientRect(), w = pop.offsetWidth;
    pop.style.left = Math.max(16, Math.min(r.left + scrollX, scrollX + innerWidth - w - 16)) + "px";
    pop.style.top = (r.bottom + scrollY + 8) + "px";
  }
  document.addEventListener("click", e => {
    const t = e.target.closest("[data-termo]");
    if (t) { e.preventDefault(); e.stopPropagation(); mostrarPop(t); return; }
    if (!e.target.closest(".pop")) { pop.hidden = true; popDe = null; }
    if (!e.target.closest(".busca")) caixa.hidden = true;
  }, true);
  document.addEventListener("keydown", e => { if (e.key === "Escape") { pop.hidden = true; popDe = null; } });

  /* ================= eventos ================= */
  main.addEventListener("click", e => {
    const sg = e.target.closest("[data-seguir]");
    if (sg) {
      e.preventDefault();
      alternarSeguir(sg.dataset.seguir);
      const nome = vereador[sg.dataset.seguir].nome;
      toast(segue(sg.dataset.seguir) ? `Seguindo ${nome}` : `Deixou de seguir ${nome}`);
      if (sg.classList.contains("seguir")) {
        sg.setAttribute("aria-pressed", segue(sg.dataset.seguir)); sg.classList.remove("pulo"); void sg.offsetWidth; sg.classList.add("pulo");
        if (estado.soSeguindo) desenharVereadores(false);
      } else rotear(false, false);
      return;
    }
    const pt = e.target.closest("[data-partido]");
    if (pt) { estado.partido = pt.dataset.partido; document.querySelectorAll("#f-partido .chip").forEach(c => c.setAttribute("aria-pressed", c === pt)); desenharVereadores(); return; }
    const tm = e.target.closest("[data-tema]");
    if (tm) { estado.tema = tm.dataset.tema; estado.mostrar = 20; desenharProjetos(); return; }
    if (e.target.closest("[data-acao='copiar']")) copiarLink();
  });
  main.addEventListener("change", e => {
    const c = e.target.closest("[data-comparar]");
    if (c) {
      comparar = c.checked ? [...comparar.filter(x => x !== c.dataset.comparar), c.dataset.comparar].slice(-2) : comparar.filter(x => x !== c.dataset.comparar);
      document.querySelectorAll("[data-comparar]").forEach(x => x.checked = comparar.includes(x.dataset.comparar));
      desenharBarraComparar(); return;
    }
    if (e.target.id === "ordem") { estado.ordem = e.target.value; desenharVereadores(); }
    if (e.target.id === "so-seguindo") { estado.soSeguindo = e.target.checked; desenharVereadores(); }
    if (e.target.id === "mostrar-leis") { estado.leis = e.target.checked; desenharProjetos(); }
  });
  main.addEventListener("input", e => {
    const mapa = {"busca": "busca", "f-tipo": "tipo", "f-sit": "sit", "f-ano": "ano"};
    if (mapa[e.target.id]) { estado[mapa[e.target.id]] = e.target.value; estado.mostrar = 20; desenharProjetos(); }
  });
  document.getElementById("barra-comparar").addEventListener("click", e => {
    if (e.target.closest(".fechar")) { comparar = []; document.querySelectorAll("[data-comparar]").forEach(x => x.checked = false); desenharBarraComparar(); }
    if (e.target.closest("a")) setTimeout(() => { comparar = []; desenharBarraComparar(); }, 0);
  });

  /* ================= animações pós-render ================= */
  function animar() {
    document.querySelectorAll(".contador").forEach(el => {
      const alvo = +el.dataset.alvo;
      if (reduzir || !alvo) { el.textContent = alvo; return; }
      const t0 = performance.now(), dur = 900 + Math.min(alvo, 50) * 8;
      const passo = t => { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3); el.textContent = Math.round(alvo * e); if (k < 1) requestAnimationFrame(passo); };
      requestAnimationFrame(passo);
    });
    document.querySelectorAll(".etapas[data-progresso]").forEach(el => requestAnimationFrame(() => requestAnimationFrame(() => el.style.setProperty("--progresso", el.dataset.progresso))));
  }

  /* ================= rotas ================= */
  function rotear(rolar = true, transicao = true) {
    const [, rota = "", a, b] = location.hash.split("/");
    const aba = {vereadores: "vereadores", vereador: "vereadores", comparar: "vereadores", projetos: "projetos", projeto: "projetos", sessoes: "sessoes", sobre: "sobre"}[rota] || "inicio";
    document.querySelectorAll("[data-aba]").forEach(x => x.dataset.aba === aba ? x.setAttribute("aria-current", "page") : x.removeAttribute("aria-current"));
    pop.hidden = true;
    document.body.classList.toggle("interna", aba !== "inicio");
    const y = scrollY;
    const desenhar = () => {
      if (rota === "vereadores") { main.innerHTML = vereadores(); desenharVereadores(); }
      else if (rota === "vereador") main.innerHTML = perfil(a);
      else if (rota === "comparar") main.innerHTML = compararVer(a, b);
      else if (rota === "projetos") {
        if (rolar) { if (a === "tema") { estado.tema = temaDeSlug(b) || ""; estado.sit = ""; } else if (a === "situacao") { estado.sit = SIT_ORDEM.find(s => slug(s) === b) || ""; estado.tema = ""; } else { estado.tema = ""; estado.sit = ""; } }
        main.innerHTML = projetos(); if (D.proposicoes.length) desenharProjetos();
      }
      else if (rota === "projeto") main.innerHTML = projeto(a);
      else if (rota === "sessoes") {
        const mes = a === "mes" ? b : null;
        main.innerHTML = sessoes(mes);
        if (D.noticias.length) { ["so-sessoes", "so-seguidos"].forEach(id => document.getElementById(id).addEventListener("change", () => desenharSessoes(mes))); desenharSessoes(mes); }
      }
      else if (rota === "sobre") main.innerHTML = sobre();
      else main.innerHTML = inicio();
      desenharBarraComparar();
      animar();
      if (rolar && location.hash) {
        const topo = document.querySelector("nav.principal").getBoundingClientRect().top + scrollY;
        if (a === "dados" && rota === "sobre") document.getElementById("dados")?.scrollIntoView();
        else if (scrollY > topo) scrollTo({top: topo});
        main.focus({preventScroll: true});
      } else if (!rolar) scrollTo({top: y});
    };
    if (transicao && rolar && document.startViewTransition && !reduzir) document.startViewTransition(desenhar);
    else desenhar();
    if (window.goatcounter?.count) window.goatcounter.count({path: "/" + (location.hash || "#/").slice(1)});
  }
  addEventListener("hashchange", () => rotear(true));
  rotear(false, false);

  /* métricas opcionais, sem cookies */
  if (CFG.goatcounter) {
    const s = document.createElement("script");
    s.async = true; s.src = "https://gc.zgo.at/count.js";
    s.dataset.goatcounter = `https://${CFG.goatcounter}.goatcounter.com/count`;
    s.dataset.goatcounterSettings = JSON.stringify({no_onload: false});
    document.head.appendChild(s);
  }
})();
