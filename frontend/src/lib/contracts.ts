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

export type ChatSession = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type CitationItem = {
  citation_index: number;
  dataset_id: string;
  source_id: string;
  source_version: number;
  locator: SourceLocator;
  excerpt_text: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: CitationItem[];
  has_uncertainty: boolean;
  has_conflict: boolean;
  created_at: string;
};

export type ChatQueryRequest = {
  question: string;
  session_id?: string;
  dataset_ids?: string[];
  profile_id?: string;
  start_time?: string;
  end_time?: string;
};

export type ChatQueryResponse = {
  session_id: string;
  message: ChatMessage;
  citations: CitationItem[];
};

export type CitationPreviewDetail = {
  citation_index: number;
  dataset_id: string;
  dataset_name: string;
  source_id: string;
  logical_filename: string;
  version_number: number;
  locator: SourceLocator;
  excerpt_text: string;
};

export type ModelConfig = {
  embedding_provider: string;
  embedding_model: string;
  embedding_dimension: number;
  index_version: string;
  llm_provider: string;
  llm_model: string;
  openai_configured: boolean;
};

export type SystemType = "WMS" | "TMS" | "API_GATEWAY" | "ERP" | "INVENTORY" | "OTHER";
export type SeverityType = "P1" | "P2" | "P3" | "P4";

export type TimelineEvent = {
  event_id: string;
  timestamp: string;
  system: SystemType;
  event_name: string;
  status: string;
  is_failure_point: boolean;
  citation_id?: number;
  source_filename: string;
  line_number?: number;
  raw_snippet: string;
};

export type IncidentClassification = {
  error_group: string;
  primary_system: SystemType;
  suggested_priority: SeverityType;
  confidence: number;
};

export type RootCauseHypothesis = {
  hypothesis: string;
  supporting_evidence_citations: number[];
  is_confirmed: boolean;
  confidence_level: string;
};

export type ActionStep = {
  step_number: number;
  action: string;
  sop_reference: string;
  sop_citation_id?: number;
  expected_outcome: string;
};

export type IncidentAnalysisDetail = {
  id: string;
  order_id: string;
  ticket_id?: string;
  title: string;
  input_mode: string;
  summary: string;
  classification: IncidentClassification;
  timeline: TimelineEvent[];
  hypotheses: RootCauseHypothesis[];
  missing_information: string[];
  recommended_actions: ActionStep[];
  citations: Array<{
    citation_id: number;
    kind: string;
    source: string;
    line?: number;
    dataset_id?: string;
    timestamp?: string;
    system?: string;
    snippet: string;
  }>;
  created_at: string;
};

export type IncidentHistoryItem = {
  id: string;
  order_id: string;
  ticket_id?: string;
  title: string;
  input_mode: string;
  error_group: string;
  primary_system: string;
  suggested_priority: string;
  created_at: string;
};


