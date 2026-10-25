"use strict";
const $ = (s) => document.querySelector(s);
const h = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const paths = {
  grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  trophy:
    "M8 3h8v7a4 4 0 0 1-8 0z M8 5H4v3a4 4 0 0 0 4 4 M16 5h4v3a4 4 0 0 1-4 4 M12 14v6 M8 21h8",
  plus: "M12 5v14 M5 12h14",
  arrow: "M5 12h14 M13 6l6 6-6 6",
  back: "M19 12H5 M11 6l-6 6 6 6",
  users:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M16 4a4 4 0 0 1 0 8 M22 21v-2a4 4 0 0 0-3-3.87 M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8",
  calendar: "M4 5h16v16H4z M8 3v4 M16 3v4 M4 10h16 M8 14h2 M14 14h2 M8 18h2",
  spark: "M12 2l2.7 7.3L22 12l-7.3 2.7L12 22l-2.7-7.3L2 12l7.3-2.7z",
  check: "M5 12l4 4L19 6",
  close: "M6 6l12 12 M6 18L18 6",
  share:
    "M8 11l8-5 M8 13l8 5 M5 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6 M19 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6 M19 16a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
  download: "M12 3v12 M7 10l5 5 5-5 M4 16v5h16v-5",
  edit: "M15 4l5 5 M4 20l5-1L21 7l-5-5L4 14z",
  search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M16 16l5 5",
  refresh: "M20 11a8 8 0 1 0-2.3 5.7 M20 4v7h-7",
  trash: "M4 7h16 M9 7V4h6v3 M6 7l1 13h10l1-13 M10 11v5 M14 11v5",
  menu: "M4 6h16 M4 12h16 M4 18h16",
  clock: "M12 8v5l3 2 M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20",
  chart: "M4 20V10h4v10 M10 20V4h4v16 M16 20v-8h4v8",
  ball: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20 M8 9l4-3 4 3-1 5H9z M3 8l5 1 M16 9l5-1 M9 14l-3 6 M15 14l3 6",
  link: "M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-2 2 M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l2-2",
};
const icon = (name) =>
  `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.ball}"/></svg>`;
document
  .querySelectorAll("[data-icon]")
  .forEach((el) => (el.outerHTML = icon(el.dataset.icon)));
const label = (f) =>
  ({
    round_robin: "Girone all’italiana",
    knockout: "Eliminazione diretta",
    groups: "Gironi + fase finale",
  })[f];
const stateLabel = (s) =>
  ({ draft: "Da preparare", active: "In corso", completed: "Concluso" })[s];
const tieLabel = (v) =>
  ({
    goal_difference: "differenza reti",
    head_to_head: "scontri diretti",
    goals_for: "reti fatte",
    wins: "vittorie",
  })[v] || "differenza reti";
const publicToken = location.pathname.startsWith("/public/")
  ? location.pathname.split("/")[2]
  : null;
let list = [],
  sports = [],
  auth = { required: false, authenticated: true },
  selectedId = null,
  data = null,
  tab = "overview",
  filter = "all",
  matchFilter = "all",
  search = "",
  wizard = {},
  wizardStep = 0,
  catalogMode = false,
  catalogSport = null,
  catalogVariant = null,
  catalogDetail = null,
  toastTimer;
const sportFor = (name) => sports.find((s) => s.name === name);
const variantFor = (slug) => {
  for (const sport of sports)
    for (const variant of sport.variants || [])
      if (variant.slug === slug) return variant;
  return null;
};
const currentSport = () =>
  data
    ? sports.find((s) => s.id === data.tournament.sport_id) ||
      sportFor(data.tournament.sport)
    : null;
const currentVariant = () =>
  data?.variant_config || variantFor(data?.tournament?.variant);
const currentRules = () => data?.rules || {};
const isSetBased = () => !!currentVariant()?.supports_sets;
const scoreLabel = () => currentVariant()?.score_label || "punti";
const scoringText = (v) =>
  v?.supports_sets
    ? `${v.sets_to_win} set su ${v.max_sets} · ${v.points_per_set} punti`
    : v?.scoring_mode === "goals"
      ? `gol${v.draw_allowed === false ? " · nessun pareggio" : ""}`
      : `punti${v?.draw_allowed === false ? " · nessun pareggio" : ""}`;
const durationText = (minutes) => {
  const value = Number(minutes);
  if (value >= 60 && value % 60 === 0) return `${value / 60} h`;
  return `${value} min`;
};
function variantOptionLabel(v) {
  return `${v.name} · ${v.players_on_field} in campo · ${durationText(v.match_duration)}`;
}
const avatar = (name, id = 0) =>
  `<span class="avatar c${Math.abs(id) % 4}" aria-hidden="true">${h(
    (name || "?")
      .replace(/Team #/, "T")
      .slice(0, 2)
      .toUpperCase(),
  )}</span>`;
const button = (text, action, cls = "", i = "") =>
  `<button class="button ${cls}" data-action="${action}">${i ? icon(i) : ""}${text}</button>`;
const teamName = (id) =>
  data?.teams.find((t) => t.id === id)?.name || "Da definire";
const dateText = (s) =>
  new Intl.DateTimeFormat("it-IT", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Rome",
  }).format(new Date(s));
