"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useWorkspaceSession } from "../layout";
import DatasetGrantPanel from "@/components/DatasetGrantPanel";
import { useDatasetRefresh } from "@/hooks/use-session";
import { api, uploadFiles } from "@/lib/api";
import type {
  Dataset,
  EvidencePreviewPage,
  Page,
  Source,
  SourceLocator,
  SourceProfile,
  SourceStatus,
  UploadBatchResponse,
} from "@/lib/contracts";

function formatProfileName(profileId: string): string {
  switch (profileId) {
    case "document":
      return "Tài liệu chung";
    case "log":
      return "Nhật ký hệ thống (Log)";
    case "ticket":
      return "Phiếu hỗ trợ (Ticket)";
    case "incident":
      return "Sự cố (Incident)";
    case "operations_table":
      return "Bảng dữ liệu vận hành";
    default:
      return profileId;
  }
}

function renderStatusLabel(status: SourceStatus | string): string {
  switch (status) {
    case "queued":
      return "Đang chờ xử lý";
    case "processing":
      return "Đang xử lý";
    case "ready":
      return "Sẵn sàng";
    case "failed":
      return "Thất bại";
    default:
      return status;
  }
}

const PROFILE_SAMPLES: Record<string, string> = {
  document: "Ví dụ: SOP quy trình vận hành trung tâm logistics, tiêu chuẩn an toàn...",
  log: "Ví dụ: 2026-10-07T12:00:00Z [INFO] [TMS] status=DELIVERED trace_id=tr-102",
  ticket: "Ví dụ: ticket_id: TCK-1029, system: WMS, status: OPEN, priority: HIGH",
  incident: "Ví dụ: incident_id: INC-402, system: GATEWAY, status: RESOLVED, priority: P1",
  operations_table: "Ví dụ: entity_id: PK-901, system: TMS, status: DISPATCHED, timestamp: 2026-10-07T10:15:00Z",
};

function renderLocatorBadge(loc: SourceLocator): string {
  const parts: string[] = [];
  if (loc.page !== undefined && loc.page !== null) parts.push(`Trang ${loc.page}`);
  if (loc.section) parts.push(`Mục: ${loc.section}`);
  if (loc.sheet && loc.row !== undefined && loc.row !== null) parts.push(`Sheet: ${loc.sheet}, Hàng: ${loc.row}`);
  else if (loc.sheet) parts.push(`Sheet: ${loc.sheet}`);
  else if (loc.row !== undefined && loc.row !== null) parts.push(`Hàng: ${loc.row}`);
  if (loc.line_start !== undefined && loc.line_start !== null) {
    if (loc.line_end !== undefined && loc.line_end !== null && loc.line_end !== loc.line_start) {
      parts.push(`Dòng: ${loc.line_start}–${loc.line_end}`);
    } else {
      parts.push(`Dòng: ${loc.line_start}`);
    }
  }
  if (loc.event !== undefined && loc.event !== null) parts.push(`Sự kiện: ${loc.event}`);
  if (loc.record !== undefined && loc.record !== null) parts.push(`Bản ghi: ${loc.record}`);
  if (loc.json_path) parts.push(`Đường dẫn: ${loc.json_path}`);
  return parts.length > 0 ? parts.join(" · ") : `v${loc.source_version}`;
}

