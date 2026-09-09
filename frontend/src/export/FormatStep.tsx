import type { Dataset, ProcessingOptions } from "../types";

interface Props {
  datasets: Dataset[];
  formats: Record<string, string>;
  onFormatsChange: (formats: Record<string, string>) => void;
  processing: ProcessingOptions;
  onProcessingChange: (p: ProcessingOptions) => void;
}

const CRS_OPTIONS = [
  { value: "", label: "Automatic (keep native / best fit)" },
  { value: "EPSG:4326", label: "WGS84 (EPSG:4326)" },
  { value: "EPSG:3857", label: "Web Mercator (EPSG:3857)" },
  { value: "EPSG:32631", label: "UTM Zone 31N (EPSG:32631)" },
  { value: "custom", label: "Custom EPSG code..." },
];

export default function FormatStep({ datasets, formats, onFormatsChange, processing, onProcessingChange }: Props) {
  function setFormat(id: string, fmt: string) {
    onFormatsChange({ ...formats, [id]: fmt });
  }

  function setP<K extends keyof ProcessingOptions>(key: K, value: ProcessingOptions[K]) {
    onProcessingChange({ ...processing, [key]: value });
  }

  return (
    <div className="panel">
      <h2>Choose your output</h2>
      <p className="help">We recommend a format for each dataset, but you can change it.</p>

      {datasets.map((d) => (
        <div key={d.id} className="format-row">
          <div>
            <b>{d.name}</b>
            <div className="meta" style={{ fontSize: 12, color: "var(--ink-soft)" }}>
              {d.format_options.find((f) => f.format === (formats[d.id] || ""))?.description}
            </div>
          </div>
          <select value={formats[d.id]} onChange={(e) => setFormat(d.id, e.target.value)}>
            {d.format_options.map((f) => (
              <option key={f.format} value={f.format}>
                {f.format} {f.recommended ? "(recommended)" : ""}
              </option>
            ))}
          </select>
        </div>
      ))}

      <div style={{ height: 22 }} />

      <div className="tab-row advanced-toggle">
        <button className={processing.mode === "basic" ? "active" : ""} onClick={() => setP("mode", "basic")}>
          Basic
        </button>
        <button className={processing.mode === "advanced" ? "active" : ""} onClick={() => setP("mode", "advanced")}>
          Advanced
        </button>
      </div>

      <label style={{ display: "flex", alignItems: "center", gap: 8, textTransform: "none" }}>
        <input type="checkbox" checked={processing.clip} onChange={(e) => setP("clip", e.target.checked)} />
        Clip precisely to my area (recommended)
      </label>

      {processing.mode === "advanced" && (
        <div style={{ marginTop: 16 }}>
          <div className="field-row">
            <div>
              <label>Reproject to</label>
              <select
                value={CRS_OPTIONS.some((o) => o.value === processing.reproject_to) ? processing.reproject_to ?? "" : "custom"}
                onChange={(e) => setP("reproject_to", e.target.value === "" ? null : e.target.value)}
              >
                {CRS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Resampling (raster)</label>
              <select value={processing.resample ?? ""} onChange={(e) => setP("resample", (e.target.value || null) as any)}>
                <option value="">Default</option>
                <option value="nearest">Nearest (categorical data)</option>
                <option value="bilinear">Bilinear (smooth, continuous data)</option>
                <option value="cubic">Cubic (highest quality)</option>
              </select>
            </div>
          </div>

          <div className="field-row">
            <div>
              <label>Simplify tolerance (vector)</label>
              <input
                type="number" step="0.0001" placeholder="e.g. 0.001"
                value={processing.simplify_tolerance ?? ""}
                onChange={(e) => setP("simplify_tolerance", e.target.value ? +e.target.value : null)}
              />
            </div>
            <div>
              <label>Buffer (meters)</label>
              <input
                type="number" placeholder="e.g. 500"
                value={processing.buffer_meters ?? ""}
                onChange={(e) => setP("buffer_meters", e.target.value ? +e.target.value : null)}
              />
            </div>
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: 8, textTransform: "none", marginBottom: 12 }}>
            <input type="checkbox" checked={processing.dissolve} onChange={(e) => setP("dissolve", e.target.checked)} />
            Dissolve features (merge by attribute)
          </label>
          {processing.dissolve && (
            <div style={{ marginBottom: 12 }}>
              <label>Dissolve by attribute</label>
              <input type="text" placeholder="e.g. unit" value={processing.dissolve_by ?? ""} onChange={(e) => setP("dissolve_by", e.target.value || null)} />
            </div>
          )}

          <label>Attribute filter (vector)</label>
          <input
            type="text" placeholder='e.g. mineral == "Gold"'
            value={processing.attribute_filter ?? ""}
            onChange={(e) => setP("attribute_filter", e.target.value || null)}
          />
        </div>
      )}
    </div>
  );
}
