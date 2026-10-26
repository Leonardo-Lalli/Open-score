/**
 * Shareable tournament infographic, built from real tournament data only.
 *
 * The module is DOM-free and UMD-lite: in the browser it exposes
 * `Infographic`, in Node it exports the same API so tests can validate the
 * generated SVG. The caller passes a plain payload; this file contains only
 * presentation and labels, never tournament data.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.Infographic = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const WIDTH = 1080;
  const HEIGHT = 1350;
  const INK = "#182923";
  const MUTED = "#738077";
  const LINE = "#e3e8df";
  const LIME = "#d6f473";
  const GREEN = "#2d694d";
  const PAPER = "#ffffff";
  const BG = "#f6f7f2";

  function escapeXml(value) {
    return String(value ?? "").replace(
      /[&<>"']/g,
      (character) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&apos;",
        })[character],
    );
  }

  function wrapText(value, maxChars, maxLines = 2) {
    const words = String(value ?? "")
      .split(/\s+/)
      .filter(Boolean);
    if (!words.length) return [];
    const lines = [];
    let index = 0;
    while (index < words.length && lines.length < maxLines) {
      let line = words[index];
      index += 1;
      while (
        index < words.length &&
        (line + " " + words[index]).length <= maxChars
      ) {
        line += " " + words[index];
        index += 1;
      }
      lines.push(line);
    }
    if (index < words.length && lines.length) {
      let last = lines[lines.length - 1];
      if (last.length >= maxChars)
        last = last.slice(0, Math.max(1, maxChars - 1));
      lines[lines.length - 1] = last + "…";
    }
    return lines;
  }

  function dateLabel(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return new Intl.DateTimeFormat("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    }).format(date);
  }

  function textBlock(x, y, lines, options = {}) {
    const size = options.size || 24;
    const weight = options.weight || 400;
    const fill = options.fill || INK;
    const lineHeight = options.lineHeight || Math.round(size * 1.18);
    const anchor = options.anchor || "start";
    if (!lines.length) return "";
    return `<text x="${x}" y="${y}" font-family="Segoe UI, Arial, sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}">${lines
      .map(
        (line, index) =>
          `<tspan x="${x}" dy="${index === 0 ? 0 : lineHeight}">${escapeXml(line)}</tspan>`,
      )
      .join("")}</text>`;
  }

  function pill(x, y, label, options = {}) {
    const text = String(label || "");
    const width = Math.max(options.minWidth || 120, text.length * 9 + 34);
    const height = options.height || 38;
    return `<g><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="${height / 2}" fill="${options.fill || INK}"/><text x="${x + width / 2}" y="${y + height / 2 + 6}" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700" fill="${options.color || "#ffffff"}" text-anchor="middle" letter-spacing="1">${escapeXml(text)}</text></g>`;
  }

  function kpi(x, y, value, label) {
    return `<g><rect x="${x}" y="${y}" width="216" height="128" rx="22" fill="${PAPER}" stroke="${LINE}"/><text x="${x + 24}" y="${y + 66}" font-family="Segoe UI, Arial, sans-serif" font-size="44" font-weight="750" fill="${INK}">${escapeXml(value)}</text><text x="${x + 24}" y="${y + 102}" font-family="Segoe UI, Arial, sans-serif" font-size="14" font-weight="600" fill="${MUTED}" letter-spacing="2">${escapeXml(label)}</text></g>`;
  }

  function podiumCard(x, y, place, name, detail, highlight) {
    const background = highlight ? LIME : PAPER;
    const detailText = detail ? String(detail) : "";
    return `<g><rect x="${x}" y="${y}" width="296" height="150" rx="22" fill="${background}" stroke="${highlight ? LIME : LINE}"/><text x="${x + 24}" y="${y + 46}" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700" fill="${highlight ? GREEN : MUTED}" letter-spacing="2">${place}</text>${textBlock(
      x + 24,
      y + 84,
      wrapText(name || "Da definire", 18, 2),
      { size: 24, weight: 700, fill: INK },
    )}<text x="${x + 24}" y="${y + 128}" font-family="Segoe UI, Arial, sans-serif" font-size="14" fill="${highlight ? GREEN : MUTED}">${escapeXml(detailText)}</text></g>`;
  }

  function qrBlock(qr, x, y, size) {
    if (!qr || !Array.isArray(qr.matrix) || !qr.matrix.length)
      return `<g><rect x="${x}" y="${y}" width="${size}" height="${size}" rx="18" fill="${PAPER}" stroke="${LINE}"/><text x="${x + size / 2}" y="${y + size / 2}" font-family="Segoe UI, Arial, sans-serif" font-size="15" fill="${MUTED}" text-anchor="middle">Link pubblico non disponibile</text></g>`;
    const count = qr.matrix.length;
    const cell = size / count;
    const modules = [];
    for (let row = 0; row < count; row += 1) {
      for (let column = 0; column < count; column += 1) {
        if (!qr.matrix[row][column]) continue;
        modules.push(
          `<rect x="${(x + column * cell).toFixed(2)}" y="${(y + row * cell).toFixed(2)}" width="${cell.toFixed(2)}" height="${cell.toFixed(2)}" fill="${INK}"/>`,
        );
      }
    }
    return `<g><rect x="${x}" y="${y}" width="${size}" height="${size}" rx="18" fill="${PAPER}" stroke="${LINE}"/>${modules.join("")}</g>`;
  }

  function buildSvg(payload, options = {}) {
    const data = payload || {};
    const title = wrapText(data.title || "Torneo", 26, 2);
    const sport = [data.sport, data.variant].filter(Boolean).join(" · ");
    const podium = Array.isArray(data.podium) ? data.podium.slice(0, 3) : [];
    const qualifiers = Array.isArray(data.qualifiers) ? data.qualifiers : [];
    const hasChampion = Boolean(data.champion);
    const progress = Math.max(0, Math.min(100, Number(data.progress) || 0));

    const titleBottom = 150 + (title.length - 1) * 56;
    const metaY = Math.max(210, titleBottom + 46);
    const kpiY = metaY + 44;
    const championY = kpiY + 246;
    const podiumY = hasChampion ? championY + 120 : championY + 10;
    const qualifierY = podiumY + 182;

    const kpiRow = [
      kpi(72, kpiY, String(data.teams ?? 0), "SQUADRE"),
      kpi(312, kpiY, String(data.students ?? 0), "STUDENTI"),
      kpi(552, kpiY, String(data.matches ?? 0), "PARTITE"),
      kpi(792, kpiY, `${progress}%`, "AVANZAMENTO"),
    ].join("");

    const progressBar = `<g><rect x="72" y="${kpiY + 158}" width="936" height="14" rx="7" fill="${LINE}"/><rect x="72" y="${kpiY + 158}" width="${(936 * progress) / 100}" height="14" rx="7" fill="${GREEN}"/><text x="72" y="${kpiY + 202}" font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="${MUTED}">${escapeXml(`${data.completed ?? 0} completate · ${data.remaining ?? 0} rimanenti`)}</text><text x="1008" y="${kpiY + 202}" font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="${MUTED}" text-anchor="end">${escapeXml(data.status || "")}</text></g>`;

    const championBanner = hasChampion
      ? `<g><rect x="72" y="${championY}" width="936" height="92" rx="22" fill="${INK}"/><text x="104" y="${championY + 36}" font-family="Segoe UI, Arial, sans-serif" font-size="14" font-weight="700" fill="${LIME}" letter-spacing="2">${escapeXml(data.winnerLabel || "CAMPIONE")}</text><text x="104" y="${championY + 74}" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="750" fill="#ffffff">${escapeXml(data.champion)}</text></g>`
      : "";

    const podiumCards = podium.length
      ? podium
          .map((entry, index) => {
            const x = 72 + index * 320;
            return podiumCard(
              x,
              podiumY,
              `${index + 1}°`,
              entry.name,
              entry.detail,
              index === 0,
            );
          })
          .join("") +
        `<text x="72" y="${podiumY - 18}" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700" fill="${MUTED}" letter-spacing="2">${escapeXml(data.podiumLabel || "PODIO")}</text>`
      : `<rect x="72" y="${podiumY}" width="936" height="150" rx="22" fill="${PAPER}" stroke="${LINE}"/><text x="108" y="${podiumY + 84}" font-family="Segoe UI, Arial, sans-serif" font-size="22" fill="${MUTED}">Classifica in aggiornamento</text>`;

    const qualifierItems = qualifiers.slice(0, 6);
    const qualifierBlock = qualifierItems.length
      ? `<text x="72" y="${qualifierY}" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700" fill="${MUTED}" letter-spacing="2">QUALIFICATI</text>${qualifierItems
          .map(
            (item, index) =>
              `<text x="72" y="${qualifierY + 36 + index * 30}" font-family="Segoe UI, Arial, sans-serif" font-size="19" fill="${INK}">${escapeXml(item.group ? item.group + " · " : "")}${escapeXml(item.name)}</text>`,
          )
          .join("")}${qualifiers.length > 6 ? `<text x="72" y="${qualifierY + 36 + 6 * 30}" font-family="Segoe UI, Arial, sans-serif" font-size="15" fill="${MUTED}">e altri ${qualifiers.length - 6}</text>` : ""}`
      : "";

    const qrY = 1080;
    const qr = qrBlock(data.qr, 72, qrY, 200);
    const qrText = data.qr
      ? `<text x="300" y="${qrY + 70}" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="700" fill="${INK}">Inquadra per seguire il torneo</text>${textBlock(
          300,
          qrY + 104,
          wrapText(data.qr.url, 46, 2),
          { size: 14, fill: MUTED },
        )}`
      : `<text x="300" y="${qrY + 70}" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="700" fill="${INK}">Condivisione pubblica non attiva</text><text x="300" y="${qrY + 104}" font-family="Segoe UI, Arial, sans-serif" font-size="14" fill="${MUTED}">Il link pubblico non è disponibile per questo torneo.</text>`;

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${HEIGHT}" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-label="${escapeXml(`${data.title || "Torneo"} · ${sport || ""} · infografica`)}"><rect width="${WIDTH}" height="${HEIGHT}" fill="${BG}"/><rect width="${WIDTH}" height="10" fill="${LIME}"/><text x="72" y="86" font-family="Segoe UI, Arial, sans-serif" font-size="17" font-weight="700" fill="${MUTED}" letter-spacing="4">OPEN SCORE</text>${pill(
      1008 -
        Math.max(120, String(data.status || "").length * 9 + 34),
      66,
      data.status || "IN CORSO",
    )}${textBlock(72, 150, title, { size: 46, weight: 750, fill: INK, lineHeight: 56 })}${textBlock(
      72,
      metaY,
      [sport || "Sport", data.period || "Periodo da definire"],
      { size: 20, fill: GREEN, lineHeight: 30 },
    )}${kpiRow}${progressBar}${championBanner}${podiumCards}${qualifierBlock}${qr}${qrText}<line x1="72" y1="1318" x2="1008" y2="1318" stroke="${LINE}"/><text x="72" y="1344" font-family="Segoe UI, Arial, sans-serif" font-size="14" fill="${MUTED}">Open Score · torneo scolastico</text><text x="1008" y="1344" font-family="Segoe UI, Arial, sans-serif" font-size="14" fill="${MUTED}" text-anchor="end">${escapeXml(data.generatedAt ? dateLabel(data.generatedAt) : "")}</text></svg>`;
    return options.xmlDeclaration
      ? `<?xml version="1.0" encoding="UTF-8"?>\n${svg}`
      : svg;
  }

  return {
    buildSvg,
    escapeXml,
    wrapText,
    constants: { WIDTH, HEIGHT },
  };
});
