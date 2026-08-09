export const PROFILE_NODE_SIZE = 50;
export const DEFAULT_NODE_SIZE = 25;

export function sameNodeIdentity(node, other) {
    if (!node || !other) return false;
    if (node.uuid && other.uuid) return node.uuid === other.uuid;
    return node.id != null && other.id != null && String(node.id) === String(other.id);
}

export function findOwnNode(nodes, authData) {
    if (!Array.isArray(nodes) || !authData) return null;
    return nodes.find(node => (
        authData.user_uuid && node.uuid === authData.user_uuid
    ) || (
        authData.user_id != null && node.id != null && String(node.id) === String(authData.user_id)
    )) || null;
}

export function canShowOwnProfileAnchor(schemaMode, authData, nodes) {
    return Boolean(schemaMode && findOwnNode(nodes, authData));
}

export function nodeSize(node, rootNode) {
    return node.__ownProfileAnchored || sameNodeIdentity(node, rootNode)
        ? PROFILE_NODE_SIZE
        : DEFAULT_NODE_SIZE;
}

export function anchorOwnNode(Graph, node, {width, height, bottom = 96} = {}) {
    if (!Graph || !node || !Number.isFinite(width) || !Number.isFinite(height)) return false;
    const point = Graph.screen2GraphCoords({
        x: width / 2,
        y: Math.max(0, height - bottom),
        z: 0,
    });
    if (!point || !['x', 'y', 'z'].every(axis => Number.isFinite(point[axis]))) return false;
    node.__ownProfileAnchored = true;
    node.x = node.fx = point.x;
    node.y = node.fy = point.y;
    node.z = node.fz = point.z;
    if (node.__threeObj) node.__threeObj.scale.set(PROFILE_NODE_SIZE, PROFILE_NODE_SIZE);
    if (Graph.d3ReheatSimulation) Graph.d3ReheatSimulation();
    return true;
}
