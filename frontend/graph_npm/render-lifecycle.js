export function bindRenderLifecycle(graph, target = document, idleMs = 1000) {
    let idleTimer = null;
    const keepAlive = () => {
        if (idleTimer !== null) clearTimeout(idleTimer);
        idleTimer = null;
    };
    const pause = () => {
        keepAlive();
        graph.pauseAnimation();
    };
    const idle = () => {
        keepAlive();
        idleTimer = setTimeout(pause, idleMs);
    };
    const resume = () => {
        if (target.hidden) return;
        graph.resumeAnimation();
        idle();
    };

    for (const event of ['pointermove', 'pointerdown', 'wheel', 'keydown']) {
        target.addEventListener(event, resume, { passive: true });
    }
    target.addEventListener('visibilitychange', () => target.hidden ? pause() : resume());

    return { idle, keepAlive, pause, resume };
}