function MetadataPanel({
  dataset,
  csrf,
  onClose,
  onSaved,
}: {
  dataset: Dataset | null;
  csrf: string;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const mounted = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    mounted.current = true;
    const el = dialog.current;
    el?.showModal();
    return () => {
      mounted.current = false;
      el?.close();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      aria-labelledby="metadata-title"
      aria-busy={busy}
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else onClose();
      }}
      style={{
        marginRight: 0,
        marginTop: 0,
        height: "100vh",
        maxHeight: "100vh",
        width: "min(460px, 100vw)",
        border: 0,
        padding: 28,
      }}
    >
      <h2 id="metadata-title">{dataset ? "Chỉnh sửa Dataset" : "Tạo Dataset"}</h2>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const form = new FormData(e.currentTarget);
          setBusy(true);
          setError("");
          try {
            await api(dataset ? `/admin/datasets/${dataset.id}` : "/admin/datasets", {
              method: dataset ? "PATCH" : "POST",
              csrf,
              body: { name: form.get("name"), description: form.get("description") },
            });
            if (!mounted.current) return;
            await onSaved();
            if (mounted.current) onClose();
          } catch (err) {
            if (mounted.current) setError(err instanceof Error ? err.message : "Không thể lưu Dataset");
          } finally {
            if (mounted.current) setBusy(false);
          }
        }}
      >
        <label htmlFor="dataset-name">Tên Dataset</label>
        <input id="dataset-name" name="name" required maxLength={128} defaultValue={dataset?.name ?? ""} />
        <label htmlFor="dataset-description">Mô tả</label>
        <textarea id="dataset-description" name="description" maxLength={2000} defaultValue={dataset?.description ?? ""} />
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button disabled={busy}>Lưu Dataset</button>{" "}
        <button type="button" disabled={busy} onClick={onClose}>
          Đóng
        </button>
      </form>
    </dialog>
  );
}

