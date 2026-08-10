const endpointId = endpoint => typeof endpoint === 'object' ? endpoint.id : endpoint;

export function allTrustPathLinks(nodes, links, viewerUuid, rootUuid) {
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

    const reverse = new Map();
    for (const [source, sourceLinks] of outgoing) {
        for (const link of sourceLinks) {
            const target = endpointId(link.target);
            if (!reverse.has(target)) reverse.set(target, []);
            reverse.get(target).push(source);
        }
    }
    const canReachRoot = new Set([root.id]);
    const pending = [root.id];
    for (let index = 0; index < pending.length; index++) {
        for (const source of reverse.get(pending[index]) || []) {
            if (!canReachRoot.has(source)) {
                canReachRoot.add(source);
                pending.push(source);
            }
        }
    }
    if (!canReachRoot.has(viewer.id)) return [];

    const selected = new Set();
    // ponytail: exhaustive paths fit the paginated Schema; bound traversal if graph sizes grow.
    const visit = (source, path) => {
        let reachesRoot = source === root.id;
        for (const link of outgoing.get(source) || []) {
            const target = endpointId(link.target);
            if (!canReachRoot.has(target) || path.has(target)) continue;
            const nextPath = new Set(path);
            nextPath.add(target);
            if (visit(target, nextPath)) {
                selected.add(link);
                reachesRoot = true;
            }
        }
        return reachesRoot;
    };
    visit(viewer.id, new Set([viewer.id]));
    return links
        .filter(link => selected.has(link))
}
