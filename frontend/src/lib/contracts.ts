export type Account = { id: string; username: string; display_name: string; role: "admin" | "technician"; active: boolean; must_change_password: boolean; created_at: string };
export type Session = { account: Account; csrf_token: string };
export type Dataset = { id: string; name: string; description: string; created_at: string };
export type DatasetInput = Pick<Dataset, "name" | "description">;
export type DatasetGrants = { dataset_ids: string[] };
export type Page<T> = { items: T[]; total: number; page: number; page_size: number };

export type SourceStatus = "queued" | "processing" | "ready" | "failed";

export type SourceProfile = {
  id: string;
  name: string;
  description: string;
  supported_formats: string[];
  expected_fields: string[];
  optional_fields: string[];
};

export type SourceVersion = {
  id: string;
  version_number: number;
  content_hash: string;
  size_bytes: number;
  mime_type: string;
  created_at: string;
};

export type Source = {
  id: string;
  dataset_id: string;
  logical_filename: string;
  profile_id: string;
  active_version_id: string | null;
  active_version_number: number | null;
  status: SourceStatus;
  error_message?: string;
  created_at: string;
  updated_at: string;
};

export type SourceLocator = {
  source_id: string;
  source_version: number;
  page?: number;
  section?: string;
  sheet?: string;
  row?: number;
  event?: number;
  record?: number;
  line_start?: number;
  line_end?: number;
  json_path?: string;
};

export type EvidenceExcerpt = {
  id: string;
  position: number;
  text: string;
  locator: SourceLocator;
  metadata: Record<string, unknown>;
};

export type EvidencePreviewPage = {
  source_id: string;
  version_number: number;
  items: EvidenceExcerpt[];
  total: number;
  page: number;
  page_size: number;
};

export type UploadResultItem = {
  filename: string;
  source_id: string;
  version_number: number;
  status: SourceStatus;
  job_id: string;
  is_duplicate: boolean;
  message: string;
};

export type UploadBatchResponse = {
  items: UploadResultItem[];
};
