export function nodePhotoUrl(node) {
    const gender = node.gender == 'm' || node.gender == 'f' ? node.gender : 'none';
    return node.photo || `images/no-photo-gender-${gender}${node.is_dead ? '-dead' : ''}.jpg`;
}
