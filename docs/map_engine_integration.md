# NORA Map Engine integration

The extractor is designed to be embedded as an iframe inside the NORA Map
Engine (or any host page) and driven via `postMessage`.

## Message the Map Engine sends

```json
{
  "type": "EXTRACT_AREA",
  "datasets": ["dem", "magnetic", "geology"],
  "aoi": {
    "type": "Polygon",
    "coordinates": [[[3.6, 7.7], [4.1, 7.7], [4.1, 8.2], [3.6, 8.2], [3.6, 7.7]]]
  }
}
```

## Host page (Map Engine) - sending the message

```html
<iframe id="extractor" src="https://your-extractor.example.com/embed"></iframe>
<script>
  document.getElementById("extractor").contentWindow.postMessage(
    {
      type: "EXTRACT_AREA",
      datasets: ["global_dem", "magnetic", "geology"],
      aoi: { type: "Polygon", coordinates: [[]] },
    },
    "https://your-extractor.example.com"
  );
</script>
```

## Extractor frontend - receiving the message

Add a listener in `frontend/src/App.tsx` (not yet wired by default - this is
the seam to implement when embedding is turned on):

```ts
useEffect(() => {
  function onMessage(e: MessageEvent) {
    if (e.origin !== TRUSTED_MAP_ENGINE_ORIGIN) return; // always check origin
    const msg = e.data;
    if (msg?.type === "EXTRACT_AREA") {
      handleAoiChange({ aoi_type: "geojson", geojson: msg.aoi }, /* run /api/aoi/validate */);
      handleDatasetChange(msg.datasets, allDatasets);
      goTo(2); // jump straight to "Choose your output"
    }
  }
  window.addEventListener("message", onMessage);
  return () => window.removeEventListener("message", onMessage);
}, []);
```

**Always validate `event.origin`** against an allowlist before trusting a
`postMessage` payload - never process a message from an unexpected origin.

## Sending status back to the Map Engine (optional)

Once a job completes, the extractor can notify the parent frame:

```ts
window.parent.postMessage(
  { type: "EXTRACTION_COMPLETE", job_id, download_url },
  TRUSTED_MAP_ENGINE_ORIGIN
);
```

## CORS

If the Map Engine calls the extractor's API directly (rather than only via
the embedded UI), add its origin to `CORS_ORIGINS` in `.env` /
`render.yaml` instead of leaving it as `["*"]` in production.
