import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { nodePhotoUrl } from './node-visual.js';
import {
    anchorOwnNode,
    canShowOwnProfileAnchor,
    findOwnNode,
    nodeSize,
    PROFILE_NODE_SIZE,
} from './own-profile-anchor.js';
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
    assert.match(source, /querySelector\('#reset-view-button'\)\.addEventListener\('click', \(\) => Graph\.zoomToFit\(750, 40\)\)/);
    assert.match(html, /<button id="anchor-own-profile-button"[^>]*title="Показать и закрепить мой профиль"[^>]*aria-label="Показать и закрепить мой профиль"[^>]*hidden>/);
    assert.match(html, /#anchor-own-profile-button\s*\{[\s\S]*top: 64px;[\s\S]*right: 12px;/);
    assert.match(source, /canShowOwnProfileAnchor\(\s*Boolean\(parm_user_trusts\)/);
    assert.match(source, /anchorOwnNode\(Graph, own_profile_node/);
});

test('own Schema anchor resolves identity, sizes, pins, and repeats idempotently', () => {
    const own = {id: 7, uuid: 'own', __threeObj: {scale: {set(...size) { this.size = size; }}}};
    const root = {id: 9, uuid: 'root'};
    assert.equal(findOwnNode([root, own], {user_id: 7, user_uuid: 'own'}), own);
    assert.equal(canShowOwnProfileAnchor(true, {user_uuid: 'own'}, [root, own]), true);
    assert.equal(canShowOwnProfileAnchor(false, {user_uuid: 'own'}, [root, own]), false);
    assert.equal(canShowOwnProfileAnchor(true, {user_uuid: 'missing'}, [root, own]), false);
    assert.equal(nodeSize(root, root), PROFILE_NODE_SIZE);
    assert.equal(nodeSize(own, root), 25);

    const points = [];
    const graph = {
        screen2GraphCoords(point) {
            points.push(point);
            return {x: 1, y: -2, z: 3};
        },
        d3ReheatSimulation() {},
    };
    assert.equal(anchorOwnNode(graph, own, {width: 400, height: 800}), true);
    assert.deepEqual(own.__threeObj.scale.size, [PROFILE_NODE_SIZE, PROFILE_NODE_SIZE]);
    assert.deepEqual([own.fx, own.fy, own.fz], [1, -2, 3]);
    assert.equal(nodeSize(own, root), PROFILE_NODE_SIZE);
    assert.equal(anchorOwnNode(graph, own, {width: 400, height: 800}), true);
    assert.equal(points.length, 2);
    assert.deepEqual(points[0], points[1]);
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
