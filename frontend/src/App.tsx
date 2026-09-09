import { useState } from "react";
import Stepper from "./components/Stepper";
import AoiStep from "./aoi/AoiStep";
import DatasetStep from "./datasets/DatasetStep";
import FormatStep from "./export/FormatStep";
import ReviewExtractStep from "./extraction/ReviewExtractStep";
import type { AoiRequest, AoiValidationResult, Dataset, ProcessingOptions } from "./types";

const STEPS = ["Choose your area", "Choose your datasets", "Choose your output", "Review and extract"];

const DEFAULT_PROCESSING: ProcessingOptions = {
  mode: "basic",
  clip: true,
  reproject_to: null,
  resample: null,
  target_resolution: null,
  simplify_tolerance: null,
  dissolve: false,
  dissolve_by: null,
  buffer_meters: null,
  attribute_filter: null,
};

export default function App() {
  const [step, setStep] = useState(0);
  const [furthest, setFurthest] = useState(0);

  const [aoi, setAoi] = useState<AoiRequest | null>(null);
  const [aoiValidation, setAoiValidation] = useState<AoiValidationResult | null>(null);

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [allDatasets, setAllDatasets] = useState<Dataset[]>([]);

  const [formats, setFormats] = useState<Record<string, string>>({});
  const [processing, setProcessing] = useState<ProcessingOptions>(DEFAULT_PROCESSING);
  const [studyAreaName, setStudyAreaName] = useState("study_area");

  function goTo(i: number) {
    setStep(i);
    setFurthest((f) => Math.max(f, i));
  }

  function handleAoiChange(req: AoiRequest, validation: AoiValidationResult) {
    setAoi(req);
    setAoiValidation(validation);
  }

  function handleDatasetChange(ids: string[], datasets: Dataset[]) {
    setSelectedIds(ids);
    setAllDatasets(datasets);
    setFormats((prev) => {
      const next = { ...prev };
      for (const id of ids) {
        if (!next[id]) {
          const ds = datasets.find((d) => d.id === id);
          next[id] = ds?.format_options.find((f) => f.recommended)?.format ?? ds?.format_options[0]?.format ?? "";
        }
      }
      return next;
    });
  }

  const selectedDatasets = allDatasets.filter((d) => selectedIds.includes(d.id));

  const canProceed = [
    !!aoiValidation?.valid,
    selectedIds.length > 0,
    true,
    true,
  ];

  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>NORA Data Extractor</h1>
        <span className="tag">Extract geospatial data for your area of interest — no GIS software required.</span>
      </div>

      <Stepper steps={STEPS} current={step} furthestReached={furthest} onSelect={goTo} />

      {step === 0 && <AoiStep aoi={aoi} onChange={handleAoiChange} />}

      {step === 1 && <DatasetStep selected={selectedIds} onChange={handleDatasetChange} />}

      {step === 2 && (
        <FormatStep
          datasets={selectedDatasets}
          formats={formats}
          onFormatsChange={setFormats}
          processing={processing}
          onProcessingChange={setProcessing}
        />
      )}

      {step === 3 && aoi && aoiValidation && (
        <ReviewExtractStep
          aoi={aoi}
          aoiValidation={aoiValidation}
          datasets={selectedDatasets}
          formats={formats}
          processing={processing}
          studyAreaName={studyAreaName}
          onStudyAreaNameChange={setStudyAreaName}
        />
      )}

      {step < 3 && (
        <div className="footer-nav">
          <button className="btn btn-ghost" disabled={step === 0} onClick={() => goTo(step - 1)}>
            Back
          </button>
          <button className="btn btn-primary" disabled={!canProceed[step]} onClick={() => goTo(step + 1)}>
            Continue
          </button>
        </div>
      )}
      {step === 3 && (
        <div className="footer-nav">
          <button className="btn btn-ghost" onClick={() => goTo(step - 1)}>Back</button>
          <span />
        </div>
      )}
    </div>
  );
}
