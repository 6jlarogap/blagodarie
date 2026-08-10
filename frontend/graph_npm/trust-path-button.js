export function trustPathUrl(basePath, viewerUuid, rootUuid) {
    if (!basePath || !viewerUuid || !rootUuid || viewerUuid === rootUuid) return '';
    const separator = basePath.includes('?') ? '&' : '?';
    return `${basePath}${separator}user_trust_path=${viewerUuid},${rootUuid}`;
}
