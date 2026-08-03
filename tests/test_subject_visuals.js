const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

function source(path) {
  return fs.readFileSync(path, 'utf8');
}

function block(src) {
  return src.match(/\/\/ SUBJECT_VISUALS_START([\s\S]+?)\/\/ SUBJECT_VISUALS_END/)[1];
}

function functionSource(src, name) {
  const start = src.indexOf(`function ${name}`);
  assert.notEqual(start, -1, name);
  const bodyStart = src.indexOf('{', src.indexOf(')', start));
  let depth = 0;
  for (let i = bodyStart; i < src.length; i += 1) {
    if (src[i] === '{') depth += 1;
    if (src[i] === '}') depth -= 1;
    if (depth === 0) return src.slice(start, i + 1);
  }
  throw new Error(`unterminated ${name}`);
}

function run(code, sandbox = {}) {
  vm.runInNewContext(code, sandbox, { filename: 'subject-visuals.vm.js' });
  return sandbox;
}

function loadVisuals(path) {
  return run(block(source(path)), { Object });
}

function loadGenesis(width) {
  const src = source('frontend/genesis/code.js');
  return run([
    'var NODE_TYPES = { USER: "user", FRIEND: "friend", PROFILE: "profile_root", FILTERED: "filtered" };',
    `var width = ${width};`,
    block(src),
    functionSource(src, 'subjectSizeName'),
    functionSource(src, 'subjectRadius'),
    functionSource(src, 'subjectClipId'),
    functionSource(src, 'subjectShapePath'),
    functionSource(src, 'initSubjectClipPaths'),
  ].join('\n'), { Object, Set });
}

function loadGenesisKeyboard() {
  const src = source('frontend/genesis/code.js');
  return run([
    'var NODE_TYPES = { USER: "user", FRIEND: "friend", PROFILE: "profile_root", FILTERED: "filtered", HOME: "home" };',
    'var clicks = [];',
    'function onNodeClick(username, nodeType) { clicks.push([username, nodeType]); }',
    functionSource(src, 'isNodeClickable'),
    functionSource(src, 'activateNode'),
    functionSource(src, 'activateNodeFromKey'),
  ].join('\n'));
}

function loadGenesisSimulationTick() {
  const src = source('frontend/genesis/code.js');
  const calls = [];
  const simulation = {
    on(event, callback) {
      calls.push(['on', event, callback]);
      this.callback = callback;
    },
  };
  const sandbox = {
    calls,
    simulation,
    ticked() { calls.push(['tick']); },
    loading: { next() { calls.push(['loading']); } },
  };
  return run(functionSource(src, 'firstSimulationTick'), sandbox);
}

function fakeNode(tag) {
  return {
    tag,
    attrs: {},
    children: [],
    attr(name, value) {
      this.attrs[name] = value;
      return this;
    },
    append(childTag) {
      const child = fakeNode(childTag);
      this.children.push(child);
      return child;
    },
    setAttribute(name, value) {
      this.attrs[name] = value;
    },
    appendChild(child) {
      this.children.push(child);
    },
  };
}

function loadRentMap() {
  const src = source('frontend/rent_map/code.js');
  const document = {
    createElement: fakeNode,
    createTextNode(text) {
      return { tag: '#text', textContent: String(text) };
    },
  };
  return run([
    block(src),
    functionSource(src, 'escapeHtml'),
    functionSource(src, 'subjectLabel'),
    functionSource(src, 'markerHtml'),
    functionSource(src, 'appendFallbackSubject'),
  ].join('\n'), { Object, document });
}

const genesis = loadVisuals('frontend/genesis/code.js');
const rentMap = loadVisuals('frontend/rent_map/code.js');
const expected = {
  person: ['circle', ''],
  organization: ['rounded-square', '🏢'],
  bot: ['square', '⚙'],
  group: ['hexagon', '👥'],
  channel: ['diamond', '📣'],
  unknown: ['circle', '?']
};

for (const [kind, [shape, badge]] of Object.entries(expected)) {
  for (const app of [genesis, rentMap]) {
    const visual = app.subjectVisualFor({ subject_kind: kind, subject_kind_confirmed: kind !== 'unknown' });
    assert.equal(visual.kind, kind);
    assert.equal(visual.shape, shape);
    assert.equal(visual.badge, badge);
    assert.ok(!/^[OBGC]$/.test(visual.badge));
  }
}

