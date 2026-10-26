/**
 * Test asset: builds the same dependency tree as `engine.knockout_plan`
 * and prints the pure layout for several bracket sizes.
 * Run with: node tests/bracket_layout_probe.js
 */
const { layout } = require("../static/bracket-layout.js");

function planFor(teamCount) {
  const size = 1 << Math.ceil(Math.log2(Math.max(2, teamCount)));
  let order = [1, 2];
  while (order.length < size) {
    const total = order.length * 2 + 1;
    const next = [];
    for (const value of order) next.push(value, total - value);
    order = next;
  }
  const slots = order.map((slot) => (slot <= teamCount ? slot : null));
  const plan = [];
  for (let position = 0; position < size / 2; position += 1) {
    const home = slots[2 * position];
    const away = slots[2 * position + 1];
    plan.push({
      id: position + 1,
      round_no: 1,
      position,
      home_team_id: home,
      away_team_id: away,
      source_home: null,
      source_away: null,
      is_bye: home === null || away === null ? 1 : 0,
    });
  }
  let previous = plan.map((match) => match.id);
  let round = 2;
  while (previous.length > 1) {
    const current = [];
    for (let position = 0; position < previous.length / 2; position += 1) {
      const id = plan.length + 1;
      plan.push({
        id,
        round_no: round,
        position,
        home_team_id: null,
        away_team_id: null,
        source_home: previous[2 * position],
        source_away: previous[2 * position + 1],
        is_bye: 0,
      });
      current.push(id);
    }
    previous = current;
    round += 1;
  }
  return plan;
}

const scenarios = {};
for (const teamCount of [4, 8, 16, 6, 5]) {
  const fixtures = planFor(teamCount);
  const result = layout(fixtures);
  const withScores = fixtures.map((match, index) => ({
    ...match,
    home_score: index % 2 ? 1 : null,
    away_score: index % 2 ? 0 : null,
    status: index % 2 ? "completed" : "waiting",
  }));
  const scored = layout(withScores);
  const reversed = layout([...fixtures].reverse());
  scenarios[teamCount] = {
    rounds: result.rounds,
    labels: result.labels,
    first: result.first,
    width: result.width,
    height: result.height,
    coords: result.coords,
    paths: result.paths,
    champion: result.champion,
    byes: fixtures.filter((match) => match.is_bye).length,
    fixtures: fixtures.map((match) => ({
      id: match.id,
      round_no: match.round_no,
      position: match.position,
      source_home: match.source_home,
      source_away: match.source_away,
    })),
    scoreInvariant:
      JSON.stringify(scored.coords) === JSON.stringify(result.coords) &&
      JSON.stringify(scored.paths) === JSON.stringify(result.paths),
    orderInvariant:
      JSON.stringify(reversed.coords) === JSON.stringify(result.coords) &&
      reversed.paths
        .map((path) => path.d)
        .sort()
        .join("|") ===
        result.paths
          .map((path) => path.d)
          .sort()
          .join("|"),
  };
}
console.log(JSON.stringify(scenarios));