function UploadSourceDialog({
  datasetId,
  csrf,
  onClose,
  onUploaded,
}: {
  datasetId: string;
  csrf: string;
  onClose: () => void;
  onUploaded: () => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const mounted = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [profiles, setProfiles] = useState<SourceProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [batchResult, setBatchResult] = useState<UploadBatchResponse | null>(null);

  useEffect(() => {
    mounted.current = true;
    const el = dialog.current;
    el?.showModal();
    api<SourceProfile[]>(`/datasets/${datasetId}/sources/profiles`)
      .then((data) => {
        if (mounted.current) {
          setProfiles(data);
          if (data.length > 0) setSelectedProfileId(data[0].id);
        }
      })
      .catch((err) => {
        if (mounted.current) setError(err instanceof Error ? err.message : "Không thể tải danh sách profile");
      });
    return () => {
      mounted.current = false;
      el?.close();
    };
  }, [datasetId]);

  const selectedProfile = profiles.find((p) => p.id === selectedProfileId);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files);
      if (files.length + selected.length > 10) {
        setError("Tối đa 10 tệp mỗi lần tải lên.");
        return;
      }
      setFiles((prev) => [...prev, ...selected].slice(0, 10));
      setError("");
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProfileId || files.length === 0) return;
    setBusy(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("profile_id", selectedProfileId);
      for (const file of files) {
        formData.append("files", file);
      }
      const result = await uploadFiles<UploadBatchResponse>(
        `/admin/datasets/${datasetId}/sources/upload`,
        formData,
        { csrf }
      );
      if (!mounted.current) return;
      setBatchResult(result);
      await onUploaded();
    } catch (err) {
      if (mounted.current) {
        setError(err instanceof Error ? err.message : "Không thể tải tệp lên");
      }
    } finally {
      if (mounted.current) setBusy(false);
    }
  };

  return (
    <dialog
      ref={dialog}
      aria-labelledby="upload-dialog-title"
      aria-busy={busy}
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else onClose();
      }}
      style={{
        marginRight: 0,
        marginTop: 0,
        height: "100vh",
        maxHeight: "100vh",
        width: "min(460px, 100vw)",
        border: 0,
        padding: 28,
      }}
    >
      <h2 id="upload-dialog-title">Tải tệp lên</h2>
      {batchResult ? (
        <div>
          <h3>Kết quả tải lên</h3>
          <p className="muted">Đã xử lý {batchResult.items.length} tệp:</p>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {batchResult.items.map((item, idx) => (
              <li
                key={idx}
                style={{
                  padding: "8px 12px",
                  borderBottom: "1px solid #e0e8ed",
                  marginBottom: 6,
                }}
              >
                <strong>{item.filename}</strong>:{" "}
                <span>
                  {item.is_duplicate
                    ? "Nội dung đã tồn tại — không tạo bản sao"
                    : renderStatusLabel(item.status)}
                </span>
                <br />
                <small className="muted">{item.message}</small>
              </li>
            ))}
          </ul>
          <button type="button" onClick={onClose}>
            Đóng
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <label htmlFor="upload-profile">Loại nguồn dữ liệu (Profile)</label>
          <select
            id="upload-profile"
            value={selectedProfileId}
            onChange={(e) => setSelectedProfileId(e.target.value)}
            disabled={busy}
            required
          >
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          {selectedProfile && (
            <div
              style={{
                background: "#f8fafb",
                border: "1px solid #d7e1e8",
                padding: 12,
                borderRadius: 4,
                marginBottom: 16,
                fontSize: 13,
              }}
            >
              <p style={{ margin: "0 0 6px" }}>
                <strong>Định dạng hỗ trợ:</strong> {selectedProfile.supported_formats.join(", ")}
              </p>
              <p style={{ margin: "0 0 6px" }}>
                <strong>Trường bắt buộc:</strong> {selectedProfile.expected_fields.join(", ")}
              </p>
              {selectedProfile.optional_fields.length > 0 && (
                <p style={{ margin: "0 0 6px" }}>
                  <strong>Trường tùy chọn:</strong> {selectedProfile.optional_fields.join(", ")}
                </p>
              )}
              <div style={{ marginTop: 8, fontStyle: "italic", color: "#587080" }}>
                {PROFILE_SAMPLES[selectedProfile.id] || "Không có mẫu xem trước"}
              </div>
            </div>
          )}

          <label htmlFor="upload-files">
            Chọn tệp tải lên (Tối đa 10 tệp/lần, không quá 50MB mỗi tệp)
          </label>
          <input
            id="upload-files"
            type="file"
            multiple
            accept={selectedProfile ? selectedProfile.supported_formats.join(",") : undefined}
            onChange={handleFileChange}
            disabled={busy}
          />

          {files.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <strong>Danh sách tệp đã chọn ({files.length}):</strong>
              <ul style={{ listStyle: "none", padding: 0, marginTop: 8 }}>
                {files.map((f, idx) => (
                  <li
                    key={idx}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "6px 0",
                      borderBottom: "1px solid #eee",
                    }}
                  >
                    <span>
                      {f.name} <span className="muted">({(f.size / 1024).toFixed(1)} KB)</span>
                    </span>
                    <button
                      type="button"
                      disabled={busy}
                      style={{ padding: "2px 8px", fontSize: 12, background: "#8195a4" }}
                      onClick={() => removeFile(idx)}
                    >
                      Bỏ tệp
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <button disabled={busy || files.length === 0 || !selectedProfileId}>
            Xác nhận tải lên
          </button>{" "}
          <button type="button" disabled={busy} onClick={onClose}>
            Hủy tải lên
          </button>
        </form>
      )}
    </dialog>
  );
}

