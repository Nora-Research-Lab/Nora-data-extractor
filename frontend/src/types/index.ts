export type DatasetKind = "raster" | "vector";

export interface FormatOption {
  format: string;
  description: string;
  recommended: boolean;
}

export interface Dataset {
  id: string;
  name: string;
  description: string;
  category: string;
  kind: DatasetKind;
  format: string;
  geometry_type: string;
  crs: string;
  coverage: string;
  resolution?: string | null;
  units?: string | null;
  source: string;
  license: string;
  format_options: FormatOption[];
}

export interface BBox {
  north: number;
  south: number;
  east: number;
  west: number;
}

export type AoiType = "bbox" | "rectangle" | "polygon" | "circle" | "geojson";

export interface AoiRequest {
  aoi_type: AoiType;
  bbox?: BBox;
  geojson?: any;
  circle?: { center_lat: number; center_lon: number; radius_km: number };
}

export interface AoiValidationResult {
  valid: boolean;
  area_km2?: number;
  bbox?: BBox;
  geojson?: any;
  errors: string[];
  warnings: string[];
}

export interface ProcessingOptions {
  mode: "basic" | "advanced";
  clip: boolean;
  reproject_to?: string | null;
  resample?: "nearest" | "bilinear" | "cubic" | null;
  target_resolution?: number | null;
  simplify_tolerance?: number | null;
  dissolve: boolean;
  dissolve_by?: string | null;
  buffer_meters?: number | null;
  attribute_filter?: string | null;
}

export interface DatasetSelection {
  dataset_id: string;
  output_format: string;
}

export type JobStatus = "queued" | "processing" | "completed" | "failed";
export type JobStage = "preparing" | "extracting" | "converting" | "packaging" | "complete" | "failed";

export interface ExtractionJobStatus {
  job_id: string;
  status: JobStatus;
  stage: JobStage;
  progress_pct?: number;
  message: string;
  result_files: string[];
  download_url?: string | null;
  error?: string | null;
}
