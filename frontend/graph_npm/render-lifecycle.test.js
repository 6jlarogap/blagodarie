import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { nodePhotoUrl } from './node-visual.js';
import {
    nodeSize,
    PROFILE_NODE_SIZE,
} from './node-visual.js';
import { shortestTrustPathLinks } from './trust-path-button.js';
import { bindRenderLifecycle } from './render-lifecycle.js';

test('shared graph renderer always creates visible photo nodes', async () => {
    const thumbnail = 'https://api.example/thumbnail/128x128.jpg';
    assert.equal(nodePhotoUrl({ photo: thumbnail }), thumbnail);
    assert.equal(
        nodePhotoUrl({ photo: '', gender: 'f', is_dead: true }),
        'images/no-photo-gender-f-dead.jpg',
    );

    const source = await readFile(new URL('./main.js', import.meta.url), 'utf8');
    assert.match(source, /ForceGraph3D\(\)[\s\S]*?\.nodeThreeObject\(node => node_draw\(node\)\)/);
    assert.match(source, /sprite\.add\(label\);\s*node\.__labelObj = label;/);
    const showNodeDetail = source.match(/function show_node_detail[\s\S]*?\n    }/)[0];
    assert.doesNotMatch(showNodeDetail, /new SpriteText/);
    assert.match(showNodeDetail, /node\.__labelObj\.visible = true/);
});

test('Schema renderer exposes a mobile reset-view control', async () => {
    const html = await readFile(new URL('./index.html', import.meta.url), 'utf8');
    const source = await readFile(new URL('./main.js', import.meta.url), 'utf8');
    assert.match(html, /<button id="reset-view-button"[^>]*title="Сбросить вид"[^>]*aria-label="Сбросить вид"/);
    assert.match(html, /#reset-view-button\s*\{[\s\S]*position: fixed;[\s\S]*top: 12px;[\s\S]*right: 12px;/);
    assert.match(source, /querySelector\('#reset-view-button'\)[\s\S]*?clear_trust_path_highlight\(\);[\s\S]*?Graph\.zoomToFit\(750, 40\)/);
    assert.match(html, /<button id="show-trust-path-button"[^>]*title="Подсветить кратчайшие пути доверия"[^>]*aria-label="Подсветить кратчайшие пути доверия"[^>]*hidden>/);
    assert.match(html, /#show-trust-path-button\s*\{[\s\S]*top: 64px;[\s\S]*right: 12px;/);
    assert.match(source, /shortestTrustPathLinks\(\s*data\.nodes, data\.links, viewer_uuid, data\.root_node && data\.root_node\.uuid/);
    assert.match(source, /linkColor\(link => highlighted_trust_path_links\.has\(link\)/);
    assert.match(source, /linkWidth\(link => highlighted_trust_path_links\.has\(link\)/);
    assert.doesNotMatch(source, /trustPathUrl|window\.location\.assign\(path\)/);
    assert.doesNotMatch(source, /anchorOwnNode|own_profile_anchor|canShowOwnProfileAnchor/);
});

test('Schema highlights all loaded directed shortest trust paths', () => {
    const nodes = ['viewer', 'left', 'right', 'root', 'outside'].map((uuid, id) => ({id, uuid}));
    const direct = {source: 0, target: 3, attitude: 't'};
    assert.deepEqual(shortestTrustPathLinks(nodes, [direct], 'viewer', 'root'), [direct]);

    const links = [
        {source: 0, target: 1, attitude: 't'},
        {source: 0, target: 2, attitude: 'a'},
        {source: 1, target: 3, attitude: 'a'},
        {source: 2, target: 3, attitude: 't'},
        {source: 1, target: 0, attitude: 't'}, // cycle
        {source: 4, target: 3, attitude: 't'}, // wrong direction
        {source: 0, target: 3, attitude: 'mt'},
    ];
    assert.deepEqual(shortestTrustPathLinks(nodes, links, 'viewer', 'root'), links.slice(0, 4));
    assert.deepEqual(shortestTrustPathLinks(nodes, links, 'root', 'viewer'), []);
    assert.deepEqual(shortestTrustPathLinks(nodes, links, 'viewer', 'outside'), []);
    assert.deepEqual(shortestTrustPathLinks(nodes, links, 'viewer', 'viewer'), []);
});

test('root profile remains the larger Schema node', () => {
    const own = {id: 7, uuid: 'own'};
    const root = {id: 9, uuid: 'root'};
    assert.equal(nodeSize(root, root), PROFILE_NODE_SIZE);
    assert.equal(nodeSize(own, root), 25);
});

test('Род renderer uses explicit wider link spacing', async () => {
    const source = await readFile(new URL('./main.js', import.meta.url), 'utf8');
    assert.match(
        source,
        /const ROD_LINK_DISTANCE = 195;\s*Graph\.d3Force\('link'\)\.distance\(parm_user_genesis_tree \? ROD_LINK_DISTANCE : 195\)/,
    );
});

test('rendering pauses when idle or hidden and resumes on interaction', async () => {
    const target = new EventTarget();
    target.hidden = false;
    const calls = { pause: 0, resume: 0 };
    const lifecycle = bindRenderLifecycle({
        pauseAnimation: () => calls.pause++,
        resumeAnimation: () => calls.resume++,
    }, target, 10);

    lifecycle.resume();
    lifecycle.keepAlive();
    await new Promise(resolve => setTimeout(resolve, 20));
    assert.deepEqual(calls, { pause: 0, resume: 1 });

    lifecycle.idle();
    await new Promise(resolve => setTimeout(resolve, 20));
    assert.deepEqual(calls, { pause: 1, resume: 1 });

    target.hidden = true;
    target.dispatchEvent(new Event('visibilitychange'));
    target.dispatchEvent(new Event('pointerdown'));
    assert.deepEqual(calls, { pause: 2, resume: 1 });

    target.hidden = false;
    target.dispatchEvent(new Event('visibilitychange'));
    await new Promise(resolve => setTimeout(resolve, 20));
    assert.deepEqual(calls, { pause: 3, resume: 2 });
});
