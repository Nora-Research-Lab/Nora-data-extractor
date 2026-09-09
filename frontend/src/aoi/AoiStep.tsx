import { useState } from "react";
import MapPreview from "../map/MapPreview";
import { api } from "../services/api";
import type { AoiRequest, AoiValidationResult, BBox } from "../types";

interface Props {
  aoi: AoiRequest | null;
  onChange: (aoi: AoiRequest, validation: AoiValidationResult) => void;
}

type Tab = "coordinates" | "draw" | "geojson";

export default function AoiStep({ aoi, onChange }: Props) {
  const [tab, setTab] = useState<Tab>("coordinates");
  const [bbox, setBbox] = useState<BBox>(
    aoi?.bbox ?? { north: 8.2, south: 7.7, east: 4.1, west: 3.6 }
  );
  const [geojsonText, setGeojsonText] = useState("");
  const [validation, setValidation] = useState<AoiValidationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runValidation(req: AoiRequest) {
    setBusy(true);
    setError(null);
    try {
      const result = await api.validateAoi(req);
      setValidation(result);
      if (result.valid) onChange(req, result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function submitBbox() {
    runValidation({ aoi_type: "bbox", bbox });
  }

  function submitGeojson() {
    try {
      const parsed = JSON.parse(geojsonText);
      runValidation({ aoi_type: "geojson", geojson: parsed });
    } catch {
      setError("That doesn't look like valid JSON.");
    }
  }

  function onRectangleDrawn(b: BBox) {
    setBbox(b);
    runValidation({ aoi_type: "bbox", bbox: b });
  }

  return (
    <div className="layout-2col">
      <div className="panel">
        <h2>Choose your area</h2>
        <p className="help">Pick the region you want to extract data for.</p>

        <div className="tab-row">
          <button className={tab === "coordinates" ? "active" : ""} onClick={() => setTab("coordinates")}>
            Coordinates
          </button>
          <button className={tab === "draw" ? "active" : ""} onClick={() => setTab("draw")}>
            Draw on map
          </button>
          <button className={tab === "geojson" ? "active" : ""} onClick={() => setTab("geojson")}>
            Upload / paste GeoJSON
          </button>
        </div>

        {tab === "coordinates" && (
          <>
            <div className="field-row">
              <div>
                <label>North</label>
                <input type="number" value={bbox.north} onChange={(e) => setBbox({ ...bbox, north: +e.target.value })} />
              </div>
              <div>
                <label>South</label>
                <input type="number" value={bbox.south} onChange={(e) => setBbox({ ...bbox, south: +e.target.value })} />
              </div>
            </div>
            <div className="field-row">
              <div>
                <label>East</label>
                <input type="number" value={bbox.east} onChange={(e) => setBbox({ ...bbox, east: +e.target.value })} />
              </div>
              <div>
                <label>West</label>
                <input type="number" value={bbox.west} onChange={(e) => setBbox({ ...bbox, west: +e.target.value })} />
              </div>
            </div>
            <button className="btn btn-primary" onClick={submitBbox} disabled={busy}>
              {busy ? "Checking..." : "Use this area"}
            </button>
          </>
        )}

        {tab === "draw" && (
          <p className="help">Click and drag a rectangle directly on the map to the right.</p>
        )}

        {tab === "geojson" && (
          <>
            <label>Paste a GeoJSON Polygon / Feature / FeatureCollection</label>
            <textarea
              rows={8}
              value={geojsonText}
              onChange={(e) => setGeojsonText(e.target.value)}
              placeholder='{"type":"Polygon","coordinates":[[...]]}'
            />
            <div style={{ height: 10 }} />
            <button className="btn btn-primary" onClick={submitGeojson} disabled={busy}>
              {busy ? "Checking..." : "Use this area"}
            </button>
          </>
        )}

        {error && <div className="callout error" style={{ marginTop: 14 }}>{error}</div>}

        {validation && (
          <div className={`callout ${validation.valid ? "" : "error"}`} style={{ marginTop: 14 }}>
            {validation.valid ? (
              <>Area of interest is valid — approximately <b>{validation.area_km2?.toLocaleString()} km²</b>.</>
            ) : (
              <>{validation.errors.join(" ")}</>
            )}
            {validation.warnings?.map((w, i) => <div key={i}>⚠ {w}</div>)}
          </div>
        )}
      </div>

      <MapPreview
        aoiGeojson={validation?.geojson ?? null}
        drawEnabled={tab === "draw"}
        onRectangleDrawn={onRectangleDrawn}
      />
    </div>
  );
}
