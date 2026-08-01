# D3 graph build

Source was recovered from
[`6jlarogap/blagodarie-site`](https://github.com/6jlarogap/blagodarie-site/tree/2848bbdcf8afe5acf7ea53a595cf16a8acee2193/graph_npm).
The local source preserves the three later production fixes: local fallback
images, no startup popup, and a larger focal node.

Use Node `24.16.0` (`.nvmrc`) and npm `12.0.1` (`packageManager`), then run:

```bash
npm ci
npm run build
node --check dist/assets/*.js
```

The lockfile is exact. Do not run `npm audit fix` as part of a reproducibility
build.

## Recovery evidence

On 2026-08-01, the upstream source and lockfile built
`index-CKyl77MJ.js` with SHA-256
`a5ac1b9b7507fe70c2ecef33330fe792c5f7f5be9ef02ecf2a3d1e7ad9ff0dd0`,
byte-identical to the repository's initial mirrored artifact at commit
`4574df4927f844393802335fd74fc077ea0d304e`.

The recovered local source differs from upstream only at the three fixes named
above. Its build produced `index-BDunKCU0.js` with SHA-256
`17fce4b1c0c9162cec83cf817827f239dcf38d1710fdc157b7ff8d3d4356fba4`;
after normalizing only the generated asset URL, its HTML was byte-identical to
the tracked deployed HTML. The tracked bundle stays unchanged until a later
renderer slice intentionally builds and deploys it.