assert.equal(genesis.subjectVisualFor({ is_org: true }).kind, 'organization');
assert.equal(rentMap.subjectVisualFor({ is_org: true }).kind, 'organization');
assert.equal(genesis.subjectVisualFor({ subject_kind: 'future-kind' }).kind, 'person');
assert.equal(rentMap.subjectVisualFor({ subject_kind: 'future-kind' }).kind, 'person');
assert.equal(rentMap.subjectVisualFor({ subject_kind: 'future-kind' }).shape, 'circle');
assert.equal(rentMap.subjectVisualFor({ subject_kind: 'unknown', subject_kind_confirmed: false }).confirmed, false);
for (const app of [genesis, rentMap]) {
  const visual = app.subjectVisualFor({ subject_kind: 'x" onclick="alert(1)', is_org: true });
  assert.equal(visual.kind, 'person');
  assert.equal(visual.shape, 'circle');
}

for (const width of [390, 1280]) {
  const app = loadGenesis(width);
  assert.equal(app.subjectSizeName({ nodeType: 'friend' }), width < 900 ? 'small' : 'medium');
  assert.equal(app.subjectClipId({ nodeType: 'friend', subject_kind: 'group' }), `clip-hexagon-${width < 900 ? 'small' : 'medium'}`);
  assert.match(app.subjectShapePath('hexagon', 16), /^M0,-16L13\.92,-8/);
  assert.match(app.subjectShapePath('diamond', 16), /^M0,-16L16,0/);
  const defs = fakeNode('defs');
  app.initSubjectClipPaths(defs);
  assert.ok(defs.children.some(node => node.attrs.id === 'clip-hexagon-small'));
  assert.ok(defs.children.some(node => node.attrs.id === 'clip-diamond-large'));
}

