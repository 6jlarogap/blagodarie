export const PROFILE_NODE_SIZE = 50;
export const DEFAULT_NODE_SIZE = 25;

export function nodePhotoUrl(node) {
    const gender = node.gender == 'm' || node.gender == 'f' ? node.gender : 'none';
    return node.photo || `images/no-photo-gender-${gender}${node.is_dead ? '-dead' : ''}.jpg`;
}

function sameNodeIdentity(node, other) {
    if (!node || !other) return false;
    if (node.uuid && other.uuid) return node.uuid === other.uuid;
    return node.id != null && other.id != null && String(node.id) === String(other.id);
}

export function nodeSize(node, rootNode) {
    return sameNodeIdentity(node, rootNode) ? PROFILE_NODE_SIZE : DEFAULT_NODE_SIZE;
}
