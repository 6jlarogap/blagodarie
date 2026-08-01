import assert from 'node:assert/strict';
import test from 'node:test';

import { bindRenderLifecycle } from './render-lifecycle.js';

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
