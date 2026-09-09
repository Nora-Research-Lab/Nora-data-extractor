import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { Dataset } from "../types";

interface Props {
  selected: string[];
  onChange: (ids: string[], datasets: Dataset[]) => void;
}

export default function DatasetStep({ selected, onChange }: Props) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listDatasets()
      .then(setDatasets)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function toggle(id: string) {
    const next = selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id];
    onChange(next, datasets);
  }

  const categories = Array.from(new Set(datasets.map((d) => d.category)));

  return (
    <div className="panel">
      <h2>Choose your datasets</h2>
      <p className="help">Select one or more datasets to extract for your area. You can mix rasters and vectors in a single job.</p>

      {loading && <p>Loading dataset catalog...</p>}
      {error && <div className="callout error">{error}</div>}

      {categories.map((cat) => (
        <div key={cat} style={{ marginBottom: 18 }}>
          <h3 style={{ textTransform: "capitalize", fontSize: 13, color: "var(--ink-soft)" }}>{cat}</h3>
          <div className="dataset-list">
            {datasets
              .filter((d) => d.category === cat)
              .map((d) => (
                <label key={d.id} className={`dataset-card ${selected.includes(d.id) ? "selected" : ""}`}>
                  <input type="checkbox" checked={selected.includes(d.id)} onChange={() => toggle(d.id)} />
                  <div>
                    <div>
                      <b>{d.name}</b>
                      <span className={`badge ${d.kind === "vector" ? "vector" : ""}`}>{d.kind}</span>
                    </div>
                    <div className="meta">{d.description}</div>
                    <div className="meta">
                      {d.coverage} coverage{d.resolution ? ` · ${d.resolution} resolution` : ""} · source: {d.source}
                    </div>
                  </div>
                </label>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