const roundName = (m) => {
  if (m.kind === "round_robin") return "Giornata " + m.round_no;
  const remaining =
    Math.max(
      ...data.matches
        .filter((x) => x.stage_id === m.stage_id)
        .map((x) => x.round_no),
    ) - m.round_no;
  return (
    [
      "Finale",
      "Semifinali",
      "Quarti di finale",
      "Ottavi di finale",
      "Sedicesimi",
    ][remaining] || "Turno " + m.round_no
  );
};
function notify(text, error = false) {
  const el = $("#toast");
  el.textContent = text;
  el.className = error ? "error" : "";
  el.style.display = "block";
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.style.display = "none"), 6000);
}
async function api(path, options = {}) {
  let res;
  try {
    res = await fetch("/api" + path, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new Error(
      "Il server non risponde. Verifica che la demo sia avviata.",
    );
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    if (res.status === 401 && path !== "/auth/login") {
      auth.authenticated = false;
      renderAuthControl();
      loginModal();
    }
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : Array.isArray(body.detail)
          ? body.detail.map((d) => d.msg).join(" · ")
          : "Operazione non riuscita (" + res.status + ")",
    );
  }
  return res.status === 204 ? null : res.json();
}
async function safely(fn) {
  try {
    await fn();
  } catch (e) {
    const box = $("#form-error");
    if ($("#modal").open && box) {
      box.textContent = e.message;
      box.classList.remove("hidden");
    } else notify(e.message, true);
  }
}
function modal(title, body, footer = "", eyebrow = "OPEN SCORE") {
  $("#modal-content").innerHTML =
    `<div class="modal-header"><div><p class="eyebrow">${eyebrow}</p><h2 id="modal-title">${title}</h2></div><button class="icon-button" data-action="close" aria-label="Chiudi finestra">${icon("close")}</button></div><div class="modal-body"><div id="form-error" class="modal-error hidden" role="alert"></div>${body}</div>${footer ? `<div class="modal-footer">${footer}</div>` : ""}`;
  if (!$("#modal").open) $("#modal").showModal();
}
function close() {
  $("#modal").close();
}
function stat(title, value, foot, i) {
  return `<div class="stat"><div class="stat-top">${title}${icon(i)}</div><div class="stat-number">${value}</div><div class="stat-foot">${foot}</div></div>`;
}
async function refreshList() {
  list = await api("/tournaments?archived=include");
  renderNav();
}
async function loadSports() {
  const result = await api("/sports");
  sports = result.sports || [];
}
const canEdit = () => !auth.required || auth.authenticated;
async function loadSession() {
  try {
    const session = await api("/auth/session");
    auth = {
      required: !!session.auth_required,
      authenticated: !!session.authenticated,
    };
  } catch {
    auth = { required: false, authenticated: true };
  }
  renderAuthControl();
}
function renderAuthControl() {
  if (publicToken) return;
  const access = auth.required
    ? auth.authenticated
      ? `<span class="auth-user">${icon("check")}Organizzatore</span><button class="button ghost compact" data-action="logout">Esci</button>`
      : `<button class="button ghost compact" data-action="login">Accedi</button>`
    : '<span class="demo-label"><i></i> MODALITÀ LOCALE</span>';
  $(".top-actions").innerHTML = `${access}<button class="button primary compact ${canEdit() ? "" : "hidden"}" data-action="new">${icon("plus")}Nuovo torneo</button>`;
  document
    .querySelectorAll(".sidebar [data-action='new']")
    .forEach((el) => el.classList.toggle("hidden", !canEdit()));
}
function renderNav() {
  const visible = list.filter((t) => !t.archived_at);
  $("#event-count").textContent = visible.length;
  $("#event-nav").innerHTML =
    visible
      .map(
        (t) =>
          `<button data-open="${t.id}" class="${t.id === selectedId ? "active" : ""}"><span class="event-dot"></span>${h(t.name)}</button>`,
      )
      .join("") || '<p class="sidebar-muted">Il primo torneo ti aspetta.</p>';
  $("#home-nav").classList.toggle("active", !selectedId && !catalogMode);
  $("#sports-nav")?.classList.toggle("active", catalogMode);
}
async function dashboard() {
  if (publicToken) return;
  selectedId = null;
  data = null;
  catalogMode = false;
  tab = "overview";
  await refreshList();
  if (location.hash) history.replaceState(null, "", location.pathname);
  $("#breadcrumb").textContent = "Panoramica";
  renderDashboard();
  $("#sidebar").classList.remove("open");
  $("#mobile-menu").setAttribute("aria-expanded", "false");
}
function renderDashboard() {
  const active = list.filter((t) => !t.archived_at);
  const shown = list.filter((t) => {
    if (!t.name.toLocaleLowerCase("it").includes(search.toLocaleLowerCase("it")))
      return false;
    if (filter === "archived") return !!t.archived_at;
    if (filter === "all") return !t.archived_at;
    return !t.archived_at && t.status === filter;
  });
  const totalTeams = active.reduce((a, t) => a + t.team_count, 0),
    done = active.reduce((a, t) => a + t.progress.completed, 0);
  $("#content").innerHTML =
    `<div class="page-heading"><div><p class="eyebrow"><span class="line"></span> MENO ORGANIZZAZIONE, PIÙ GIOCO</p><h1>Ogni torneo comincia qui.</h1><p>Metti in campo le tue idee. Noi teniamo il punteggio.</p></div><span class="date-note">Uno spazio, tutte le tue sfide.</span></div>
 <section class="hero" aria-label="Inizia a organizzare"><div class="hero-copy"><p class="eyebrow">IL PROSSIMO FISCHIO D’INIZIO</p><h2>Lo sport unisce.<br><em>Organizzarlo è semplice.</em></h2><p>Dalle partite in palestra alla coppa d’istituto: squadre, incontri e risultati, tutti nello stesso posto.</p><div class="hero-buttons">${canEdit() ? button("Crea il tuo torneo", "new", "primary", "plus") : button("Accedi per organizzare", "login", "primary", "check")}${button("Esplora la demo", "explore", "ghost", "arrow")}</div></div><div class="hero-art" aria-hidden="true"><div class="court"><div class="court-circle"></div></div><div class="hero-score"><div class="score-kicker">IL TUO PROSSIMO TORNEO <span>● SI GIOCA</span></div><div class="score-line">${avatar("A", 2)}La tua squadra <b>—</b></div><div class="score-line">${avatar("B", 1)}Una nuova sfida <b>—</b></div></div><div class="hero-sticker">${icon("trophy")}</div></div></section>
 <div class="stat-grid">${stat("Tornei creati", active.length, "Tutte le tue competizioni", "trophy")}${stat("Partecipanti", totalTeams, "Pronti a scendere in campo", "users")}${stat("Tornei in corso", active.filter((t) => t.status === "active").length, "Il gioco continua", "ball")}${stat("Risultati registrati", done, "Ogni partita conta", "check")}</div>
 <section><div class="section-header"><div><h2>I tuoi tornei <span class="muted">${active.length.toString().padStart(2, "0")}</span></h2><p class="section-sub">Scegli una competizione e porta avanti il gioco.</p></div><div class="filters" aria-label="Filtra tornei">${[
   ["all", "Tutti"],
   ["active", "In corso"],
   ["completed", "Conclusi"],
   ["archived", "Archiviati"],
 ]
   .map(
     ([v, l]) =>
       `<button class="filter ${filter === v ? "active" : ""}" data-filter="${v}" aria-pressed="${filter === v}">${l}</button>`,
   )
   .join("")}</div></div>
 <div class="tournament-grid">${shown.map(eventCard).join("") || `<div class="panel empty">${icon("trophy")}<h2>Il campo è libero.</h2><p>${filter === "archived" ? "Nessun torneo archiviato, per ora." : list.length ? "Nessun torneo con questo filtro." : "Crea il primo torneo oppure carica gli esempi per iniziare."}</p>${filter === "archived" ? "" : canEdit() ? button("Nuovo torneo", "new", "primary") + button("Carica esempi", "seed", "ghost") : button("Accedi per organizzare", "login", "primary", "check")}</div>`}</div></section>
 <div class="note-banner">${icon("spark")}<div><strong>Un progetto aperto, anche alle tue idee.</strong><p>Questa è la nostra prima demo. Il prossimo passo lo scegliamo insieme.</p></div><button class="text-button" data-action="project">Il progetto ${icon("arrow")}</button></div>`;
  $("#content").setAttribute("aria-busy", "false");
}
function eventCard(t, i) {
  const progress = t.progress.total
    ? Math.round((t.progress.completed / t.progress.total) * 100)
    : 0;
  return `<article class="event-card ${t.archived_at ? "archived" : ""}"><div class="event-card-top"><div class="sport-symbol ${["", "gold", "blue", "rose"][i % 4]}">${icon(t.format === "knockout" ? "trophy" : t.format === "groups" ? "grid" : "ball")}</div>${t.archived_at ? '<span class="tag archived"><i></i>Archiviato</span>' : `<span class="tag ${t.status}"><i></i>${stateLabel(t.status)}</span>`}</div><h3>${h(t.name)}</h3><p class="event-format">${h(t.sport)}${t.variant ? ` · ${h(variantFor(t.variant)?.name || t.variant)}` : ""} <span aria-hidden="true">/</span> ${label(t.format)}</p><div class="event-meta"><span>${icon("users")}${t.team_count} ${t.participant_kind === "team" ? "squadre" : "giocatori"}</span><span>${icon("calendar")}${t.progress.total} incontri${t.format === "groups" ? " · gironi" : ""}</span></div><div class="progress-track" role="progressbar" aria-label="Incontri completati" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"><span style="width:${progress}%"></span></div><div class="progress-copy"><span>${t.progress.completed} di ${t.progress.total} incontri completati</span><span>${progress}%</span></div><div class="event-card-footer"><div class="avatar-stack"><span>${h(t.sport.slice(0, 1))}</span><span>OS</span><small>${t.demo_key ? "Torneo dimostrativo" : "Il nostro torneo"}</small></div><div class="card-actions"><button class="text-button" data-open="${t.id}">Apri ${icon("arrow")}</button>${t.archived_at && canEdit() ? `<button class="text-button" data-restore="${t.id}">Ripristina ${icon("refresh")}</button>` : ""}</div></div></article>`;
}
function hashRoute() {
  const parts = location.hash
    .replace(/^#\/?/, "")
    .split("/")
    .map((part) => {
      try {
        return decodeURIComponent(part);
      } catch {
        return part;
      }
    });
  return { kind: parts[0] || "", sport: parts[1] || null, variant: parts[2] || null };
}
async function openCatalog(sportName = null, variantSlug = null) {
  if (publicToken) return;
  catalogMode = true;
  selectedId = null;
  data = null;
  catalogSport = sportName || null;
  catalogVariant = sportName && variantSlug ? variantSlug : null;
  catalogDetail = null;
  if (catalogSport && catalogVariant) {
    catalogDetail = await api(
      `/sports/${encodeURIComponent(catalogSport)}/variants/${encodeURIComponent(catalogVariant)}`,
    );
    catalogVariant = catalogDetail.slug;
  }
  $("#breadcrumb").textContent = catalogSport
    ? catalogVariant
      ? `${catalogSport} / ${catalogDetail?.name || catalogVariant}`
      : catalogSport
    : "Sport e regole";
  const hash = catalogSport
    ? `#/sport/${encodeURIComponent(catalogSport)}${catalogVariant ? "/" + encodeURIComponent(catalogVariant) : ""}`
    : "#/sport";
  history.replaceState(null, "", location.pathname + hash);
  renderCatalog();
  $("#sidebar").classList.remove("open");
  $("#mobile-menu").setAttribute("aria-expanded", "false");
}
function catalogSportCard(sport) {
  const variants = sport.variants || [];
  return `<article class="event-card catalog-card"><div class="event-card-top"><div class="sport-symbol">${icon("ball")}</div><span class="tag">${variants.length} varianti</span></div><h3>${h(sport.name)}</h3><p class="event-format">${h(sport.description)}</p><div class="catalog-chips">${variants.map((v) => `<span>${h(v.name)}</span>`).join("")}</div><div class="event-card-footer"><small>${variants.reduce((max, v) => Math.max(max, v.players_on_field), 0)} giocatori in campo al massimo</small><button class="text-button" data-catalog-sport="${h(sport.name)}">Scopri ${icon("arrow")}</button></div></article>`;
}
function catalogVariantCard(variant) {
  return `<article class="event-card catalog-card"><div class="event-card-top"><div class="sport-symbol gold">${icon(variant.supports_sets ? "chart" : "ball")}</div><span class="tag">${h(variant.participant_kind === "team" ? "Squadre" : "Individuale")}</span></div><h3>${h(variant.name)}</h3><p class="event-format">${h(variant.description)}</p><div class="rule-pills"><span>${icon("users")}${variant.players_on_field} in campo</span><span>${icon("clock")}${durationText(variant.match_duration)}</span><span>${icon("spark")}${h(scoringText(variant))}</span></div><div class="event-card-footer"><small>Rosa fino a ${variant.max_roster}</small><button class="text-button" data-catalog-variant="${h(variant.slug)}" data-catalog-parent="${h(variant.sport)}">Apri regole ${icon("arrow")}</button></div></article>`;
}
function renderCatalog() {
  let body = "";
  if (!catalogSport) {
    body = `<div class="page-heading"><div><p class="eyebrow"><span class="line"></span> SPORT E REGOLE</p><h1>Ogni sport, la sua variante.</h1><p>Sei sport, sedici modi di giocare. Scegli la variante e portala in campo: regole, rose e durata si adattano da sole.</p></div><span class="date-note">Regolamenti pronti da usare.</span></div><div class="catalog-grid">${sports.map(catalogSportCard).join("")}</div>`;
  } else if (!catalogVariant) {
    const sport = sportFor(catalogSport);
    body = `<button class="back-link" data-action="catalog">${icon("back")} Tutti gli sport</button><div class="page-heading"><div><p class="eyebrow"><span class="line"></span> ${h(catalogSport)}</p><h1>${h(sport?.description || catalogSport)}</h1><p>Scegli la variante: la scheda mostra composizione, durata e regolamento prima di creare il torneo.</p></div></div><div class="catalog-grid">${(sport?.variants || []).map(catalogVariantCard).join("") || '<div class="panel empty">Nessuna variante configurata.</div>'}</div>`;
  } else {
    const v = catalogDetail;
    const rows = [
      ["Giocatori in campo", v.players_on_field],
      ["Minimo in campo", v.min_lineup],
      ["Rosa massima", v.max_roster],
      ["Durata partita", durationText(v.match_duration)],
      ["Punteggio", scoringText(v)],
      ["Campo", v.surface],
    ];
    const rules = v.rules || {};
    const extra = [
      rules.periods ? `${rules.periods} periodi da ${rules.period_minutes} minuti` : "",
      rules.sets_to_win ? `Vittoria con ${rules.sets_to_win} set su ${rules.max_sets}` : "",
      rules.win_by_two ? "Ogni set richiede almeno 2 punti di scarto" : "",
      rules.max_points ? `Limite del set a ${rules.max_points} punti` : "",
      rules.target_goals ? `Vince chi arriva per primo a ${rules.target_goals} gol` : "",
      rules.notes || "",
    ].filter(Boolean);
    body = `<button class="back-link" data-action="catalog" data-catalog-sport="${h(v.sport)}">${icon("back")} ${h(v.sport)}</button><div class="page-heading"><div><p class="eyebrow"><span class="line"></span> ${h(v.sport)} / ${h(v.name)}</p><h1>${h(v.name)}</h1><p>${h(v.description)}</p></div><div class="toolbar">${canEdit() ? `<button class="button primary" data-action="new-variant" data-sport="${h(v.sport)}" data-variant="${h(v.slug)}">${icon("plus")}Crea torneo</button>` : button("Accedi per organizzare", "login", "primary", "check")}</div></div><div class="stat-grid">${rows.map(([label, value]) => stat(label, value, "", "ball")).join("")}</div><div class="catalog-detail-grid"><section class="panel"><div class="section-header"><h2>Regolamento</h2><span class="panel-label">${h(v.participant_kind === "team" ? "A SQUADRE" : "INDIVIDUALE")}</span></div><div class="regulation-copy">${v.regulation.split(/\n\n+/).map((p) => `<p>${h(p)}</p>`).join("")}</div></section><section class="panel"><h2>In sintesi</h2><details class="result-schedule" open><summary>Dettagli di gioco</summary><ul class="rule-list">${extra.map((item) => `<li>${h(item)}</li>`).join("")}</ul></details><div class="catalog-cta">${canEdit() ? `<button class="button primary" data-action="new-variant" data-sport="${h(v.sport)}" data-variant="${h(v.slug)}">${icon("plus")}Crea torneo ${h(v.name)}</button>` : ""}<button class="button ghost" data-action="catalog">Torna al catalogo</button></div></section></div>`;
  }
  $("#content").innerHTML = body;
  $("#content").setAttribute("aria-busy", "false");
  renderNav();
}
async function openTournament(id, keepTab = false) {
  const next = await api(
    publicToken
      ? "/public/" + encodeURIComponent(publicToken)
      : "/tournaments/" + id,
  );
  selectedId = next.tournament.id;
  data = next;
  catalogMode = false;
  if (location.hash) history.replaceState(null, "", location.pathname);
  if (!keepTab) tab = "overview";
  if (!publicToken) await refreshList();
  $("#breadcrumb").textContent = publicToken
    ? "Torneo condiviso"
    : data.tournament.name;
  $("#sidebar").classList.remove("open");
  $("#mobile-menu").setAttribute("aria-expanded", "false");
  renderTournament();
}
function champion() {
  if (!data.champion_team_id) return "";
  return `<div class="champion-banner">${icon("trophy")}<div><small>IL TORNEO HA IL SUO CAMPIONE</small><h2>${h(teamName(data.champion_team_id))}</h2></div><p>Una bella storia di sport.</p></div>`;
}
function renderTournament() {
  const t = data.tournament;
  const tabs = [
    ["overview", "Panoramica"],
    ["participants", "Partecipanti"],
    ["matches", "Partite"],
    ["regulation", "Regolamento"],
  ];
  if (t.format !== "knockout") tabs.push(["standings", "Classifiche"]);
  if (t.format !== "round_robin") tabs.push(["bracket", "Tabellone"]);
  const variant = currentVariant();
  let body =
    tab === "participants"
      ? participants()
      : tab === "matches"
        ? matchesView()
        : tab === "standings"
          ? standingsView()
          : tab === "bracket"
            ? bracket()
            : tab === "regulation"
              ? regulationView()
              : overview();
  const legacy = data.legacy_sport;
  $("#content").innerHTML =
    `${!publicToken ? `<button class="back-link" data-action="dashboard">${icon("back")} Tutti i tornei</button>` : '<p class="eyebrow">SEGUI IL TORNEO · SOLA LETTURA</p>'}<div class="tournament-heading"><div><p class="eyebrow">${h(t.sport)} <span>/</span> ${h(variant?.name || "Sport storico")} <span>/</span> ${label(t.format)} ${t.archived_at ? '<span class="tag archived"><i></i>Archiviato</span>' : legacy ? '<span class="tag archived"><i></i>Solo lettura</span>' : `<span class="tag ${data.status}">${stateLabel(data.status)}</span>`}</p><h1>${h(t.name)}</h1><p>${h(t.description || "Ogni partita, un passo verso una nuova sfida.")}</p></div><div class="toolbar">${publicToken ? button("Aggiorna", "refresh", "", "check") : t.archived_at ? `${canEdit() ? button("Ripristina", "restore", "primary", "refresh") : button("Accedi", "login", "", "check")}<a class="button" href="/api/tournaments/${t.id}/export.csv" download>${icon("download")}Esporta</a>` : `${!legacy && canEdit() ? button("Modifica", "edit", "", "edit") : !legacy ? button("Accedi", "login", "", "check") : ""}${button("Condividi", "share", "", "share")}<a class="button" href="/api/tournaments/${t.id}/export.csv" download>${icon("download")}Esporta</a>${!legacy && canEdit() ? button("Archivia", "archive", "danger") : ""}`}</div></div><div class="tabs" role="tablist" aria-label="Sezioni torneo">${tabs.map(([v, l]) => `<button class="tab ${tab === v ? "active" : ""}" role="tab" id="tab-${v}" aria-controls="tournament-panel" tabindex="${tab === v ? 0 : -1}" aria-selected="${tab === v}" data-tab="${v}">${l}</button>`).join("")}</div><div id="tournament-panel" role="tabpanel" aria-labelledby="tab-${tab}">${champion()}${body}</div>`;
  $("#content").setAttribute("aria-busy", "false");
}
function overview() {
  const t = data.tournament,
    p = data.progress,
    fixtures = data.matches;
  const next = fixtures.filter((m) => m.status === "ready").slice(0, 3);
  const groupsComplete =
    t.format === "groups" && fixtures.some((m) => m.kind === "knockout");
  return `<div class="stat-grid">${stat("Partecipanti", data.teams.length, t.participant_kind === "team" ? "Squadre iscritte" : "Giocatori iscritti", "users")}${stat("Incontri", p.total, "Esclusi i passaggi per BYE", "calendar")}${stat("Completati", p.completed, "Risultati confermati", "check")}${stat("Da giocare", p.total - p.completed, "Il campo vi aspetta", "ball")}</div><div class="overview-grid"><div><div class="panel"><div class="section-header"><h2>${data.status === "completed" ? "Torneo completato" : "Il prossimo passo"}</h2><span class="panel-label">SI SCENDE IN CAMPO</span></div><p class="muted" style="font-size:12px">${publicToken ? "Segui gli incontri e aggiorna la pagina per vedere gli ultimi risultati." : !fixtures.length ? "Aggiungi i partecipanti e genera gli incontri per dare inizio al torneo." : data.status === "completed" ? "Tutte le partite sono state giocate. Puoi rivedere il percorso e i risultati." : t.format === "groups" && !groupsComplete ? "Completa tutte le partite dei gironi: le qualificate passeranno automaticamente alla fase finale." : "Registra il risultato di un incontro: classifica e percorso si aggiornano subito."}</p><div class="steps"><div class="step ${data.teams.length >= 2 ? "done" : ""}">01<b>Partecipanti</b>Le squadre sono pronte</div><div class="step ${fixtures.length ? "done" : ""}">02<b>Si gioca</b>Incontri e risultati</div><div class="step ${data.status === "completed" ? "done" : ""}">03<b>La finale</b>${t.format === "round_robin" ? "Una classifica completa" : "Un campione da celebrare"}</div></div>${!fixtures.length && !publicToken && canEdit() ? `<div style="margin-top:25px">${button("Genera incontri", "generate", "primary", "spark")}</div>` : ""}</div><div class="panel"><div class="section-header"><h2>${next.length ? "Pronte da giocare" : "Le ultime partite"}</h2><button class="text-button" data-tab="matches">Vedi tutte ${icon("arrow")}</button></div>${(next.length ? next : fixtures.filter((m) => m.status === "completed").slice(-3)).map(matchRow).join("") || '<p class="muted" style="font-size:12px">Gli incontri compariranno qui dopo la generazione.</p>'}</div></div><div><div class="panel"><h2>Il torneo in breve</h2><dl class="details-list"><div><dt>Sport</dt><dd>${h(t.sport)}</dd></div>${currentVariant() ? `<div><dt>Variante</dt><dd>${h(currentVariant().name)}</dd></div>` : ""}<div><dt>Formato</dt><dd>${label(t.format)}</dd></div><div><dt>Partecipanti</dt><dd>${t.participant_kind === "team" ? "Squadre" : "Giocatori individuali"}</dd></div>${t.format === "groups" ? `<div><dt>Qualificazione</dt><dd>Prime ${t.qualifiers} di ${t.group_count} gironi</dd></div>` : ""}<div><dt>Andata / ritorno</dt><dd>${t.legs === 2 ? "Andata e ritorno" : "Sola andata"}</dd></div>${t.format !== "knockout" ? `<div><dt>Punti V / N / P</dt><dd>${t.win_points} / ${t.draw_points} / ${t.loss_points}</dd></div>` : ""}<div><dt>Orari</dt><dd>Europe/Rome</dd></div></dl></div>${
    !publicToken
      ? `<div class="panel"><h2>Diario del torneo</h2>${(data.audit || [])
          .slice(0, 5)
          .map(
            (a) =>
              `<div class="timeline-item"><i></i><div>${{ created: "Torneo creato", updated: "Torneo modificato", archived: "Torneo archiviato", restored: "Torneo ripristinato", generated: "Incontri generati", result_saved: "Risultato registrato", result_cleared: "Risultato cancellato", qualified: "Qualificate alla fase finale", invalidated: "Incontri dipendenti annullati", scheduled: "Orario aggiornato", team_added: "Partecipante aggiunto", team_renamed: "Nome aggiornato" }[a.action] || "Torneo aggiornato"}<small>${dateText(a.created_at)}</small></div></div>`,
          )
          .join("")}</div>`
      : ""
  }</div></div>`;
}
function matchRow(m) {
  const ready = m.status === "ready" || m.status === "completed";
  const group = data.groups.find((g) => g.id === m.group_id);
  const setDetail = (m.sets || []).map((s) => `${s.home}-${s.away}`).join(" · ");
  return `<div class="match-row"><div class="match-round">${group ? h(group.name) + "<br>" : ""}${h(roundName(m))}</div><div class="match-players"><div class="match-player">${avatar(teamName(m.home_team_id), m.home_team_id)}<span>${h(m.home_team_id ? teamName(m.home_team_id) : m.is_bye ? "Riposo" : "Da definire")}</span></div><span class="score">${m.home_score ?? "–"} : ${m.away_score ?? "–"}</span><div class="match-player"><span>${h(m.away_team_id ? teamName(m.away_team_id) : m.is_bye ? "Riposo" : "Da definire")}</span>${avatar(teamName(m.away_team_id), m.away_team_id)}</div></div><div class="match-actions">${!publicToken && ready ? `<button class="button ${m.status === "ready" ? "primary" : ""}" data-result="${m.id}">${m.status === "ready" ? "Risultato" : "Modifica"}</button>` : `<span class="tag">${m.is_bye ? "BYE" : m.status === "waiting" ? "In attesa" : m.status === "completed" ? "Giocata" : "Da giocare"}</span>`}</div></div>${setDetail ? `<p class="match-note">${icon("chart")}Set: ${h(setDetail)}</p>` : ""}${m.scheduled_at || m.location ? `<p class="match-note">${icon("clock")}${m.scheduled_at ? h(dateText(m.scheduled_at)) : "Orario da definire"}${m.location ? " · " + h(m.location) : ""}</p>` : ""}`;
}
function matchesView() {
  let fixtures = data.matches
    .filter((m) => !m.is_bye)
    .filter(
      (m) =>
        matchFilter === "all" ||
        (matchFilter === "completed"
          ? m.status === "completed"
          : m.status !== "completed"),
    );
  const sets = new Map();
  fixtures.forEach((m) => {
    const group = data.groups.find((g) => g.id === m.group_id);
    const k = (group ? group.name + " · " : "") + roundName(m);
    if (!sets.has(k)) sets.set(k, []);
    sets.get(k).push(m);
  });
  return `<div class="section-header"><div><h2>Ogni partita conta.</h2><p class="section-sub">${data.progress.completed} risultati registrati su ${data.progress.total} incontri.</p></div><div class="filters">${[
    ["all", "Tutte"],
    ["pending", "Da giocare"],
    ["completed", "Giocate"],
  ]
    .map(
      ([v, l]) =>
        `<button class="filter ${matchFilter === v ? "active" : ""}" data-match-filter="${v}">${l}</button>`,
    )
    .join(
      "",
    )}</div></div><div class="panel">${[...sets].map(([k, ms]) => `<div class="round-title">${h(k)} <span>${ms.length} incontri</span></div>${ms.map(matchRow).join("")}`).join("") || '<div class="empty">Nessun incontro in questa vista.</div>'}</div>`;
}
function participants() {
  const generated = data.matches.length > 0;
  return `<div class="section-header"><div><h2>Le persone fanno il torneo.</h2><p class="section-sub">${data.teams.length} ${data.tournament.participant_kind === "team" ? "squadre" : "giocatori"} · I nomi si possono modificare anche a torneo iniziato.</p></div>${!generated && !publicToken && canEdit() ? button("Genera incontri", "generate", "primary", "spark") : ""}</div>${!generated && !publicToken && canEdit() ? '<form id="team-form" class="inline-form"><input name="name" required maxlength="60" aria-label="Nome del partecipante" placeholder="Nome del partecipante"><button class="button primary">Aggiungi</button></form>' : ""}<div class="roster">${data.teams.map((p, i) => `<div class="roster-item"><button type="button" class="roster-info" data-team="${p.id}" aria-label="Apri la scheda di ${h(p.name)}">${avatar(p.name, i)}<span><strong>${h(p.name)}</strong><small>${h(data.groups.find((g) => g.id === p.group_id)?.name || "Partecipante " + (i + 1).toString().padStart(2, "0"))}</small></span></button>${!publicToken && canEdit() ? `<button class="icon-button" data-rename="${p.id}" aria-label="Rinomina ${h(p.name)}">${icon("edit")}</button>${!generated ? `<button class="icon-button" data-remove="${p.id}" aria-label="Elimina ${h(p.name)}">${icon("close")}</button>` : ""}` : ""}</div>`).join("") || '<p class="muted">Aggiungi almeno due partecipanti per cominciare.</p>'}</div>`;
}
function standingsTable(rows, qualifiers = 0) {
  return `<div class="table-wrap"><table><thead><tr><th>#</th><th>Partecipante</th><th>G</th><th>V</th><th>N</th><th>P</th><th>F</th><th>S</th><th>DR</th><th>PT</th></tr></thead><tbody>${rows.map((r, i) => `<tr class="${i < qualifiers ? "qualifier" : ""}"><td>${i + 1}</td><td>${avatar(r.name, r.team_id)}${h(r.name)}</td><td>${r.played}</td><td>${r.won}</td><td>${r.drawn}</td><td>${r.lost}</td><td>${r.goals_for}</td><td>${r.goals_against}</td><td>${r.goal_difference}</td><td>${r.points}</td></tr>`).join("")}</tbody></table></div>`;
}
function standingsView() {
  const t = data.tournament;
  return `<div class="section-header"><div><h2>La classifica si scrive in campo.</h2><p class="section-sub">Si aggiorna a ogni risultato confermato.</p></div></div>${data.groups.length ? `<div class="groups-grid">${data.groups.map((g) => `<section class="panel"><div class="group-heading"><h2>${h(g.name)}</h2><span>Passano le prime ${t.qualifiers}</span></div>${standingsTable(g.standings, t.qualifiers)}<p class="table-note"><span class="legend-dot"></span>Posizioni di qualificazione · definitive a gironi completati</p></section>`).join("")}</div>` : `<div class="panel">${standingsTable(data.standings)}</div>`}<p class="table-note">G: giocate · V/N/P: vittorie, pareggi, sconfitte · F/S: ${isSetBased() ? "set fatti e subiti" : "punti fatti e subiti"} · DR: differenza · PT: punti in classifica.<br>A parità di punti: ${tieLabel(t.tie_breaker)}; poi nome e ID. Punteggio: ${t.win_points}/${t.draw_points}/${t.loss_points}. ${isSetBased() ? "Nei tornei a set la classifica usa i set vinti e, dove previsto, il bonus per la partita al set decisivo." : "I criteri sono quelli della variante scelta."}</p>`;
}
function regulationView() {
  const t = data.tournament;
  const v = currentVariant();
  if (!v) {
    return `<div class="panel empty">${icon("ball")}<h2>Sport storico.</h2><p>${h(t.sport)} non fa più parte del catalogo. Il torneo resta consultabile in sola lettura.</p></div>`;
  }
  const rules = data.rules || {};
  const summary = [
    ["Giocatori in campo", v.players_on_field],
    ["Minimo in campo", v.min_lineup],
    ["Rosa massima", v.max_roster],
    ["Durata partita", durationText(v.match_duration)],
    ["Punteggio", scoringText(v)],
    ["Criterio classifica", tieLabel(t.tie_breaker)],
  ];
  const details = [
    rules.periods ? `${rules.periods} periodi da ${rules.period_minutes} minuti` : "",
    rules.sets_to_win
      ? `Vittoria con ${rules.sets_to_win} set su ${rules.max_sets}; il set decisivo si gioca a ${rules.tiebreak_points} punti`
      : "",
    rules.win_by_two ? "Ogni set richiede almeno 2 punti di scarto" : "",
    rules.max_points ? `Limite del set a ${rules.max_points} punti` : "",
    rules.target_goals ? `Vince chi arriva per primo a ${rules.target_goals} gol` : "",
    rules.substitutions || rules.notes || "",
  ].filter(Boolean);
  return `<div class="section-header"><div><h2>Le regole scendono in campo.</h2><p class="section-sub">${h(t.sport)} · ${h(v.name)}. Il regolamento è congelato alla creazione del torneo.</p></div><button class="button ghost" data-action="print">${icon("download")}Stampa</button></div><div class="stat-grid">${summary.map(([label, value]) => stat(label, value, "", "ball")).join("")}</div><div class="catalog-detail-grid"><section class="panel"><h2>Regolamento applicato</h2><div class="regulation-copy">${(data.regulation || "").split(/\n\n+/).map((p) => `<p>${h(p)}</p>`).join("")}</div></section><section class="panel"><h2>Dettagli</h2><ul class="rule-list">${details.map((d) => `<li>${h(d)}</li>`).join("")}</ul><p class="field-help">Punti in classifica: vittoria ${t.win_points}, pareggio ${t.draw_points}, sconfitta ${t.loss_points}. A parità: ${tieLabel(t.tie_breaker)}.</p></section></div>`;
}
function bracket() {
  const fixtures = data.matches.filter((m) => m.kind === "knockout");
  if (!fixtures.length)
    return `<div class="panel empty">${icon("trophy")}<h2>La finale si conquista.</h2><p>${data.tournament.format === "groups" ? "Completa tutti i gironi. Le squadre qualificate riempiranno automaticamente il tabellone." : "Genera gli incontri per vedere il percorso verso la coppa."}</p>${button("Vai alle partite", "matches", "primary")}</div>`;
  const rounds = Math.max(...fixtures.map((m) => m.round_no));
  const first = fixtures.filter((m) => m.round_no === 1).length;
  const coords = Object.fromEntries(
    fixtures.map((m) => [
      m.id,
      {
        x: (m.round_no - 1) * 295,
        y: 40 + 2 ** (m.round_no - 1) * 128 * (m.position + 0.5),
      },
    ]),
  );
  let lines = "";
  for (const m of fixtures) {
    const end = coords[m.id];
    for (const source of [m.source_home, m.source_away])
      if (source) {
        const a = coords[source];
        lines += `<path d="M${a.x + 246},${a.y}H${a.x + 270}V${end.y}H${end.x}"/>`;
      }
  }
  return `<div class="section-header"><div><h2>La strada verso la coppa.</h2><p class="section-sub">${publicToken ? "Segui ogni passaggio del torneo." : "Seleziona un incontro per registrare o correggere il risultato."}</p></div></div><div class="bracket-scroll"><div class="bracket-tree" style="width:${rounds * 295 - 48}px;height:${Math.max(210, first * 128 + 60)}px"><svg width="${rounds * 295 - 48}" height="${first * 128 + 60}" aria-hidden="true"><g fill="none" stroke="#c5d1b5" stroke-width="1.5">${lines}</g></svg>${Array.from({ length: rounds }, (_, i) => `<div class="bracket-title" style="left:${i * 295}px;top:0">${h(roundName(fixtures.find((m) => m.round_no === i + 1)))}</div>`).join("")}${fixtures
    .map((m) => {
      const pos = coords[m.id],
        editable =
          !publicToken &&
          !m.is_bye &&
          ["ready", "completed"].includes(m.status),
        el = editable ? "button" : "div";
      return `<${el} class="bracket-card ${m.status}" style="left:${pos.x}px;top:${pos.y - 42}px" ${editable ? `data-result="${m.id}" aria-label="${h(teamName(m.home_team_id))} contro ${h(teamName(m.away_team_id))}, inserisci risultato"` : ""}>${["home", "away"].map((side) => `<span class="bracket-team ${m[side + "_team_id"] && m[side + "_team_id"] === m.winner_team_id ? "winner" : ""}">${avatar(m[side + "_team_id"] ? teamName(m[side + "_team_id"]) : "–", m[side + "_team_id"])}<span class="team-name">${h(m[side + "_team_id"] ? teamName(m[side + "_team_id"]) : m.is_bye ? "Riposo · BYE" : `Vincente incontro ${m["source_" + side] || "precedente"}`)}</span><strong>${m[side + "_score"] ?? "–"}</strong></span>`).join("")}<span class="bracket-status">${m.is_bye ? "PASSAGGIO AUTOMATICO" : m.status === "completed" ? "RISULTATO CONFERMATO" : m.status === "ready" ? "DA GIOCARE" : "IN ATTESA"}</span></${el}>`;
    })
    .join(
      "",
    )}</div></div><p class="tree-help">${icon("link")} I vincitori avanzano automaticamente. ${publicToken ? "Aggiorna la pagina per seguire i risultati." : "Le correzioni che cambiano il percorso richiedono una conferma."}</p>`;
}
async function teamModal(id) {
  const info = await api(`/tournaments/${selectedId}/teams/${id}`);
  const standing = info.standing;
  const stats = standing
    ? `<div class="stat-grid">${stat("Posizione", info.position ?? "–", "Nel girone o in classifica", "chart")}${stat("Giocate", standing.played, "Incontri disputati", "calendar")}${stat("Punti", standing.points, `V ${standing.won} · N ${standing.drawn} · P ${standing.lost}`, "check")}${stat("Differenza", (standing.goal_difference > 0 ? "+" : "") + standing.goal_difference, `${standing.goals_for} fatti · ${standing.goals_against} subiti`, "ball")}</div>`
    : "";
  const roster =
    info.participant_kind === "team"
      ? `<h3 class="subsection-title" style="margin-top:24px">Rosa <span class="muted">${info.players.length}/${info.max_roster}</span></h3><div class="panel" style="margin:0">${!publicToken && canEdit() ? `<form id="player-form" data-team="${info.team.id}" class="inline-form"><input name="name" required maxlength="60" aria-label="Nome del giocatore" placeholder="Nome del giocatore"><input name="shirt_number" type="number" min="0" max="99" aria-label="Numero di maglia" placeholder="N." style="max-width:80px"><button class="button primary">Aggiungi</button></form>` : ""}${info.players.map((p) => `<div class="roster-item"><div class="roster-info">${avatar(p.name, p.id)}<span><strong>${h(p.name)}</strong><small>${p.shirt_number !== null ? "Maglia " + p.shirt_number : "Giocatore"}</small></span></div>${!publicToken && canEdit() ? `<button class="icon-button" data-remove-player="${p.id}" data-player-team="${info.team.id}" aria-label="Rimuovi ${h(p.name)}">${icon("close")}</button>` : ""}</div>`).join("") || '<p class="muted" style="padding:16px">Nessun giocatore in rosa. Aggiungi i nomi per completare la squadra.</p>'}</div>`
      : "";
  const rows = info.matches
    .map((m) => {
      const own = m.home_team_id === info.team.id;
      const scored = own ? m.home_score : m.away_score;
      const conceded = own ? m.away_score : m.home_score;
      const label =
        m.status === "bye"
          ? "Riposo"
          : m.status === "waiting"
            ? "In attesa"
            : m.status === "ready"
              ? "Da giocare"
              : scored > conceded
                ? "Vittoria"
                : scored < conceded
                  ? "Sconfitta"
                  : "Pareggio";
      const group = data.groups.find((g) => g.id === m.group_id);
      return `<div class="match-row"><div class="match-round">${group ? h(group.name) + "<br>" : ""}${h(roundName(m))}</div><div class="match-players"><div class="match-player"><span>${h(m.opponent_name || "Da definire")}</span></div><span class="score">${scored ?? "–"} : ${conceded ?? "–"}</span></div><div class="match-actions"><span class="tag ${m.status}">${label}</span></div></div>${m.scheduled_at || m.location ? `<p class="match-note">${icon("clock")}${m.scheduled_at ? h(dateText(m.scheduled_at)) : "Orario da definire"}${m.location ? " · " + h(m.location) : ""}</p>` : ""}`;
    })
    .join("");
  modal(
    h(info.team.name),
    `<div class="team-summary">${avatar(info.team.name, info.team.id)}<div><strong>${h(info.team.name)}</strong><small>${info.team.group_name ? h(info.team.group_name) : "Partecipante"}${standing ? " · " + info.position + "° posto" : ""}</small></div></div>${stats}${roster}<h3 class="subsection-title" style="margin-top:24px">Partite</h3><div class="panel" style="margin:0">${rows || '<div class="empty">Nessun incontro generato.</div>'}</div>`,
    `${button("Chiudi", "close", "primary")}`,
    "SCHEDA SQUADRA",
  );
}
function resultModal(id) {
  const m = data.matches.find((x) => x.id === Number(id));
  if (!m || publicToken) return;
  if (!canEdit()) return loginModal();
  const variant = currentVariant();
  const setMode = !!variant?.supports_sets;
  const maxSets = variant?.max_sets || 5;
  const label = scoreLabel();
  let local = "";
  if (m.scheduled_at) {
    const d = new Date(m.scheduled_at);
    local = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
  }
  const setInputs = setMode
    ? `<div class="set-inputs">${Array.from({ length: maxSets }, (_, index) => {
        const number = index + 1;
        const existing = (m.sets || []).find((s) => s.set === number);
        const target =
          number === maxSets
            ? variant.tiebreak_points
            : variant.points_per_set;
        return `<div class="set-row"><span>Set ${number}<small>a ${target}</small></span><input name="home_set_${number}" aria-label="Punti ${h(teamName(m.home_team_id))} set ${number}" type="number" min="0" max="999" step="1" value="${existing?.home ?? ""}" placeholder="–"><b>:</b><input name="away_set_${number}" aria-label="Punti ${h(teamName(m.away_team_id))} set ${number}" type="number" min="0" max="999" step="1" value="${existing?.away ?? ""}" placeholder="–"></div>`;
      }).join("")}</div><p class="field-help">Inserisci solo i set giocati. La partita termina a ${variant.sets_to_win} set vinti; ogni set deve rispettare il punteggio della variante.</p>`
    : `<div class="result-inputs"><label>${avatar(teamName(m.home_team_id), m.home_team_id)}<span>${h(teamName(m.home_team_id))}</span><input name="home_score" aria-label="${h(label)} ${h(teamName(m.home_team_id))}" type="number" min="0" max="999" step="1" value="${m.home_score ?? ""}" required></label><span>:</span><label>${avatar(teamName(m.away_team_id), m.away_team_id)}<span>${h(teamName(m.away_team_id))}</span><input name="away_score" aria-label="${h(label)} ${h(teamName(m.away_team_id))}" type="number" min="0" max="999" step="1" value="${m.away_score ?? ""}" required></label></div><p class="field-help">${variant?.draw_allowed === false ? "Questa variante non ammette pareggi. " : ""}${m.kind === "knockout" ? "Serve un punteggio decisivo. " : ""}La classifica verrà aggiornata dopo il salvataggio.</p>`;
  modal(
    m.status === "completed"
      ? "Ogni risultato conta."
      : "Com’è andata in campo?",
    `<form id="result-form" data-id="${m.id}">${setInputs}${m.home_score !== null ? '<label class="checkbox"><input type="checkbox" name="invalidate">Se questa correzione cambia qualificazioni o avversari, confermo l’annullamento dei risultati e degli orari dipendenti.</label>' : ""}</form><details class="result-schedule"><summary>Orario e campo</summary><form id="schedule-form" data-id="${m.id}"><div class="form-grid"><label>Data e ora locale<input name="scheduled_at" type="datetime-local" value="${local}"></label><label>Campo<input name="location" maxlength="80" placeholder="Es. Palestra · campo A" value="${h(m.location || "")}"></label><label>Durata in minuti<input name="duration" type="number" min="1" max="240" value="${m.duration || variant?.match_duration || 20}" required></label></div><p class="field-help">L’orario usa il fuso del dispositivo. Gli orari sono mostrati nel torneo in Europe/Rome.</p><button class="button" style="margin-top:13px">Salva orario e campo</button></form></details>`,
    `${m.home_score !== null ? `<button class="button danger" data-clear="${m.id}">Cancella risultato</button>` : button("Annulla", "close", "ghost")}<button type="submit" form="result-form" class="button primary">${icon("check")}Salva risultato</button>`,
    h(roundName(m)),
  );
}
function variantOptionsFor(sportName, current) {
  const sport = sportFor(sportName);
  const variants = sport?.variants || [];
  return variants
    .map(
      (v) =>
        `<option value="${h(v.slug)}" ${v.slug === current ? "selected" : ""}>${h(variantOptionLabel(v))}</option>`,
    )
    .join("");
}
function applyVariantToWizard(variant) {
  if (!variant) return;
  wizard.variant = variant.slug;
  wizard.participant_kind = variant.participant_kind;
  const hidden = $("#wizard-form [name=participant_kind]");
  if (hidden) hidden.value = variant.participant_kind;
  wizard.win_points = variant.standings?.win ?? 3;
  wizard.draw_points = variant.standings?.draw ?? 0;
  wizard.loss_points = variant.standings?.loss ?? 0;
  wizard.tie_breaker = variant.default_tie_breaker || "goal_difference";
}
function variantRulesPanel(variant) {
  if (!variant) return "";
  return `<div class="panel rules-preview"><div class="section-header"><h2>${h(variant.name)}</h2><span class="panel-label">REGOLE DELLA VARIANTE</span></div><div class="rule-pills"><span>${icon("users")}${variant.players_on_field} in campo</span><span>${icon("users")}Rosa max ${variant.max_roster}</span><span>${icon("clock")}${durationText(variant.match_duration)}</span><span>${icon("spark")}${h(scoringText(variant))}</span></div><p class="field-help" style="margin-bottom:0">${h(variant.description)}</p></div>`;
}
function syncEditVariant(variant) {
  if (!variant) return;
  const sportSelect = $("#edit-sport");
  if (sportSelect) sportSelect.value = variant.sport;
  const kind = $("#tournament-form [name=participant_kind]");
  if (kind) {
    kind.value = variant.participant_kind;
    const display = kind.previousElementSibling;
    if (display)
      display.value =
        variant.participant_kind === "team"
          ? "Squadre"
          : "Giocatori individuali";
  }
  const points = variant.standings || {};
  for (const key of ["win_points", "draw_points", "loss_points"]) {
    const input = $(`#tournament-form [name=${key}]`);
    if (input && points[key] !== undefined) input.value = points[key];
  }
  const tie = $("#tournament-form [name=tie_breaker]");
  if (tie && variant.default_tie_breaker) tie.value = variant.default_tie_breaker;
  const preview = $("#edit-variant-preview");
  if (preview) preview.innerHTML = variantRulesPanel(variant);
}
function startWizard(sportName = null, variantSlug = null) {
  const sport =
    sportFor(sportName) || sports[0] || { name: "Calcio", variants: [] };
  const selected =
    (variantSlug && sport.variants?.find((v) => v.slug === variantSlug)) ||
    sport.variants?.find((v) => v.slug === sport.default_variant) ||
    sport.variants?.[0];
  wizard = {
    name: "",
    sport: sport.name,
    variant: selected?.slug || "",
    format: "knockout",
    count: 8,
    group_count: 2,
    qualifiers: 2,
    legs: 1,
    names: "",
    description: "",
    participant_kind: selected?.participant_kind || "team",
    win_points: selected?.standings?.win ?? 3,
    draw_points: selected?.standings?.draw ?? 1,
    loss_points: selected?.standings?.loss ?? 0,
    tie_breaker: selected?.default_tie_breaker || "goal_difference",
  };
  wizardStep = 0;
  renderWizard();
}
function readWizard() {
  const form = $("#wizard-form");
  if (!form) return;
  for (const [k, v] of new FormData(form))
    wizard[k] = [
      "count",
      "group_count",
      "qualifiers",
      "legs",
      "win_points",
      "draw_points",
      "loss_points",
    ].includes(k)
      ? Number(v)
      : v;
}
function sportOptions() {
  const names = sports.length
    ? sports.map((s) => s.name)
    : ["Calcio", "Basket", "Pallavolo", "Badminton", "Ping pong", "Biliardino"];
  if (!names.includes(wizard.sport)) wizard.sport = names[0];
  return names
    .map(
      (s) =>
        `<option value="${h(s)}" ${s === wizard.sport ? "selected" : ""}>${h(s)}</option>`,
    )
    .join("");
}
function sportOptionsFor(current) {
  return (sports.length ? sports.map((s) => s.name) : [current])
    .map(
      (s) =>
        `<option value="${h(s)}" ${s === current ? "selected" : ""}>${h(s)}</option>`,
    )
    .join("");
}
function loginModal() {
  if (!auth.required || auth.authenticated) return;
  if ($("#modal").open) close();
  modal(
    "Entra come organizzatore.",
    `<p class="project-intro">Creare tornei, modificare regole e registrare risultati richiede la password di organizzazione. Chi segue il torneo può usare il link pubblico senza accedere.</p><form id="login-form"><label>Password<input type="password" name="password" required autofocus autocomplete="current-password" maxlength="200"></label></form>`,
    `${button("Annulla", "close", "ghost")}<button class="button primary" form="login-form">${icon("check")}Accedi</button>`,
    "ACCESSO ORGANIZZATORE",
  );
}
function editTournament() {
  if (!canEdit()) return loginModal();
  const t = data.tournament;
  const generated = data.matches.length > 0;
  const variant = currentVariant();
  const kind = variant?.participant_kind || t.participant_kind;
  const structure = generated
    ? '<p class="field-help">Sport, variante, formato e regole sono bloccati perché gli incontri sono già stati generati. Nome e descrizione restano modificabili.</p>'
    : `<fieldset class="format-fieldset" style="margin-top:18px"><legend>Formato e regole</legend><div class="form-grid"><label>Sport<select name="sport" id="edit-sport">${sportOptionsFor(t.sport)}</select></label><label>Variante<select name="variant" id="edit-variant">${variantOptionsFor(t.sport, t.variant)}</select></label><label>Partecipanti<input value="${kind === "team" ? "Squadre" : "Giocatori individuali"}" disabled><input type="hidden" name="participant_kind" value="${kind}"></label><label>Gare del girone<select name="legs"><option value="1" ${t.legs === 1 ? "selected" : ""}>Sola andata</option><option value="2" ${t.legs === 2 ? "selected" : ""}>Andata e ritorno</option></select></label><label>Numero gironi<select name="group_count">${[2, 4, 8].map((n) => `<option value="${n}" ${t.group_count === n ? "selected" : ""}>${n} gironi</option>`).join("")}</select></label><label>Qualificate per girone<select name="qualifiers"><option value="1" ${t.qualifiers === 1 ? "selected" : ""}>La prima</option><option value="2" ${t.qualifiers === 2 ? "selected" : ""}>Le prime due</option></select></label></div><div class="form-grid">${[
        ["win_points", "Punti vittoria", t.win_points],
        ["draw_points", "Punti pareggio", t.draw_points],
        ["loss_points", "Punti sconfitta", t.loss_points],
      ]
        .map(
          ([n, l, v]) =>
            `<label>${l}<input name="${n}" type="number" min="0" max="10" value="${v}" required></label>`,
        )
        .join("")}<label class="full">Criterio a parità di punti<select name="tie_breaker">${[
        ["goal_difference", "Differenza reti"],
        ["head_to_head", "Scontri diretti"],
        ["goals_for", "Reti fatte"],
        ["wins", "Vittorie"],
      ]
        .map(
          ([v, l]) =>
            `<option value="${v}" ${t.tie_breaker === v ? "selected" : ""}>${l}</option>`,
        )
        .join("")}</select></label></div><div id="edit-variant-preview">${variantRulesPanel(variant)}</div></fieldset>`;
  modal(
    "Ritocca il torneo.",
    `<form id="tournament-form"><div class="form-grid"><label class="full">Nome del torneo<input name="name" value="${h(t.name)}" minlength="2" maxlength="120" required autofocus></label><label class="full">Descrizione<textarea name="description" maxlength="1000" rows="3">${h(t.description)}</textarea></label></div>${structure}</form>`,
    `${button("Annulla", "close", "ghost")}<button class="button primary" form="tournament-form">${icon("check")}Salva modifiche</button>`,
    "MODIFICA TORNEO",
  );
}
function renderWizard() {
  let body = "";
  if (wizardStep === 0)
    body = `<div class="form-grid"><label class="full">Nome del torneo<input name="name" value="${h(wizard.name)}" placeholder="Es. Coppa d’istituto" minlength="2" maxlength="120" required autofocus></label><label>Sport<select name="sport" id="wizard-sport">${sportOptions()}</select></label><label>Variante<select name="variant" id="wizard-variant">${variantOptionsFor(wizard.sport, wizard.variant)}</select></label><input type="hidden" name="participant_kind" value="${h(wizard.participant_kind)}"></div><div id="wizard-variant-preview">${variantRulesPanel(variantFor(wizard.variant))}</div><fieldset class="format-fieldset"><legend>Scegli il percorso</legend><div class="format-options">${[
      ["knockout", "Eliminazione", "Una sconfitta, sei fuori"],
      ["round_robin", "Girone unico", "Tutti contro tutti"],
      ["groups", "Gironi + finali", "Prima il gruppo, poi la coppa"],
    ]
      .map(
        ([v, l, d]) =>
          `<label class="format-option"><input type="radio" name="format" value="${v}" ${wizard.format === v ? "checked" : ""}><span>${l}<small>${d}</small></span></label>`,
      )
      .join(
        "",
      )}</div></fieldset><div class="form-grid"><label>Numero partecipanti<input type="number" name="count" min="2" max="32" value="${wizard.count}" required></label><label>Gare del girone<select name="legs"><option value="1" ${wizard.legs === 1 ? "selected" : ""}>Sola andata</option><option value="2" ${wizard.legs === 2 ? "selected" : ""}>Andata e ritorno</option></select></label></div><div class="form-grid groups-options ${wizard.format === "groups" ? "" : "hidden"}" id="group-options"><label>Numero gironi<select name="group_count">${[2, 4, 8].map((n) => `<option value="${n}" ${wizard.group_count === n ? "selected" : ""}>${n} gironi</option>`).join("")}</select></label><label>Qualificate per girone<select name="qualifiers"><option value="1" ${wizard.qualifiers === 1 ? "selected" : ""}>La prima</option><option value="2" ${wizard.qualifiers === 2 ? "selected" : ""}>Le prime due</option></select></label></div>`;
  if (wizardStep === 1)
    body = `<div class="form-grid"><label class="full">${wizard.participant_kind === "team" ? "Come si chiamano le squadre?" : "Chi scende in campo?"}<textarea name="names" placeholder="Un nome per riga, ad esempio:&#10;Falchi&#10;Leoni&#10;Aquile" rows="7">${h(wizard.names)}</textarea></label><label class="full">Una descrizione, se ti va<textarea name="description" maxlength="1000" rows="2" style="min-height:65px" placeholder="Dove si gioca, perché ci incontriamo…">${h(wizard.description)}</textarea></label></div><p class="field-help">Servono ${wizard.count} nomi distinti. Lascia vuoto per usare ${wizard.participant_kind === "team" ? "Team" : "Giocatore"} #1, #2, … Potrai rinominarli in seguito.</p>${
      wizard.format !== "knockout"
        ? `<details class="result-schedule"><summary>Punti in classifica</summary><div class="form-grid" style="margin-top:15px">${[
            ["win_points", "Vittoria"],
            ["draw_points", "Pareggio"],
            ["loss_points", "Sconfitta"],
          ]
            .map(
              ([n, l]) =>
                `<label>${l}<input name="${n}" type="number" min="0" max="10" value="${wizard[n]}" required></label>`,
            )
            .join("")}<label class="full">Criterio a parità di punti<select name="tie_breaker">${[
              ["goal_difference", "Differenza reti"],
              ["head_to_head", "Scontri diretti"],
              ["goals_for", "Reti fatte"],
              ["wins", "Vittorie"],
            ]
              .map(
                ([v, l]) =>
                  `<option value="${v}" ${wizard.tie_breaker === v ? "selected" : ""}>${l}</option>`,
              )
              .join("")}</select></label></div></details>`
        : ""
    }`;
  if (wizardStep === 2) {
    const v = variantFor(wizard.variant);
    body = `<div class="panel" style="margin:0;background:#f7f9f0"><p class="eyebrow">TUTTO PRONTO PER GIOCARE</p><h2>${h(wizard.name)}</h2><dl class="details-list"><div><dt>Sport</dt><dd>${h(wizard.sport)}</dd></div><div><dt>Variante</dt><dd>${h(v?.name || wizard.variant || "Standard")}</dd></div><div><dt>Formato</dt><dd>${label(wizard.format)}</dd></div><div><dt>Partecipanti</dt><dd>${wizard.count}</dd></div>${wizard.format === "groups" ? `<div><dt>Qualificazione</dt><dd>${wizard.group_count} gironi · prime ${wizard.qualifiers}</dd></div>` : ""}<div><dt>Gare</dt><dd>${wizard.legs === 2 ? "Andata e ritorno" : "Sola andata"}</dd></div>${v ? `<div><dt>Durata partita</dt><dd>${durationText(v.match_duration)}</dd></div><div><dt>Punteggio</dt><dd>${h(scoringText(v))}</dd></div>` : ""}<div><dt>Classifica</dt><dd>${wizard.win_points}/${wizard.draw_points}/${wizard.loss_points}</dd></div></dl></div><p class="field-help">Creeremo il torneo e genereremo gli incontri. La variante porta con sé rose, durata e regolamento: da quel momento potrai modificare i nomi e inserire i risultati.</p>`;
  }
  modal(
    "Il prossimo torneo è il tuo.",
    `<div class="wizard-steps">${["Il torneo", "I partecipanti", "Si comincia"].map((l, i) => `<span class="wizard-step ${i <= wizardStep ? "active" : ""}">0${i + 1} ${l}</span>`).join("")}</div><form id="wizard-form">${body}</form>`,
    `${button(wizardStep ? "Indietro" : "Annulla", wizardStep ? "wizard-back" : "close", "ghost")}<button class="button primary" form="wizard-form" type="submit">${wizardStep === 2 ? "Crea e genera incontri" : "Continua"}${icon("arrow")}</button>`,
    "NUOVA COMPETIZIONE",
  );
  updateWizardFormat();
}
function updateWizardFormat() {
  if (wizardStep !== 0) return;
  const fmt = $('#wizard-form [name="format"]:checked')?.value;
  $("#group-options").classList.toggle("hidden", fmt !== "groups");
  const legs = $('#wizard-form [name="legs"]');
  legs.disabled = fmt === "knockout";
  if (legs.disabled) legs.value = "1";
}
async function wizardSubmit() {
  const form = $("#wizard-form");
  if (!form.reportValidity()) return;
  readWizard();
  if (wizardStep === 0) {
    if (wizard.format === "knockout") wizard.legs = 1;
    if (
      wizard.format === "groups" &&
      (wizard.count % wizard.group_count ||
        wizard.count / wizard.group_count < Math.max(2, wizard.qualifiers))
    )
      throw new Error(
        "Scegli gironi uguali con almeno due partecipanti ciascuno.",
      );
  }
  if (wizardStep === 1) {
    const names = wizard.names
      .split("\n")
      .map((n) => n.trim())
      .filter(Boolean);
    if (names.length && names.length !== wizard.count)
      throw new Error(
        "Inserisci esattamente " + wizard.count + " nomi, oppure lascia vuoto.",
      );
    if (
      new Set(names.map((n) => n.toLocaleLowerCase("it"))).size !== names.length
    )
      throw new Error("Ogni partecipante deve avere un nome diverso.");
  }
  if (wizardStep < 2) {
    wizardStep++;
    renderWizard();
    return;
  }
  const { count, names, ...payload } = wizard;
  payload.team_names = names.trim()
    ? names
        .split("\n")
        .map((n) => n.trim())
        .filter(Boolean)
    : Array.from(
        { length: count },
        (_, i) =>
          (wizard.participant_kind === "team" ? "Team" : "Giocatore") +
          " #" +
          (i + 1),
      );
  const created = await api("/tournaments", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  try {
    await api("/tournaments/" + created.id + "/generate", { method: "POST" });
  } catch (e) {
    close();
    await openTournament(created.id);
    throw new Error("Torneo salvato in bozza. " + e.message);
  }
  close();
  await openTournament(created.id);
  tab = wizard.format === "knockout" ? "bracket" : "matches";
  renderTournament();
  notify("Il torneo è pronto. Buon gioco!");
}
function project() {
  modal(
    "Un campo aperto alle idee.",
    `<p class="project-intro">Open Score è un progetto di Leonardo e del suo collaboratore per organizzare tornei a scuola. Nome e direzione si scelgono insieme al professore.</p><ol class="project-list"><li><strong>Oggi:</strong> una demo locale con gironi, tabelloni, risultati e qualificazioni.</li><li><strong>Il prossimo incontro:</strong> scegliere lo sport, le regole e il primo torneo da provare in palestra.</li><li><strong>Poi:</strong> sport a set, account e collaborazione online, pianificazione e nuovi formati.</li></ol><p class="field-help">Il codice della demo è indipendente. Gli esempi sono dimostrativi; non è ancora un servizio pubblico con account.</p><p class="field-help"><a href="https://github.com/Leonardo-Lalli/Open-score" target="_blank" rel="noopener">Codice, roadmap e report su GitHub ↗</a></p>`,
    `${button("Torna in campo", "close", "primary")}`,
    "IL PROGETTO",
  );
}
async function share() {
  const url = location.origin + "/public/" + data.tournament.public_token;
  modal(
    "Il torneo è più bello insieme.",
    `<p class="project-intro">Condividi calendario, risultati e tabellone con chi segue il torneo. Questa vista è di sola lettura.</p><div class="share-url"><input id="share-url" aria-label="Link del torneo" value="${h(url)}" readonly><button class="button primary" data-action="copy">Copia link</button></div><p class="field-help">La demo è sul tuo computer: il link funziona sui browser che possono raggiungere questo server locale. Per condividerla online servirà l’hosting previsto nella roadmap.</p>`,
    `<a class="button primary" href="${h(url)}" target="_blank" rel="noopener">Apri vista spettatore ${icon("arrow")}</a>`,
    "CONDIVIDI IL GIOCO",
  );
}
const actions = {
  dashboard,
  new: () => (canEdit() ? startWizard() : loginModal()),
  catalog: (el) =>
    openCatalog(el?.dataset?.catalogSport || null, el?.dataset?.catalogVariant || null),
  "new-variant": (el) =>
    canEdit()
      ? startWizard(el.dataset.sport, el.dataset.variant)
      : loginModal(),
  print: () => window.print(),
  login: loginModal,
  logout: async () => {
    await api("/auth/logout", { method: "POST" });
    auth.authenticated = false;
    renderAuthControl();
    await dashboard();
    notify("Sessione chiusa.");
  },
  project,
  close,
  share,
  edit: editTournament,
  archive: () => {
    if (!canEdit()) return loginModal();
    modal(
      "Archiviare il torneo?",
      `<p class="project-intro">“${h(data.tournament.name)}” uscirà dall’elenco principale. Potrai ripristinarlo dal filtro Archiviati: nessun dato viene cancellato.</p>`,
      `${button("Annulla", "close", "ghost")}<button class="button danger" data-confirm-archive>Archivia</button>`,
      "ARCHIVIO",
    );
  },
  restore: async () => {
    if (!canEdit()) return loginModal();
    await api(`/tournaments/${selectedId}/restore`, { method: "POST" });
    await openTournament(selectedId, true);
    notify("Torneo ripristinato.");
  },
  matches: () => {
    tab = "matches";
    renderTournament();
  },
  refresh: () =>
    selectedId || publicToken ? openTournament(selectedId, true) : dashboard(),
  generate: async () => {
    if (!canEdit()) return loginModal();
    await api("/tournaments/" + selectedId + "/generate", { method: "POST" });
    await openTournament(selectedId, true);
    notify("Incontri generati. Si gioca!");
  },
  seed: async () => {
    if (!canEdit()) return loginModal();
    await api("/demo", { method: "POST" });
    await dashboard();
    notify("Gli esempi sono pronti.");
  },
  explore: async () => {
    if (!canEdit()) return loginModal();
    if (!list.length) await actions.seed();
    const t =
      list.find((t) => !t.archived_at && t.demo_key === "school-cup") ||
      list.find((t) => !t.archived_at);
    if (t) {
      await openTournament(t.id);
      tab = "bracket";
      renderTournament();
    }
  },
  copy: async () => {
    const el = $("#share-url");
    try {
      await navigator.clipboard.writeText(el.value);
      notify("Link copiato.");
    } catch {
      el.select();
      notify("Seleziona e copia il link con Ctrl+C.");
    }
  },
  "wizard-back": () => {
    readWizard();
    wizardStep--;
    renderWizard();
  },
};
const spaEnabled = document.body.dataset.app === "spa";
if (!spaEnabled) {
  // Pagine di design statiche: i pulsanti principali portano alle pagine reali.
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-action]");
    if (!a) return;
    if (a.dataset.action === "dashboard") location.href = "../";
    if (a.dataset.action === "new") location.href = "create.html";
  });
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-open]")) location.href = "panoramica_torneo.html";
  });
}
document.addEventListener("click", (e) => {
  if (!spaEnabled) return;
  const a = e.target.closest("[data-action]");
  if (a) {
    e.preventDefault();
    const fn = actions[a.dataset.action];
    if (fn) safely(() => fn(a));
  }
  const open = e.target.closest("[data-open]");
  if (open) safely(() => openTournament(Number(open.dataset.open)));
  const catalogSport = e.target.closest("[data-catalog-sport]");
  if (catalogSport)
    safely(() => openCatalog(catalogSport.dataset.catalogSport));
  const catalogVariant = e.target.closest("[data-catalog-variant]");
  if (catalogVariant)
    safely(() =>
      openCatalog(
        catalogVariant.dataset.catalogParent,
        catalogVariant.dataset.catalogVariant,
      ),
    );
  const removePlayer = e.target.closest("[data-remove-player]");
  if (removePlayer)
    safely(async () => {
      await api(
        `/tournaments/${selectedId}/teams/${removePlayer.dataset.playerTeam}/players/${removePlayer.dataset.removePlayer}`,
        { method: "DELETE" },
      );
      await openTournament(selectedId, true);
      if ($("#modal").open) await teamModal(removePlayer.dataset.playerTeam);
      notify("Giocatore rimosso dalla rosa.");
    });
  const t = e.target.closest("[data-tab]");
  if (t) {
    tab = t.dataset.tab;
    renderTournament();
  }
  const f = e.target.closest("[data-filter]");
  if (f) {
    filter = f.dataset.filter;
    renderDashboard();
  }
  const mf = e.target.closest("[data-match-filter]");
  if (mf) {
    matchFilter = mf.dataset.matchFilter;
    renderTournament();
  }
  const team = e.target.closest("[data-team]");
  if (team) safely(() => teamModal(team.dataset.team));
  const r = e.target.closest("[data-result]");
  if (r) resultModal(r.dataset.result);
  const rename = e.target.closest("[data-rename]");
  if (rename) {
    const p = data.teams.find((t) => t.id === Number(rename.dataset.rename));
    modal(
      "Un nome da portare in campo.",
      `<form id="rename-form" data-id="${p.id}"><label>Nome del partecipante<input name="name" value="${h(p.name)}" maxlength="60" required autofocus></label></form>`,
      `${button("Annulla", "close", "ghost")}<button class="button primary" form="rename-form">Salva nome</button>`,
      "PARTECIPANTE",
    );
  }
  const remove = e.target.closest("[data-remove]");
  if (remove) {
    const id = Number(remove.dataset.remove);
    modal(
      "Rimuovere il partecipante?",
      `<p class="project-intro">${h(teamName(id))} verrà rimosso dalla bozza del torneo.</p>`,
      `${button("Annulla", "close", "ghost")}<button class="button danger" data-confirm-remove="${id}">Rimuovi</button>`,
    );
  }
  const confirmRemove = e.target.closest("[data-confirm-remove]");
  if (confirmRemove)
    safely(async () => {
      await api(
        `/tournaments/${selectedId}/teams/${confirmRemove.dataset.confirmRemove}`,
        { method: "DELETE" },
      );
      close();
      await openTournament(selectedId, true);
      notify("Partecipante rimosso.");
    });
  const restore = e.target.closest("[data-restore]");
  if (restore)
    safely(async () => {
      await api(`/tournaments/${restore.dataset.restore}/restore`, {
        method: "POST",
      });
      await dashboard();
      notify("Torneo ripristinato.");
    });
  const confirmArchive = e.target.closest("[data-confirm-archive]");
  if (confirmArchive)
    safely(async () => {
      await api(`/tournaments/${selectedId}/archive`, { method: "POST" });
      close();
      selectedId = null;
      data = null;
      await dashboard();
      notify("Torneo archiviato. Lo trovi nel filtro Archiviati.");
    });
  const clear = e.target.closest("[data-clear]");
  if (clear)
    safely(async () => {
      const m = data.matches.find((m) => m.id === Number(clear.dataset.clear));
      const invalidate = !!$('#result-form [name="invalidate"]')?.checked;
      await api(`/tournaments/${selectedId}/matches/${m.id}/result`, {
        method: "DELETE",
        body: JSON.stringify({ version: m.version, invalidate }),
      });
      close();
      await openTournament(selectedId, true);
      notify("Risultato cancellato.");
    });
});
document.addEventListener("change", (e) => {
  if (e.target.id === "wizard-sport") {
    readWizard();
    const sport = sportFor(wizard.sport);
    const variant =
      sport?.variants?.find((v) => v.slug === sport.default_variant) ||
      sport?.variants?.[0];
    applyVariantToWizard(variant);
    const select = $("#wizard-variant");
    if (select) select.innerHTML = variantOptionsFor(wizard.sport, wizard.variant);
    $("#wizard-variant-preview").innerHTML = variantRulesPanel(variant);
  }
  if (e.target.id === "wizard-variant") {
    readWizard();
    const variant = variantFor(wizard.variant);
    applyVariantToWizard(variant);
    $("#wizard-variant-preview").innerHTML = variantRulesPanel(variant);
  }
  if (e.target.id === "sport-edit") {
    const sport = sportFor(e.target.value);
    const variant =
      sport?.variants?.find((v) => v.slug === sport.default_variant) ||
      sport?.variants?.[0];
    const select = $("#edit-variant");
    if (select && variant) select.innerHTML = variantOptionsFor(sport.name, variant.slug);
    applyVariantToWizard(variant);
    syncEditVariant(variant);
  }
  if (e.target.id === "edit-variant") {
    applyVariantToWizard(variantFor(e.target.value));
    syncEditVariant(variantFor(e.target.value));
  }
  if (e.target.name === "format" && $("#wizard-form")) updateWizardFormat();
});
document.addEventListener("submit", (e) => {
  e.preventDefault();
  const form = e.target;
  safely(async () => {
    const submitter = e.submitter;
    if (submitter) submitter.disabled = true;
    try {
      const fd = new FormData(form);
      if (form.id === "wizard-form") await wizardSubmit();
      if (form.id === "team-form") {
        await api("/tournaments/" + selectedId + "/teams", {
          method: "POST",
          body: JSON.stringify({ name: fd.get("name") }),
        });
        await openTournament(selectedId, true);
        notify("Partecipante aggiunto.");
      }
      if (form.id === "player-form") {
        await api(
          `/tournaments/${selectedId}/teams/${form.dataset.team}/players`,
          {
            method: "POST",
            body: JSON.stringify({
              name: fd.get("name"),
              shirt_number: fd.get("shirt_number")
                ? Number(fd.get("shirt_number"))
                : null,
            }),
          },
        );
        await openTournament(selectedId, true);
        await teamModal(form.dataset.team);
        notify("Giocatore aggiunto alla rosa.");
      }
      if (form.id === "rename-form") {
        await api(`/tournaments/${selectedId}/teams/${form.dataset.id}`, {
          method: "PATCH",
          body: JSON.stringify({ name: fd.get("name") }),
        });
        close();
        await openTournament(selectedId, true);
        notify("Nome aggiornato.");
      }
      if (form.id === "tournament-form") {
        const payload = {
          name: fd.get("name"),
          description: fd.get("description") || "",
        };
        if (fd.has("sport")) {
          payload.sport = fd.get("sport");
          payload.variant = fd.get("variant");
          payload.format = fd.get("format");
          payload.participant_kind = fd.get("participant_kind");
          payload.legs =
            fd.get("format") === "knockout" ? 1 : Number(fd.get("legs"));
          payload.group_count = Number(fd.get("group_count"));
          payload.qualifiers = Number(fd.get("qualifiers"));
          payload.win_points = Number(fd.get("win_points"));
          payload.draw_points = Number(fd.get("draw_points"));
          payload.loss_points = Number(fd.get("loss_points"));
          payload.tie_breaker = fd.get("tie_breaker");
        }
        await api(`/tournaments/${selectedId}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
        close();
        await openTournament(selectedId, true);
        notify("Torneo aggiornato.");
      }
      if (form.id === "login-form") {
        const result = await api("/auth/login", {
          method: "POST",
          body: JSON.stringify({ password: fd.get("password") }),
        });
        auth = { required: !!result.auth_required, authenticated: true };
        renderAuthControl();
        close();
        await (selectedId && !publicToken ? openTournament(selectedId, true) : dashboard());
        notify("Accesso eseguito. Ora puoi organizzare.");
      }
      if (form.id === "result-form" || form.id === "schedule-form") {
        const m = data.matches.find((m) => m.id === Number(form.dataset.id));
        const schedule = form.id === "schedule-form";
        let payload;
        if (schedule) {
          payload = {
            version: m.version,
            scheduled_at: fd.get("scheduled_at")
              ? new Date(fd.get("scheduled_at")).toISOString()
              : null,
            location: fd.get("location"),
            duration: Number(fd.get("duration")),
          };
        } else if (isSetBased()) {
          const sets = [];
          for (let index = 1; index <= (currentVariant()?.max_sets || 7); index++) {
            const home = fd.get(`home_set_${index}`);
            const away = fd.get(`away_set_${index}`);
            if (home === null && away === null) continue;
            if (home === "" && away === "") continue;
            if (home === "" || away === "")
              throw new Error(`Completa il set ${index} con entrambi i punteggi.`);
            sets.push({ home: Number(home), away: Number(away) });
          }
          if (!sets.length) throw new Error("Inserisci almeno un set.");
          payload = {
            version: m.version,
            sets,
            invalidate: fd.has("invalidate"),
          };
        } else {
          payload = {
            version: m.version,
            home_score: Number(fd.get("home_score")),
            away_score: Number(fd.get("away_score")),
            invalidate: fd.has("invalidate"),
          };
        }
        await api(
          `/tournaments/${selectedId}/matches/${m.id}${schedule ? "/schedule" : ""}`,
          { method: "PATCH", body: JSON.stringify(payload) },
        );
        close();
        await openTournament(selectedId, true);
        notify(
          schedule
            ? "Orario e campo aggiornati."
            : data.champion_team_id
              ? "Il torneo ha il suo campione!"
              : "Risultato salvato. Il torneo è aggiornato.",
        );
      }
    } finally {
      if (submitter) submitter.disabled = false;
    }
  });
});
$("#modal").addEventListener("click", (e) => {
  if (e.target === $("#modal")) {
    const rect = $("#modal").getBoundingClientRect();
    if (
      e.clientX < rect.left ||
      e.clientX > rect.right ||
      e.clientY < rect.top ||
      e.clientY > rect.bottom
    )
      close();
  }
});
$("#mobile-menu").addEventListener("click", () => {
  const open = $("#sidebar").classList.toggle("open");
  $("#mobile-menu").setAttribute("aria-expanded", String(open));
});
async function init() {
  try {
    if (publicToken) {
      $("#sidebar").classList.add("hidden");
      $(".app-shell").style.marginLeft = "0";
      $(".top-actions").innerHTML =
        '<span class="demo-label">VISTA SPETTATORE · SOLA LETTURA</span>';
      $("#mobile-menu").classList.add("hidden");
      await openTournament(null);
      setInterval(() => {
        if (!document.hidden && !$("#modal").open)
          safely(() => openTournament(null, true));
      }, 30000);
    } else {
      await loadSession();
      await loadSports();
      const route = hashRoute();
      if (route.kind === "sport") await openCatalog(route.sport, route.variant);
      else await dashboard();
    }
  } catch (e) {
    $("#content").innerHTML =
      `<div class="error-page"><h1>Il campo non è raggiungibile.</h1><p>${h(e.message)}</p><button class="button primary" data-action="refresh">Riprova</button></div>`;
    $("#content").setAttribute("aria-busy", "false");
  }
}
if (spaEnabled) init();
window.addEventListener("hashchange", () => {
  if (!spaEnabled || publicToken) return;
  const route = hashRoute();
  safely(() =>
    route.kind === "sport"
      ? openCatalog(route.sport, route.variant)
      : dashboard(),
  );
});

document.addEventListener("keydown", (e) => {
  if (!spaEnabled) return;
  const current = e.target.closest("[role=tab]");
  if (!current || !["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key))
    return;
  e.preventDefault();
  const tabs = [...document.querySelectorAll("[role=tab]")];
  let i = tabs.indexOf(current);
  i =
    e.key === "Home"
      ? 0
      : e.key === "End"
        ? tabs.length - 1
        : (i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
  tab = tabs[i].dataset.tab;
  renderTournament();
  document.querySelector("#tab-" + tab).focus();
});