function DeleteSourceDialog({
  datasetId,
  source,
  csrf,
  onClose,
  onDeleted,
}: {
  datasetId: string;
  source: Source;
  csrf: string;
  onClose: () => void;
  onDeleted: () => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const el = dialog.current;
    el?.showModal();
    return () => {
      el?.close();
    };
  }, []);

  const handleDelete = async () => {
    setBusy(true);
    setError("");
    try {
      await api(`/admin/datasets/${datasetId}/sources/${source.id}`, {
        method: "DELETE",
        csrf,
      });
      await onDeleted();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể xóa nguồn dữ liệu");
    } finally {
      setBusy(false);
    }
  };

  return (
    <dialog
      ref={dialog}
      aria-labelledby="delete-dialog-title"
      aria-busy={busy}
      style={{
        margin: "12vh auto",
        padding: 24,
        background: "white",
        border: "1px solid #d7e1e8",
        borderRadius: 8,
        maxWidth: 480,
      }}
    >
      <h2 id="delete-dialog-title">Xóa nguồn</h2>
      <p>
        Xóa nguồn “{source.logical_filename}”? Nguồn sẽ không còn hiển thị hoặc được dùng trong lần
        truy xuất mới. Việc xóa không thể hoàn tác.
      </p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div style={{ marginTop: 20 }}>
        <button
          type="button"
          disabled={busy}
          style={{ background: "#a22a28", borderColor: "#a22a28", color: "white", marginRight: 8 }}
          onClick={handleDelete}
        >
          Xóa nguồn
        </button>
        <button type="button" disabled={busy} onClick={onClose}>
          Giữ nguồn
        </button>
      </div>
    </dialog>
  );
}

