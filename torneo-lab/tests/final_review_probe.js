// Execute production functions, including navigation while a request is pending.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const box = {innerHTML: ''};
const notice = {textContent: ''};
let resolveRequest;
let renders = 0;
const ctx = {
  selectedId: 1, tab: 'stats', data: {tournament: {id: 1}, matches: [], teams: []},
  approvalSummary: {tournamentId: null, count: null},
  approvalsCache: [], approvalsTournamentId: null,
  resultProposalsAdapter: {ready: true, list: async () => [{id: 1}, {id: 2}]},
  canManage: () => true, publicToken: null,
  api: () => new Promise(resolve => {resolveRequest = resolve;}),
  renderTournament: () => {renders++;},
  currentVariant: () => null, label: () => '', stateLabel: () => '', periodLabel: () => '',
  infographicPodium: () => [], infographicQualifiers: () => [], infographicChampion: () => null,
  location: {origin: 'http://test.local'}, Date,
  $: selector => selector === '#upcoming-matches' ? box : selector === '#pending-proposals' ? notice : null,
};
vm.createContext(ctx);
const start = source.indexOf('function buildInfographicPayload(');
vm.runInContext(source.slice(start, source.indexOf('\nfunction ', start + 1)), ctx);
vm.runInContext(source.slice(source.indexOf('async function loadPendingCount('), source.indexOf('function proposalScoreFields(')), ctx);
vm.runInContext(source.slice(source.indexOf('async function loadUpcoming('), source.indexOf('function loadingMarkup(')), ctx);
(async () => {
  assert.equal(ctx.buildInfographicPayload().pending, null);
  const first = ctx.loadPendingCount();
  resolveRequest({pending_proposals: 3});
  await first;
  assert.equal(ctx.buildInfographicPayload().pending, 3);
  assert.equal(renders, 1);
  ctx.selectedId = 2;
  ctx.data.tournament.id = 2;
  assert.equal(ctx.buildInfographicPayload().pending, null);
  const stale = ctx.loadPendingCount();
  const completeOld = resolveRequest;
  ctx.selectedId = 1;
  ctx.data.tournament.id = 1;
  ctx.approvalSummary = {tournamentId: null, count: null};
  completeOld({pending_proposals: 99});
  await stale;
  assert.equal(ctx.buildInfographicPayload().pending, null);
  ctx.canManage = () => false;
  ctx.approvalSummary = {tournamentId: 1, count: 30};
  assert.equal(ctx.buildInfographicPayload().pending, null);
  const dashboard = ctx.loadUpcoming();
  resolveRequest({pending_proposals: 2, upcoming: []});
  await dashboard;
  assert.match(notice.textContent, /^2 proposte da verificare/);
  process.stdout.write('Pending counts scoped, unknown states and stale responses verified.\n');
})().catch(error => {console.error(error); process.exitCode = 1;});
