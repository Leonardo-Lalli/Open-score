/**
 * Pure layout for the knockout bracket.
 *
 * The progression is derived only from `source_home` / `source_away`, the
 * dependency ids returned by the backend. Array order is never used to invent
 * a winner. Scores and statuses do not move cards: they only change the card
 * content produced by app.js.
 *
 * UMD-lite: in the browser it exposes `BracketLayout`, in Node it exports the
 * same object so tests can exercise the geometry without a DOM.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BracketLayout = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const COLUMN = 295;
  const CARD_WIDTH = 246;
  const CARD_HEIGHT = 84;
  const ROW = 128;
  const TITLE_OFFSET = 40;
  const CONNECTOR = 24;

  function roundLabels(roundNumbers) {
    return roundNumbers.map((round, index) => {
      const remaining = roundNumbers.length - index - 1;
      if (remaining === 0) return "Finale";
      if (remaining === 1) return "Semifinali";
      if (remaining === 2) return "Quarti di finale";
      if (remaining === 3) return "Ottavi di finale";
      return "Turno " + round;
    });
  }

  function layout(fixtures) {
    const list = (fixtures || []).filter(
      (match) => match && Number.isFinite(Number(match.round_no)),
    );
    if (!list.length)
      return {
        fixtures: [],
        rounds: 0,
        roundNumbers: [],
        labels: [],
        first: 0,
        width: 0,
        height: 0,
        coords: {},
        paths: [],
        lines: "",
        champion: null,
        cardWidth: CARD_WIDTH,
        cardHeight: CARD_HEIGHT,
        columnWidth: COLUMN,
      };

    const roundNumbers = [...new Set(list.map((m) => Number(m.round_no)))].sort(
      (a, b) => a - b,
    );
    const labels = roundLabels(roundNumbers);
    const firstRound = roundNumbers[0];
    const first = list.filter((m) => Number(m.round_no) === firstRound).length;
    const coords = {};
    for (const match of list) {
      const roundIndex = roundNumbers.indexOf(Number(match.round_no));
      const position = Number(match.position) || 0;
      coords[String(match.id)] = {
        x: roundIndex * COLUMN,
        y: TITLE_OFFSET + 2 ** roundIndex * ROW * (position + 0.5),
        roundIndex,
      };
    }

    const paths = [];
    for (const match of list) {
      const end = coords[String(match.id)];
      for (const source of [match.source_home, match.source_away]) {
        if (source === null || source === undefined) continue;
        const from = coords[String(source)];
        if (!from) continue;
        paths.push({
          fromMatch: String(source),
          toMatch: String(match.id),
          d: `M${from.x + CARD_WIDTH},${from.y}H${from.x + CARD_WIDTH + CONNECTOR}V${end.y}H${end.x}`,
        });
      }
    }

    const finalRound = roundNumbers[roundNumbers.length - 1];
    const finalMatch =
      list.find(
        (m) => Number(m.round_no) === finalRound && Number(m.position) === 0,
      ) || list.find((m) => Number(m.round_no) === finalRound);
    const finalCoord = finalMatch ? coords[String(finalMatch.id)] : null;
    const championX = roundNumbers.length * COLUMN;
    const champion = finalCoord
      ? {
          x: championX,
          y: finalCoord.y,
          d: `M${finalCoord.x + CARD_WIDTH},${finalCoord.y}H${championX}`,
        }
      : null;
    if (champion) {
      paths.push({ fromMatch: String(finalMatch.id), toMatch: "champion", d: champion.d });
    }

    return {
      fixtures: list,
      rounds: roundNumbers.length,
      roundNumbers,
      labels,
      first,
      width: (roundNumbers.length + 1) * COLUMN - 48,
      height: Math.max(210, first * ROW + 60),
      coords,
      paths,
      lines: paths.map((path) => path.d).join(""),
      champion,
      cardWidth: CARD_WIDTH,
      cardHeight: CARD_HEIGHT,
      columnWidth: COLUMN,
    };
  }

  return {
    layout,
    roundLabels,
    constants: { COLUMN, CARD_WIDTH, CARD_HEIGHT, ROW, TITLE_OFFSET, CONNECTOR },
  };
});