function SourcePreviewModal({
  datasetId,
  source,
  onClose,
}: {
  datasetId: string;
  source: Source;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const mounted = useRef(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [data, setData] = useState<EvidencePreviewPage | null>(null);
  const [page, setPage] = useState(1);

  const loadPreview = useCallback(
    async (p: number) => {
      setLoading(true);
      setError("");
      try {
        const res = await api<EvidencePreviewPage>(
          `/datasets/${datasetId}/sources/${source.id}/preview?page=${p}&page_size=25`
        );
        if (mounted.current) {
          setData(res);
          setPage(p);
        }
      } catch {
        if (mounted.current) {
          setData(null);
          setError("Quyền truy cập đã thay đổi hoặc nguồn không còn khả dụng.");
        }
      } finally {
        if (mounted.current) setLoading(false);
      }
    },
    [datasetId, source.id]
  );

  useEffect(() => {
    mounted.current = true;
    const el = dialog.current;
    el?.showModal();
    void loadPreview(1);

    const onAccessChanged = () => {
      if (mounted.current) {
        setData(null);
        setError("Quyền truy cập đã thay đổi hoặc nguồn không còn khả dụng.");
      }
    };
    window.addEventListener("dataset-access-changed", onAccessChanged);

    return () => {
      mounted.current = false;
      window.removeEventListener("dataset-access-changed", onAccessChanged);
      el?.close();
    };
  }, [loadPreview]);

  return (
    <dialog
      ref={dialog}
      aria-labelledby="preview-dialog-title"
      aria-busy={loading}
      style={{
        margin: "8vh auto",
        padding: 28,
        background: "white",
        border: "1px solid #d7e1e8",
        borderRadius: 8,
        width: "min(720px, 95vw)",
        maxHeight: "85vh",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 id="preview-dialog-title" style={{ margin: "0 0 4px" }}>
            {source.logical_filename}
          </h2>
          <div className="muted" style={{ fontSize: 13, marginBottom: 16 }}>
            <span>v{source.active_version_number ?? 1} · đang dùng</span> ·{" "}
            <span>{formatProfileName(source.profile_id)}</span>
          </div>
        </div>
        <button type="button" onClick={onClose} style={{ padding: "6px 12px", fontSize: 13 }}>
          Đóng
        </button>
      </div>

      {loading && <p role="status">Đang tải đoạn trích…</p>}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {data && (
        <div>
          {data.items.length === 0 ? (
            <p className="muted">Không có đoạn trích dữ liệu nào.</p>
          ) : (
            <div>
              <p className="muted" style={{ fontSize: 13 }}>
                Tổng cộng {data.total} đoạn trích (Trang {data.page}/
                {Math.ceil(data.total / data.page_size)})
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {data.items.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      border: "1px solid #e0e8ed",
                      borderRadius: 6,
                      padding: 12,
                      background: "#fafbfc",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        fontSize: 12,
                        marginBottom: 6,
                      }}
                    >
                      <span
                        style={{
                          fontWeight: "bold",
                          color: "#075b79",
                          background: "#e9f3f8",
                          padding: "2px 6px",
                          borderRadius: 3,
                        }}
                      >
                        {renderLocatorBadge(item.locator)}
                      </span>
                      {Object.keys(item.metadata).length > 0 && (
                        <span className="muted">
                          {Object.entries(item.metadata)
                            .slice(0, 3)
                            .map(([k, v]) => `${k}: ${String(v)}`)
                            .join(" | ")}
                        </span>
                      )}
                    </div>
                    <div
                      style={{
                        whiteSpace: "pre-wrap",
                        fontSize: 14,
                        lineHeight: 1.5,
                        color: "#172b3a",
                      }}
                    >
                      {item.text}
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16, display: "flex", gap: 8, alignItems: "center" }}>
                <button
                  disabled={page <= 1 || loading}
                  onClick={() => void loadPreview(page - 1)}
                  style={{ padding: "6px 12px", fontSize: 13 }}
                >
                  Trang trước
                </button>
                <span style={{ fontSize: 13 }}>Trang {page}</span>
                <button
                  disabled={page * data.page_size >= data.total || loading}
                  onClick={() => void loadPreview(page + 1)}
                  style={{ padding: "6px 12px", fontSize: 13 }}
                >
                  Trang sau
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </dialog>
  );
}

function DiagnosticErrorDialog({
  source,
  onClose,
}: {
  source: Source;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const el = dialog.current;
    el?.showModal();
    return () => {
      el?.close();
    };
  }, []);

  return (
    <dialog
      ref={dialog}
      aria-labelledby="diag-title"
      style={{
        margin: "12vh auto",
        padding: 24,
        background: "white",
        border: "1px solid #d7e1e8",
        borderRadius: 8,
        maxWidth: 540,
      }}
    >
      <h2 id="diag-title">Chi tiết lỗi xử lý: {source.logical_filename}</h2>
      <p className="error" role="alert">
        Không thể xử lý tệp này. Mở chi tiết để xem dòng/trường và nguyên nhân; sửa tệp rồi tải
        lại, hoặc chọn Thử lại nếu đây là lỗi tạm thời.
      </p>
      {source.error_message && (
        <div
          style={{
            background: "#fff5f5",
            border: "1px solid #fed7d7",
            padding: 12,
            borderRadius: 4,
            margin: "12px 0",
            fontSize: 14,
          }}
        >
          <strong>Nguyên nhân:</strong> {source.error_message}
        </div>
      )}
      <div style={{ marginTop: 16, textAlign: "right" }}>
        <button type="button" onClick={onClose}>
          Đóng
        </button>
      </div>
    </dialog>
  );
}

export default function Datasets() {
  const session = useWorkspaceSession();
  const [data, setData] = useState<Page<Dataset> | null>(null);
  const [error, setError] = useState("");
  const [panel, setPanel] = useState<Dataset | null | undefined>();
  const [detail, setDetail] = useState<Dataset | null>(null);
  const [page, setPage] = useState(1);
  const sequence = useRef(0);
  const [grantPanel, setGrantPanel] = useState(false);
  const detailSequence = useRef(0);
  const selectedId = useRef<string | null>(null);

  // Sources management state
  const [sourcesData, setSourcesData] = useState<Page<Source> | null>(null);
  const [sourcesPage, setSourcesPage] = useState(1);
  const [showUpload, setShowUpload] = useState(false);
  const [previewSource, setPreviewSource] = useState<Source | null>(null);
  const [deleteSource, setDeleteSource] = useState<Source | null>(null);
  const [diagnosticSource, setDiagnosticSource] = useState<Source | null>(null);
  const [sourceActionBusy, setSourceActionBusy] = useState(false);

  const refreshSources = useCallback(async () => {
    if (!selectedId.current) {
      setSourcesData(null);
      return;
    }
    try {
      const res = await api<Page<Source>>(
        `/datasets/${selectedId.current}/sources?page=${sourcesPage}&page_size=25`
      );
      setSourcesData(res);
    } catch {
      setSourcesData(null);
    }
  }, [sourcesPage]);

  const clear = useCallback(() => {
    sequence.current++;
    detailSequence.current++;
    selectedId.current = null;
    setData(null);
    setDetail(null);
    setPanel(undefined);
    setGrantPanel(false);
    setSourcesData(null);
    setShowUpload(false);
    setPreviewSource(null);
    setDeleteSource(null);
    setDiagnosticSource(null);
    setError("Quyền truy cập đã thay đổi");
  }, []);

  const refresh = useCallback(async () => {
    const current = ++sequence.current;
    try {
      const result = await api<Page<Dataset>>(`/datasets?page=${page}`);
      if (current !== sequence.current) return;
      if (selectedId.current && !result.items.some((d) => d.id === selectedId.current)) {
        detailSequence.current++;
        selectedId.current = null;
        setDetail(null);
        setSourcesData(null);
      }
      setData(result);
      setError("");
      setDetail((old) => (old ? result.items.find((d) => d.id === old.id) ?? null : null));
    } catch (err) {
      if (current !== sequence.current) return;
      detailSequence.current++;
      selectedId.current = null;
      setData(null);
      setDetail(null);
      setPanel(undefined);
      setSourcesData(null);
      setError(err instanceof Error ? err.message : "Không thể tải Dataset");
    }
  }, [page]);

  useEffect(() => {
    void refresh();
    return () => {
      sequence.current++;
      detailSequence.current++;
      selectedId.current = null;
    };
  }, [refresh]);

  useEffect(() => {
    if (detail) {
      void refreshSources();
    } else {
      setSourcesData(null);
    }
  }, [detail, refreshSources]);

  useDatasetRefresh(refresh, clear);

  if (!session) return null;
  const admin = session.account.role === "admin";

  const handleRetry = async (sourceId: string) => {
    if (!detail) return;
    setSourceActionBusy(true);
    try {
      await api(`/admin/datasets/${detail.id}/sources/${sourceId}/retry`, {
        method: "POST",
        csrf: session.csrf_token,
      });
      await refreshSources();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Không thể thử lại tác vụ");
    } finally {
      setSourceActionBusy(false);
    }
  };

  const handleReprocess = async (sourceId: string) => {
    if (!detail) return;
    setSourceActionBusy(true);
    try {
      await api(`/admin/datasets/${detail.id}/sources/${sourceId}/reprocess`, {
        method: "POST",
        csrf: session.csrf_token,
      });
      await refreshSources();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Không thể nạp lại nguồn");
    } finally {
      setSourceActionBusy(false);
    }
  };

  return (
    <>
      <div className="eyebrow">{admin ? "Quản trị" : "Không gian làm việc"}</div>
      <h1>Dataset</h1>
      <section className="card">
        {admin && (
          <>
            <button onClick={() => setPanel(null)}>Tạo Dataset</button>{" "}
            <button onClick={() => setGrantPanel(true)}>Cấp quyền Dataset</button>
          </>
        )}
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : !data ? (
          <p role="status">Đang tải Dataset…</p>
        ) : data.total === 0 ? (
          <div className="empty">
            {admin
              ? "Chưa có Dataset. Tạo Dataset để quản lý phạm vi dữ liệu."
              : "Chưa có Dataset trong phạm vi của bạn. Liên hệ Admin để được cấp quyền."}
          </div>
        ) : (
          <>
            <p className="muted">{data.total} Dataset trong phạm vi của bạn</p>
            <table>
              <thead>
                <tr>
                  <th>Tên Dataset</th>
                  <th>Mô tả</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((d) => (
                  <tr key={d.id}>
                    <td>{d.name}</td>
                    <td>{d.description}</td>
                    <td>
                      <button
                        aria-label={`Xem ${d.name}`}
                        onClick={async () => {
                          const current = ++detailSequence.current;
                          selectedId.current = d.id;
                          setDetail(null);
                          setSourcesPage(1);
                          try {
                            const result = await api<Dataset>(`/datasets/${d.id}`);
                            if (current === detailSequence.current && selectedId.current === d.id) {
                              setDetail(result);
                            }
                          } catch (err) {
                            if (current === detailSequence.current) {
                              selectedId.current = null;
                              setDetail(null);
                              setData(null);
                              setError(err instanceof Error ? err.message : "Quyền truy cập đã thay đổi");
                            }
                          }
                        }}
                      >
                        Xem
                      </button>
                      {admin && (
                        <>
                          {" "}
                          <button aria-label={`Chỉnh sửa ${d.name}`} onClick={() => setPanel(d)}>
                            Chỉnh sửa
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button
              disabled={page <= 1}
              onClick={() => {
                setDetail(null);
                detailSequence.current++;
                selectedId.current = null;
                setPage(page - 1);
              }}
            >
              Trang trước
            </button>{" "}
            <span>Trang {page}</span>{" "}
            <button
              disabled={page * data.page_size >= data.total}
              onClick={() => {
                setDetail(null);
                detailSequence.current++;
                selectedId.current = null;
                setPage(page + 1);
              }}
            >
              Trang sau
            </button>
          </>
        )}
      </section>

      {detail && (
        <section className="card" aria-label="Chi tiết Dataset" style={{ marginTop: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h2>{detail.name}</h2>
              <p>{detail.description}</p>
            </div>
            <button
              onClick={() => {
                detailSequence.current++;
                selectedId.current = null;
                setDetail(null);
              }}
            >
              Đóng chi tiết
            </button>
          </div>

          <hr style={{ border: 0, borderTop: "1px solid #d7e1e8", margin: "20px 0" }} />

          {/* Sources Section */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ margin: 0 }}>
              Nguồn dữ liệu ({sourcesData ? sourcesData.total : 0})
            </h3>
            {admin && (
              <button onClick={() => setShowUpload(true)}>
                Tải tệp lên
              </button>
            )}
          </div>

          {!sourcesData ? (
            <p role="status">Đang tải nguồn dữ liệu…</p>
          ) : sourcesData.total === 0 ? (
            <div className="empty">
              <h3>Chưa có nguồn dữ liệu</h3>
              <p>Tải tệp đầu tiên lên để bắt đầu quản lý dữ liệu trong Dataset này.</p>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table aria-label="Danh sách nguồn dữ liệu" style={{ minWidth: 640 }}>
                <thead>
                  <tr>
                    <th>Tên tệp</th>
                    <th>Profile</th>
                    <th>Phiên bản</th>
                    <th>Trạng thái</th>
                    <th>Cập nhật</th>
                    <th>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {sourcesData.items.map((src) => (
                    <tr key={src.id}>
                      <td style={{ fontWeight: 600 }}>{src.logical_filename}</td>
                      <td>{formatProfileName(src.profile_id)}</td>
                      <td>
                        {src.active_version_number !== null ? (
                          <span
                            style={{
                              background: "#e9f3f8",
                              color: "#075b79",
                              padding: "2px 8px",
                              borderRadius: 4,
                              fontWeight: "bold",
                              fontSize: 12,
                            }}
                          >
                            v{src.active_version_number} · đang dùng
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        <span
                          style={{
                            color: src.status === "failed" ? "#a22a28" : src.status === "ready" ? "#0a6c44" : "#587080",
                            fontWeight: 600,
                          }}
                        >
                          {renderStatusLabel(src.status)}
                        </span>
                        {src.status === "failed" && (
                          <button
                            type="button"
                            onClick={() => setDiagnosticSource(src)}
                            style={{
                              marginLeft: 8,
                              padding: "2px 6px",
                              fontSize: 11,
                              background: "none",
                              color: "#a22a28",
                              borderColor: "#a22a28",
                            }}
                          >
                            Chi tiết lỗi
                          </button>
                        )}
                      </td>
                      <td style={{ fontSize: 13 }} className="muted">
                        {new Date(src.updated_at).toLocaleString("vi-VN")}
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                          {(src.active_version_id !== null || src.status === "ready") && (
                            <button
                              aria-label={`Xem đoạn trích ${src.logical_filename}`}
                              style={{ padding: "6px 12px", fontSize: 13 }}
                              onClick={() => setPreviewSource(src)}
                            >
                              Xem đoạn trích
                            </button>
                          )}
                          {admin && (
                            <>
                              {src.status === "failed" && (
                                <button
                                  disabled={sourceActionBusy}
                                  style={{ padding: "6px 12px", fontSize: 13 }}
                                  onClick={() => handleRetry(src.id)}
                                >
                                  Thử lại
                                </button>
                              )}
                              {(src.active_version_id !== null || src.status === "ready") && (
                                <button
                                  disabled={sourceActionBusy}
                                  style={{ padding: "6px 12px", fontSize: 13 }}
                                  onClick={() => handleReprocess(src.id)}
                                >
                                  Nạp lại nguồn
                                </button>
                              )}
                              <button
                                disabled={sourceActionBusy}
                                style={{
                                  padding: "6px 12px",
                                  fontSize: 13,
                                  background: "#a22a28",
                                  borderColor: "#a22a28",
                                  color: "white",
                                }}
                                onClick={() => setDeleteSource(src)}
                              >
                                Xóa nguồn
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {sourcesData.total > sourcesData.page_size && (
                <div style={{ marginTop: 16, display: "flex", gap: 8, alignItems: "center" }}>
                  <button
                    disabled={sourcesPage <= 1}
                    onClick={() => setSourcesPage((p) => p - 1)}
                    style={{ padding: "6px 12px", fontSize: 13 }}
                  >
                    Trang trước
                  </button>
                  <span style={{ fontSize: 13 }}>Trang {sourcesPage}</span>
                  <button
                    disabled={sourcesPage * sourcesData.page_size >= sourcesData.total}
                    onClick={() => setSourcesPage((p) => p + 1)}
                    style={{ padding: "6px 12px", fontSize: 13 }}
                  >
                    Trang sau
                  </button>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* Upload Source Dialog */}
      {showUpload && detail && (
        <UploadSourceDialog
          datasetId={detail.id}
          csrf={session.csrf_token}
          onClose={() => setShowUpload(false)}
          onUploaded={refreshSources}
        />
      )}

      {/* Delete Source Dialog */}
      {deleteSource && detail && (
        <DeleteSourceDialog
          datasetId={detail.id}
          source={deleteSource}
          csrf={session.csrf_token}
          onClose={() => setDeleteSource(null)}
          onDeleted={refreshSources}
        />
      )}

      {/* Source Preview Modal */}
      {previewSource && detail && (
        <SourcePreviewModal
          datasetId={detail.id}
          source={previewSource}
          onClose={() => setPreviewSource(null)}
        />
      )}

      {/* Diagnostic Error Dialog */}
      {diagnosticSource && (
        <DiagnosticErrorDialog
          source={diagnosticSource}
          onClose={() => setDiagnosticSource(null)}
        />
      )}

      {/* Existing Dataset Metadata Panel & Grant Panel */}
      {panel !== undefined && (
        <MetadataPanel
          key={panel?.id ?? "new"}
          dataset={panel}
          csrf={session.csrf_token}
          onClose={() => setPanel(undefined)}
          onSaved={refresh}
        />
      )}
      {grantPanel && (
        <DatasetGrantPanel
          csrf={session.csrf_token}
          onClose={() => setGrantPanel(false)}
          onSaved={refresh}
        />
      )}
    </>
  );
}
