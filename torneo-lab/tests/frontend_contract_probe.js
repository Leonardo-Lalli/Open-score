// Exercise production adapter functions with JSON returned by the Python API.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const calls = [];
const context = {
  URLSearchParams,
  fieldsCache: [input.field],
  FIELD_MESSAGES: {}, CALENDAR_MESSAGES: {},
  apiWithMessages: async (url, options) => { calls.push({url,options}); return {}; },
};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function normalizeCalendarEvent('), source.indexOf('function intervalFor(')), context);
vm.runInContext(source.slice(source.indexOf('const fieldsAdapter ='), source.indexOf('function enableReorder('))+'\nthis.fieldsAdapter=fieldsAdapter;this.calendarAdapter=calendarAdapter;', context);
(async () => {
  const event = context.normalizeCalendarEvent(input.calendar.events[0]);
  const team = context.normalizeCalendarTeam(input.calendar.teams[0]);
  await context.calendarAdapter.list({team: `${team.tournamentId}:${team.id}`,tournament:'all',status:'played'});
  const params = new URL('http://test.local'+calls[0].url).searchParams;
  await context.fieldsAdapter.save({name: input.field.name,sports:input.field.sports,description:'Aggiornata'}, input.field.id);
  const body = JSON.parse(calls[1].options.body);
  process.stdout.write(JSON.stringify({score:event.score,teamTournament:team.tournamentId,teamQuery:params.get('team'),tournamentQuery:params.get('tournament'),availability:body.availability_intervals}));
})().catch(error => { console.error(error); process.exitCode=1; });
