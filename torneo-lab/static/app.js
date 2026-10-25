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
const publicToken = location.pathname.startsWith("/public/")
  ? location.pathname.split("/")[2]
  : null;
let list = [],
  sports = [],
  selectedId = null,
  data = null,
  tab = "overview",
  filter = "all",
  matchFilter = "all",
  search = "",
  wizard = {},
  wizardStep = 0,
  toastTimer;
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
  list = await api("/tournaments");
  renderNav();
}
async function loadSports() {
  const result = await api("/sports");
  sports = result.sports || [];
}
function renderNav() {
  $("#event-count").textContent = list.length;
  $("#event-nav").innerHTML =
    list
      .map(
        (t) =>
          `<button data-open="${t.id}" class="${t.id === selectedId ? "active" : ""}"><span class="event-dot"></span>${h(t.name)}</button>`,
      )
      .join("") || '<p class="sidebar-muted">Il primo torneo ti aspetta.</p>';
  $("#home-nav").classList.toggle("active", !selectedId);
}
async function dashboard() {
  if (publicToken) return;
  selectedId = null;
  data = null;
  tab = "overview";
  await refreshList();
  $("#breadcrumb").textContent = "Panoramica";
  renderDashboard();
  $("#sidebar").classList.remove("open");
  $("#mobile-menu").setAttribute("aria-expanded", "false");
}
function renderDashboard() {
  const shown = list.filter(
    (t) =>
      (filter === "all" || t.status === filter) &&
      t.name.toLocaleLowerCase("it").includes(search.toLocaleLowerCase("it")),
  );
  const totalTeams = list.reduce((a, t) => a + t.team_count, 0),
    done = list.reduce((a, t) => a + t.progress.completed, 0);
  $("#content").innerHTML =
    `<div class="page-heading"><div><p class="eyebrow"><span class="line"></span> MENO ORGANIZZAZIONE, PIÙ GIOCO</p><h1>Ogni torneo comincia qui.</h1><p>Metti in campo le tue idee. Noi teniamo il punteggio.</p></div><span class="date-note">Uno spazio, tutte le tue sfide.</span></div>
 <section class="hero" aria-label="Inizia a organizzare"><div class="hero-copy"><p class="eyebrow">IL PROSSIMO FISCHIO D’INIZIO</p><h2>Lo sport unisce.<br><em>Organizzarlo è semplice.</em></h2><p>Dalle partite in palestra alla coppa d’istituto: squadre, incontri e risultati, tutti nello stesso posto.</p><div class="hero-buttons">${button("Crea il tuo torneo", "new", "primary", "plus")}${button("Esplora la demo", "explore", "ghost", "arrow")}</div></div><div class="hero-art" aria-hidden="true"><div class="court"><div class="court-circle"></div></div><div class="hero-score"><div class="score-kicker">IL TUO PROSSIMO TORNEO <span>● SI GIOCA</span></div><div class="score-line">${avatar("A", 2)}La tua squadra <b>—</b></div><div class="score-line">${avatar("B", 1)}Una nuova sfida <b>—</b></div></div><div class="hero-sticker">${icon("trophy")}</div></div></section>
 <div class="stat-grid">${stat("Tornei creati", list.length, "Tutte le tue competizioni", "trophy")}${stat("Partecipanti", totalTeams, "Pronti a scendere in campo", "users")}${stat("Tornei in corso", list.filter((t) => t.status === "active").length, "Il gioco continua", "ball")}${stat("Risultati registrati", done, "Ogni partita conta", "check")}</div>
 <section><div class="section-header"><div><h2>I tuoi tornei <span class="muted">${list.length.toString().padStart(2, "0")}</span></h2><p class="section-sub">Scegli una competizione e porta avanti il gioco.</p></div><div class="filters" aria-label="Filtra tornei">${[
   ["all", "Tutti"],
   ["active", "In corso"],
   ["completed", "Conclusi"],
 ]
   .map(
     ([v, l]) =>
       `<button class="filter ${filter === v ? "active" : ""}" data-filter="${v}" aria-pressed="${filter === v}">${l}</button>`,
   )
   .join("")}</div></div>
 <div class="tournament-grid">${shown.map(eventCard).join("") || `<div class="panel empty">${icon("trophy")}<h2>Il campo è libero.</h2><p>${list.length ? "Nessun torneo con questo filtro." : "Crea il primo torneo oppure carica gli esempi per iniziare."}</p>${button("Nuovo torneo", "new", "primary")}${button("Carica esempi", "seed", "ghost")}</div>`}</div></section>
 <div class="note-banner">${icon("spark")}<div><strong>Un progetto aperto, anche alle tue idee.</strong><p>Questa è la nostra prima demo. Il prossimo passo lo scegliamo insieme.</p></div><button class="text-button" data-action="project">Il progetto ${icon("arrow")}</button></div>`;
  $("#content").setAttribute("aria-busy", "false");
}
function eventCard(t, i) {
  const progress = t.progress.total
    ? Math.round((t.progress.completed / t.progress.total) * 100)
    : 0;
  return `<article class="event-card"><div class="event-card-top"><div class="sport-symbol ${["", "gold", "blue", "rose"][i % 4]}">${icon(t.format === "knockout" ? "trophy" : t.format === "groups" ? "grid" : "ball")}</div><span class="tag ${t.status}"><i></i>${stateLabel(t.status)}</span></div><h3>${h(t.name)}</h3><p class="event-format">${h(t.sport)} <span aria-hidden="true">/</span> ${label(t.format)}</p><div class="event-meta"><span>${icon("users")}${t.team_count} ${t.participant_kind === "team" ? "squadre" : "giocatori"}</span><span>${icon("calendar")}${t.progress.total} incontri${t.format === "groups" ? " · gironi" : ""}</span></div><div class="progress-track" role="progressbar" aria-label="Incontri completati" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"><span style="width:${progress}%"></span></div><div class="progress-copy"><span>${t.progress.completed} di ${t.progress.total} incontri completati</span><span>${progress}%</span></div><div class="event-card-footer"><div class="avatar-stack"><span>${h(t.sport.slice(0, 1))}</span><span>OS</span><small>${t.demo_key ? "Torneo dimostrativo" : "Il nostro torneo"}</small></div><button class="text-button" data-open="${t.id}">Apri torneo ${icon("arrow")}</button></div></article>`;
}
async function openTournament(id, keepTab = false) {
  const next = await api(
    publicToken
      ? "/public/" + encodeURIComponent(publicToken)
      : "/tournaments/" + id,
  );
  selectedId = next.tournament.id;
  data = next;
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
  ];
  if (t.format !== "knockout") tabs.push(["standings", "Classifiche"]);
  if (t.format !== "round_robin") tabs.push(["bracket", "Tabellone"]);
  let body =
    tab === "participants"
      ? participants()
      : tab === "matches"
        ? matchesView()
        : tab === "standings"
          ? standingsView()
          : tab === "bracket"
            ? bracket()
            : overview();
  $("#content").innerHTML =
    `${!publicToken ? `<button class="back-link" data-action="dashboard">${icon("back")} Tutti i tornei</button>` : '<p class="eyebrow">SEGUI IL TORNEO · SOLA LETTURA</p>'}<div class="tournament-heading"><div><p class="eyebrow">${h(t.sport)} <span>/</span> ${label(t.format)} <span class="tag ${data.status}">${stateLabel(data.status)}</span></p><h1>${h(t.name)}</h1><p>${h(t.description || "Ogni partita, un passo verso una nuova sfida.")}</p></div><div class="toolbar">${publicToken ? button("Aggiorna", "refresh", "", "check") : `${button("Condividi", "share", "", "share")}<a class="button" href="/api/tournaments/${t.id}/export.csv" download>${icon("download")}Esporta</a>`}</div></div><div class="tabs" role="tablist" aria-label="Sezioni torneo">${tabs.map(([v, l]) => `<button class="tab ${tab === v ? "active" : ""}" role="tab" id="tab-${v}" aria-controls="tournament-panel" tabindex="${tab === v ? 0 : -1}" aria-selected="${tab === v}" data-tab="${v}">${l}</button>`).join("")}</div><div id="tournament-panel" role="tabpanel" aria-labelledby="tab-${tab}">${champion()}${body}</div>`;
  $("#content").setAttribute("aria-busy", "false");
}
function overview() {
  const t = data.tournament,
    p = data.progress,
    fixtures = data.matches;
  const next = fixtures.filter((m) => m.status === "ready").slice(0, 3);
  const groupsComplete =
    t.format === "groups" && fixtures.some((m) => m.kind === "knockout");
  return `<div class="stat-grid">${stat("Partecipanti", data.teams.length, t.participant_kind === "team" ? "Squadre iscritte" : "Giocatori iscritti", "users")}${stat("Incontri", p.total, "Esclusi i passaggi per BYE", "calendar")}${stat("Completati", p.completed, "Risultati confermati", "check")}${stat("Da giocare", p.total - p.completed, "Il campo vi aspetta", "ball")}</div><div class="overview-grid"><div><div class="panel"><div class="section-header"><h2>${data.status === "completed" ? "Torneo completato" : "Il prossimo passo"}</h2><span class="panel-label">SI SCENDE IN CAMPO</span></div><p class="muted" style="font-size:12px">${publicToken ? "Segui gli incontri e aggiorna la pagina per vedere gli ultimi risultati." : !fixtures.length ? "Aggiungi i partecipanti e genera gli incontri per dare inizio al torneo." : data.status === "completed" ? "Tutte le partite sono state giocate. Puoi rivedere il percorso e i risultati." : t.format === "groups" && !groupsComplete ? "Completa tutte le partite dei gironi: le qualificate passeranno automaticamente alla fase finale." : "Registra il risultato di un incontro: classifica e percorso si aggiornano subito."}</p><div class="steps"><div class="step ${data.teams.length >= 2 ? "done" : ""}">01<b>Partecipanti</b>Le squadre sono pronte</div><div class="step ${fixtures.length ? "done" : ""}">02<b>Si gioca</b>Incontri e risultati</div><div class="step ${data.status === "completed" ? "done" : ""}">03<b>La finale</b>${t.format === "round_robin" ? "Una classifica completa" : "Un campione da celebrare"}</div></div>${!fixtures.length && !publicToken ? `<div style="margin-top:25px">${button("Genera incontri", "generate", "primary", "spark")}</div>` : ""}</div><div class="panel"><div class="section-header"><h2>${next.length ? "Pronte da giocare" : "Le ultime partite"}</h2><button class="text-button" data-tab="matches">Vedi tutte ${icon("arrow")}</button></div>${(next.length ? next : fixtures.filter((m) => m.status === "completed").slice(-3)).map(matchRow).join("") || '<p class="muted" style="font-size:12px">Gli incontri compariranno qui dopo la generazione.</p>'}</div></div><div><div class="panel"><h2>Il torneo in breve</h2><dl class="details-list"><div><dt>Sport</dt><dd>${h(t.sport)}</dd></div><div><dt>Formato</dt><dd>${label(t.format)}</dd></div><div><dt>Partecipanti</dt><dd>${t.participant_kind === "team" ? "Squadre" : "Giocatori individuali"}</dd></div>${t.format === "groups" ? `<div><dt>Qualificazione</dt><dd>Prime ${t.qualifiers} di ${t.group_count} gironi</dd></div>` : ""}<div><dt>Andata / ritorno</dt><dd>${t.legs === 2 ? "Andata e ritorno" : "Sola andata"}</dd></div>${t.format !== "knockout" ? `<div><dt>Punti V / N / P</dt><dd>${t.win_points} / ${t.draw_points} / ${t.loss_points}</dd></div>` : ""}<div><dt>Orari</dt><dd>Europe/Rome</dd></div></dl></div>${
    !publicToken
      ? `<div class="panel"><h2>Diario del torneo</h2>${(data.audit || [])
          .slice(0, 5)
          .map(
            (a) =>
              `<div class="timeline-item"><i></i><div>${{ created: "Torneo creato", generated: "Incontri generati", result_saved: "Risultato registrato", result_cleared: "Risultato cancellato", qualified: "Qualificate alla fase finale", invalidated: "Incontri dipendenti annullati", scheduled: "Orario aggiornato", team_added: "Partecipante aggiunto", team_renamed: "Nome aggiornato" }[a.action] || "Torneo aggiornato"}<small>${dateText(a.created_at)}</small></div></div>`,
          )
          .join("")}</div>`
      : ""
  }</div></div>`;
}
function matchRow(m) {
  const ready = m.status === "ready" || m.status === "completed";
  const group = data.groups.find((g) => g.id === m.group_id);
  return `<div class="match-row"><div class="match-round">${group ? h(group.name) + "<br>" : ""}${h(roundName(m))}</div><div class="match-players"><div class="match-player">${avatar(teamName(m.home_team_id), m.home_team_id)}<span>${h(m.home_team_id ? teamName(m.home_team_id) : m.is_bye ? "Riposo" : "Da definire")}</span></div><span class="score">${m.home_score ?? "–"} : ${m.away_score ?? "–"}</span><div class="match-player"><span>${h(m.away_team_id ? teamName(m.away_team_id) : m.is_bye ? "Riposo" : "Da definire")}</span>${avatar(teamName(m.away_team_id), m.away_team_id)}</div></div><div class="match-actions">${!publicToken && ready ? `<button class="button ${m.status === "ready" ? "primary" : ""}" data-result="${m.id}">${m.status === "ready" ? "Risultato" : "Modifica"}</button>` : `<span class="tag">${m.is_bye ? "BYE" : m.status === "waiting" ? "In attesa" : m.status === "completed" ? "Giocata" : "Da giocare"}</span>`}</div></div>${m.scheduled_at || m.location ? `<p class="match-note">${icon("clock")}${m.scheduled_at ? h(dateText(m.scheduled_at)) : "Orario da definire"}${m.location ? " · " + h(m.location) : ""}</p>` : ""}`;
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
  return `<div class="section-header"><div><h2>Le persone fanno il torneo.</h2><p class="section-sub">${data.teams.length} ${data.tournament.participant_kind === "team" ? "squadre" : "giocatori"} · I nomi si possono modificare anche a torneo iniziato.</p></div>${!generated && !publicToken ? button("Genera incontri", "generate", "primary", "spark") : ""}</div>${!generated && !publicToken ? '<form id="team-form" class="inline-form"><input name="name" required maxlength="60" aria-label="Nome del partecipante" placeholder="Nome del partecipante"><button class="button primary">Aggiungi</button></form>' : ""}<div class="roster">${data.teams.map((p, i) => `<div class="roster-item">${avatar(p.name, i)}<div><strong>${h(p.name)}</strong><small>${h(data.groups.find((g) => g.id === p.group_id)?.name || "Partecipante " + (i + 1).toString().padStart(2, "0"))}</small></div>${!publicToken ? `<button class="icon-button" data-rename="${p.id}" aria-label="Rinomina ${h(p.name)}">${icon("edit")}</button>${!generated ? `<button class="icon-button" data-remove="${p.id}" aria-label="Elimina ${h(p.name)}">${icon("close")}</button>` : ""}` : ""}</div>`).join("") || '<p class="muted">Aggiungi almeno due partecipanti per cominciare.</p>'}</div>`;
}
function standingsTable(rows, qualifiers = 0) {
  return `<div class="table-wrap"><table><thead><tr><th>#</th><th>Partecipante</th><th>G</th><th>V</th><th>N</th><th>P</th><th>F</th><th>S</th><th>DR</th><th>PT</th></tr></thead><tbody>${rows.map((r, i) => `<tr class="${i < qualifiers ? "qualifier" : ""}"><td>${i + 1}</td><td>${avatar(r.name, r.team_id)}${h(r.name)}</td><td>${r.played}</td><td>${r.won}</td><td>${r.drawn}</td><td>${r.lost}</td><td>${r.goals_for}</td><td>${r.goals_against}</td><td>${r.goal_difference}</td><td>${r.points}</td></tr>`).join("")}</tbody></table></div>`;
}
function standingsView() {
  const t = data.tournament;
  return `<div class="section-header"><div><h2>La classifica si scrive in campo.</h2><p class="section-sub">Si aggiorna a ogni risultato confermato.</p></div></div>${data.groups.length ? `<div class="groups-grid">${data.groups.map((g) => `<section class="panel"><div class="group-heading"><h2>${h(g.name)}</h2><span>Passano le prime ${t.qualifiers}</span></div>${standingsTable(g.standings, t.qualifiers)}<p class="table-note"><span class="legend-dot"></span>Posizioni di qualificazione · definitive a gironi completati</p></section>`).join("")}</div>` : `<div class="panel">${standingsTable(data.standings)}</div>`}<p class="table-note">G: giocate · V/N/P: vittorie, pareggi, sconfitte · F/S: punti fatti e subiti · DR: differenza · PT: punti in classifica.<br>Ordine: punti → differenza → punti fatti → nome → ID. Punteggio: ${t.win_points}/${t.draw_points}/${t.loss_points}. I criteri sono quelli di questa demo.</p>`;
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
function resultModal(id) {
  const m = data.matches.find((x) => x.id === Number(id));
  if (!m || publicToken) return;
  let local = "";
  if (m.scheduled_at) {
    const d = new Date(m.scheduled_at);
    local = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
  }
  modal(
    m.status === "completed"
      ? "Ogni risultato conta."
      : "Com’è andata in campo?",
    `<form id="result-form" data-id="${m.id}"><div class="result-inputs"><label>${avatar(teamName(m.home_team_id), m.home_team_id)}<span>${h(teamName(m.home_team_id))}</span><input name="home_score" aria-label="Punteggio ${h(teamName(m.home_team_id))}" type="number" min="0" max="999" step="1" value="${m.home_score ?? ""}" required></label><span>:</span><label>${avatar(teamName(m.away_team_id), m.away_team_id)}<span>${h(teamName(m.away_team_id))}</span><input name="away_score" aria-label="Punteggio ${h(teamName(m.away_team_id))}" type="number" min="0" max="999" step="1" value="${m.away_score ?? ""}" required></label></div>${m.home_score !== null ? '<label class="checkbox"><input type="checkbox" name="invalidate">Se questa correzione cambia qualificazioni o avversari, confermo l’annullamento dei risultati e degli orari dipendenti.</label>' : ""}<p class="field-help">${m.kind === "knockout" ? "Serve un punteggio decisivo. Questa demo non gestisce ancora set, rigori o supplementari." : "La classifica verrà aggiornata dopo il salvataggio."}</p></form><details class="result-schedule"><summary>Orario e campo</summary><form id="schedule-form" data-id="${m.id}"><div class="form-grid"><label>Data e ora locale<input name="scheduled_at" type="datetime-local" value="${local}"></label><label>Campo<input name="location" maxlength="80" placeholder="Es. Palestra · campo A" value="${h(m.location || "")}"></label><label>Durata in minuti<input name="duration" type="number" min="1" max="240" value="${m.duration}" required></label></div><p class="field-help">L’orario usa il fuso del dispositivo. Gli orari sono mostrati nel torneo in Europe/Rome.</p><button class="button" style="margin-top:13px">Salva orario e campo</button></form></details>`,
    `${m.home_score !== null ? `<button class="button danger" data-clear="${m.id}">Cancella risultato</button>` : button("Annulla", "close", "ghost")}<button type="submit" form="result-form" class="button primary">${icon("check")}Salva risultato</button>`,
    h(roundName(m)),
  );
}
function startWizard() {
  wizard = {
    name: "",
    sport: "Calcio a 5",
    format: "knockout",
    count: 8,
    group_count: 2,
    qualifiers: 2,
    legs: 1,
    names: "",
    description: "",
    participant_kind: "team",
    win_points: 3,
    draw_points: 1,
    loss_points: 0,
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
    : [
        "Calcio",
        "Calcio a 5",
        "Basket",
        "Pallamano",
        "Badminton",
        "Tennis",
        "Pallavolo",
      ];
  if (!names.includes(wizard.sport)) wizard.sport = names[0];
  return names
    .map(
      (s) =>
        `<option value="${h(s)}" ${s === wizard.sport ? "selected" : ""}>${h(s)}</option>`,
    )
    .join("");
}
function renderWizard() {
  let body = "";
  if (wizardStep === 0)
    body = `<div class="form-grid"><label class="full">Nome del torneo<input name="name" value="${h(wizard.name)}" placeholder="Es. Coppa d’istituto" minlength="2" maxlength="120" required autofocus></label><label>Sport<select name="sport">${sportOptions()}</select></label><label>Partecipanti<select name="participant_kind"><option value="team" ${wizard.participant_kind === "team" ? "selected" : ""}>Squadre</option><option value="individual" ${wizard.participant_kind === "individual" ? "selected" : ""}>Giocatori individuali</option></select></label></div><fieldset class="format-fieldset"><legend>Scegli il percorso</legend><div class="format-options">${[
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
            .join("")}</div></details>`
        : ""
    }`;
  if (wizardStep === 2)
    body = `<div class="panel" style="margin:0;background:#f7f9f0"><p class="eyebrow">TUTTO PRONTO PER GIOCARE</p><h2>${h(wizard.name)}</h2><dl class="details-list"><div><dt>Sport</dt><dd>${h(wizard.sport)}</dd></div><div><dt>Formato</dt><dd>${label(wizard.format)}</dd></div><div><dt>Partecipanti</dt><dd>${wizard.count}</dd></div>${wizard.format === "groups" ? `<div><dt>Qualificazione</dt><dd>${wizard.group_count} gironi · prime ${wizard.qualifiers}</dd></div>` : ""}<div><dt>Gare</dt><dd>${wizard.legs === 2 ? "Andata e ritorno" : "Sola andata"}</dd></div></dl></div><p class="field-help">Creeremo il torneo e genereremo gli incontri. Da quel momento potrai modificare i nomi e inserire i risultati.</p>`;
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
  new: startWizard,
  project,
  close,
  share,
  matches: () => {
    tab = "matches";
    renderTournament();
  },
  refresh: () =>
    selectedId || publicToken ? openTournament(selectedId, true) : dashboard(),
  generate: async () => {
    await api("/tournaments/" + selectedId + "/generate", { method: "POST" });
    await openTournament(selectedId, true);
    notify("Incontri generati. Si gioca!");
  },
  seed: async () => {
    await api("/demo", { method: "POST" });
    await dashboard();
    notify("Gli esempi sono pronti.");
  },
  explore: async () => {
    if (!list.length) await actions.seed();
    const t = list.find((t) => t.demo_key === "school-cup") || list[0];
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
    if (fn) safely(fn);
  }
  const open = e.target.closest("[data-open]");
  if (open) safely(() => openTournament(Number(open.dataset.open)));
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
      if (form.id === "rename-form") {
        await api(`/tournaments/${selectedId}/teams/${form.dataset.id}`, {
          method: "PATCH",
          body: JSON.stringify({ name: fd.get("name") }),
        });
        close();
        await openTournament(selectedId, true);
        notify("Nome aggiornato.");
      }
      if (form.id === "result-form" || form.id === "schedule-form") {
        const m = data.matches.find((m) => m.id === Number(form.dataset.id));
        const schedule = form.id === "schedule-form";
        const payload = schedule
          ? {
              version: m.version,
              scheduled_at: fd.get("scheduled_at")
                ? new Date(fd.get("scheduled_at")).toISOString()
                : null,
              location: fd.get("location"),
              duration: Number(fd.get("duration")),
            }
          : {
              version: m.version,
              home_score: Number(fd.get("home_score")),
              away_score: Number(fd.get("away_score")),
              invalidate: fd.has("invalidate"),
            };
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
    } else {
      await loadSports();
      await dashboard();
    }
  } catch (e) {
    $("#content").innerHTML =
      `<div class="error-page"><h1>Il campo non è raggiungibile.</h1><p>${h(e.message)}</p><button class="button primary" data-action="refresh">Riprova</button></div>`;
    $("#content").setAttribute("aria-busy", "false");
  }
}
if (spaEnabled) init();

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