const rent = loadRentMap();
const marker = rent.markerHtml({
  title: '<Group>',
  subject_kind: 'group',
  subject_kind_label: 'Группа',
}, true);
assert.match(marker, /class="rent-marker[^"]*is-selected/);
const outerClassMatch = marker.match(/^<div class="([^"]*)"/);
assert.ok(outerClassMatch);
assert.doesNotMatch(outerClassMatch[1], /subject-shape-[a-z-]+/);
assert.match(marker, /rent-marker-frame subject-shape-hexagon/);
assert.match(marker, /subject-marker-badge">👥<\/span>/);
assert.match(marker, /&lt;Group&gt;: Группа/);
assert.ok(!/subject-shape-hexagon[^>]*>R[^<]*<span class="subject-marker-badge"/.test(marker));

const button = fakeNode('button');
rent.appendFallbackSubject(button, { subject_kind: 'channel', subject_kind_confirmed: false });
assert.equal(button.children[0].className, 'fallback-subject subject-shape-diamond is-unconfirmed');
assert.equal(button.children[0].textContent, '📣');

const maliciousMarker = rent.markerHtml({ title: 'Bad', subject_kind: 'x" onclick="alert(1)' }, false);
assert.match(maliciousMarker, /subject-kind-person/);
assert.doesNotMatch(maliciousMarker, /onclick|alert\(1\)|subject-kind-x/);

const genesisSource = source('frontend/genesis/code.js');
assert.match(genesisSource, /\.attr\("fill", "#16221d"\)[\s\S]*\.attr\("class", \[NODE_TYPES\.USER, NODE_TYPES\.PROFILE\]/);
const graphLoad = genesisSource.slice(genesisSource.indexOf('d3.json(apiUrl'), genesisSource.indexOf('links.push('));
assert.doesNotMatch(graphLoad, /urlAsBase64|base64Url|fetch\(/);
assert.match(functionSource(genesisSource, 'prepareSvg'), /await Promise\.all\(nodes\.map\([\s\S]*imageBase64Url\(node\.image\)/);
assert.match(functionSource(genesisSource, 'makeSvgBlob'), /const prepared = await prepareSvg\('main'\)/);
const urlAsBase64Source = 'async ' + functionSource(genesisSource, 'urlAsBase64');
const imageConversion = run(urlAsBase64Source, {
  fetch: async () => { throw new Error('network'); },
  blobAsBase64: async () => 'data:image/jpeg;base64,eA==',
  console: { warn() {} },
});
imageConversion.urlAsBase64('https://example.invalid/photo.jpg').then(result => {
  assert.equal(result, 'https://example.invalid/photo.jpg');
});
const successfulImageConversion = run(urlAsBase64Source, {
  fetch: async () => ({ ok: true, blob: async () => ({}) }),
  blobAsBase64: async () => 'data:image/jpeg;base64,eA==',
  console: { warn() {} },
});
successfulImageConversion.urlAsBase64('https://example.test/photo.jpg').then(result => {
  assert.equal(result, 'data:image/jpeg;base64,eA==');
});
const d2 = run(functionSource(genesisSource, 'buildLinks'), { Map });
assert.deepEqual(d2.buildLinks([
  { source: 'a', target: 'b', is_trust: false },
  { source: 'b', target: 'a', is_trust: true },
  { source: 'b', target: 'c', is_trust: null },
]), [
  { source: 'a', target: 'b', is_trust: true, reverse_is_trust: true },
  { source: 'b', target: 'a', is_trust: true, reverse_is_trust: false },
  { source: 'b', target: 'c', is_trust: true, reverse_is_trust: true },
]);
assert.doesNotMatch(genesisSource, /new Worker|alphaTarget\(1\)/);
assert.doesNotMatch(genesisSource, /\.on\('end', \(\) => loading\.next\(\)\)/);
assert.match(genesisSource, /\.on\('tick', firstSimulationTick\)/);
assert.match(genesisSource, /\.alphaDecay\(0\.1\)/);
const firstTick = loadGenesisSimulationTick();
firstTick.firstSimulationTick();
assert.deepEqual(firstTick.calls.slice(0, 3).map(call => call.slice(0, 2)), [
  ['tick'],
  ['loading'],
  ['on', 'tick'],
]);
firstTick.simulation.callback();
assert.deepEqual(firstTick.calls[3], ['tick']);
assert.doesNotMatch(genesisSource, /\.attr\('onclick'/);
assert.match(genesisSource, /\.attr\('role', d => isNodeClickable\(d\.nodeType\) \? 'button' : 'img'\)/);
assert.match(genesisSource, /\.attr\('tabindex', d => isNodeClickable\(d\.nodeType\) \? 0 : null\)/);
const keyboard = loadGenesisKeyboard();
assert.equal(keyboard.isNodeClickable('friend'), true);
assert.equal(keyboard.isNodeClickable('home'), false);
const enter = { key: 'Enter', preventDefault() { this.prevented = true; } };
keyboard.activateNodeFromKey(enter, { username: 'alice', nodeType: 'friend' });
assert.equal(enter.prevented, true);
const space = { key: ' ', preventDefault() { this.prevented = true; } };
keyboard.activateNodeFromKey(space, { username: 'bob', nodeType: 'filtered' });
assert.equal(space.prevented, true);
const escape = { key: 'Escape', preventDefault() { this.prevented = true; } };
keyboard.activateNodeFromKey(escape, { username: 'carol', nodeType: 'friend' });
assert.equal(escape.prevented, undefined);
assert.deepEqual(keyboard.clicks, [['alice', 'friend'], ['bob', 'filtered']]);

const rentStyle = source('frontend/rent_map/style.css');
const genesisStyle = source('frontend/genesis/style.css');
const genesisNameStyle = genesisStyle.match(/\.userName, \.friendName \{([^}]+)\}/)[1];
assert.match(genesisNameStyle, /fill: #16221d;/);
assert.doesNotMatch(genesisNameStyle, /paint-order|stroke/);
assert.match(genesisStyle, /#main \{[\s\S]*background-color: #ffffff;/);
const mediaNginx = source('deploy/nginx/sites-available/api.doverabot.ru');
assert.match(mediaNginx, /"https:\/\/doverabot\.ru" \$http_origin;/);
assert.ok(mediaNginx.includes('~^https://(?:d2|d3|map|mgraph)\\.doverabot\\.ru$ $http_origin;'));
assert.match(mediaNginx, /location \/media\/ \{[\s\S]*add_header Access-Control-Allow-Origin \$doverabot_media_origin always;[\s\S]*add_header Vary Origin always;/);
assert.doesNotMatch(mediaNginx, /Access-Control-Allow-Credentials|Access-Control-Allow-Origin\s+["']?\*/);
assert.match(rentStyle, /\.subject-legend \{[\s\S]*left: 56px;/);
const mobileLegendTopMatch = rentStyle.match(/@media \(max-width: 520px\) \{[\s\S]*\.subject-legend \{[\s\S]*top: (\d+)px;/);
assert.ok(mobileLegendTopMatch);
assert.ok(Number(mobileLegendTopMatch[1]) > 66, `mobile legend top must clear the 66px Leaflet control bottom, got ${mobileLegendTopMatch[1]}px`);

for (const htmlPath of ['frontend/genesis/index.html', 'frontend/rent_map/index.html']) {
  const html = source(htmlPath);
  assert.match(html, /class="subject-legend"/);
  assert.match(html, /aria-label="[^"]+"/);
  assert.match(html, /🏢/);
  assert.match(html, /⚙/);
  assert.match(html, /👥/);
  assert.match(html, /📣/);
}
