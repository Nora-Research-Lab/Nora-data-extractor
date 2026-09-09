import { useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import type { AoiRequest, AoiValidationResult, Dataset, ExtractionJobStatus, ProcessingOptions } from "../types";

interface Props {
  aoi: AoiRequest;
  aoiValidation: AoiValidationResult;
  datasets: Dataset[];
  formats: Record<string, string>;
  processing: ProcessingOptions;
  studyAreaName: string;
  onStudyAreaNameChange: (v: string) => void;
}

const STAGES: { key: string; label: string }[] = [
  { key: "preparing", label: "Preparing" },
  { key: "extracting", label: "Extracting" },
  { key: "converting", label: "Converting" },
  { key: "packaging", label: "Packaging" },
  { key: "complete", label: "Complete" },
];

export default function ReviewExtractStep({
  aoi, aoiValidation, datasets, formats, processing, studyAreaName, onStudyAreaNameChange,
}: Props) {
  const [job, setJob] = useState<ExtractionJobStatus | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  useEffect(() => () => {
    if (pollRef.current) window.clearInterval(pollRef.current);
  }, []);

  async function startExtraction() {
    setSubmitting(true);
    setError(null);
    try {
      const { job_id } = await api.createExtraction({
        aoi,
        datasets: datasets.map((d) => ({ dataset_id: d.id, output_format: formats[d.id] })),
        processing,
        study_area_name: studyAreaName || "study_area",
      });
      poll(job_id);
    } catch (e: any) {
      setError(e.message);
      setSubmitting(false);
    }
  }

  function poll(jobId: string) {
    const tick = async () => {
      try {
        const status = await api.getExtraction(jobId);
        setJob(status);
        if (status.status === "completed" || status.status === "failed") {
          if (pollRef.current) window.clearInterval(pollRef.current);
        }
      } catch (e: any) {
        setError(e.message);
        if (pollRef.current) window.clearInterval(pollRef.current);
      }
    };
    tick();
    pollRef.current = window.setInterval(tick, 1200);
  }

  const stageIndex = job ? STAGES.findIndex((s) => s.key === job.stage) : -1;

  return (
    <div className="panel">
      <h2>Review and extract</h2>

      {!job && (
        <>
          <div className="review-section">
            <h3>Study area name</h3>
            <input type="text" value={studyAreaName} onChange={(e) => onStudyAreaNameChange(e.target.value)} />
          </div>

          <div className="review-section">
            <h3>Area of interest</h3>
            <div className="kv"><b>Approx. area</b><span>{aoiValidation.area_km2?.toLocaleString()} km²</span></div>
            {aoiValidation.bbox && (
              <div className="kv">
                <b>Bounding box</b>
                <span>
                  N {aoiValidation.bbox.north}, S {aoiValidation.bbox.south}, E {aoiValidation.bbox.east}, W {aoiValidation.bbox.west}
                </span>
              </div>
            )}
          </div>

          <div className="review-section">
            <h3>Datasets & formats</h3>
            {datasets.map((d) => (
              <div className="kv" key={d.id}>
                <b>{d.name}</b><span>{formats[d.id]}</span>
              </div>
            ))}
          </div>

          <div className="review-section">
            <h3>Processing</h3>
            <div className="kv"><b>Mode</b><span>{processing.mode}</span></div>
            <div className="kv"><b>Clip to area</b><span>{processing.clip ? "Yes" : "No"}</span></div>
            {processing.reproject_to && <div className="kv"><b>Reproject to</b><span>{processing.reproject_to}</span></div>}
          </div>

          {error && <div className="callout error">{error}</div>}

          <button className="btn btn-primary" onClick={startExtraction} disabled={submitting}>
            {submitting ? "Starting..." : "Extract data"}
          </button>
        </>
      )}

      {job && (
        <div>
          <div className="stage-list" style={{ marginBottom: 6 }}>
            {STAGES.map((s, i) => (
              <span key={s.key} className={`stage ${i === stageIndex ? "active" : i < stageIndex ? "done" : ""}`}>
                {s.label}{i < STAGES.length - 1 ? " →" : ""}
              </span>
            ))}
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${job.progress_pct ?? 0}%` }} />
          </div>
          <p className="help">{job.message}</p>

          {job.status === "failed" && (
            <div className="callout error">Extraction failed: {job.error ?? "Unknown error"}</div>
          )}

          {job.status === "completed" && (
            <div className="download-box">
              <div className="icon">📦</div>
              <h2>Your study area package is ready</h2>
              <p className="help">Includes each dataset, metadata.json, and a README describing the extraction.</p>
              <a className="btn btn-primary" href={job.download_url ?? "#"} download>
                Download ZIP
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
