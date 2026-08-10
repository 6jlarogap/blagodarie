const endpointId = endpoint => typeof endpoint === 'object' ? endpoint.id : endpoint;

export function shortestTrustPathLinks(nodes, links, viewerUuid, rootUuid) {
    if (!viewerUuid || !rootUuid || viewerUuid === rootUuid) return [];

    const viewer = nodes.find(node => node.uuid === viewerUuid);
    const root = nodes.find(node => node.uuid === rootUuid);
    if (!viewer || !root) return [];

    const nodeIds = new Set(nodes.map(node => node.id));
    const outgoing = new Map();
    for (const link of links) {
        const source = endpointId(link.source);
        const target = endpointId(link.target);
        if (!['a', 't'].includes(link.attitude) || !nodeIds.has(source) || !nodeIds.has(target)) continue;
        if (!outgoing.has(source)) outgoing.set(source, []);
        outgoing.get(source).push(link);
    }

    const distances = new Map([[viewer.id, 0]]);
    const predecessors = new Map();
    const queue = [viewer.id];
    for (let index = 0; index < queue.length; index++) {
        const source = queue[index];
        for (const link of outgoing.get(source) || []) {
            const target = endpointId(link.target);
            const distance = distances.get(source) + 1;
            if (!distances.has(target)) {
                distances.set(target, distance);
                predecessors.set(target, [link]);
                queue.push(target);
            } else if (distances.get(target) === distance) {
                predecessors.get(target).push(link);
            }
        }
    }
    if (!distances.has(root.id)) return [];

    const selected = new Set();
    const pending = [root.id];
    const visited = new Set();
    while (pending.length) {
        const target = pending.pop();
        if (visited.has(target)) continue;
        visited.add(target);
        for (const link of predecessors.get(target) || []) {
            selected.add(link);
            pending.push(endpointId(link.source));
        }
    }
    return links
        .filter(link => selected.has(link))
        .sort((left, right) => distances.get(endpointId(left.target)) - distances.get(endpointId(right.target)));
}
