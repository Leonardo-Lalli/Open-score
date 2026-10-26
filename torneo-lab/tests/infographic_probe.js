/**
 * Test asset: renders the infographic SVG from a plain payload.
 * Run with: node tests/infographic_probe.js
 */
const { buildSvg } = require("../static/infographic.js");

const payload = {
  title: "Coppa <5A> & amici",
  sport: "Calcio",
  variant: "Calcio a 5",
  format: "Gironi + fase finale",
  status: "In corso",
  period: "3 novembre 2026 – 10 novembre 2026",
  teams: 8,
  students: 42,
  matches: 15,
  completed: 6,
  remaining: 9,
  progress: 40,
  pending: null,
  podium: [
    { name: "5A", detail: "12 punti · 4V 0N 1P" },
    { name: "5B", detail: "9 punti · 3V 0N 2P" },
    { name: "5C", detail: "6 punti · 2V 0N 3P" },
  ],
  qualifiers: [
    { group: "Girone A", name: "5A" },
    { group: "Girone A", name: "5B" },
    { group: "Girone B", name: "5C" },
  ],
  champion: "5A",
  winnerLabel: "CAMPIONE",
  qr: {
    url: "http://192.168.1.10:8000/public/abc",
    matrix: Array.from({ length: 21 }, () =>
      Array.from({ length: 21 }, () => true),
    ),
  },
  generatedAt: "2026-10-26T12:00:00.000Z",
};

const strict = buildSvg(payload, { xmlDeclaration: true });
const inline = buildSvg(payload, { xmlDeclaration: false });
const noQr = buildSvg(
  {
    ...payload,
    champion: null,
    podium: [],
    qualifiers: [],
    qr: null,
  },
  { xmlDeclaration: false },
);
const minimal = buildSvg({}, { xmlDeclaration: false });

console.log(
  JSON.stringify({
    strict,
    inline,
    noQr,
    minimal,
    strictStart: strict.slice(0, 60),
    inlineStart: inline.slice(0, 60),
    qrRects: (strict.match(/<rect /g) || []).length,
    noQrRects: (noQr.match(/<rect /g) || []).length,
  }),
);
