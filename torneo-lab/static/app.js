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
  field: "M4 5h16v14H4z M12 5v14 M4 9h3v6H4 M17 9h3v6h-3",
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
// The invite landing page is client-only until Team A ships the invite API:
// `/?invite=<token>` and `#/join/<token>` open the same read-only view.
const inviteToken = (() => {
  const query = new URLSearchParams(location.search).get("invite");
  if (query) return query;
  const kind = location.hash.replace(/^#\/?/, "").split("/")[0];
  if (!["join", "invito", "invite"].includes(kind)) return null;
  const value = location.hash.replace(/^#\/?/, "").split("/")[1];
  if (!value) return null;
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
})();
let list = [],
  sports = [],
  auth = { role: null, authenticated: false, teacher: null },
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
  studentTeamId = null,
  studentSearch = "",
  bulkState = null,
  approvalsCache = [],
  inviteState = null,
  pendingInviteToken = null,
  calendarMode = false,
  fieldsMode = false,
  calendarState = { events: [], conflicts: [], teams: [], fields: [], loadedAt: 0 },
  calendarFilters = {
    tournament: "all",
    team: "all",
    day: "",
    field: "all",
    status: "all",
  },
  calendarError = "",
  calendarLoading = false,
  fieldsCache = [],
  fieldsError = "",
  editState = null,
  toastTimer;
const sportFor = (name) => sports.find((s) => s.name === name);
const variantFor = (slug) => {
  for (const sport of sports)
    for (const variant of sport.variants || [])
      if (variant.slug === slug) return variant;
  return null;
};
const currentVariant = () =>
  data?.variant_config || variantFor(data?.tournament?.variant);
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
// ---------------------------------------------------------------------------
// Regole: metadati della variante
//
// La variante è la fonte autorevole. Il backend può descrivere i parametri
// modificabili con `config_schema` (o `rule_schema` / `configurable`); finché
// non lo fa usiamo il contratto condiviso di `TournamentInput` come fallback.
// Le regole non modificabili vengono comunque mostrate leggendo `variant.rules`.
// ---------------------------------------------------------------------------
const RULE_LABELS = {
  players_on_field: "Giocatori in campo",
  min_lineup: "Minimo in campo",
  max_roster: "Rosa massima",
  match_duration: "Durata partita",
  periods: "Tempi",
  period_minutes: "Minuti per tempo",
  scoring_mode: "Modalità punteggio",
  score_label: "Unità di punteggio",
  draw_allowed: "Pareggio ammesso",
  sets_to_win: "Set per vincere",
  max_sets: "Set massimi",
  points_per_set: "Punti per set",
  tiebreak_points: "Punti del set decisivo",
  win_by_two: "Vantaggio di 2 punti",
  max_points: "Limite punti del set",
  target_goals: "Gol per vincere",
  standings: "Punti classifica",
  default_tie_breaker: "Criterio predefinito",
  surface: "Campo",
  court_type: "Tipo di campo",
  field_type: "Tipo di campo",
  substitutions: "Sostituzioni",
  notes: "Note",
};
const TIE_BREAKER_FALLBACK = [
  { value: "goal_difference", label: "Differenza reti" },
  { value: "head_to_head", label: "Scontri diretti" },
  { value: "goals_for", label: "Reti fatte" },
  { value: "wins", label: "Vittorie" },
];
function humanizeRuleKey(key) {
  return String(key)
    .replace(/[_-]+/g, " ")
    .replace(/^./, (letter) => letter.toUpperCase());
}
function optionList(raw, fallback = []) {
  const source = Array.isArray(raw) && raw.length ? raw : fallback;
  return (source || []).map((item) =>
    item && typeof item === "object"
      ? { value: String(item.value), label: String(item.label ?? item.value) }
      : { value: String(item), label: String(item) },
  );
}
function formatRuleValue(key, value) {
  if (value === null || value === undefined) return "–";
  if (typeof value === "boolean") return value ? "Sì" : "No";
  if (key === "match_duration" || key === "period_minutes" || key === "duration")
    return durationText(value);
  if (key === "scoring_mode")
    return { sets: "Set", points: "Punti", time: "Tempo" }[value] || String(value);
  if (key === "standings" && typeof value === "object")
    return `Vittoria ${value.win ?? "–"} · Pareggio ${value.draw ?? "–"} · Sconfitta ${value.loss ?? "–"}`;
  if (Array.isArray(value)) return value.join(" · ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
function derivedRuleItems(variant) {
  const rules = variant?.rules || {};
  return Object.entries(rules)
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(([key, value]) => ({
      key,
      label: RULE_LABELS[key] || humanizeRuleKey(key),
      value: formatRuleValue(key, value),
    }));
}
function fallbackRuleSchema(variant) {
  const standings = variant?.standings || {};
  const drawAllowed = !variant || variant.draw_allowed !== false;
  const items = [
    {
      key: "win_points",
      label: "Punti vittoria",
      type: "number",
      min: 0,
      max: 10,
      step: 1,
      default: standings.win ?? 3,
      stages: ["round_robin", "groups"],
      help: "Punti in classifica per una vittoria.",
    },
    {
      key: "draw_points",
      label: "Punti pareggio",
      type: "number",
      min: 0,
      max: 10,
      step: 1,
      default: drawAllowed ? (standings.draw ?? 1) : 0,
      disabled: !drawAllowed,
      stages: ["round_robin", "groups"],
      help: drawAllowed
        ? "Punti in classifica per un pareggio."
        : "Questa variante non ammette pareggi: il valore resta 0.",
    },
    {
      key: "loss_points",
      label: "Punti sconfitta",
      type: "number",
      min: 0,
      max: 10,
      step: 1,
      default: standings.loss ?? 0,
      stages: ["round_robin", "groups"],
      help: "Punti in classifica per una sconfitta.",
    },
    {
      key: "tie_breaker",
      label: "Criterio a parità di punti",
      type: "select",
      options: optionList(variant?.tie_breakers, TIE_BREAKER_FALLBACK),
      default: variant?.default_tie_breaker || "goal_difference",
      stages: ["round_robin", "groups"],
      help: "Usato quando due partecipanti hanno gli stessi punti.",
    },
    {
      key: "legs",
      label: "Gare del girone",
      type: "select",
      options: [
        { value: "1", label: "Sola andata" },
        { value: "2", label: "Andata e ritorno" },
      ],
      default: 1,
      stages: ["round_robin", "groups"],
      help: "Numero di incontri tra le stesse due squadre.",
    },
    {
      key: "group_count",
      label: "Numero gironi",
      type: "select",
      options: [
        { value: "2", label: "2 gironi" },
        { value: "4", label: "4 gironi" },
        { value: "8", label: "8 gironi" },
      ],
      default: 2,
      stages: ["groups"],
      help: "I gironi devono avere lo stesso numero di partecipanti.",
    },
    {
      key: "qualifiers",
      label: "Qualificate per girone",
      type: "select",
      options: [
        { value: "1", label: "La prima" },
        { value: "2", label: "Le prime due" },
      ],
      default: 2,
      stages: ["groups"],
      help: "Quante squadre passano alla fase finale.",
    },
  ];
  return items.map((item) => ({ scope: "tournament", required: true, ...item }));
}
function variantRuleSchema(variant) {
  if (!variant) return [];
  const supplied =
    variant.config_schema || variant.rule_schema || variant.configurable;
  if (!Array.isArray(supplied) || !supplied.length)
    return fallbackRuleSchema(variant);
  return supplied
    .filter((field) => field && field.key)
    .map((field) => {
      const type = field.type || "text";
      const options = optionList(field.options, []);
      return {
        key: field.key,
        label: field.label || RULE_LABELS[field.key] || humanizeRuleKey(field.key),
        type: type === "select" && !options.length ? "text" : type,
        min: field.min,
        max: field.max,
        step: field.step,
        options,
        required: field.required !== false,
        help: field.help || "",
        default: field.default,
        scope: field.scope || "tournament",
        stages: Array.isArray(field.stages) ? field.stages : null,
        disabled: !!field.disabled,
      };
    });
}
function ruleValue(field, values, variant) {
  if (field.disabled && field.default !== undefined) return field.default;
  const value = values?.[field.key];
  if (value !== undefined && value !== null && value !== "") return value;
  if (field.default !== undefined) return field.default;
  const fromVariant = variant?.rules?.[field.key];
  return fromVariant === undefined ? "" : fromVariant;
}
function ruleConstraintText(field) {
  if (field.type === "number")
    return `Numero · ${field.min ?? 0}–${field.max ?? "∞"}`;
  if (field.type === "select")
    return field.options.map((option) => option.label).join(" · ");
  if (field.type === "checkbox") return "Sì / No";
  return "Testo";
}
function ruleInputHtml(field, value) {
  const id = "rule-" + field.key;
  const help = [
    field.help,
    field.type === "number" || field.type === "select"
      ? `Valori consentiti: ${ruleConstraintText(field)}.`
      : "",
  ]
    .filter(Boolean)
    .join(" ");
  const disabled = field.disabled ? "disabled" : "";
  const required = field.required ? "required" : "";
  if (field.type === "select") {
    return `<label>${h(field.label)}<select id="${id}" name="${h(field.key)}" ${required} ${disabled}>${field.options.map((option) => `<option value="${h(option.value)}" ${String(value) === String(option.value) ? "selected" : ""}>${h(option.label)}</option>`).join("")}</select>${help ? `<small class="field-help">${h(help)}</small>` : ""}</label>`;
  }
  if (field.type === "checkbox") {
    const checked = value === true || value === 1 || value === "1" || value === "true";
    return `<label class="checkbox"><input id="${id}" name="${h(field.key)}" type="checkbox" ${checked ? "checked" : ""} ${disabled}>${h(field.label)}${help ? `<small class="field-help">${h(help)}</small>` : ""}</label>`;
  }
  const type = field.type === "number" ? "number" : "text";
  return `<label>${h(field.label)}<input id="${id}" name="${h(field.key)}" type="${type}" value="${h(value)}" ${field.min != null ? `min="${field.min}"` : ""} ${field.max != null ? `max="${field.max}"` : ""} ${field.step != null ? `step="${field.step}"` : ""} ${required} ${disabled}>${help ? `<small class="field-help">${h(help)}</small>` : ""}</label>`;
}
function ruleWarnings(variant, values, format) {
  const warnings = [];
  for (const field of variantRuleSchema(variant)) {
    if (field.scope === "variant") continue;
    if (field.stages && !field.stages.includes(format)) continue;
    if (!field.required) continue;
    const value = values?.[field.key];
    if (value === undefined || value === null || String(value).trim() === "") {
      warnings.push(`${field.label} è obbligatorio.`);
      continue;
    }
    if (field.type === "number") {
      const number = Number(value);
      if (!Number.isFinite(number))
        warnings.push(`${field.label}: inserisci un numero.`);
      else {
        if (field.min != null && number < field.min)
          warnings.push(`${field.label}: minimo ${field.min}.`);
        if (field.max != null && number > field.max)
          warnings.push(`${field.label}: massimo ${field.max}.`);
      }
    }
  }
  if (format === "knockout" && Number(values?.legs) > 1)
    warnings.push("L’eliminazione diretta prevede una sola gara per incontro.");
  if (format === "groups") {
    const count = Number(values?.count);
    const groups = Number(values?.group_count);
    const qualifiers = Number(values?.qualifiers);
    if (
      count &&
      groups &&
      (count % groups || count / groups < Math.max(2, qualifiers))
    )
      warnings.push(
        "Con i gironi servono gruppi uguali con almeno due partecipanti e abbastanza qualificate.",
      );
  }
  return [...new Set(warnings)];
}
function ruleFieldsetHtml(
  variant,
  values,
  format,
  { id = "rule-fields", title = "Regole del torneo" } = {},
) {
  const fields = variantRuleSchema(variant)
    .filter((field) => field.scope !== "variant")
    .filter((field) => !field.stages || field.stages.includes(format));
  const warnings = ruleWarnings(variant, values, format);
  const derived = derivedRuleItems(variant);
  return `<fieldset class="rule-fieldset" id="${id}"><legend>${h(title)}</legend><p class="field-help">I valori iniziali arrivano dalla variante. Il backend valida ogni modifica: qui vedi i limiti dichiarati.</p><div class="form-grid">${fields.map((field) => ruleInputHtml(field, ruleValue(field, values, variant))).join("")}</div><div id="${id}-warnings" class="rule-warnings ${warnings.length ? "" : "hidden"}" role="alert">${warnings.map((warning) => `<p>${h(warning)}</p>`).join("")}</div>${derived.length ? `<details class="rule-derived"><summary>Regole definite dalla variante</summary><ul class="rule-list">${derived.map((item) => `<li><strong>${h(item.label)}:</strong> ${h(item.value)}</li>`).join("")}</ul><p class="field-help">Queste regole sono congelate nel torneo con la variante. Per cambiarle scegli un’altra variante.</p></details>` : ""}</fieldset>`;
}
function updateRuleWarnings(id, variant, values, format) {
  const box = document.getElementById(id + "-warnings");
  if (!box) return;
  const warnings = ruleWarnings(variant, values, format);
  box.innerHTML = warnings.map((warning) => `<p>${h(warning)}</p>`).join("");
  box.classList.toggle("hidden", !warnings.length);
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
      "Il server non risponde. Verifica che sia avviato.",
    );
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    if (res.status === 401 && path !== "/auth/login") {
      auth = { role: null, authenticated: false, teacher: null };
      renderAuthControl();
      showRoleGate("login");
    }
    const error = new Error(
      typeof body.detail === "string"
        ? body.detail
        : Array.isArray(body.detail)
          ? body.detail.map((d) => d.msg).join(" · ")
          : "Operazione non riuscita (" + res.status + ")",
    );
    error.status = res.status;
    throw error;
  }
  return res.status === 204 ? null : res.json();
}
async function safely(fn) {
  try {
    await fn();
  } catch (e) {
    if (e.status === 401) {
      auth = { role: null, authenticated: false, teacher: null };
      renderAuthControl();
      showRoleGate("login");
    }
    const box = $("#form-error");
    if ($("#modal").open && box) {
      box.textContent = e.message;
      box.classList.remove("hidden");
    } else notify(e.message, true);
  }
}
function moveItem(items, from, to) {
  const next = [...items];
  if (
    from < 0 ||
    from >= next.length ||
    to < 0 ||
    to >= next.length ||
    from === to
  )
    return next;
  const [item] = next.splice(from, 1);
  next.splice(to, 0, item);
  return next;
}
const resultProposalsAdapter = {
  // Team A: esporre le proposte e la revisione. Finché `ready` è false
  // l'interfaccia resta in attesa e non simula alcun salvataggio.
  ready: false,
  async list(tournamentId) {
    if (!this.ready) return [];
    const response = await fetch(
      `/api/tournaments/${tournamentId}/proposals?status=pending`,
      { headers: { Accept: "application/json" } },
    );
    if (!response.ok) throw await proposalError(response);
    const body = await response.json().catch(() => ({}));
    return body.proposals || [];
  },
  async propose(tournamentId, matchId, payload) {
    if (!this.ready) throw new Error("Invio proposte non ancora disponibile.");
    const response = await fetch(
      `/api/tournaments/${tournamentId}/matches/${matchId}/proposals`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) throw await proposalError(response);
    return response.json();
  },
  async decide(proposalId, action, payload = {}) {
    if (!this.ready)
      throw new Error("Revisione delle proposte non ancora disponibile.");
    const response = await fetch(`/api/proposals/${proposalId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, ...payload }),
    });
    if (!response.ok) throw await proposalError(response);
    return response.json();
  },
};
async function proposalError(response) {
  const body = await response.json().catch(() => ({}));
  const messages = {
    401: "Sessione scaduta. Accedi di nuovo.",
    403: "Non hai i permessi per questa azione.",
    404: "Partita o proposta non trovata.",
    409: "La proposta è già stata revisionata o modificata da un altro utente.",
  };
  const error = new Error(
    messages[response.status] ||
      body.detail ||
      `Operazione non riuscita (${response.status})`,
  );
  error.status = response.status;
  return error;
}
const teamOrderAdapter = {
  // Team A: esporre PATCH /api/tournaments/{id}/teams/order {team_ids:[...]}.
  // Finché non esiste, l'ordine resta solo in anteprima locale.
  ready: false,
  async save(tournamentId, teamIds) {
    if (!this.ready) return { saved: false };
    const response = await fetch(`/api/tournaments/${tournamentId}/teams/order`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team_ids: teamIds }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(
        typeof body.detail === "string"
          ? body.detail
          : "Ordine non salvato dal server",
      );
    }
    return { saved: true };
  },
};
const inviteAdapter = {
  // Team A: esporre gli inviti con token dedicati. Finché `ready` è false la
  // pagina mostra solo l'anteprima del torneo tramite il link pubblico
  // esistente: nessuna adesione viene simulata.
  ready: false,
  async resolve(token) {
    if (this.ready) {
      const response = await fetch(`/api/invites/${encodeURIComponent(token)}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw await inviteError(response);
      return response.json();
    }
    // Read-only preview through the existing public link. The flag below makes
    // the UI state explicit: the invite has not been verified server-side.
    const preview = await api("/public/" + encodeURIComponent(token));
    const tournament = preview.tournament || {};
    return {
      status: "unverified",
      kind: "tournament",
      tournament: {
        name: tournament.name,
        sport: tournament.sport,
        variant: tournament.variant,
        format: tournament.format,
        participant_kind: tournament.participant_kind,
      },
      team_count: (preview.teams || []).length,
      match_count: (preview.matches || []).length,
      organizer: null,
    };
  },
  async join(token) {
    if (!this.ready) throw new Error("Adesione non ancora disponibile.");
    const response = await fetch(
      `/api/invites/${encodeURIComponent(token)}/join`,
      { method: "POST", headers: { "Content-Type": "application/json" } },
    );
    if (!response.ok) throw await inviteError(response);
    return response.json();
  },
};
async function inviteError(response) {
  const body = await response.json().catch(() => ({}));
  const messages = {
    401: "Accedi come prof per completare l'adesione.",
    403: "Non hai i permessi per questo invito.",
    404: "Questo invito non esiste o è stato revocato.",
    409: "Sei già iscritto oppure la squadra è completa.",
    410: "Questo invito è scaduto.",
  };
  const error = new Error(
    messages[response.status] ||
      body.detail ||
      `Operazione non riuscita (${response.status})`,
  );
  error.status = response.status;
  return error;
}
const fieldsAdapter = {
  // Team A: esporre i campi del docente. Finché `ready` è false la pagina
  // mostra solo i campi citati negli incontri e non invia alcun salvataggio.
  ready: false,
  async list() {
    if (!this.ready) return [];
    const response = await fetch("/api/fields", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw await fieldError(response);
    const body = await response.json().catch(() => ({}));
    return body.fields || [];
  },
  async save(payload, fieldId = null) {
    if (!this.ready)
      throw new Error("Salvataggio dei campi non ancora disponibile.");
    const response = await fetch(
      fieldId ? `/api/fields/${fieldId}` : "/api/fields",
      {
        method: fieldId ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) throw await fieldError(response);
    return response.json();
  },
  async deactivate(fieldId) {
    if (!this.ready)
      throw new Error("Disattivazione dei campi non ancora disponibile.");
    const response = await fetch(`/api/fields/${fieldId}`, { method: "DELETE" });
    if (!response.ok) throw await fieldError(response);
    return response.json().catch(() => ({}));
  },
};
async function fieldError(response) {
  const body = await response.json().catch(() => ({}));
  const messages = {
    401: "Sessione scaduta. Accedi di nuovo.",
    403: "Non hai i permessi per gestire i campi.",
    404: "Campo non trovato.",
    409: "Esiste già un campo con questo nome.",
    422: "Controlla i dati del campo: nome, sede o sport non validi.",
  };
  const error = new Error(
    messages[response.status] ||
      body.detail ||
      `Operazione non riuscita (${response.status})`,
  );
  error.status = response.status;
  return error;
}
const calendarAdapter = {
  // Team A: esporre un aggregato del calendario con i conflitti calcolati dal
  // server. Finché `ready` è false il frontend aggrega i dettagli dei tornei
  // già esistenti e segnala solo i conflitti visibili.
  ready: false,
  async list(filters) {
    if (!this.ready) return null;
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value && value !== "all") params.set(key, value);
    }
    const response = await fetch(`/api/calendar?${params}`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw await calendarApiError(response);
    return response.json();
  },
};
async function calendarApiError(response) {
  const body = await response.json().catch(() => ({}));
  const messages = {
    401: "Sessione scaduta. Accedi di nuovo.",
    403: "Non hai i permessi per questo calendario.",
    409: "Conflitto di calendario segnalato dal server.",
  };
  const error = new Error(
    messages[response.status] ||
      body.detail ||
      `Operazione non riuscita (${response.status})`,
  );
  error.status = response.status;
  return error;
}
function enableReorder(list, onReorder, liveSelector = "#reorder-live") {
  if (!list) return;
  const live = $(liveSelector);
  const items = () => [...list.querySelectorAll("[data-reorder-item]")];
  const order = () => items().map((item) => item.dataset.id);
  const announce = (text) => {
    if (live) live.textContent = text;
  };
  const positions = () => {
    items().forEach((item, index) => {
      const slot = item.querySelector(".reorder-position, .order-position");
      if (slot) slot.textContent = String(index + 1);
    });
  };
  let dragging = null;
  let pointerId = null;
  let previous = null;
  const finish = () => {
    if (!dragging) return;
    const moved = dragging;
    dragging.classList.remove("dragging");
    list.querySelectorAll(".drag-target").forEach((item) => item.classList.remove("drag-target"));
    const index = items().indexOf(moved);
    dragging = null;
    pointerId = null;
    const before = previous;
    previous = null;
    document.body.classList.remove("reorder-active");
    positions();
    onReorder(order(), before);
    announce(
      `${moved.dataset.id} spostato in posizione ${index + 1} di ${items().length}.`,
    );
  };
  list.addEventListener("pointerdown", (event) => {
    const handle = event.target.closest("[data-drag-handle]");
    if (!handle) return;
    const item = handle.closest("[data-reorder-item]");
    if (!item) return;
    event.preventDefault();
    dragging = item;
    pointerId = event.pointerId;
    previous = order();
    item.classList.add("dragging");
    document.body.classList.add("reorder-active");
    handle.setPointerCapture(pointerId);
  });
  list.addEventListener("pointermove", (event) => {
    if (!dragging || event.pointerId !== pointerId) return;
    event.preventDefault();
    const target = document
      .elementFromPoint(event.clientX, event.clientY)
      ?.closest("[data-reorder-item]");
    if (!target || target === dragging || target.parentElement !== list) return;
    items().forEach((item) => item.classList.remove("drag-target"));
    target.classList.add("drag-target");
    const rect = target.getBoundingClientRect();
    const before = event.clientY < rect.top + rect.height / 2;
    list.insertBefore(dragging, before ? target : target.nextSibling);
    positions();
  });
  list.addEventListener("pointerup", finish);
  list.addEventListener("pointercancel", finish);
  list.addEventListener("keydown", (event) => {
    const handle = event.target.closest("[data-drag-handle]");
    if (!handle) return;
    if (!["ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
    const item = handle.closest("[data-reorder-item]");
    const current = items();
    const from = current.indexOf(item);
    let to = from;
    if (event.key === "ArrowUp") to = Math.max(0, from - 1);
    if (event.key === "ArrowDown") to = Math.min(current.length - 1, from + 1);
    if (event.key === "Home") to = 0;
    if (event.key === "End") to = current.length - 1;
    if (to === from) return;
    event.preventDefault();
    const before = order();
    const next = moveItem(current, from, to);
    next.forEach((item) => list.appendChild(item));
    positions();
    onReorder(next.map((item) => item.dataset.id), before);
    announce(
      `${item.dataset.id} spostato in posizione ${to + 1} di ${current.length}.`,
    );
  });
}
function modal(title, body, footer = "", eyebrow = "OPEN SCORE") {
  $("#modal-content").innerHTML =
    `<div class="modal-header"><div><p class="eyebrow">${eyebrow}</p><h2 id="modal-title">${title}</h2></div><button class="icon-button" data-action="close" aria-label="Chiudi finestra">${icon("close")}</button></div><div class="modal-body"><div id="form-error" class="modal-error hidden" role="alert"></div>${body}</div>${footer ? `<div class="modal-footer">${footer}</div>` : ""}`;
  if (!$("#modal").open) $("#modal").showModal();
  document.body.classList.add("modal-open");
}
function close() {
  $("#modal").close();
}
function setMenu(open) {
  $("#sidebar").classList.toggle("open", open);
  document.body.classList.toggle("menu-open", open);
  $("#mobile-menu").setAttribute("aria-expanded", String(open));
}
function stat(title, value, foot, i) {
  return `<div class="stat"><div class="stat-top">${title}${icon(i)}</div><div class="stat-number">${value}</div><div class="stat-foot">${foot}</div></div>`;
}
async function refreshList() {
  const mine = canEdit() ? "&mine=1" : "";
  list = await api("/tournaments?archived=include" + mine);
  renderNav();
}
async function loadSports() {
  const result = await api("/sports");
  sports = result.sports || [];
}
const ROLE_KEY = "openScoreRole";
const storedRole = () => localStorage.getItem(ROLE_KEY);
const setStoredRole = (value) => {
  if (value) localStorage.setItem(ROLE_KEY, value);
  else localStorage.removeItem(ROLE_KEY);
};
const canEdit = () => auth.role === "teacher" && auth.authenticated;
const canManage = () => canEdit() && data?.can_manage === true;
function requireManage() {
  if (canManage()) return true;
  if (!canEdit()) showRoleGate("login");
  else notify("Non hai i permessi su questo torneo.", true);
  return false;
}
async function loadSession() {
  try {
    const session = await api("/auth/session");
    auth = {
      role: session.authenticated ? "teacher" : null,
      authenticated: !!session.authenticated,
      teacher: session.teacher || null,
    };
  } catch {
    auth = { role: null, authenticated: false, teacher: null };
  }
  renderAuthControl();
}
function renderAuthControl() {
  if (publicToken || inviteToken) return;
  const access = canEdit()
    ? `<span class="auth-user">${icon("check")}${h(auth.teacher?.display_name || auth.teacher?.email || "Prof")}</span><button class="button ghost compact" data-action="logout">Esci</button>`
    : `<span class="auth-user">${icon("users")}Studente · sola lettura</span><button class="button ghost compact" data-action="login">Accedi come prof</button>`;
  $(".top-actions").innerHTML = `${access}<button class="button primary compact ${canEdit() ? "" : "hidden"}" data-action="new">${icon("plus")}Nuovo torneo</button>`;
  document
    .querySelectorAll(".sidebar [data-action='new']")
    .forEach((el) => el.classList.toggle("hidden", !canEdit()));
  document
    .querySelectorAll("[data-teacher-only]")
    .forEach((el) => el.classList.toggle("hidden", !canEdit()));
}
function showRoleGate(view = "choice") {
  const gate = $("#role-gate");
  if (!gate) return;
  if ($("#modal").open) close();
  gate.hidden = false;
  document.body.classList.add("role-pending");
  $("#role-options").classList.toggle("hidden", view !== "choice");
  $("#role-login-form").classList.toggle("hidden", view !== "login");
  $("#role-switch-student").classList.toggle("hidden", view !== "login");
  $("#role-title").textContent =
    view === "login" ? "Accedi come prof" : "Come vuoi entrare?";
  $("#role-intro").textContent =
    view === "login"
      ? "Inserisci l'email e la password del tuo account docente."
      : "Scegli il tuo ruolo. Potrai cambiarlo in seguito dalla barra in alto.";
  const error = $("#role-login-error");
  if (error) error.classList.add("hidden");
  if (view === "login") {
    const email = $('#role-login-form [name="email"]');
    if (email) email.focus();
  }
}
function hideRoleGate() {
  const gate = $("#role-gate");
  if (gate) gate.hidden = true;
  document.body.classList.remove("role-pending");
}
async function enterStudentMode() {
  try {
    await api("/auth/logout", { method: "POST" });
  } catch {
    // A missing session is fine: student mode is the anonymous state.
  }
  setStoredRole("student");
  auth = { role: "student", authenticated: false, teacher: null };
  hideRoleGate();
  renderAuthControl();
  if (inviteToken) {
    showInviteShell();
    await openInvite(inviteToken);
    return;
  }
  await startApp();
}
async function loginTeacher(formData) {
  const error = $("#role-login-error");
  if (error) error.classList.add("hidden");
  try {
    const result = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });
    setStoredRole("teacher");
    auth = { role: "teacher", authenticated: true, teacher: result.teacher };
    renderAuthControl();
    if (pendingInviteToken) {
      const token = pendingInviteToken;
      pendingInviteToken = null;
      showInviteShell();
      await openInvite(token);
    } else {
      await startApp();
    }
    hideRoleGate();
    notify(`Benvenuto, ${result.teacher.display_name || result.teacher.email}.`);
  } catch (e) {
    if (error) {
      error.textContent = e.message;
      error.classList.remove("hidden");
    } else notify(e.message, true);
  }
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
  $("#home-nav").classList.toggle(
    "active",
    !selectedId && !catalogMode && !calendarMode && !fieldsMode,
  );
  $("#sports-nav")?.classList.toggle("active", catalogMode);
  $("#calendar-nav")?.classList.toggle("active", calendarMode);
  $("#fields-nav")?.classList.toggle("active", fieldsMode);
}
async function dashboard() {
  if (publicToken) return;
  selectedId = null;
  data = null;
  catalogMode = false;
  calendarMode = false;
  fieldsMode = false;
  tab = "overview";
  await refreshList();
  if (location.hash) history.replaceState(null, "", location.pathname);
  $("#breadcrumb").textContent = "Panoramica";
  renderDashboard();
  if (canEdit()) safely(() => loadUpcoming());
  setMenu(false);
}
function showInviteShell() {
  hideRoleGate();
  $("#sidebar").classList.add("hidden");
  $(".app-shell").style.marginLeft = "0";
  $("#mobile-menu").classList.add("hidden");
  $(".top-actions").innerHTML =
    '<span class="context-label">INVITO · SOLA LETTURA</span>';
}
const inviteStatusCopy = {
  active: { tone: "ok", title: "Invito attivo" },
  unverified: { tone: "wait", title: "Anteprima dell’invito" },
  pending: { tone: "ok", title: "Richiesta inviata" },
  accepted: { tone: "ok", title: "Adesione confermata" },
  "already-member": { tone: "ok", title: "Sei già iscritto" },
  rejected: { tone: "warn", title: "Richiesta respinta" },
  full: { tone: "warn", title: "Squadra completa" },
  expired: { tone: "warn", title: "Invito scaduto" },
  revoked: { tone: "warn", title: "Invito revocato" },
  invalid: { tone: "warn", title: "Invito non valido" },
  error: { tone: "warn", title: "Invito non raggiungibile" },
};
function inviteMessage(state) {
  switch (state.status) {
    case "active":
      return state.requires_approval
        ? "Conferma la richiesta: il prof dovrà approvarla prima dell’inizio del torneo."
        : "Conferma per entrare subito nel torneo.";
    case "unverified":
      return "Stai vedendo l’anteprima del torneo tramite il link pubblico. L’adesione guidata non è ancora attiva: serve l’API inviti del Team A.";
    case "pending":
      return "La richiesta è stata registrata. Il prof la vedrà tra quelle da approvare.";
    case "accepted":
      return "Il server ha confermato l’adesione: il torneo è ora disponibile nella tua area.";
    case "already-member":
      return "Risulti già iscritto a questo torneo: non serve una nuova adesione.";
    case "rejected":
      return "Il prof ha respinto la richiesta. Puoi chiedere un nuovo invito.";
    case "full":
      return "Non ci sono più posti disponibili in questa squadra.";
    case "expired":
      return "Il link è scaduto. Chiedi al prof di generarne uno nuovo.";
    case "revoked":
      return "Il prof ha revocato questo invito.";
    case "invalid":
      return "Il link non corrisponde a nessun invito. Controlla di averlo copiato per intero.";
    default:
      return (
        state.message ||
        "Non è stato possibile verificare l’invito. Riprova tra poco."
      );
  }
}
async function openInvite(token) {
  selectedId = null;
  data = null;
  catalogMode = false;
  inviteState = null;
  $("#breadcrumb").textContent = "Invito";
  $("#content").innerHTML =
    '<div class="loading"><div class="spinner"></div><p>Apro l’invito…</p></div>';
  $("#content").setAttribute("aria-busy", "true");
  try {
    inviteState = await inviteAdapter.resolve(token);
  } catch (e) {
    inviteState = {
      status: e.status === 404 ? "invalid" : "error",
      message: e.message,
    };
  }
  renderInvite();
  setMenu(false);
}
function renderInvite() {
  const state = inviteState || { status: "error" };
  const meta = inviteStatusCopy[state.status] || inviteStatusCopy.error;
  const tournament = state.tournament || {};
  const team = state.kind === "team" ? state.team || null : null;
  const variant = tournament.variant ? variantFor(tournament.variant) : null;
  const sportName = tournament.sport || variant?.sport || "";
  const facts = [
    [
      "Sport",
      sportName
        ? `${sportName}${variant ? " · " + variant.name : ""}`
        : null,
    ],
    ["Formato", tournament.format ? label(tournament.format) : null],
    [
      "Partecipanti",
      Number.isFinite(state.team_count)
        ? `${state.team_count} ${tournament.participant_kind === "player" ? "giocatori" : "squadre"}`
        : null,
    ],
    [
      "Organizzatore",
      state.organizer?.display_name || state.organizer?.name || null,
    ],
    ["Squadra", team?.name],
    [
      "Posti disponibili",
      Number.isFinite(state.available_slots)
        ? String(state.available_slots)
        : null,
    ],
    [
      "Iscrizione",
      team
        ? state.requires_approval
          ? "Serve l’approvazione del prof"
          : "Automatica"
        : null,
    ],
  ].filter(([, value]) => value);
  const title =
    tournament.name || (team ? `Squadra ${team.name}` : "Invito Open Score");
  const needsLogin = !auth.authenticated;
  let action;
  if (state.status === "active") {
    action = `<div class="invite-actions"><button type="button" class="button primary" data-action="${needsLogin ? "invite-login" : "invite-join"}">${icon(needsLogin ? "users" : "check")}${needsLogin ? "Accedi per aderire" : "Conferma adesione"}</button><a class="button ghost" href="/">Torna alla home</a></div>`;
  } else if (state.status === "unverified") {
    action = `<div class="invite-actions"><button type="button" class="button primary" disabled>Adesione non ancora disponibile</button><a class="button ghost" href="/public/${h(encodeURIComponent(inviteToken))}">Apri il torneo</a></div>`;
  } else if (state.status === "error") {
    action = `<div class="invite-actions"><button type="button" class="button primary" data-action="invite-retry">Riprova</button><a class="button ghost" href="/">Torna alla home</a></div>`;
  } else {
    action = `<div class="invite-actions"><a class="button primary" href="/">Torna alla home</a></div>`;
  }
  $("#content").innerHTML = `<div class="invite-page"><section class="panel invite-card"><p class="eyebrow"><span class="line"></span> ${team ? "INVITO ALLA SQUADRA" : "INVITO AL TORNEO"}</p><h1>${h(title)}</h1>${sportName ? `<p class="invite-sport">${icon("ball")}${h(sportName)}${variant ? " · " + h(variant.name) : ""}</p>` : ""}<div class="invite-facts">${facts.map(([key, value]) => `<div><span>${key}</span><strong>${h(value)}</strong></div>`).join("")}</div><div class="invite-status ${meta.tone}"><i></i><div><strong>${meta.title}</strong><p>${h(inviteMessage(state))}</p></div></div>${action}</section><section class="panel invite-help"><h2>Come funziona</h2><ul><li>L’adesione è confermata solo dopo la risposta del server.</li><li>Se il torneo lo richiede, la richiesta resta in attesa dell’approvazione del prof.</li><li>Non mostriamo i dati personali degli altri studenti: la pagina resta in sola lettura.</li></ul></section></div>`;
  $("#content").setAttribute("aria-busy", "false");
}
async function joinInvite() {
  if (!inviteAdapter.ready) {
    notify("L’adesione guidata non è ancora attiva.", true);
    return;
  }
  if (!auth.authenticated) {
    pendingInviteToken = inviteToken;
    showRoleGate("login");
    return;
  }
  const result = await inviteAdapter.join(inviteToken);
  inviteState = { ...inviteState, ...result };
  renderInvite();
  notify(
    result.status === "pending"
      ? "Richiesta inviata al prof."
      : "Adesione confermata.",
  );
}
function renderStudentDashboard() {
  const active = list.filter((t) => !t.archived_at);
  const shown = list.filter((t) => {
    if (!t.name.toLocaleLowerCase("it").includes(search.toLocaleLowerCase("it")))
      return false;
    if (filter === "archived") return !!t.archived_at;
    if (filter === "all") return !t.archived_at;
    return !t.archived_at && t.status === filter;
  });
  const filters = [
    ["all", "Tutti"],
    ["active", "In corso"],
    ["completed", "Conclusi"],
    ["archived", "Archiviati"],
  ];
  $("#content").innerHTML =
    `<div class="page-heading"><div><p class="eyebrow"><span class="line"></span> IN SOLA LETTURA</p><h1>Segui i tornei.</h1><p>Sport, partite, classifiche e tabelloni: tutto consultabile, senza modifiche.</p></div><span class="date-note">${active.length} tornei disponibili</span></div>
 <div class="stat-grid">${stat("Tornei", active.length, "Disponibili da seguire", "trophy")}${stat("In corso", active.filter((t) => t.status === "active").length, "In campo adesso", "ball")}${stat("Conclusi", active.filter((t) => t.status === "completed").length, "Già decisi", "check")}</div>
 <section><div class="section-header"><div><h2>Esplora i tornei <span class="muted">${active.length.toString().padStart(2, "0")}</span></h2><p class="section-sub">Apri un torneo per vedere partite, classifica e tabellone.</p></div><div class="filters" aria-label="Filtra tornei">${filters.map(([v, l]) => `<button class="filter ${filter === v ? "active" : ""}" data-filter="${v}" aria-pressed="${filter === v}">${l}</button>`).join("")}</div></div>
 <div class="tournament-grid">${shown.map(eventCard).join("") || `<div class="panel empty">${icon("trophy")}<h2>Nessun torneo, per ora.</h2><p>${list.length ? "Nessun torneo con questo filtro." : "Quando un prof crea un torneo lo troverai qui."}</p></div>`}</div></section>
 <div class="note-banner">${icon("spark")}<div><strong>Vuoi organizzare anche tu?</strong><p>Per creare e gestire i tornei serve un account docente.</p></div><button class="text-button" data-action="login">Accedi come prof</button></div>`;
  $("#content").setAttribute("aria-busy", "false");
}
function renderDashboard() {
  if (!canEdit()) return renderStudentDashboard();
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
 <section class="hero" aria-label="Inizia a organizzare"><div class="hero-copy"><p class="eyebrow">IL PROSSIMO FISCHIO D’INIZIO</p><h2>Lo sport unisce.<br><em>Organizzarlo è semplice.</em></h2><p>Dalle partite in palestra alla coppa d’istituto: squadre, incontri e risultati, tutti nello stesso posto.</p><div class="hero-buttons">${canEdit() ? button("Crea il tuo torneo", "new", "primary", "plus") : button("Accedi per organizzare", "login", "primary", "check")}${button("Sport e regole", "catalog", "ghost", "ball")}</div></div><div class="hero-art" aria-hidden="true"><div class="court"><div class="court-circle"></div></div><div class="hero-score"><div class="score-kicker">IL TUO PROSSIMO TORNEO <span>● SI GIOCA</span></div><div class="score-line">${avatar("A", 2)}La tua squadra <b>—</b></div><div class="score-line">${avatar("B", 1)}Una nuova sfida <b>—</b></div></div><div class="hero-sticker">${icon("trophy")}</div></div></section>
 <div class="stat-grid">${stat("Tornei creati", active.length, "Tutte le tue competizioni", "trophy")}${stat("Partecipanti", totalTeams, "Pronti a scendere in campo", "users")}${stat("Tornei in corso", active.filter((t) => t.status === "active").length, "Il gioco continua", "ball")}${stat("Risultati registrati", done, "Ogni partita conta", "check")}</div>
 ${canEdit() ? `<section class="upcoming-section" aria-label="Prossime partite"><div class="section-header"><div><h2>Prossime partite</h2><p class="section-sub">I prossimi incontri da giocare o da programmare.</p></div></div><div id="upcoming-matches" class="upcoming-grid"><p class="muted">Caricamento prossime partite…</p></div></section>` : ""}
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
 <div class="tournament-grid">${shown.map(eventCard).join("") || `<div class="panel empty">${icon("trophy")}<h2>Il campo è libero.</h2><p>${filter === "archived" ? "Nessun torneo archiviato, per ora." : list.length ? "Nessun torneo con questo filtro." : "Crea il primo torneo per iniziare."}</p>${filter === "archived" ? "" : canEdit() ? button("Nuovo torneo", "new", "primary") : button("Accedi per organizzare", "login", "primary", "check")}</div>`}</div></section>
 <div class="note-banner">${icon("spark")}<div><strong>Un progetto aperto, anche alle tue idee.</strong><p>Il prossimo passo lo scegliamo insieme.</p></div><button class="text-button" data-action="project">Il progetto ${icon("arrow")}</button></div>`;
  $("#content").setAttribute("aria-busy", "false");
}
async function loadUpcoming() {
  const box = $("#upcoming-matches");
  if (!box) return;
  const targets = list.filter((t) => !t.archived_at && t.can_manage);
  if (!targets.length) {
    box.innerHTML = '<p class="muted">Nessun torneo attivo da seguire.</p>';
    return;
  }
  const upcoming = [];
  const now = Date.now();
  await Promise.all(
    targets.map(async (t) => {
      try {
        const detail = await api("/tournaments/" + t.id);
        const teams = detail.teams || [];
        for (const m of detail.matches || []) {
          if (m.is_bye || m.status !== "ready") continue;
          const time = m.scheduled_at ? new Date(m.scheduled_at).getTime() : null;
          if (time && time < now) continue;
          upcoming.push({
            id: t.id,
            tournament: detail.tournament.name,
            home: teams.find((x) => x.id === m.home_team_id)?.name || "Da definire",
            away: teams.find((x) => x.id === m.away_team_id)?.name || "Da definire",
            scheduled_at: m.scheduled_at,
            location: m.location,
          });
        }
      } catch {
        // Un torneo non leggibile non blocca il riepilogo.
      }
    }),
  );
  upcoming.sort((a, b) => {
    const ta = a.scheduled_at ? new Date(a.scheduled_at).getTime() : Infinity;
    const tb = b.scheduled_at ? new Date(b.scheduled_at).getTime() : Infinity;
    return ta - tb;
  });
  box.innerHTML = upcoming.length
    ? upcoming
        .slice(0, 5)
        .map(
          (m) =>
            `<button class="upcoming-row" data-open="${m.id}"><span class="upcoming-time">${m.scheduled_at ? h(dateText(m.scheduled_at)) : "Da programmare"}</span><span class="upcoming-match">${h(m.home)} <b>—</b> ${h(m.away)}</span><span class="upcoming-tournament">${h(m.tournament)}${m.location ? " · " + h(m.location) : ""}</span></button>`,
        )
        .join("")
    : '<p class="muted">Nessuna partita in arrivo. Genera gli incontri o programma le partite.</p>';
}
function loadingMarkup(text) {
  return `<div class="loading"><div class="spinner"></div><p>${h(text)}</p></div>`;
}
// ---------------------------------------------------------------------------
// Campi
// ---------------------------------------------------------------------------
function fieldSportNames(field) {
  const raw = Array.isArray(field?.sports) ? field.sports : [];
  return raw
    .map((sport) => (typeof sport === "string" ? sport : sport?.name))
    .filter(Boolean);
}
function fieldStatusLabel(field) {
  return field.active === false ? "Disattivato" : "Attivo";
}
async function openFields() {
  if (!canEdit()) {
    notify("Serve un account prof per gestire i campi.", true);
    await dashboard();
    return;
  }
  catalogMode = false;
  calendarMode = false;
  fieldsMode = true;
  selectedId = null;
  data = null;
  tab = "overview";
  $("#breadcrumb").textContent = "Campi";
  history.replaceState(null, "", location.pathname + "#/fields");
  $("#content").innerHTML = loadingMarkup("Carico i campi…");
  fieldsError = "";
  try {
    fieldsCache = await fieldsAdapter.list();
  } catch (e) {
    fieldsError = e.message;
    fieldsCache = [];
  }
  if (!calendarState.loadedAt) {
    try {
      await reloadCalendar();
    } catch (e) {
      calendarError = e.message;
    }
  }
  renderFields();
  setMenu(false);
}
function fieldCard(field) {
  const sportsList = fieldSportNames(field);
  const inactive = field.active === false;
  return `<article class="field-card ${inactive ? "inactive" : ""}"><div class="field-card-top"><div class="sport-symbol">${icon("field")}</div><span class="tag ${inactive ? "archived" : "active"}"><i></i>${fieldStatusLabel(field)}</span></div><h3>${h(field.name || "Campo senza nome")}</h3><p class="field-venue">${icon("ball")}${h(field.venue || "Sede da definire")}</p>${field.description ? `<p class="field-description">${h(field.description)}</p>` : ""}<div class="catalog-chips">${sportsList.map((sport) => `<span>${h(sport)}</span>`).join("") || "<span>Sport da assegnare</span>"}</div>${field.availability ? `<p class="field-availability">${icon("clock")}${h(field.availability)}</p>` : ""}<div class="field-actions"><button type="button" class="text-button" data-action="field-edit" data-field="${field.id}">Modifica ${icon("edit")}</button>${inactive ? "" : `<button type="button" class="text-button danger-text" data-action="field-toggle" data-field="${field.id}">Disattiva</button>`}</div></article>`;
}
function renderFields() {
  const venues = calendarState.fields || [];
  const programmed = (calendarState.events || []).filter(
    (event) => event.scheduled_at && event.location,
  );
  const active = fieldsCache.filter((field) => field.active !== false).length;
  const heading = `<div class="page-heading"><div><p class="eyebrow"><span class="line"></span> CAMPI E PALESTRE</p><h1>Dove si gioca.</h1><p>Campi, sedi e disponibilità: scegli il campo quando programmi una partita.</p></div><button type="button" class="button primary" data-action="field-new">${icon("plus")}Nuovo campo</button></div>`;
  const notice = fieldsError
    ? `<div class="panel error-page"><h2>Impossibile caricare i campi</h2><p>${h(fieldsError)}</p><button type="button" class="button" data-action="fields-refresh">Riprova</button></div>`
    : fieldsAdapter.ready
      ? ""
      : `<div class="note-banner">${icon("spark")}<div><strong>API campi in attesa</strong><p>Il Team A esporrà <code>GET /api/fields</code> e le operazioni di creazione, modifica e disattivazione. Nel frattempo vedi i campi citati negli incontri e puoi preparare la scheda di un nuovo campo senza salvare.</p></div><button type="button" class="text-button" data-action="field-new">Prepara una scheda ${icon("arrow")}</button></div>`;
  const empty = `<div class="panel empty">${icon("field")}<h2>Nessun campo configurato.</h2><p>${fieldsAdapter.ready ? "Crea il primo campo per iniziare a programmare le partite." : "La gestione dei campi arriverà con l’API del Team A. Intanto puoi usare i campi citati negli incontri."}</p>${fieldsAdapter.ready ? button("Nuovo campo", "field-new", "primary", "plus") : ""}</div>`;
  const venueRows = venues
    .map((venue) => {
      const count = programmed.filter((event) => event.location === venue).length;
      return `<div class="venue-row"><strong>${h(venue)}</strong><span>${count} ${count === 1 ? "incontro programmato" : "incontri programmati"}</span></div>`;
    })
    .join("");
  $("#content").innerHTML = `${heading}<div class="stat-grid">${stat("Campi attivi", active, "Configurati e disponibili", "field")}${stat("Campi citati", venues.length, "Usati negli incontri", "ball")}${stat("Incontri con campo", programmed.length, "Già assegnati a una sede", "calendar")}</div>${notice}<section><div class="section-header"><div><h2>Campi del docente</h2><p class="section-sub">Nome, sede, sport supportati e disponibilità.</p></div><span class="tag archived"><i></i>${fieldsAdapter.ready ? "Sincronizzato" : "In attesa API"}</span></div><div class="field-grid">${fieldsCache.map(fieldCard).join("") || empty}</div></section><section class="panel"><div class="section-header"><div><h2>Campi citati negli incontri</h2><p class="section-sub">Testi di campo salvati finora, ricavati dagli incontri reali.</p></div></div>${venueRows ? `<div class="venue-list">${venueRows}</div>` : '<p class="muted">Nessun incontro ha ancora un campo assegnato.</p>'}</section>`;
  $("#content").setAttribute("aria-busy", "false");
}
function fieldModal(field = null) {
  if (!canEdit()) {
    loginModal();
    return;
  }
  const editing = !!field;
  const sportsList = sports.map((sport) => sport.name);
  const selected = new Set(fieldSportNames(field));
  modal(
    editing ? "Modifica il campo." : "Un nuovo campo.",
    `<form id="field-form" data-id="${editing ? field.id : ""}"><div class="form-grid"><label class="full">Nome<input name="name" required minlength="2" maxlength="80" value="${h(field?.name || "")}" placeholder="Es. Palestra A"></label><label>Sede<input name="venue" maxlength="120" value="${h(field?.venue || "")}" placeholder="Es. Plesso centrale"></label><label>Disponibilità<input name="availability" maxlength="160" value="${h(field?.availability || "")}" placeholder="Es. Lun–Ven 8:00–13:00"></label><label class="full">Descrizione<textarea name="description" maxlength="400" rows="2" placeholder="Note su accesso, attrezzatura, capienza…">${h(field?.description || "")}</textarea></label></div><fieldset class="field-checkboxes"><legend>Sport supportati</legend>${sportsList.map((name) => `<label class="checkbox"><input type="checkbox" name="sports" value="${h(name)}" ${selected.has(name) ? "checked" : ""}>${h(name)}</label>`).join("")}</fieldset>${editing ? `<label class="checkbox"><input type="checkbox" name="active" ${field.active === false ? "" : "checked"}>Campo attivo</label>` : ""}${fieldsAdapter.ready ? "" : '<p class="field-help">Anteprima: l’API campi non è ancora attiva, quindi il salvataggio verrà bloccato senza inviare dati.</p>'}</form>`,
    `${button("Annulla", "close", "ghost")}<button type="submit" form="field-form" class="button primary">${icon("check")}${fieldsAdapter.ready ? "Salva campo" : "Verifica anteprima"}</button>`,
    "CAMPI",
  );
}
function knownFieldOptions() {
  const names = new Set();
  for (const field of fieldsCache)
    if (field.active !== false && field.name) names.add(field.name);
  for (const event of calendarState.events || [])
    if (event.location) names.add(event.location);
  for (const match of data?.matches || [])
    if (match.location && match.location.trim()) names.add(match.location.trim());
  return [...names].sort((a, b) => a.localeCompare(b, "it"));
}
function fieldPickerHtml() {
  const names = knownFieldOptions();
  if (!names.length) return "";
  return `<datalist id="known-fields">${names.map((name) => `<option value="${h(name)}"></option>`).join("")}</datalist>`;
}
// ---------------------------------------------------------------------------
// Calendario
// ---------------------------------------------------------------------------
function dayKey(iso) {
  return new Date(iso).toLocaleDateString("sv-SE", { timeZone: "Europe/Rome" });
}
function dayLabel(key) {
  const date = new Date(key + "T12:00:00Z");
  const text = new Intl.DateTimeFormat("it-IT", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Europe/Rome",
  }).format(date);
  return text.charAt(0).toUpperCase() + text.slice(1);
}
function timeLabel(iso) {
  return new Intl.DateTimeFormat("it-IT", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Rome",
  }).format(new Date(iso));
}
function calendarEventStatus(event) {
  if (!event.scheduled_at) return { cls: "draft", label: "Da programmare" };
  if (event.status === "completed") return { cls: "completed", label: "Giocata" };
  if (event.status === "ready") return { cls: "active", label: "Da giocare" };
  return { cls: "draft", label: "In attesa" };
}
function buildCalendarEvents(details) {
  const events = [];
  for (const detail of details) {
    const tournament = detail.tournament || {};
    const teams = new Map((detail.teams || []).map((team) => [team.id, team.name]));
    const duration =
      Number(detail.variant_config?.match_duration) ||
      Number(detail.rules?.match_duration) ||
      20;
    for (const match of detail.matches || []) {
      if (match.is_bye) continue;
      events.push({
        id: `${tournament.id}-${match.id}`,
        tournamentId: tournament.id,
        tournamentName: tournament.name,
        matchId: match.id,
        homeTeamId: match.home_team_id,
        awayTeamId: match.away_team_id,
        home: teams.get(match.home_team_id) || "Da definire",
        away: teams.get(match.away_team_id) || "Da definire",
        round: match.round_no,
        kind: match.kind,
        scheduled_at: match.scheduled_at || null,
        location: (match.location || "").trim(),
        fieldId: null,
        duration: Number(match.duration) || duration,
        status: match.status || "waiting",
        score:
          match.home_score !== null ? `${match.home_score}–${match.away_score}` : null,
        group: (detail.groups || []).find((group) => group.id === match.group_id)?.name || null,
      });
    }
  }
  return events;
}
function normalizeCalendarEvent(event) {
  return {
    id: event.id || `${event.tournament_id}-${event.match_id}`,
    tournamentId: event.tournament_id ?? event.tournamentId,
    tournamentName: event.tournament_name ?? event.tournamentName ?? "Torneo",
    matchId: event.match_id ?? event.matchId,
    homeTeamId: event.home_team_id ?? null,
    awayTeamId: event.away_team_id ?? null,
    home: event.home ?? event.home_name ?? "Da definire",
    away: event.away ?? event.away_name ?? "Da definire",
    round: event.round_no ?? null,
    kind: event.kind || "round_robin",
    scheduled_at: event.scheduled_at || null,
    location: (event.field || event.location || "").trim(),
    fieldId: event.field_id ?? null,
    duration: Number(event.duration) || 20,
    status: event.status || "waiting",
    score: event.score || null,
    group: event.group || null,
  };
}
function intervalFor(event) {
  const start = new Date(event.scheduled_at).getTime();
  return [start, start + Math.max(1, Number(event.duration) || 20) * 60000];
}
function sharesTeam(a, b) {
  if (a.tournamentId !== b.tournamentId) return false;
  const ids = (event) => [event.homeTeamId, event.awayTeamId].filter(Boolean);
  return ids(a).some((id) => ids(b).includes(id));
}
function detectCalendarConflicts(events) {
  const scheduled = events.filter((event) => event.scheduled_at);
  const conflicts = [];
  for (let i = 0; i < scheduled.length; i++) {
    for (let j = i + 1; j < scheduled.length; j++) {
      const a = scheduled[i];
      const b = scheduled[j];
      const [aStart, aEnd] = intervalFor(a);
      const [bStart, bEnd] = intervalFor(b);
      if (!(aStart < bEnd && bStart < aEnd)) continue;
      const windowText = `${timeLabel(a.scheduled_at)}–${timeLabel(
        new Date(Math.max(aEnd, bEnd)).toISOString(),
      )}`;
      const sameField =
        a.location &&
        b.location &&
        a.location.toLocaleLowerCase("it") === b.location.toLocaleLowerCase("it");
      if (sameField) {
        conflicts.push({
          kind: "field",
          aId: a.id,
          bId: b.id,
          aMatchId: a.matchId,
          bMatchId: b.matchId,
          message: `Campo “${a.location}” · ${windowText}: ${a.home} – ${a.away} e ${b.home} – ${b.away} si sovrappongono.`,
        });
      }
      if (sharesTeam(a, b)) {
        conflicts.push({
          kind: "team",
          aId: a.id,
          bId: b.id,
          aMatchId: a.matchId,
          bMatchId: b.matchId,
          message: `Stessa squadra in due partite sovrapposte · ${windowText}: ${a.home} – ${a.away} e ${b.home} – ${b.away}.`,
        });
      }
    }
  }
  return conflicts;
}
async function reloadCalendar() {
  if (calendarLoading) return;
  calendarLoading = true;
  calendarError = "";
  try {
    await refreshList();
    const remote = await calendarAdapter.list(calendarFilters);
    if (remote) {
      const events = (remote.events || []).map(normalizeCalendarEvent);
      calendarState = {
        events,
        conflicts: remote.conflicts || [],
        teams: remote.teams || [],
        fields:
          remote.fields ||
          [...new Set(events.map((event) => event.location).filter(Boolean))],
        loadedAt: Date.now(),
        source: "server",
      };
    } else {
      const details = [];
      for (const tournament of list.filter((item) => !item.archived_at)) {
        try {
          details.push(await api("/tournaments/" + tournament.id));
        } catch {
          // Un torneo non leggibile non blocca il calendario.
        }
      }
      const events = buildCalendarEvents(details);
      calendarState = {
        events,
        conflicts: detectCalendarConflicts(events),
        teams: details.flatMap((detail) =>
          (detail.teams || []).map((team) => ({
            tournamentId: detail.tournament.id,
            id: team.id,
            name: team.name,
          })),
        ),
        fields: [...new Set(events.map((event) => event.location).filter(Boolean))].sort(
          (a, b) => a.localeCompare(b, "it"),
        ),
        loadedAt: Date.now(),
        source: "client",
      };
    }
  } catch (e) {
    calendarError = e.message;
  } finally {
    calendarLoading = false;
  }
  if (calendarMode) renderCalendar();
}
function filterCalendarEvents(events) {
  const filters = calendarFilters;
  return events.filter((event) => {
    if (filters.tournament !== "all" && String(event.tournamentId) !== filters.tournament)
      return false;
    if (filters.team !== "all") {
      const [tournamentId, teamId] = filters.team.split(":");
      if (String(event.tournamentId) !== tournamentId) return false;
      if (String(event.homeTeamId) !== teamId && String(event.awayTeamId) !== teamId)
        return false;
    }
    if (filters.day) {
      if (!event.scheduled_at || dayKey(event.scheduled_at) !== filters.day) return false;
    }
    if (filters.field !== "all" && event.location !== filters.field) return false;
    if (filters.status !== "all") {
      const bucket = !event.scheduled_at
        ? "unscheduled"
        : event.status === "completed"
          ? "played"
          : "to-play";
      if (bucket !== filters.status) return false;
    }
    return true;
  });
}
function calendarConflictMessages(event, conflicts) {
  return conflicts
    .filter((conflict) => {
      const eventIds = [conflict.aId, conflict.bId].filter(Boolean).map(String);
      if (eventIds.length) return eventIds.includes(String(event.id));
      const matchIds = [conflict.match_id, conflict.other_match_id]
        .filter((value) => value != null)
        .map(String);
      return matchIds.includes(String(event.matchId));
    })
    .map((conflict) => conflict.message || "Sovrapposizione di orario.");
}
function calendarEventRow(event, conflicts) {
  const status = calendarEventStatus(event);
  const messages = calendarConflictMessages(event, conflicts);
  const manageable =
    canEdit() &&
    (list.find((tournament) => tournament.id === event.tournamentId)?.can_manage !== false);
  return `<article class="calendar-event ${messages.length ? "has-conflict" : ""}"><div class="calendar-time"><strong>${event.scheduled_at ? h(timeLabel(event.scheduled_at)) : "—"}</strong><small>${event.duration ? h(durationText(event.duration)) : ""}</small></div><div class="calendar-main"><p class="calendar-title">${h(event.home)} <b>—</b> ${h(event.away)}</p><p class="calendar-meta">${h(event.tournamentName)}${event.location ? " · " + h(event.location) : ""}${event.group ? " · " + h(event.group) : ""}</p>${messages.map((message) => `<p class="calendar-conflict">${icon("spark")}${h(message)}</p>`).join("")}</div><div class="calendar-side"><span class="tag ${status.cls}">${status.label}</span>${event.score ? `<span class="calendar-score">${h(event.score)}</span>` : ""}${manageable ? `<button type="button" class="button compact" data-action="calendar-open" data-tournament="${event.tournamentId}" data-match="${event.matchId}">${event.scheduled_at ? "Modifica" : "Programma"}</button>` : ""}</div></article>`;
}
function renderCalendar() {
  if (!calendarMode) return;
  const events = filterCalendarEvents(calendarState.events);
  const scheduled = events
    .filter((event) => event.scheduled_at)
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));
  const unscheduled = events
    .filter((event) => !event.scheduled_at)
    .sort((a, b) => (a.round || 0) - (b.round || 0));
  const visibleEvents = new Set(events.map((event) => String(event.id)));
  const visibleMatches = new Set(events.map((event) => String(event.matchId)));
  const conflicts = (calendarState.conflicts || []).filter((conflict) => {
    const eventIds = [conflict.aId, conflict.bId].filter(Boolean).map(String);
    if (eventIds.length) return eventIds.some((id) => visibleEvents.has(id));
    const matchIds = [conflict.match_id, conflict.other_match_id]
      .filter((value) => value != null)
      .map(String);
    return !matchIds.length || matchIds.some((id) => visibleMatches.has(id));
  });
  const days = new Map();
  for (const event of scheduled) {
    const key = dayKey(event.scheduled_at);
    if (!days.has(key)) days.set(key, []);
    days.get(key).push(event);
  }
  const daySections = [...days.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(
      ([key, items]) =>
        `<section class="calendar-day"><h2>${h(dayLabel(key))}</h2><div class="calendar-list">${items.map((event) => calendarEventRow(event, conflicts)).join("")}</div></section>`,
    )
    .join("");
  const unscheduledSection = unscheduled.length
    ? `<section class="calendar-day"><h2>Da programmare <span class="muted">${unscheduled.length}</span></h2><div class="calendar-list">${unscheduled.map((event) => calendarEventRow(event, conflicts)).join("")}</div></section>`
    : "";
  const tournamentOptions = [
    ...new Map(
      calendarState.events.map((event) => [event.tournamentId, event.tournamentName]),
    ).entries(),
  ].sort((a, b) => String(a[1]).localeCompare(String(b[1]), "it"));
  const teamOptions = calendarState.teams
    .filter(
      (team) =>
        calendarFilters.tournament === "all" ||
        String(team.tournamentId) === calendarFilters.tournament,
    )
    .sort((a, b) => a.name.localeCompare(b.name, "it"));
  const filterPanel = `<div class="calendar-filters" role="group" aria-label="Filtra il calendario"><label>Torneo<select data-calendar-filter="tournament"><option value="all">Tutti i tornei</option>${tournamentOptions.map(([id, name]) => `<option value="${id}" ${calendarFilters.tournament === String(id) ? "selected" : ""}>${h(name)}</option>`).join("")}</select></label><label>Squadra<select data-calendar-filter="team"><option value="all">Tutte le squadre</option>${teamOptions.map((team) => `<option value="${team.tournamentId}:${team.id}" ${calendarFilters.team === `${team.tournamentId}:${team.id}` ? "selected" : ""}>${h(team.name)} · ${h(tournamentOptions.find(([id]) => String(id) === String(team.tournamentId))?.[1] || "")}</option>`).join("")}</select></label><label>Giorno<input type="date" data-calendar-filter="day" value="${h(calendarFilters.day)}"></label><label>Campo<select data-calendar-filter="field"><option value="all">Tutti i campi</option>${(calendarState.fields || []).map((field) => `<option value="${h(field)}" ${calendarFilters.field === field ? "selected" : ""}>${h(field)}</option>`).join("")}</select></label><label>Stato<select data-calendar-filter="status">${[
    ["all", "Tutti"],
    ["to-play", "Da giocare"],
    ["played", "Giocate"],
    ["unscheduled", "Da programmare"],
  ]
    .map(([value, text]) => `<option value="${value}" ${calendarFilters.status === value ? "selected" : ""}>${text}</option>`)
    .join("")}</select></label><button type="button" class="text-button" data-action="calendar-reset">Azzera filtri</button></div>`;
  const conflictPanel = conflicts.length
    ? `<div class="calendar-conflict-panel" role="status"><div class="section-header"><div><h2>${conflicts.length} ${conflicts.length === 1 ? "conflitto da controllare" : "conflitti da controllare"}</h2><p class="section-sub">${calendarState.source === "server" ? "Segnalati dal server." : "Rilevati dal browser incrociando campo e orario: il server resta l’unica fonte autorevole."}</p></div><span class="tag archived"><i></i>${calendarState.source === "server" ? "Server" : "Anteprima client"}</span></div><ul>${conflicts.map((conflict) => `<li>${h(conflict.message || "Sovrapposizione di orario.")}</li>`).join("")}</ul></div>`
    : "";
  const notice = calendarError
    ? `<div class="panel error-page"><h2>Calendario non aggiornato</h2><p>${h(calendarError)}</p><button type="button" class="button" data-action="calendar-refresh">Riprova</button></div>`
    : calendarState.source === "client"
      ? '<p class="field-help">Il calendario aggrega i tornei che puoi leggere. I conflitti sono un’anteprima del browser; l’API calendario del Team A fornirà la verifica definitiva.</p>'
      : "";
  const heading = `<div class="page-heading"><div><p class="eyebrow"><span class="line"></span> CALENDARIO</p><h1>Tutto il gioco, giorno per giorno.</h1><p>Partite, orari, campi e conflitti in un’unica vista.</p></div><button type="button" class="button" data-action="calendar-refresh">${icon("refresh")}Aggiorna</button></div>`;
  $("#content").innerHTML = `${heading}<div class="stat-grid">${stat("In calendario", scheduled.length, "Con data e ora", "calendar")}${stat("Da programmare", unscheduled.length, "Ancora senza orario", "clock")}${stat("Giornate", days.size, "Giorni con partite", "grid")}${stat("Conflitti", conflicts.length, "Da verificare", "spark")}</div>${notice}${conflictPanel}${filterPanel}${daySections}${unscheduledSection}${events.length ? "" : '<div class="panel empty">' + icon("calendar") + "<h2>Nessun incontro con questi filtri.</h2><p>Prova ad azzerare i filtri o programma nuove partite.</p></div>"}`;
  $("#content").setAttribute("aria-busy", "false");
}
async function openCalendar() {
  catalogMode = false;
  fieldsMode = false;
  calendarMode = true;
  selectedId = null;
  data = null;
  tab = "overview";
  $("#breadcrumb").textContent = "Calendario";
  history.replaceState(null, "", location.pathname + "#/calendar");
  $("#content").innerHTML = loadingMarkup("Preparo il calendario…");
  await reloadCalendar();
  setMenu(false);
}
function updateScheduleConflictHint() {
  const form = $("#schedule-form");
  const box = $("#schedule-conflict");
  if (!form || !box || !data) return;
  const match = data.matches.find((item) => item.id === Number(form.dataset.id));
  const at = form.querySelector('[name="scheduled_at"]')?.value;
  const location = (form.querySelector('[name="location"]')?.value || "").trim();
  const duration =
    Number(form.querySelector('[name="duration"]')?.value) ||
    Number(match?.duration) ||
    currentVariant()?.match_duration ||
    20;
  if (!match || !at || !location) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  const start = new Date(at).getTime();
  const end = start + duration * 60000;
  const conflicts = (data.matches || []).filter((other) => {
    if (other.id === match.id || other.is_bye || !other.scheduled_at) return false;
    if (
      (other.location || "").trim().toLocaleLowerCase("it") !==
      location.toLocaleLowerCase("it")
    )
      return false;
    const otherStart = new Date(other.scheduled_at).getTime();
    const otherEnd = otherStart + (Number(other.duration) || 20) * 60000;
    return start < otherEnd && otherStart < end;
  });
  if (!conflicts.length) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  box.textContent = `Attenzione: ${
    conflicts.length === 1
      ? "un’altra partita occupa"
      : conflicts.length + " altre partite occupano"
  } questo campo nello stesso orario. Il server deciderà se il salvataggio è valido.`;
  box.classList.remove("hidden");
}
function scheduleError(error) {
  if (error.status === 409 && !/conflitt/i.test(error.message))
    return new Error("Conflitto di calendario: " + error.message);
  return error;
}
function eventCard(t, i) {
  const progress = t.progress.total
    ? Math.round((t.progress.completed / t.progress.total) * 100)
    : 0;
  return `<article class="event-card ${t.archived_at ? "archived" : ""}"><div class="event-card-top"><div class="sport-symbol ${["", "gold", "blue", "rose"][i % 4]}">${icon(t.format === "knockout" ? "trophy" : t.format === "groups" ? "grid" : "ball")}</div>${t.archived_at ? '<span class="tag archived"><i></i>Archiviato</span>' : `<span class="tag ${t.status}"><i></i>${stateLabel(t.status)}</span>`}${!t.can_manage && canEdit() ? '<span class="tag archived"><i></i>Solo lettura</span>' : ""}</div><h3>${h(t.name)}</h3><p class="event-format">${h(t.sport)}${t.variant ? ` · ${h(variantFor(t.variant)?.name || t.variant)}` : ""} <span aria-hidden="true">/</span> ${label(t.format)}</p><div class="event-meta"><span>${icon("users")}${t.team_count} ${t.participant_kind === "team" ? "squadre" : "giocatori"}</span><span>${icon("calendar")}${t.progress.total} incontri${t.format === "groups" ? " · gironi" : ""}</span></div><div class="progress-track" role="progressbar" aria-label="Incontri completati" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"><span style="width:${progress}%"></span></div><div class="progress-copy"><span>${t.progress.completed} di ${t.progress.total} incontri completati</span><span>${progress}%</span></div><div class="event-card-footer"><div class="avatar-stack"><span>${h(t.sport.slice(0, 1))}</span><span>OS</span><small>Il nostro torneo</small></div><div class="card-actions"><button class="text-button" data-open="${t.id}">Apri ${icon("arrow")}</button>${t.archived_at && t.can_manage ? `<button class="text-button" data-restore="${t.id}">Ripristina ${icon("refresh")}</button>` : ""}</div></div></article>`;
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
  calendarMode = false;
  fieldsMode = false;
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
  setMenu(false);
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
    const derived = derivedRuleItems(v).map(
      (item) => `${item.label}: ${item.value}`,
    );
    const configurable = variantRuleSchema(v).filter(
      (field) => field.scope !== "variant",
    );
    body = `<button class="back-link" data-action="catalog" data-catalog-sport="${h(v.sport)}">${icon("back")} ${h(v.sport)}</button><div class="page-heading"><div><p class="eyebrow"><span class="line"></span> ${h(v.sport)} / ${h(v.name)}</p><h1>${h(v.name)}</h1><p>${h(v.description)}</p></div><div class="toolbar">${canEdit() ? `<button class="button primary" data-action="new-variant" data-sport="${h(v.sport)}" data-variant="${h(v.slug)}">${icon("plus")}Crea torneo</button>` : button("Accedi per organizzare", "login", "primary", "check")}</div></div><div class="stat-grid">${rows.map(([label, value]) => stat(label, value, "", "ball")).join("")}</div><div class="catalog-detail-grid"><section class="panel"><div class="section-header"><h2>Regolamento</h2><span class="panel-label">${h(v.participant_kind === "team" ? "A SQUADRE" : "INDIVIDUALE")}</span></div><div class="regulation-copy">${v.regulation.split(/\n\n+/).map((p) => `<p>${h(p)}</p>`).join("")}</div></section><section class="panel"><h2>In sintesi</h2><details class="result-schedule" open><summary>Dettagli di gioco</summary><ul class="rule-list">${derived.map((item) => `<li>${h(item)}</li>`).join("")}</ul></details>${configurable.length ? `<h2>Parametri configurabili</h2><div class="rule-config-list">${configurable.map((field) => `<div class="rule-config-row"><strong>${h(field.label)}</strong><span>${h(ruleConstraintText(field))}</span></div>`).join("")}</div><p class="field-help">I limiti e i valori ammessi arrivano dai metadati della variante; il backend resta l’autorità sul salvataggio.</p>` : ""}<div class="catalog-cta">${canEdit() ? `<button class="button primary" data-action="new-variant" data-sport="${h(v.sport)}" data-variant="${h(v.slug)}">${icon("plus")}Crea torneo ${h(v.name)}</button>` : ""}<button class="button ghost" data-action="catalog">Torna al catalogo</button></div></section></div>`;
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
  calendarMode = false;
  fieldsMode = false;
  if (location.hash) history.replaceState(null, "", location.pathname);
  if (!keepTab) tab = "overview";
  if (!publicToken) await refreshList();
  $("#breadcrumb").textContent = publicToken
    ? "Torneo condiviso"
    : data.tournament.name;
  setMenu(false);
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
  const teamMode = t.participant_kind === "team";
  if (teamMode && canEdit()) tabs.splice(2, 0, ["students", "Studenti"]);
  if (canManage()) {
    const at = tabs.findIndex(([key]) => key === "matches") + 1;
    tabs.splice(at, 0, ["approvals", "Da verificare"]);
  }
  const variant = currentVariant();
  let body =
    tab === "participants"
      ? participants()
      : tab === "students"
        ? studentsView()
        : tab === "approvals"
          ? approvalsView()
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
    `${!publicToken ? `<button class="back-link" data-action="dashboard">${icon("back")} Tutti i tornei</button>` : '<p class="eyebrow">SEGUI IL TORNEO · SOLA LETTURA</p>'}<div class="tournament-heading"><div><p class="eyebrow">${h(t.sport)} <span>/</span> ${h(variant?.name || "Sport storico")} <span>/</span> ${label(t.format)} ${t.archived_at ? '<span class="tag archived"><i></i>Archiviato</span>' : legacy ? '<span class="tag archived"><i></i>Solo lettura</span>' : `<span class="tag ${data.status}">${stateLabel(data.status)}</span>${!canManage() ? '<span class="tag archived"><i></i>Solo lettura</span>' : ''}`}</p><h1>${h(t.name)}</h1><p>${h(t.description || "Ogni partita, un passo verso una nuova sfida.")}</p></div><div class="toolbar">${publicToken ? button("Aggiorna", "refresh", "", "check") : `${t.archived_at && canManage() ? button("Ripristina", "restore", "primary", "refresh") : ""}${!t.archived_at && !legacy && canManage() ? button("Modifica", "edit", "", "edit") : ""}${button("Condividi", "share", "", "share")}<a class="button" href="/api/tournaments/${t.id}/export.csv" download>${icon("download")}Esporta</a>${!t.archived_at && !legacy && canManage() ? button("Archivia", "archive", "danger") : ""}`}</div></div><div class="tabs" role="tablist" aria-label="Sezioni torneo">${tabs.map(([v, l]) => `<button class="tab ${tab === v ? "active" : ""}" role="tab" id="tab-${v}" aria-controls="tournament-panel" tabindex="${tab === v ? 0 : -1}" aria-selected="${tab === v}" data-tab="${v}">${l}</button>`).join("")}</div><div id="tournament-panel" role="tabpanel" aria-labelledby="tab-${tab}">${champion()}${body}</div>`;
  $("#content").setAttribute("aria-busy", "false");
  if (tab === "students") safely(() => loadStudentsDetail());
  if (tab === "approvals") safely(() => loadApprovals());
  if (tab === "participants")
    enableReorder(
      $("#team-order-body"),
      (order, previous) => saveTeamOrder(order, previous),
      "#team-order-live",
    );
}
function overview() {
  const t = data.tournament,
    p = data.progress,
    fixtures = data.matches;
  const next = fixtures.filter((m) => m.status === "ready").slice(0, 3);
  const groupsComplete =
    t.format === "groups" && fixtures.some((m) => m.kind === "knockout");
  return `<div class="stat-grid">${stat("Partecipanti", data.teams.length, t.participant_kind === "team" ? "Squadre iscritte" : "Giocatori iscritti", "users")}${stat("Incontri", p.total, "Esclusi i passaggi per BYE", "calendar")}${stat("Completati", p.completed, "Risultati confermati", "check")}${stat("Da giocare", p.total - p.completed, "Il campo vi aspetta", "ball")}</div><div class="overview-grid"><div><div class="panel"><div class="section-header"><h2>${data.status === "completed" ? "Torneo completato" : "Il prossimo passo"}</h2><span class="panel-label">SI SCENDE IN CAMPO</span></div><p class="muted" style="font-size:12px">${publicToken ? "Segui gli incontri e aggiorna la pagina per vedere gli ultimi risultati." : !fixtures.length ? "Aggiungi i partecipanti e genera gli incontri per dare inizio al torneo." : data.status === "completed" ? "Tutte le partite sono state giocate. Puoi rivedere il percorso e i risultati." : t.format === "groups" && !groupsComplete ? "Completa tutte le partite dei gironi: le qualificate passeranno automaticamente alla fase finale." : "Registra il risultato di un incontro: classifica e percorso si aggiornano subito."}</p><div class="steps"><div class="step ${data.teams.length >= 2 ? "done" : ""}">01<b>Partecipanti</b>Le squadre sono pronte</div><div class="step ${fixtures.length ? "done" : ""}">02<b>Si gioca</b>Incontri e risultati</div><div class="step ${data.status === "completed" ? "done" : ""}">03<b>La finale</b>${t.format === "round_robin" ? "Una classifica completa" : "Un campione da celebrare"}</div></div>${!fixtures.length && !publicToken && canManage() ? `<div style="margin-top:25px">${button("Genera incontri", "generate", "primary", "spark")}</div>` : ""}</div><div class="panel"><div class="section-header"><h2>${next.length ? "Pronte da giocare" : "Le ultime partite"}</h2><button class="text-button" data-tab="matches">Vedi tutte ${icon("arrow")}</button></div>${(next.length ? next : fixtures.filter((m) => m.status === "completed").slice(-3)).map(matchRow).join("") || '<p class="muted" style="font-size:12px">Gli incontri compariranno qui dopo la generazione.</p>'}</div></div><div><div class="panel"><h2>Il torneo in breve</h2><dl class="details-list"><div><dt>Sport</dt><dd>${h(t.sport)}</dd></div>${currentVariant() ? `<div><dt>Variante</dt><dd>${h(currentVariant().name)}</dd></div>` : ""}<div><dt>Formato</dt><dd>${label(t.format)}</dd></div><div><dt>Partecipanti</dt><dd>${t.participant_kind === "team" ? "Squadre" : "Giocatori individuali"}</dd></div>${t.format === "groups" ? `<div><dt>Qualificazione</dt><dd>Prime ${t.qualifiers} di ${t.group_count} gironi</dd></div>` : ""}<div><dt>Andata / ritorno</dt><dd>${t.legs === 2 ? "Andata e ritorno" : "Sola andata"}</dd></div>${t.format !== "knockout" ? `<div><dt>Punti V / N / P</dt><dd>${t.win_points} / ${t.draw_points} / ${t.loss_points}</dd></div>` : ""}<div><dt>Orari</dt><dd>Europe/Rome</dd></div></dl></div>${
    !publicToken && canEdit()
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
  return `<div class="match-row"><div class="match-round">${group ? h(group.name) + "<br>" : ""}${h(roundName(m))}</div><div class="match-players"><div class="match-player">${avatar(teamName(m.home_team_id), m.home_team_id)}<span>${h(m.home_team_id ? teamName(m.home_team_id) : m.is_bye ? "Riposo" : "Da definire")}</span></div><span class="score">${m.home_score ?? "–"} : ${m.away_score ?? "–"}</span><div class="match-player"><span>${h(m.away_team_id ? teamName(m.away_team_id) : m.is_bye ? "Riposo" : "Da definire")}</span>${avatar(teamName(m.away_team_id), m.away_team_id)}</div></div><div class="match-actions">${!publicToken && canManage() && ready ? `<button class="button ${m.status === "ready" ? "primary" : ""}" data-result="${m.id}">${m.status === "ready" ? "Risultato" : "Modifica"}</button>` : `<span class="tag">${m.is_bye ? "BYE" : m.status === "waiting" ? "In attesa" : m.status === "completed" ? "Giocata" : "Da giocare"}</span>`}${!publicToken && auth.role === "student" && resultProposalsAdapter.ready && m.status === "ready" ? `<button class="button compact" data-action="propose-result" data-match="${m.id}">Proponi</button>` : ""}</div></div>${setDetail ? `<p class="match-note">${icon("chart")}Set: ${h(setDetail)}</p>` : ""}${m.scheduled_at || m.location ? `<p class="match-note">${icon("clock")}${m.scheduled_at ? h(dateText(m.scheduled_at)) : "Orario da definire"}${m.location ? " · " + h(m.location) : ""}</p>` : ""}`;
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
function teamOrderPanel() {
  if (data.tournament.participant_kind !== "team" || !canManage()) return "";
  const teams = data.teams || [];
  if (teams.length < 2) return "";
  const max = currentVariant()?.max_roster || 0;
  const rows = teams
    .map(
      (team, i) =>
        `<tr class="team-order-row" data-reorder-item data-id="${team.id}"><td class="order-position">${i + 1}</td><td><button type="button" class="reorder-handle" data-drag-handle aria-label="Trascina ${h(team.name)}" aria-describedby="team-order-help">${icon("menu")}</button></td><td><strong>${h(team.name)}</strong></td><td>${h(data.groups.find((g) => g.id === team.group_id)?.name || "–")}</td><td>${team.player_count || 0}/${max}</td><td><div class="order-actions"><button type="button" class="icon-button order-move" data-action="team-order-move" data-team="${team.id}" data-direction="up" aria-label="Sposta su ${h(team.name)}" ${i === 0 ? "disabled" : ""}>↑</button><button type="button" class="icon-button order-move" data-action="team-order-move" data-team="${team.id}" data-direction="down" aria-label="Sposta giù ${h(team.name)}" ${i === teams.length - 1 ? "disabled" : ""}>↓</button></div></td></tr>`,
    )
    .join("");
  return `<section class="panel team-order-panel"><div class="section-header"><div><h2>Ordine delle squadre</h2><p class="section-sub">Trascina le righe o usa le frecce. L'ordine è solo di visualizzazione: non cambia classifica o seeding.</p></div><span class="tag archived"><i></i>${teamOrderAdapter.ready ? "Salvataggio attivo" : "Anteprima locale"}</span></div><div class="table-wrap"><table class="team-order-table"><thead><tr><th>#</th><th><span class="sr-only">Trascina</span></th><th>Squadra</th><th>Girone</th><th>Rosa</th><th>Sposta</th></tr></thead><tbody id="team-order-body">${rows}</tbody></table></div><p class="field-help" id="team-order-help">Trascina con mouse o dito, oppure usa le frecce. Da tastiera: frecce su/giù sull'handle. L'ordine non modifica classifiche o accoppiamenti.</p><p class="field-help" id="team-order-status" aria-live="polite">${teamOrderAdapter.ready ? "Ordine sincronizzato con il server." : "Anteprima locale: il salvataggio API è in attesa del Team A. Al reload torna l'ordine del server."}</p><p class="sr-only" id="team-order-live" aria-live="polite"></p></section>`;
}
async function saveTeamOrder(order, previous) {
  if (!order || order.length < 2) return;
  try {
    const result = await teamOrderAdapter.save(selectedId, order.map(Number));
    applyTeamOrder(order);
    renderTournament();
    const status = $("#team-order-status");
    if (result.saved) {
      if (status) status.textContent = "Ordine salvato sul server.";
      notify("Ordine delle squadre salvato.");
    } else {
      if (status)
        status.textContent =
          "Anteprima locale: ordine non salvato. Al reload torna l'ordine del server.";
      notify(
        "Ordine aggiornato solo in anteprima: l'API di salvataggio è in attesa del Team A.",
      );
    }
  } catch (e) {
    try {
      await openTournament(selectedId, true);
    } catch {
      const tbody = $("#team-order-body");
      if (tbody && previous) {
        const rows = new Map(
          [...tbody.querySelectorAll("[data-reorder-item]")].map((row) => [
            row.dataset.id,
            row,
          ]),
        );
        previous.forEach((id) => {
          const row = rows.get(String(id));
          if (row) tbody.appendChild(row);
        });
        applyTeamOrder(previous);
        renderTournament();
      }
    }
    notify(e.message, true);
  }
}
function applyTeamOrder(order) {
  const byId = new Map((data.teams || []).map((team) => [team.id, team]));
  const next = order.map((id) => byId.get(Number(id))).filter(Boolean);
  if (next.length === data.teams.length) data.teams = next;
}
function participants() {
  const generated = data.matches.length > 0;
  const variant = currentVariant();
  const teamMode = data.tournament.participant_kind === "team";
  const minimum = variant?.min_lineup || 1;
  const ready = teamMode && variant
    ? data.teams.filter((p) => (p.player_count || 0) >= minimum).length
    : 0;
  const rosterNote = teamMode && variant
    ? ` · Rose pronte ${ready}/${data.teams.length} (minimo ${minimum})`
    : "";
  return `<div class="section-header"><div><h2>Le persone fanno il torneo.</h2><p class="section-sub">${data.teams.length} ${teamMode ? "squadre" : "giocatori"} · I nomi si possono modificare anche a torneo iniziato.${rosterNote}</p></div>${teamOrderPanel()}${!generated && !publicToken && canManage() ? button("Genera incontri", "generate", "primary", "spark") : ""}</div>${!generated && !publicToken && canManage() ? '<form id="team-form" class="inline-form"><input name="name" required maxlength="60" aria-label="Nome del partecipante" placeholder="Nome del partecipante"><button class="button primary">Aggiungi</button></form>' : ""}<div class="roster">${data.teams.map((p, i) => {
    const group = data.groups.find((g) => g.id === p.group_id)?.name;
    const roster = teamMode && variant
      ? ` · ${p.player_count || 0}/${variant.max_roster} in rosa${(p.player_count || 0) < minimum ? ` · mancano ${minimum - (p.player_count || 0)}` : ""}`
      : "";
    return `<div class="roster-item"><button type="button" class="roster-info" data-team="${p.id}" aria-label="Apri la scheda di ${h(p.name)}">${avatar(p.name, i)}<span><strong>${h(p.name)}</strong><small>${h(group || "Partecipante " + (i + 1).toString().padStart(2, "0"))}${roster}</small></span></button>${!publicToken && canManage() ? `<button class="icon-button" data-rename="${p.id}" aria-label="Rinomina ${h(p.name)}">${icon("edit")}</button>${!generated ? `<button class="icon-button" data-remove="${p.id}" aria-label="Elimina ${h(p.name)}">${icon("close")}</button>` : ""}` : ""}</div>`;
  }).join("") || '<p class="muted">Aggiungi almeno due partecipanti per cominciare.</p>'}</div>`;
}
function studentTeamsListHtml() {
  const max = currentVariant()?.max_roster || 0;
  const needle = studentSearch.toLocaleLowerCase("it");
  const teams = (data.teams || []).filter((t) =>
    t.name.toLocaleLowerCase("it").includes(needle),
  );
  if (!teams.length)
    return '<p class="muted" style="padding:12px">Nessuna squadra trovata.</p>';
  return teams
    .map(
      (t) =>
        `<button type="button" class="student-team ${t.id === studentTeamId ? "active" : ""}" data-action="student-team" data-student-team="${t.id}" aria-pressed="${t.id === studentTeamId}"><span>${h(t.name)}</span><small>${t.player_count || 0}/${max} studenti</small></button>`,
    )
    .join("");
}
function studentsView() {
  const teams = data.teams || [];
  const max = currentVariant()?.max_roster || 0;
  if (!teams.length)
    return `<div class="panel empty">${icon("users")}<h2>Prima le squadre.</h2><p>Aggiungi almeno due partecipanti nella scheda Partecipanti.</p><button class="button primary" data-tab="participants">Vai ai partecipanti</button></div>`;
  if (!teams.some((t) => t.id === studentTeamId)) studentTeamId = teams[0].id;
  const total = teams.reduce((sum, t) => sum + (t.player_count || 0), 0);
  return `<div class="section-header"><div><h2>Studenti nelle squadre.</h2><p class="section-sub">${total} studenti assegnati · rosa massima ${max} per squadra</p></div></div><div class="students-layout"><section class="panel students-teams"><div class="section-header"><h2>Squadre</h2><span class="panel-label">${teams.length}</span></div><label class="sr-only" for="student-team-search">Cerca squadra</label><input id="student-team-search" class="student-search" type="search" placeholder="Cerca squadra…" value="${h(studentSearch)}"><div class="students-team-list">${studentTeamsListHtml()}</div></section><section class="panel students-detail" id="students-detail"><p class="muted">Caricamento studenti…</p></section></div><section class="panel students-unassigned"><div class="section-header"><div><h2>Studenti non assegnati</h2><p class="section-sub">Spostamento e archivio studenti della scuola</p></div><span class="tag archived"><i></i>In attesa API</span></div><p class="muted">Il backend non espone ancora un elenco separato dalle squadre. Quando sarà disponibile, qui compariranno gli studenti non assegnati e lo spostamento tra squadre.</p><p class="field-help">Richiesta al Team A: elenco studenti, assegnazione/spostamento e import massivo atomico.</p></section>`;
}
async function loadStudentsDetail() {
  const box = $("#students-detail");
  if (!box || !studentTeamId) return;
  const info = await api(`/tournaments/${selectedId}/teams/${studentTeamId}`);
  const max = info.max_roster || currentVariant()?.max_roster || 0;
  const players = info.players || [];
  const min = info.min_lineup || 0;
  const manage = !publicToken && canManage();
  const missing = min && players.length < min ? min - players.length : 0;
  const full = max > 0 && players.length >= max;
  bulkState = { teamId: info.team.id, players, max };
  box.innerHTML = `<div class="section-header"><div><h2>${h(info.team.name)}</h2><p class="section-sub">${players.length}/${max} studenti${missing ? ` · mancano ${missing} per la lineup` : ""}</p></div><span class="tag ${full ? "completed" : "active"}">${full ? "Rosa completa" : "Spazio disponibile"}</span></div>${manage ? `<form id="student-form" data-team="${info.team.id}" class="inline-form"><input name="name" required maxlength="60" aria-label="Nome dello studente" placeholder="Nome dello studente"><input name="shirt_number" type="number" min="0" max="99" aria-label="Numero di maglia" placeholder="N." style="max-width:80px"><button class="button primary" ${full ? "disabled" : ""}>Aggiungi</button></form>` : ""}<div class="roster">${players.map((p) => `<div class="roster-item"><div class="roster-info">${avatar(p.name, p.id)}<span><strong>${h(p.name)}</strong><small>${p.shirt_number !== null ? "Maglia " + p.shirt_number : "Studente"}</small></span></div>${manage ? `<button type="button" class="icon-button" data-remove-player="${p.id}" data-player-team="${info.team.id}" aria-label="Rimuovi ${h(p.name)}">${icon("close")}</button>` : ""}</div>`).join("") || '<p class="muted" style="padding:16px">Nessuno studente assegnato. Aggiungi il primo nome.</p>'}</div>${manage ? bulkImportPanel() : ""}`;
}
function bulkImportPanel() {
  return `<details class="result-schedule student-bulk"><summary>Inserimento rapido</summary><div class="student-bulk-body"><p class="field-help">Incolla un nome per riga, oppure carica un CSV con colonne <code>nome</code> e, se vuoi, <code>numero</code>. L'anteprima non salva nulla.</p><textarea id="bulk-names" rows="5" placeholder="Mario Rossi&#10;Giulia Bianchi, 7"></textarea><div class="inline-form"><input type="file" id="bulk-file" accept=".csv,text/csv" aria-label="Carica un CSV di studenti"><button type="button" class="button ghost" data-action="bulk-parse">Anteprima</button></div><div id="bulk-preview" class="student-bulk-preview"></div><p class="field-help">Il salvataggio usa l'API di aggiunta singola per ogni studente: non è atomico. L'import massivo lato backend è in attesa del Team A.</p></div></details>`;
}
function parseStudentList(text, existing, max) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length && /^(nome|name)\b/i.test(lines[0])) lines.shift();
  const seen = new Set(existing.map((p) => p.name.toLocaleLowerCase("it")));
  const rows = [];
  for (const line of lines) {
    const parts = line
      .split(/[,;\t]/)
      .map((part) => part.trim().replace(/^"|"$/g, ""));
    const name = (parts[0] || "").trim();
    const shirtText = (parts[1] || "").trim();
    const shirt = shirtText === "" ? null : Number(shirtText);
    let status = "ok";
    let message = "";
    const validCount = rows.filter((row) => row.status === "ok").length;
    const full = max > 0 && existing.length + validCount >= max;
    if (!name || name.length > 60) {
      status = "error";
      message = "Nome non valido";
    } else if (seen.has(name.toLocaleLowerCase("it"))) {
      status = "duplicate";
      message = "Già presente";
    } else if (
      shirt !== null &&
      (!Number.isInteger(shirt) || shirt < 0 || shirt > 99)
    ) {
      status = "error";
      message = "Numero non valido";
    } else if (full) {
      status = "limit";
      message = "Rosa completa";
    } else {
      seen.add(name.toLocaleLowerCase("it"));
    }
    rows.push({ name, shirt_number: shirt, status, message });
  }
  return rows;
}
function renderBulkPreview() {
  const box = $("#bulk-preview");
  if (!box || !bulkState) return;
  const text = $("#bulk-names")?.value || "";
  const rows = parseStudentList(text, bulkState.players, bulkState.max);
  const valid = rows.filter((row) => row.status === "ok");
  if (!rows.length) {
    box.innerHTML =
      '<p class="muted">Incolla almeno un nome per vedere l\'anteprima.</p>';
    return;
  }
  box.innerHTML = `<p class="field-help">${valid.length} da aggiungere · ${rows.length - valid.length} da correggere</p><div class="table-wrap"><table><thead><tr><th>#</th><th>Studente</th><th>Numero</th><th>Stato</th></tr></thead><tbody>${rows.map((row, i) => `<tr><td>${i + 1}</td><td>${h(row.name || "–")}</td><td>${row.shirt_number ?? "–"}</td><td>${row.status === "ok" ? "Pronto" : h(row.message)}</td></tr>`).join("")}</tbody></table></div><button type="button" class="button primary" data-action="bulk-save" ${valid.length ? "" : "disabled"}>Aggiungi ${valid.length} studenti</button><p class="field-help">Salvataggio sequenziale tramite l'API di aggiunta singola; non è atomico. L'import massivo backend è in attesa del Team A.</p>`;
}
async function saveBulk() {
  if (!bulkState) return;
  const text = $("#bulk-names")?.value || "";
  const rows = parseStudentList(text, bulkState.players, bulkState.max).filter(
    (row) => row.status === "ok",
  );
  if (!rows.length) return;
  let added = 0;
  let failed = 0;
  for (const row of rows) {
    try {
      await api(`/tournaments/${selectedId}/teams/${bulkState.teamId}/players`, {
        method: "POST",
        body: JSON.stringify({
          name: row.name,
          shirt_number: row.shirt_number,
        }),
      });
      added++;
    } catch {
      failed++;
    }
  }
  await openTournament(selectedId, true);
  notify(`${added} studenti aggiunti${failed ? `, ${failed} non salvati` : ""}.`);
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
  const summary = [
    ["Giocatori in campo", v.players_on_field],
    ["Minimo in campo", v.min_lineup],
    ["Rosa massima", v.max_roster],
    ["Durata partita", durationText(v.match_duration)],
    ["Punteggio", scoringText(v)],
    ["Criterio classifica", tieLabel(t.tie_breaker)],
  ];
  const details = derivedRuleItems(v).map(
    (item) => `${item.label}: ${item.value}`,
  );
  const generated = data.matches.length > 0;
  return `${generated ? `<div class="rule-warning-banner" role="status">${icon("clock")}<div><strong>Torneo già iniziato.</strong><p>Le regole sono congelate: cambiarle richiederebbe di rigenerare gli incontri. Puoi ancora modificare nomi, orari e risultati.</p></div></div>` : ""}<div class="section-header"><div><h2>Le regole scendono in campo.</h2><p class="section-sub">${h(t.sport)} · ${h(v.name)}. Il regolamento è congelato alla creazione del torneo.</p></div><div class="toolbar">${canManage() && !generated ? `<button class="button" data-action="edit">${icon("edit")}Modifica regole</button>` : ""}<button class="button ghost" data-action="print">${icon("download")}Stampa</button></div></div><div class="stat-grid">${summary.map(([label, value]) => stat(label, value, "", "ball")).join("")}</div><div class="catalog-detail-grid"><section class="panel"><h2>Regolamento applicato</h2><div class="regulation-copy">${(data.regulation || "").split(/\n\n+/).map((p) => `<p>${h(p)}</p>`).join("")}</div></section><section class="panel"><h2>Dettagli</h2><ul class="rule-list">${details.map((d) => `<li>${h(d)}</li>`).join("")}</ul><p class="field-help">Punti in classifica: vittoria ${t.win_points}, pareggio ${t.draw_points}, sconfitta ${t.loss_points}. A parità: ${tieLabel(t.tie_breaker)}.</p></section></div>`;
}
function approvalsView() {
  if (!resultProposalsAdapter.ready) {
    return `<div class="panel"><div class="section-header"><div><h2>Risultati da verificare</h2><p class="section-sub">Proposte degli studenti in attesa di approvazione.</p></div><span class="tag archived"><i></i>In attesa API</span></div><p class="muted">Il backend non espone ancora le proposte di risultato né l'identità degli studenti. Questa sezione è pronta: quando l'API sarà attiva compariranno partita, squadre, risultato proposto, autore, data, conflitti e azioni.</p><p class="field-help">Contratto proposto: <code>GET /api/tournaments/{id}/proposals?status=pending</code> e <code>PATCH /api/proposals/{id}</code> con azione <code>approve</code>, <code>reject</code> o <code>correct</code>.</p></div>`;
  }
  return `<div class="section-header"><div><h2>Risultati da verificare</h2><p class="section-sub">Approva, respingi o correggi le proposte degli studenti.</p></div></div><div id="approvals-list"><p class="muted">Caricamento proposte…</p></div>`;
}
function proposalErrorMessage(error) {
  if (!error) return "Operazione non riuscita.";
  if (error.status === 401) return "Sessione scaduta. Accedi di nuovo.";
  if (error.status === 403) return "Non hai i permessi per questa azione.";
  if (error.status === 404) return "Partita o proposta non trovata.";
  if (error.status === 409)
    return "La proposta è già stata revisionata o modificata da un altro utente.";
  if (!error.status) return error.message || "Server non raggiungibile.";
  return error.message || "Operazione non riuscita.";
}
function handleProposalError(error) {
  if (error?.status === 401) {
    auth = { role: null, authenticated: false, teacher: null };
    renderAuthControl();
    showRoleGate("login");
  }
  notify(proposalErrorMessage(error), true);
}
function proposalRow(proposal) {
  const score = proposal.proposed_sets?.length
    ? proposal.proposed_sets.map((set) => `${set.home}-${set.away}`).join(" · ")
    : `${proposal.proposed_home_score ?? "–"} : ${proposal.proposed_away_score ?? "–"}`;
  const conflicts = proposal.conflicts?.length
    ? `<span class="tag archived"><i></i>${proposal.conflicts.length} proposte contrastanti</span>`
    : "";
  return `<tr><td>${h(proposal.tournament_name || data.tournament.name)}</td><td>${h(proposal.home_name || "–")} – ${h(proposal.away_name || "–")}</td><td><strong>${h(score)}</strong></td><td>${proposal.author ? h(proposal.author) : "–"}</td><td>${proposal.created_at ? h(dateText(proposal.created_at)) : "–"}</td><td><span class="tag">${h(proposal.status || "pending")}</span>${conflicts}</td><td><div class="proposal-actions"><button type="button" class="button compact primary" data-action="approve-proposal" data-proposal="${proposal.id}">Approva</button><button type="button" class="button compact danger" data-action="reject-proposal" data-proposal="${proposal.id}">Respingi</button><button type="button" class="button compact ghost" data-action="correct-proposal" data-proposal="${proposal.id}">Correggi</button></div></td></tr>`;
}
async function loadApprovals() {
  const box = $("#approvals-list");
  if (!box || !resultProposalsAdapter.ready) return;
  try {
    approvalsCache = await resultProposalsAdapter.list(selectedId);
    box.innerHTML = approvalsCache.length
      ? `<div class="table-wrap"><table><thead><tr><th>Torneo</th><th>Partita</th><th>Risultato proposto</th><th>Autore</th><th>Data</th><th>Stato</th><th>Azioni</th></tr></thead><tbody>${approvalsCache.map(proposalRow).join("")}</tbody></table></div>`
      : '<div class="panel empty">Nessuna proposta in attesa.</div>';
  } catch (e) {
    box.innerHTML = `<div class="panel empty">${h(proposalErrorMessage(e))}</div>`;
    if (e.status === 401) handleProposalError(e);
  }
}
function proposalScoreFields(match, proposal = null) {
  const variant = currentVariant();
  const setMode = !!variant?.supports_sets;
  const maxSets = variant?.max_sets || 5;
  if (!setMode) {
    return `<div class="result-inputs"><label>${avatar(teamName(match.home_team_id), match.home_team_id)}<span>${h(teamName(match.home_team_id))}</span><input name="home_score" aria-label="${h(scoreLabel())} ${h(teamName(match.home_team_id))}" type="number" min="0" max="999" step="1" value="${proposal?.proposed_home_score ?? ""}" required></label><span>:</span><label>${avatar(teamName(match.away_team_id), match.away_team_id)}<span>${h(teamName(match.away_team_id))}</span><input name="away_score" aria-label="${h(scoreLabel())} ${h(teamName(match.away_team_id))}" type="number" min="0" max="999" step="1" value="${proposal?.proposed_away_score ?? ""}" required></label></div>`;
  }
  return `<div class="set-inputs">${Array.from({ length: maxSets }, (_, index) => {
    const number = index + 1;
    const existing = (proposal?.proposed_sets || []).find(
      (set) => set.set === number,
    );
    return `<div class="set-row"><span>Set ${number}</span><input name="home_set_${number}" aria-label="Punti ${h(teamName(match.home_team_id))} set ${number}" type="number" min="0" max="999" step="1" value="${existing?.home ?? ""}" placeholder="–"><b>:</b><input name="away_set_${number}" aria-label="Punti ${h(teamName(match.away_team_id))} set ${number}" type="number" min="0" max="999" step="1" value="${existing?.away ?? ""}" placeholder="–"></div>`;
  }).join("")}</div>`;
}
function readProposalPayload(form) {
  const fd = new FormData(form);
  const variant = currentVariant();
  if (variant?.supports_sets) {
    const sets = [];
    for (let index = 1; index <= (variant.max_sets || 5); index++) {
      const home = fd.get(`home_set_${index}`);
      const away = fd.get(`away_set_${index}`);
      if ((home === "" || home === null) && (away === "" || away === null)) continue;
      if (home === "" || away === "" || home === null || away === null)
        throw new Error(`Completa il set ${index} con entrambi i punteggi.`);
      const hScore = Number(home);
      const aScore = Number(away);
      if (!Number.isInteger(hScore) || !Number.isInteger(aScore) || hScore < 0 || aScore < 0 || hScore > 999 || aScore > 999)
        throw new Error(`Punteggi non validi nel set ${index}.`);
      sets.push({ home: hScore, away: aScore });
    }
    if (!sets.length) throw new Error("Inserisci almeno un set.");
    return { sets };
  }
  const home = Number(fd.get("home_score"));
  const away = Number(fd.get("away_score"));
  if (!Number.isInteger(home) || !Number.isInteger(away) || home < 0 || away < 0 || home > 999 || away > 999)
    throw new Error("Inserisci due punteggi validi.");
  return { home_score: home, away_score: away };
}
function proposeResultModal(matchId) {
  if (!resultProposalsAdapter.ready) {
    notify("Le proposte di risultato non sono ancora disponibili.", true);
    return;
  }
  const match = data.matches.find((item) => item.id === Number(matchId));
  if (!match || publicToken || match.status !== "ready") {
    notify("Partita non disponibile per una proposta.", true);
    return;
  }
  const variant = currentVariant();
  modal(
    "Proponi il risultato.",
    `<div class="proposal-banner"><span class="tag archived"><i></i>PROPOSTA · NON UFFICIALE</span><p class="field-help">La classifica ufficiale non cambierà finché il professore non approva.</p></div><form id="proposal-form" data-match="${match.id}">${proposalScoreFields(match)}<p class="field-help">${variant?.supports_sets ? "Inserisci solo i set giocati." : variant?.draw_allowed === false ? "Questa variante non ammette pareggi." : "Inserisci il punteggio finale."}</p></form>`,
    `${button("Annulla", "close", "ghost")}<button type="submit" form="proposal-form" class="button primary">${icon("check")}Invia proposta</button>`,
    h(roundName(match)),
  );
}
function proposalCorrectModal(proposal) {
  const match = data.matches.find((item) => item.id === Number(proposal.match_id));
  if (!match) {
    notify("Partita non trovata.", true);
    return;
  }
  modal(
    "Correggi la proposta.",
    `<div class="proposal-banner"><span class="tag archived"><i></i>PROPOSTA · NON UFFICIALE</span><p class="field-help">La correzione resta una proposta finché non viene approvata.</p></div><form id="proposal-correct-form" data-proposal="${proposal.id}" data-match="${match.id}">${proposalScoreFields(match, proposal)}</form>`,
    `${button("Annulla", "close", "ghost")}<button type="submit" form="proposal-correct-form" class="button primary">${icon("check")}Salva correzione</button>`,
    h(roundName(match)),
  );
}
function bracketSourceLabel(sourceId) {
  if (!sourceId) return "Turno precedente";
  const source = data.matches.find((match) => match.id === Number(sourceId));
  if (!source) return "Turno precedente";
  return `Vincente ${roundName(source)} ${Number(source.position) + 1}`;
}
function bracketStatus(match) {
  if (match.is_bye) return "PASSAGGIO AUTOMATICO";
  if (match.status === "completed") return "RISULTATO CONFERMATO";
  if (match.status === "ready") return "DA GIOCARE";
  return "IN ATTESA DEGLI INCONTRI PRECEDENTI";
}
function bracket() {
  const fixtures = data.matches.filter((m) => m.kind === "knockout");
  if (!fixtures.length)
    return `<div class="panel empty">${icon("trophy")}<h2>La finale si conquista.</h2><p>${data.tournament.format === "groups" ? "Completa tutti i gironi. Le squadre qualificate riempiranno automaticamente il tabellone." : "Genera gli incontri per vedere il percorso verso la coppa."}</p>${button("Vai alle partite", "matches", "primary")}</div>`;
  if (typeof BracketLayout === "undefined")
    return `<div class="panel empty">${icon("trophy")}<h2>Tabellone non disponibile.</h2><p>Ricarica la pagina per caricare il componente del tabellone.</p></div>`;
  const view = BracketLayout.layout(fixtures);
  const championTeam = data.champion_team_id
    ? teamName(data.champion_team_id)
    : null;
  const roundList = view.roundNumbers.map((number, index) => ({
    number,
    name: view.labels[index],
  }));
  const championCard = view.champion
    ? `<div class="bracket-title" style="left:${view.champion.x}px;top:0">Campione</div><div class="bracket-card champion-card ${championTeam ? "completed" : "waiting"}" style="left:${view.champion.x}px;top:${view.champion.y - view.cardHeight / 2}px" role="group" aria-label="${championTeam ? `Campione: ${h(championTeam)}` : "Campione ancora da decidere"}"><span class="bracket-trophy">${icon("trophy")}</span><span class="champion-name">${championTeam ? h(championTeam) : "Da decidere"}</span><span class="bracket-status">${championTeam ? "CAMPIONE" : "LA FINALE DECIDE"}</span></div>`
    : "";
  return `<div class="section-header"><div><h2>La strada verso la coppa.</h2><p class="section-sub">${publicToken ? "Segui ogni passaggio del torneo." : "Seleziona un incontro per registrare o correggere il risultato."}</p></div></div><div class="bracket-mobile-nav" role="group" aria-label="Vai a un turno"><p class="bracket-mobile-hint">${icon("link")} Scorri il tabellone o scegli un turno.</p><div class="bracket-rounds">${roundList.map((round, i) => `<button type="button" class="bracket-round-chip ${i === 0 ? "active" : ""}" data-action="bracket-round" data-round="${i + 1}" aria-pressed="${i === 0}">${h(round.name)}</button>`).join("")}${view.champion ? `<button type="button" class="bracket-round-chip" data-action="bracket-round" data-round="${view.roundNumbers.length + 1}" aria-pressed="false">Campione</button>` : ""}</div></div><div class="bracket-scroll" tabindex="0" role="region" aria-label="Tabellone del torneo"><div class="bracket-tree" style="width:${view.width}px;height:${view.height}px"><svg width="${view.width}" height="${view.height}" aria-hidden="true"><g fill="none" stroke="#c5d1b5" stroke-width="1.5">${view.paths.map((path) => `<path d="${path.d}"/>`).join("")}</g></svg>${view.roundNumbers.map((number, index) => `<div class="bracket-title" style="left:${index * view.columnWidth}px;top:0">${h(view.labels[index])}</div>`).join("")}${fixtures
    .map((m) => {
      const pos = view.coords[String(m.id)];
      if (!pos) return "";
      const editable =
        !publicToken &&
        canManage() &&
        !m.is_bye &&
        ["ready", "completed"].includes(m.status);
      const el = editable ? "button" : "div";
      const status = bracketStatus(m);
      const home = m.home_team_id
        ? teamName(m.home_team_id)
        : m.is_bye
          ? "Riposo · BYE"
          : bracketSourceLabel(m.source_home);
      const away = m.away_team_id
        ? teamName(m.away_team_id)
        : m.is_bye
          ? "Riposo · BYE"
          : bracketSourceLabel(m.source_away);
      const label = `${roundName(m)}: ${home} contro ${away}. ${status}`;
      return `<${el} class="bracket-card ${m.status}" style="left:${pos.x}px;top:${pos.y - view.cardHeight / 2}px" ${editable ? `data-result="${m.id}" aria-label="${h(label)}. Inserisci risultato"` : `role="group" aria-label="${h(label)}"`}>${["home", "away"].map((side) => `<span class="bracket-team ${m[side + "_team_id"] && m[side + "_team_id"] === m.winner_team_id ? "winner" : ""}">${avatar(m[side + "_team_id"] ? teamName(m[side + "_team_id"]) : "–", m[side + "_team_id"])}<span class="team-name">${h(m[side + "_team_id"] ? teamName(m[side + "_team_id"]) : m.is_bye ? "Riposo · BYE" : bracketSourceLabel(m["source_" + side]))}</span><strong>${m[side + "_score"] ?? "–"}</strong></span>`).join("")}<span class="bracket-status">${status}</span></${el}>`;
    })
    .join(
      "",
    )}${championCard}</div></div><p class="tree-help">${icon("link")} I vincitori avanzano automaticamente. ${publicToken ? "Aggiorna la pagina per seguire i risultati." : "Il tabellone usa solo i risultati confermati: le proposte non approvate non fanno avanzare nessuno."}</p>`;
}
async function teamModal(id) {
  const info = await api(`/tournaments/${selectedId}/teams/${id}`);
  const standing = info.standing;
  const stats = standing
    ? `<div class="stat-grid">${stat("Posizione", info.position ?? "–", "Nel girone o in classifica", "chart")}${stat("Giocate", standing.played, "Incontri disputati", "calendar")}${stat("Punti", standing.points, `V ${standing.won} · N ${standing.drawn} · P ${standing.lost}`, "check")}${stat("Differenza", (standing.goal_difference > 0 ? "+" : "") + standing.goal_difference, `${standing.goals_for} fatti · ${standing.goals_against} subiti`, "ball")}</div>`
    : "";
  const lineup =
    info.participant_kind === "team"
      ? `<p class="field-help" style="margin:4px 0 12px">${info.variant_name ? h(info.variant_name) + " · " : ""}${info.players_on_field} in campo · minimo ${info.min_lineup} per iniziare${info.players.length < info.min_lineup ? ` · mancano ${info.min_lineup - info.players.length} giocatori` : ""}</p>`
      : "";
  const roster =
    info.participant_kind === "team"
      ? `<h3 class="subsection-title" style="margin-top:24px">Rosa <span class="muted">${info.players.length}/${info.max_roster}</span></h3>${lineup}<div class="panel" style="margin:0">${!publicToken && canManage() ? `<form id="player-form" data-team="${info.team.id}" class="inline-form"><input name="name" required maxlength="60" aria-label="Nome del giocatore" placeholder="Nome del giocatore"><input name="shirt_number" type="number" min="0" max="99" aria-label="Numero di maglia" placeholder="N." style="max-width:80px"><button class="button primary">Aggiungi</button></form>` : ""}${info.players.map((p) => `<div class="roster-item"><div class="roster-info">${avatar(p.name, p.id)}<span><strong>${h(p.name)}</strong><small>${p.shirt_number !== null ? "Maglia " + p.shirt_number : "Giocatore"}</small></span></div>${!publicToken && canManage() ? `<button class="icon-button" data-remove-player="${p.id}" data-player-team="${info.team.id}" aria-label="Rimuovi ${h(p.name)}">${icon("close")}</button>` : ""}</div>`).join("") || '<p class="muted" style="padding:16px">Nessun giocatore in rosa. Aggiungi i nomi per completare la squadra.</p>'}</div>`
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
  if (!canManage()) {
    requireManage();
    return;
  }
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
    `<form id="result-form" data-id="${m.id}">${setInputs}${m.home_score !== null ? '<label class="checkbox"><input type="checkbox" name="invalidate">Se questa correzione cambia qualificazioni o avversari, confermo l’annullamento dei risultati e degli orari dipendenti.</label>' : ""}</form><details class="result-schedule"><summary>Orario e campo</summary><form id="schedule-form" data-id="${m.id}"><div class="form-grid"><label>Data e ora locale<input name="scheduled_at" type="datetime-local" value="${local}"></label><label>Campo<input name="location" maxlength="80" list="known-fields" placeholder="Es. Palestra · campo A" value="${h(m.location || "")}"></label><label>Durata in minuti<input name="duration" type="number" min="1" max="240" value="${m.duration || variant?.match_duration || 20}" required></label></div>${fieldPickerHtml()}<p class="field-help">L’orario usa il fuso del dispositivo. Gli orari sono mostrati nel torneo in Europe/Rome. Scegli un campo già usato dall’elenco o scrivine uno nuovo.</p><p class="field-help schedule-conflict hidden" id="schedule-conflict" role="status"></p><button class="button" style="margin-top:13px">Salva orario e campo</button></form></details>`,
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
  wizard.draw_points =
    variant.draw_allowed === false ? 0 : (variant.standings?.draw ?? 0);
  wizard.loss_points = variant.standings?.loss ?? 0;
  wizard.tie_breaker = variant.default_tie_breaker || "goal_difference";
}
function variantRulesPanel(variant) {
  if (!variant) return "";
  const configurable = variantRuleSchema(variant)
    .filter((field) => field.scope !== "variant")
    .map((field) => field.label);
  return `<div class="panel rules-preview"><div class="section-header"><h2>${h(variant.name)}</h2><span class="panel-label">REGOLE DELLA VARIANTE</span></div><div class="rule-pills"><span>${icon("users")}${variant.players_on_field} in campo</span><span>${icon("users")}Rosa max ${variant.max_roster}</span><span>${icon("clock")}${durationText(variant.match_duration)}</span><span>${icon("spark")}${h(scoringText(variant))}</span></div><p class="field-help" style="margin-bottom:0">${h(variant.description)}</p>${configurable.length ? `<p class="field-help" style="margin-bottom:0">Parametri configurabili: ${h(configurable.join(" · "))}.</p>` : ""}</div>`;
}
function syncEditVariant(variant) {
  if (!variant || !editState) return;
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
  editState.variant = variant.slug;
  editState.values = {
    ...editState.values,
    win_points: variant.standings?.win ?? 3,
    draw_points:
      variant.draw_allowed === false ? 0 : (variant.standings?.draw ?? 0),
    loss_points: variant.standings?.loss ?? 0,
    tie_breaker: variant.default_tie_breaker || "goal_difference",
  };
  const preview = $("#edit-variant-preview");
  if (preview) preview.innerHTML = variantRulesPanel(variant);
  renderEditRules();
}
function readEditRules() {
  const form = $("#tournament-form");
  if (!form || !editState) return;
  const fd = new FormData(form);
  if (fd.has("format")) editState.format = fd.get("format");
  if (fd.has("variant")) editState.variant = fd.get("variant");
  for (const key of ["win_points", "draw_points", "loss_points"])
    if (fd.has(key)) editState.values[key] = Number(fd.get(key));
  for (const key of ["legs", "group_count", "qualifiers"])
    if (fd.has(key)) editState.values[key] = Number(fd.get(key));
  if (fd.has("tie_breaker")) editState.values.tie_breaker = fd.get("tie_breaker");
  editState.values.count = data?.teams?.length || editState.values.count;
}
function renderEditRules() {
  const target = $("#edit-rule-fields");
  if (!target || !editState) return;
  target.outerHTML = ruleFieldsetHtml(
    variantFor(editState.variant),
    editState.values,
    editState.format,
    { id: "edit-rule-fields", title: "Regole e punteggi" },
  );
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
    draw_points:
      selected?.draw_allowed === false ? 0 : (selected?.standings?.draw ?? 1),
    loss_points: selected?.standings?.loss ?? 0,
    tie_breaker: selected?.default_tie_breaker || "goal_difference",
    order: null,
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
function wizardParticipantNames() {
  const entered = wizard.names
    .split("\n")
    .map((name) => name.trim())
    .filter(Boolean);
  if (entered.length) return entered;
  return Array.from(
    { length: wizard.count },
    (_, i) =>
      (wizard.participant_kind === "team" ? "Team" : "Giocatore") +
      " #" +
      (i + 1),
  );
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
  if (canEdit()) return;
  showRoleGate("login");
}
function editTournament() {
  if (!canManage()) {
    requireManage();
    return;
  }
  const t = data.tournament;
  const generated = data.matches.length > 0;
  const variant = currentVariant();
  const kind = variant?.participant_kind || t.participant_kind;
  editState = {
    variant: variant?.slug || t.variant || null,
    format: t.format,
    values: {
      win_points: t.win_points,
      draw_points: t.draw_points,
      loss_points: t.loss_points,
      tie_breaker: t.tie_breaker,
      legs: t.legs,
      group_count: t.group_count,
      qualifiers: t.qualifiers,
      count: data.teams.length,
    },
  };
  const structure = generated
    ? `<div class="rule-warning-banner" role="status">${icon("clock")}<div><strong>Torneo già iniziato.</strong><p>Gli incontri sono stati generati: sport, variante, formato e regole sono bloccati dal backend. Puoi modificare nome e descrizione; per nuove regole serve un nuovo torneo.</p></div></div><details class="result-schedule"><summary>Regole applicate</summary><ul class="rule-list">${derivedRuleItems(variant).map((item) => `<li><strong>${h(item.label)}:</strong> ${h(item.value)}</li>`).join("")}</ul><p class="field-help">Punti in classifica: ${t.win_points}/${t.draw_points}/${t.loss_points} · ${h(tieLabel(t.tie_breaker))} · ${t.legs === 2 ? "andata e ritorno" : "sola andata"}.</p></details>`
    : `<fieldset class="format-fieldset" style="margin-top:18px"><legend>Sport e formato</legend><div class="form-grid"><label>Formato<select name="format" id="edit-format">${[["knockout", "Eliminazione"], ["round_robin", "Girone unico"], ["groups", "Gironi + finali"]].map(([v, l]) => `<option value="${v}" ${t.format === v ? "selected" : ""}>${l}</option>`).join("")}</select></label><label>Sport<select name="sport" id="edit-sport">${sportOptionsFor(t.sport)}</select></label><label>Variante<select name="variant" id="edit-variant">${variantOptionsFor(t.sport, t.variant)}</select></label><label>Partecipanti<input value="${kind === "team" ? "Squadre" : "Giocatori individuali"}" disabled><input type="hidden" name="participant_kind" value="${kind}"></label></div><div id="edit-variant-preview">${variantRulesPanel(variant)}</div></fieldset>${ruleFieldsetHtml(variant, editState.values, t.format, { id: "edit-rule-fields", title: "Regole e punteggi" })}`;
  modal(
    "Ritocca il torneo.",
    `<form id="tournament-form"><div class="form-grid"><label class="full">Nome del torneo<input name="name" value="${h(t.name)}" minlength="2" maxlength="120" required autofocus></label><label class="full">Descrizione<textarea name="description" maxlength="1000" rows="3">${h(t.description)}</textarea></label></div>${structure}</form>`,
    `${button("Annulla", "close", "ghost")}<button class="button primary" form="tournament-form">${icon("check")}Salva modifiche</button>`,
    "MODIFICA TORNEO",
  );
  updateEditFormat();
}
function updateEditFormat() {
  const form = $("#tournament-form");
  if (!form || !editState) return;
  readEditRules();
  if (editState.format === "knockout") editState.values.legs = 1;
  renderEditRules();
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
      )}</div></fieldset><div class="form-grid"><label>Numero partecipanti<input type="number" name="count" min="2" max="32" value="${wizard.count}" required></label></div>${ruleFieldsetHtml(variantFor(wizard.variant), wizard, wizard.format, { id: "wizard-rule-fields" })}`;
  if (wizardStep === 1)
    body = `<div class="form-grid"><label class="full">${wizard.participant_kind === "team" ? "Come si chiamano le squadre?" : "Chi scende in campo?"}<textarea name="names" placeholder="Un nome per riga, ad esempio:&#10;Falchi&#10;Leoni&#10;Aquile" rows="7">${h(wizard.names)}</textarea></label><label class="full">Una descrizione, se ti va<textarea name="description" maxlength="1000" rows="2" style="min-height:65px" placeholder="Dove si gioca, perché ci incontriamo…">${h(wizard.description)}</textarea></label></div><p class="field-help">Servono ${wizard.count} nomi distinti. Lascia vuoto per usare ${wizard.participant_kind === "team" ? "Team" : "Giocatore"} #1, #2, … Potrai rinominarli in seguito.</p>`;
  if (wizardStep === 2) {
    const v = variantFor(wizard.variant);
    const order =
      wizard.order && wizard.order.length === wizard.count
        ? wizard.order
        : wizardParticipantNames();
    const orderBlock =
      order.length > 1
        ? `<div class="reorder-block"><div class="section-header"><div><h3 class="reorder-title">Ordine di seeding</h3><p class="section-sub">Trascina o usa le frecce per decidere l'ordine di partenza.</p></div><span class="panel-label">${order.length} partecipanti</span></div><ol class="reorder-list" id="wizard-order" aria-label="Ordine dei partecipanti">${order.map((name, i) => `<li class="reorder-item" data-reorder-item data-id="${h(name)}"><span class="reorder-position">${i + 1}</span><button type="button" class="reorder-handle" data-drag-handle aria-label="Sposta ${h(name)}" aria-describedby="reorder-help" aria-keyshortcuts="ArrowUp ArrowDown Home End">${icon("menu")}</button><span class="reorder-name">${h(name)}</span></li>`).join("")}</ol><p class="field-help" id="reorder-help">Trascina con il mouse o il dito. Da tastiera: frecce su/giù per spostare, Home/End per gli estremi.</p><p class="sr-only" id="reorder-live" aria-live="polite"></p></div>`
        : "";
    body = `<div class="panel" style="margin:0;background:#f7f9f0"><p class="eyebrow">TUTTO PRONTO PER GIOCARE</p><h2>${h(wizard.name)}</h2><dl class="details-list"><div><dt>Sport</dt><dd>${h(wizard.sport)}</dd></div><div><dt>Variante</dt><dd>${h(v?.name || wizard.variant || "Standard")}</dd></div><div><dt>Formato</dt><dd>${label(wizard.format)}</dd></div><div><dt>Partecipanti</dt><dd>${wizard.count}</dd></div>${wizard.format === "groups" ? `<div><dt>Qualificazione</dt><dd>${wizard.group_count} gironi · prime ${wizard.qualifiers}</dd></div>` : ""}<div><dt>Gare</dt><dd>${wizard.legs === 2 ? "Andata e ritorno" : "Sola andata"}</dd></div>${v ? `<div><dt>Durata partita</dt><dd>${durationText(v.match_duration)}</dd></div><div><dt>Punteggio</dt><dd>${h(scoringText(v))}</dd></div>` : ""}<div><dt>Classifica</dt><dd>${wizard.win_points}/${wizard.draw_points}/${wizard.loss_points}</dd></div></dl></div>${orderBlock}<p class="field-help">Creeremo il torneo e genereremo gli incontri. La variante porta con sé rose, durata e regolamento: da quel momento potrai modificare i nomi e inserire i risultati.</p>`;
  }
  modal(
    "Il prossimo torneo è il tuo.",
    `<div class="wizard-steps">${["Il torneo", "I partecipanti", "Si comincia"].map((l, i) => `<span class="wizard-step ${i <= wizardStep ? "active" : ""}">0${i + 1} ${l}</span>`).join("")}</div><form id="wizard-form">${body}</form>`,
    `${button(wizardStep ? "Indietro" : "Annulla", wizardStep ? "wizard-back" : "close", "ghost")}<button class="button primary" form="wizard-form" type="submit">${wizardStep === 2 ? "Crea e genera incontri" : "Continua"}${icon("arrow")}</button>`,
    "NUOVA COMPETIZIONE",
  );
  if (wizardStep === 2) {
    enableReorder($("#wizard-order"), (order) => {
      wizard.order = order;
    });
  }
  updateWizardFormat();
}
function updateWizardFormat() {
  if (wizardStep !== 0) return;
  readWizard();
  if (wizard.format === "knockout") wizard.legs = 1;
  const target = $("#wizard-rule-fields");
  if (target)
    target.outerHTML = ruleFieldsetHtml(
      variantFor(wizard.variant),
      wizard,
      wizard.format,
      { id: "wizard-rule-fields" },
    );
}
async function wizardSubmit() {
  const form = $("#wizard-form");
  if (!form.reportValidity()) return;
  readWizard();
  if (wizardStep === 0) {
    if (wizard.format === "knockout") wizard.legs = 1;
    const warnings = ruleWarnings(
      variantFor(wizard.variant),
      wizard,
      wizard.format,
    );
    if (warnings.length) throw new Error(warnings.join(" "));
  }
  if (wizardStep === 1) {
    const names = wizardParticipantNames();
    if (wizard.names.trim() && names.length !== wizard.count)
      throw new Error(
        "Inserisci esattamente " + wizard.count + " nomi, oppure lascia vuoto.",
      );
    if (
      new Set(names.map((n) => n.toLocaleLowerCase("it"))).size !== names.length
    )
      throw new Error("Ogni partecipante deve avere un nome diverso.");
    const current = wizard.order || [];
    const same =
      current.length === names.length &&
      names.every((name) => current.includes(name));
    wizard.order = same ? current : names;
  }
  if (wizardStep < 2) {
    wizardStep++;
    renderWizard();
    return;
  }
  const { count, names, order, ...payload } = wizard;
  payload.team_names =
    order && order.length === count ? order : wizardParticipantNames();
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
    `<p class="project-intro">Open Score è un progetto di Leonardo e del suo collaboratore per organizzare tornei a scuola. Nome e direzione si scelgono insieme al professore.</p><ol class="project-list"><li><strong>Oggi:</strong> una webapp con gironi, tabelloni, risultati, qualificazioni e account docenti separati.</li><li><strong>Il prossimo incontro:</strong> scegliere lo sport, le regole e il primo torneo da provare in palestra.</li><li><strong>Poi:</strong> pianificazione automatica, statistiche e nuovi formati.</li></ol><p class="field-help">Il codice è indipendente. I dati restano sul server della scuola; non è ancora un servizio pubblico su Internet.</p><p class="field-help"><a href="https://github.com/Leonardo-Lalli/Open-score" target="_blank" rel="noopener">Codice, roadmap e report su GitHub ↗</a></p>`,
    `${button("Torna in campo", "close", "primary")}`,
    "IL PROGETTO",
  );
}
function qrSvg(url) {
  if (typeof qrcode !== "function") return "";
  try {
    const qr = qrcode(0, "M");
    qr.addData(url);
    qr.make();
    return qr.createSvgTag({
      cellSize: 5,
      margin: 3,
      scalable: true,
      alt: "Codice QR per aprire la vista spettatore",
      title: "Link spettatore del torneo",
    });
  } catch {
    return "";
  }
}
async function share() {
  const url = location.origin + "/public/" + data.tournament.public_token;
  const qr = qrSvg(url);
  const localOnly = ["localhost", "127.0.0.1", "::1"].includes(
    location.hostname,
  );
  const help = localOnly
    ? "Stai usando localhost: per far funzionare il QR sul telefono apri l'app con l'indirizzo IP del server nella LAN."
    : "L'app è sul tuo computer: il link funziona sui browser che possono raggiungere questo server locale. Per condividerla online servirà l’hosting previsto nella roadmap.";
  modal(
    "Il torneo è più bello insieme.",
    `<p class="project-intro">Condividi calendario, risultati e tabellone con chi segue il torneo. Questa vista è di sola lettura.</p>${qr ? `<div class="share-qr" id="share-qr">${qr}<p class="field-help">Inquadra il QR con il telefono per aprire la vista spettatore.</p></div>` : ""}<div class="share-url"><input id="share-url" aria-label="Link del torneo" value="${h(url)}" readonly><button class="button primary" data-action="copy">Copia link</button></div><div class="share-actions"><button type="button" class="button" data-action="download-qr">Scarica QR</button><button type="button" class="button" data-action="print-qr">Stampa</button><button type="button" class="button" data-action="share-qr">Condividi</button></div><div class="share-invite"><strong>Invitare chi gioca</strong><p class="field-help">Il link di adesione con QR arriverà con l'API inviti del Team A. Oggi puoi condividere la vista spettatore in sola lettura.</p></div><p class="field-help">Visibilità: link pubblico in sola lettura. La modifica della visibilità non è ancora disponibile.</p><p class="field-help">${help}</p>`,
    `<a class="button primary" href="${h(url)}" target="_blank" rel="noopener">Apri vista spettatore ${icon("arrow")}</a>`,
    "CONDIVIDI IL GIOCO",
  );
}
function downloadQr() {
  const svg = $("#share-qr svg");
  if (!svg) {
    notify("QR non disponibile: condividi il link.", true);
    return;
  }
  const source = new XMLSerializer().serializeToString(svg);
  const blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>\n' + source], {
    type: "image/svg+xml;charset=utf-8",
  });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = `qr-${data?.tournament?.public_token || "torneo"}.svg`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(href), 1000);
  notify("QR scaricato in formato SVG.");
}
function printQr() {
  const svg = $("#share-qr svg");
  if (!svg) {
    notify("QR non disponibile: usa il link.", true);
    return;
  }
  document.querySelectorAll("#print-sheet").forEach((el) => el.remove());
  const sheet = document.createElement("div");
  sheet.id = "print-sheet";
  sheet.innerHTML = `<h1>${h(data?.tournament?.name || "Torneo")}</h1><p>Inquadra il QR per aprire il torneo in sola lettura.</p>${svg.outerHTML}<p class="print-url">${h($("#share-url")?.value || "")}</p>`;
  document.body.appendChild(sheet);
  document.body.classList.add("printing");
  let done = false;
  const cleanup = () => {
    if (done) return;
    done = true;
    document.body.classList.remove("printing");
    sheet.remove();
  };
  window.addEventListener("afterprint", cleanup, { once: true });
  setTimeout(cleanup, 60000);
  window.print();
}
async function shareLink() {
  const url = $("#share-url")?.value || "";
  if (navigator.share) {
    try {
      await navigator.share({
        title: data?.tournament?.name || "Open Score",
        text: "Segui il torneo su Open Score",
        url,
      });
      return;
    } catch (e) {
      if (e?.name === "AbortError") return;
    }
  }
  try {
    await navigator.clipboard.writeText(url);
    notify("Condivisione non supportata: link copiato.");
  } catch {
    $("#share-url")?.select();
    notify("Seleziona e copia il link con Ctrl+C.");
  }
}
const actions = {
  dashboard,
  new: () => (canEdit() ? startWizard() : loginModal()),
  catalog: (el) =>
    openCatalog(el?.dataset?.catalogSport || null, el?.dataset?.catalogVariant || null),
  calendar: () => openCalendar(),
  fields: () => openFields(),
  "calendar-refresh": () => reloadCalendar(),
  "calendar-reset": () => {
    calendarFilters = {
      tournament: "all",
      team: "all",
      day: "",
      field: "all",
      status: "all",
    };
    renderCalendar();
  },
  "calendar-open": async (el) => {
    await openTournament(Number(el.dataset.tournament));
    tab = "matches";
    renderTournament();
    if (!canManage()) return;
    const match = data.matches.find((item) => item.id === Number(el.dataset.match));
    if (match) resultModal(match.id);
  },
  "fields-refresh": () => openFields(),
  "field-new": () => fieldModal(),
  "field-edit": (el) => {
    const field = fieldsCache.find((item) => String(item.id) === el.dataset.field);
    if (field) fieldModal(field);
    else notify("Campo non trovato.", true);
  },
  "field-toggle": async (el) => {
    if (!fieldsAdapter.ready) {
      notify("La disattivazione dei campi non è ancora attiva.", true);
      return;
    }
    const field = fieldsCache.find((item) => String(item.id) === el.dataset.field);
    if (!field) return;
    await fieldsAdapter.deactivate(field.id);
    fieldsCache = await fieldsAdapter.list();
    renderFields();
    notify(`Campo “${field.name}” disattivato.`);
  },
  "new-variant": (el) =>
    canEdit()
      ? startWizard(el.dataset.sport, el.dataset.variant)
      : loginModal(),
  print: () => window.print(),
  login: loginModal,
  logout: async () => {
    await api("/auth/logout", { method: "POST" });
    setStoredRole(null);
    auth = { role: null, authenticated: false, teacher: null };
    selectedId = null;
    data = null;
    list = [];
    renderAuthControl();
    showRoleGate("choice");
    notify("Sessione chiusa.");
  },
  project,
  close,
  share,
  edit: editTournament,
  archive: () => {
    if (!requireManage()) return;
    modal(
      "Archiviare il torneo?",
      `<p class="project-intro">“${h(data.tournament.name)}” uscirà dall’elenco principale. Potrai ripristinarlo dal filtro Archiviati: nessun dato viene cancellato.</p>`,
      `${button("Annulla", "close", "ghost")}<button class="button danger" data-confirm-archive>Archivia</button>`,
      "ARCHIVIO",
    );
  },
  restore: async () => {
    if (!requireManage()) return;
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
    if (!requireManage()) return;
    await api("/tournaments/" + selectedId + "/generate", { method: "POST" });
    await openTournament(selectedId, true);
    notify("Incontri generati. Si gioca!");
  },
  "bracket-round": (el) => {
    const round = Number(el.dataset.round);
    const scroll = $(".bracket-scroll");
    if (!scroll || !Number.isFinite(round)) return;
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth";
    scroll.scrollTo({ left: (round - 1) * 295, behavior });
    document.querySelectorAll(".bracket-round-chip").forEach((chip) => {
      const active = chip === el;
      chip.classList.toggle("active", active);
      chip.setAttribute("aria-pressed", String(active));
    });
  },
  "propose-result": (el) => proposeResultModal(el.dataset.match),
  "approve-proposal": async (el) => {
    try {
      await resultProposalsAdapter.decide(el.dataset.proposal, "approve");
      await openTournament(selectedId, true);
      notify("Risultato approvato. Classifica e tabellone aggiornati.");
    } catch (e) {
      if (e.status !== 401) await loadApprovals();
      throw e;
    }
  },
  "reject-proposal": async (el) => {
    try {
      await resultProposalsAdapter.decide(el.dataset.proposal, "reject");
      await loadApprovals();
      notify("Proposta respinta.");
    } catch (e) {
      if (e.status !== 401) await loadApprovals();
      throw e;
    }
  },
  "correct-proposal": (el) => {
    const proposal = approvalsCache.find(
      (item) => String(item.id) === String(el.dataset.proposal),
    );
    if (proposal) proposalCorrectModal(proposal);
    else notify("Proposta non trovata.", true);
  },
  "team-order-move": (el) => {
    const tbody = $("#team-order-body");
    if (!tbody) return;
    const rows = [...tbody.querySelectorAll("[data-reorder-item]")];
    const row = rows.find((item) => item.dataset.id === String(el.dataset.team));
    if (!row) return;
    const index = rows.indexOf(row);
    const to = el.dataset.direction === "up" ? index - 1 : index + 1;
    if (to < 0 || to >= rows.length) return;
    const previous = rows.map((item) => item.dataset.id);
    tbody.insertBefore(
      row,
      el.dataset.direction === "up" ? rows[to] : rows[to].nextSibling,
    );
    saveTeamOrder(
      [...tbody.querySelectorAll("[data-reorder-item]")].map(
        (item) => item.dataset.id,
      ),
      previous,
    );
  },
  "student-team": (el) => {
    studentTeamId = Number(el.dataset.studentTeam);
    renderTournament();
  },
  "bulk-parse": () => renderBulkPreview(),
  "bulk-save": () => saveBulk(),
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
  "download-qr": () => downloadQr(),
  "print-qr": () => printQr(),
  "share-qr": () => shareLink(),
  "invite-join": () => joinInvite(),
  "invite-login": () => {
    pendingInviteToken = inviteToken;
    showRoleGate("login");
  },
  "invite-retry": () => safely(() => openInvite(inviteToken)),
  "wizard-back": () => {
    readWizard();
    wizardStep--;
    renderWizard();
  },
};
document.addEventListener("click", (e) => {
  const a = e.target.closest("[data-action]");
  if (a) {
    e.preventDefault();
    setMenu(false);
    const fn = actions[a.dataset.action];
    if (fn) safely(() => fn(a));
  }
  const open = e.target.closest("[data-open]");
  if (open) {
    setMenu(false);
    safely(() => openTournament(Number(open.dataset.open)));
  }
  if (
    document.body.classList.contains("menu-open") &&
    !e.target.closest("#sidebar") &&
    !e.target.closest("#mobile-menu")
  )
    setMenu(false);
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
document.addEventListener("input", (e) => {
  if (e.target.closest("#wizard-form") && wizardStep === 0) {
    readWizard();
    updateRuleWarnings(
      "wizard-rule-fields",
      variantFor(wizard.variant),
      wizard,
      wizard.format,
    );
    return;
  }
  if (e.target.closest("#tournament-form") && editState) {
    readEditRules();
    updateRuleWarnings(
      "edit-rule-fields",
      variantFor(editState.variant),
      editState.values,
      editState.format,
    );
    return;
  }
  if (e.target.closest("#schedule-form")) {
    updateScheduleConflictHint();
    return;
  }
  if (e.target.id !== "student-team-search") return;
  studentSearch = e.target.value;
  const list = document.querySelector(".students-team-list");
  if (list) list.innerHTML = studentTeamsListHtml();
});
document.addEventListener("change", (e) => {
  const calendarFilter = e.target.closest("[data-calendar-filter]");
  if (calendarFilter) {
    const key = calendarFilter.dataset.calendarFilter;
    calendarFilters[key] = calendarFilter.value;
    if (key === "tournament") calendarFilters.team = "all";
    renderCalendar();
    return;
  }
  if (e.target.closest("#schedule-form")) updateScheduleConflictHint();
  if (e.target.closest("#wizard-form") && wizardStep === 0) {
    readWizard();
    updateRuleWarnings(
      "wizard-rule-fields",
      variantFor(wizard.variant),
      wizard,
      wizard.format,
    );
  }
  if (e.target.closest("#tournament-form") && editState) {
    readEditRules();
    updateRuleWarnings(
      "edit-rule-fields",
      variantFor(editState.variant),
      editState.values,
      editState.format,
    );
  }
  if (e.target.id === "bulk-file") {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const textarea = $("#bulk-names");
      if (textarea) textarea.value = String(reader.result || "");
      renderBulkPreview();
    };
    reader.readAsText(file);
    return;
  }
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
    const rules = $("#wizard-rule-fields");
    if (rules)
      rules.outerHTML = ruleFieldsetHtml(variant, wizard, wizard.format, {
        id: "wizard-rule-fields",
      });
  }
  if (e.target.id === "wizard-variant") {
    readWizard();
    const variant = variantFor(wizard.variant);
    applyVariantToWizard(variant);
    $("#wizard-variant-preview").innerHTML = variantRulesPanel(variant);
    const rules = $("#wizard-rule-fields");
    if (rules)
      rules.outerHTML = ruleFieldsetHtml(variant, wizard, wizard.format, {
        id: "wizard-rule-fields",
      });
  }
  if (e.target.id === "edit-sport") {
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
  if (e.target.name === "format") {
    if ($("#wizard-form")) updateWizardFormat();
    if ($("#tournament-form")) updateEditFormat();
  }
});
document.addEventListener("submit", (e) => {
  e.preventDefault();
  const form = e.target;
  if (form.id === "role-login-form") {
    loginTeacher(new FormData(form));
    return;
  }
  safely(async () => {
    const submitter = e.submitter;
    if (submitter) submitter.disabled = true;
    try {
      const fd = new FormData(form);
      if (form.id === "wizard-form") await wizardSubmit();
      if (form.id === "field-form") {
        const payload = {
          name: String(fd.get("name") || "").trim(),
          description: String(fd.get("description") || "").trim(),
          venue: String(fd.get("venue") || "").trim(),
          availability: String(fd.get("availability") || "").trim(),
          sports: fd.getAll("sports"),
          active: form.dataset.id ? fd.has("active") : true,
        };
        if (!payload.name) throw new Error("Il nome del campo è obbligatorio.");
        if (!fieldsAdapter.ready) {
          const box = $("#form-error");
          if (box) {
            box.textContent =
              "Salvataggio non disponibile: l’API campi del Team A non è ancora attiva. Nessun dato è stato inviato.";
            box.classList.remove("hidden");
          }
          return;
        }
        const fieldId = form.dataset.id ? Number(form.dataset.id) : null;
        await fieldsAdapter.save(payload, fieldId);
        close();
        await openFields();
        notify(fieldId ? "Campo aggiornato." : "Campo creato.");
        return;
      }
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
      if (form.id === "student-form") {
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
        notify("Studente aggiunto alla squadra.");
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
          if (fd.has("format")) payload.format = fd.get("format");
          payload.participant_kind = fd.get("participant_kind");
          const format = payload.format || data.tournament.format;
          const variant = variantFor(editState?.variant || payload.variant);
          for (const field of variantRuleSchema(variant)) {
            if (field.scope === "variant") continue;
            if (field.stages && !field.stages.includes(format)) continue;
            const input = form.querySelector(`[name="${field.key}"]`);
            if (field.type === "checkbox") {
              if (input) payload[field.key] = fd.has(field.key);
              continue;
            }
            if (input) {
              const raw = fd.get(field.key);
              payload[field.key] = field.type === "number" ? Number(raw) : raw;
            } else if (field.disabled) {
              payload[field.key] =
                editState?.values?.[field.key] ?? field.default ?? 0;
            }
          }
          if (format === "knockout") payload.legs = 1;
          const values = {
            ...(editState?.values || {}),
            ...payload,
            count: data.teams.length,
          };
          const warnings = ruleWarnings(
            variantFor(editState?.variant || payload.variant),
            values,
            format,
          );
          if (warnings.length) throw new Error(warnings.join(" "));
        }
        await api(`/tournaments/${selectedId}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
        close();
        await openTournament(selectedId, true);
        notify("Torneo aggiornato.");
      }

      if (form.id === "proposal-form") {
        const match = data.matches.find(
          (item) => item.id === Number(form.dataset.match),
        );
        if (!match) throw new Error("Partita non trovata.");
        const payload = { ...readProposalPayload(form), version: match.version };
        await resultProposalsAdapter.propose(selectedId, match.id, payload);
        close();
        notify("Proposta inviata. Il risultato non è ancora ufficiale.");
      }
      if (form.id === "proposal-correct-form") {
        const payload = readProposalPayload(form);
        await resultProposalsAdapter.decide(
          form.dataset.proposal,
          "correct",
          payload,
        );
        close();
        await openTournament(selectedId, true);
        notify("Proposta corretta; resta in attesa di approvazione.");
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
        try {
          await api(
            `/tournaments/${selectedId}/matches/${m.id}${schedule ? "/schedule" : ""}`,
            { method: "PATCH", body: JSON.stringify(payload) },
          );
        } catch (e) {
          if (schedule) throw scheduleError(e);
          throw e;
        }
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
$("#modal").addEventListener("close", () => {
  document.body.classList.remove("modal-open");
});
$("#mobile-menu").addEventListener("click", () => {
  setMenu(!$("#sidebar").classList.contains("open"));
});
window.addEventListener("resize", () => {
  if (window.innerWidth > 800 && document.body.classList.contains("menu-open"))
    setMenu(false);
});
document.addEventListener("click", (e) => {
  const choice = e.target.closest("[data-role]");
  if (!choice) return;
  e.preventDefault();
  if (choice.dataset.role === "student")
    safely(() => enterStudentMode());
  else if (choice.dataset.role === "teacher") showRoleGate("login");
  else if (choice.dataset.role === "back") {
    if (inviteToken) hideRoleGate();
    else showRoleGate("choice");
  }
});
async function startApp() {
  selectedId = null;
  data = null;
  catalogMode = false;
  calendarMode = false;
  fieldsMode = false;
  tab = "overview";
  await loadSports();
  const route = hashRoute();
  if (route.kind === "sport") await openCatalog(route.sport, route.variant);
  else if (route.kind === "calendar") await openCalendar();
  else if (route.kind === "fields") await openFields();
  else await dashboard();
}
async function init() {
  try {
    if (publicToken) {
      hideRoleGate();
      $("#sidebar").classList.add("hidden");
      $(".app-shell").style.marginLeft = "0";
      $(".top-actions").innerHTML =
        '<span class="context-label">VISTA SPETTATORE · SOLA LETTURA</span>';
      $("#mobile-menu").classList.add("hidden");
      await openTournament(null);
      setInterval(() => {
        if (!document.hidden && !$("#modal").open)
          safely(() => openTournament(null, true));
      }, 30000);
      return;
    }
    if (inviteToken) {
      showInviteShell();
      await loadSession();
      await loadSports().catch(() => {});
      await openInvite(inviteToken);
      return;
    }
    await loadSession();
    if (auth.authenticated) {
      hideRoleGate();
      await startApp();
      return;
    }
    const preference = storedRole();
    if (preference === "student") {
      auth.role = "student";
      hideRoleGate();
      renderAuthControl();
      await startApp();
      return;
    }
    showRoleGate(preference === "teacher" ? "login" : "choice");
    renderAuthControl();
  } catch (e) {
    $("#content").innerHTML =
      `<div class="error-page"><h1>Il campo non è raggiungibile.</h1><p>${h(e.message)}</p><button class="button primary" data-action="refresh">Riprova</button></div>`;
    $("#content").setAttribute("aria-busy", "false");
  }
}
init();
window.addEventListener("hashchange", () => {
  if (publicToken || inviteToken || document.body.classList.contains("role-pending")) return;
  const route = hashRoute();
  safely(() => {
    if (route.kind === "sport") return openCatalog(route.sport, route.variant);
    if (route.kind === "calendar") return openCalendar();
    if (route.kind === "fields") return openFields();
    return dashboard();
  });
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && document.body.classList.contains("menu-open")) {
    setMenu(false);
    return;
  }
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
