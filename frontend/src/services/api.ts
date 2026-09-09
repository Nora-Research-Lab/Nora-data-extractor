import type {
  AoiRequest,
  AoiValidationResult,
  Dataset,
  DatasetSelection,
  ExtractionJobStatus,
  ProcessingOptions,
} from "../types";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = JSON.stringify(body.detail ?? body);
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  listDatasets: () => req<Dataset[]>("/api/datasets"),

  validateAoi: (aoi: AoiRequest) =>
    req<AoiValidationResult>("/api/aoi/validate", {
      method: "POST",
      body: JSON.stringify(aoi),
    }),

  createExtraction: (payload: {
    aoi: AoiRequest;
    datasets: DatasetSelection[];
    processing: ProcessingOptions;
    study_area_name: string;
  }) =>
    req<{ job_id: string; status: string }>("/api/extractions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getExtraction: (jobId: string) =>
    req<ExtractionJobStatus>(`/api/extractions/${jobId}`),
};
