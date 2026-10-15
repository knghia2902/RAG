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

function renderStatusBadge(status: SourceStatus | string) {
  switch (status) {
    case "ready":
      return <span className="badge badge-pastel-green">Sẵn sàng</span>;
    case "processing":
      return <span className="badge badge-pastel-amber">Đang xử lý</span>;
    case "queued":
      return <span className="badge badge-pastel-amber">Đang chờ</span>;
    case "failed":
      return <span className="badge badge-pastel-rose">Thất bại</span>;
    default:
      return <span className="badge badge-pastel-slate">{status}</span>;
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

function getFileExtension(filename: string): string {
  const ext = filename.split(".").pop();
  return ext && ext !== filename ? ext.toUpperCase() : "DOC";
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
        margin: "auto",
        maxWidth: 500,
        width: "92vw",
        borderRadius: "var(--radius-lg)",
        padding: 28,
        border: "1px solid var(--border-subtle)",
        boxShadow: "var(--shadow-floating)",
        background: "#ffffff",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h2 id="metadata-title" style={{ margin: 0, fontSize: 20, color: "var(--color-text-main)" }}>
          {dataset ? "Chỉnh sửa Dataset" : "Tạo Dataset"}
        </h2>
        <button
          type="button"
          aria-label="Đóng hộp thoại"
          onClick={onClose}
          disabled={busy}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--color-text-muted)",
            padding: 4,
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

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
        <div style={{ marginBottom: 16 }}>
          <label htmlFor="dataset-name" style={{ display: "block", marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
            Tên Dataset
          </label>
          <input
            id="dataset-name"
            name="name"
            required
            maxLength={128}
            defaultValue={dataset?.name ?? ""}
            placeholder="Ví dụ: Kho Vận miền Bắc (WMS)"
          />
        </div>

        <div style={{ marginBottom: 20 }}>
          <label htmlFor="dataset-description" style={{ display: "block", marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
            Mô tả
          </label>
          <textarea
            id="dataset-description"
            name="description"
            rows={4}
            maxLength={2000}
            defaultValue={dataset?.description ?? ""}
            placeholder="Mô tả các nguồn tài liệu, quy trình SOP hoặc dữ liệu log chứa trong dataset này..."
          />
        </div>

        {error && (
          <p className="error" role="alert" style={{ marginBottom: 16 }}>
            {error}
          </p>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button type="button" className="btn-secondary" disabled={busy} onClick={onClose}>
            Đóng
          </button>
          <button type="submit" className="btn-primary" disabled={busy}>
            {busy ? "Đang lưu…" : "Lưu Dataset"}
          </button>
        </div>
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
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mounted = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [profiles, setProfiles] = useState<SourceProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [batchResult, setBatchResult] = useState<UploadBatchResponse | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

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

  const handleFileChange = (newFiles: FileList | null) => {
    if (!newFiles) return;
    const selected = Array.from(newFiles);
    if (files.length + selected.length > 10) {
      setError("Tối đa 10 tệp mỗi lần tải lên.");
      return;
    }
    setFiles((prev) => [...prev, ...selected].slice(0, 10));
    setError("");
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
        margin: "auto",
        maxWidth: 580,
        width: "92vw",
        borderRadius: "var(--radius-lg)",
        padding: 28,
        border: "1px solid var(--border-subtle)",
        boxShadow: "var(--shadow-floating)",
        background: "#ffffff",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h2 id="upload-dialog-title" style={{ margin: 0, fontSize: 20, color: "var(--color-text-main)" }}>
          Tải lên tài liệu
        </h2>
        <button
          type="button"
          aria-label="Đóng hộp thoại tải lên"
          onClick={onClose}
          disabled={busy}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--color-text-muted)",
            padding: 4,
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {batchResult ? (
        <div>
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ margin: "0 0 4px", fontSize: 16, color: "var(--color-emerald-dark)" }}>
              Kết quả tải lên
            </h3>
            <p className="muted" style={{ margin: 0 }}>
              Đã xử lý {batchResult.items.length} tệp:
            </p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: "40vh", overflowY: "auto", marginBottom: 20 }}>
            {batchResult.items.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: "10px 14px",
                  borderRadius: "var(--radius-sm)",
                  background: "var(--bg-app)",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{item.filename}</div>
                  <small className="muted">{item.message}</small>
                </div>
                <div>
                  {item.is_duplicate ? (
                    <span className="badge badge-pastel-slate">Nội dung đã tồn tại — không tạo bản sao</span>
                  ) : (
                    renderStatusBadge(item.status)
                  )}
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button type="button" className="btn-primary" onClick={onClose}>
              Đóng
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label htmlFor="upload-profile" style={{ display: "block", marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
              Loại nguồn dữ liệu (Profile)
            </label>
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
          </div>

          {selectedProfile && (
            <div
              style={{
                background: "var(--color-pastel-50)",
                border: "1px solid var(--color-mint-border)",
                padding: "12px 16px",
                borderRadius: "var(--radius-sm)",
                marginBottom: 16,
                fontSize: 13,
              }}
            >
              <div style={{ marginBottom: 4 }}>
                <strong>Định dạng hỗ trợ:</strong>{" "}
                <span className="muted">{selectedProfile.supported_formats.join(", ")}</span>
              </div>
              <div style={{ marginBottom: 4 }}>
                <strong>Trường bắt buộc:</strong>{" "}
                <span className="muted">{selectedProfile.expected_fields.join(", ")}</span>
              </div>
              <div style={{ fontStyle: "italic", color: "var(--color-emerald-dark)", marginTop: 6 }}>
                {PROFILE_SAMPLES[selectedProfile.id] || "Không có mẫu xem trước"}
              </div>
            </div>
          )}

          {/* Dialog Upload Dropzone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragOver(false);
              handleFileChange(e.dataTransfer.files);
            }}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${isDragOver ? "var(--color-primary-green)" : "var(--color-mint-border)"}`,
              borderRadius: "var(--radius-md)",
              backgroundColor: isDragOver ? "var(--color-pastel-100)" : "var(--color-pastel-50)",
              padding: "24px 16px",
              textAlign: "center",
              cursor: "pointer",
              transition: "all 150ms ease",
              marginBottom: 16,
            }}
          >
            <div style={{ color: "var(--color-primary-green)", marginBottom: 8 }}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ margin: "0 auto" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <div style={{ fontWeight: 600, fontSize: 14, color: "var(--color-text-main)", marginBottom: 4 }}>
              Kéo thả tài liệu vào đây hoặc click để chọn tệp
            </div>
            <div className="muted" style={{ fontSize: 12 }}>
              Tối đa 10 tệp mỗi lần, dung lượng không quá 50MB mỗi tệp
            </div>
            <input
              ref={fileInputRef}
              id="upload-files"
              type="file"
              multiple
              accept={selectedProfile ? selectedProfile.supported_formats.join(",") : undefined}
              onChange={(e) => handleFileChange(e.target.files)}
              disabled={busy}
              style={{ display: "none" }}
            />
          </div>

          {files.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: "var(--color-text-main)" }}>
                Danh sách tệp đã chọn ({files.length}):
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: "25vh", overflowY: "auto" }}>
                {files.map((f, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "8px 12px",
                      background: "var(--bg-app)",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--border-subtle)",
                      fontSize: 13,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8, overflow: "hidden" }}>
                      <span className="badge badge-pastel-green" style={{ fontSize: 10, padding: "2px 6px" }}>
                        {getFileExtension(f.name)}
                      </span>
                      <span style={{ fontWeight: 500, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                        {f.name}
                      </span>
                      <span className="muted" style={{ fontSize: 12 }}>
                        ({(f.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                    <button
                      type="button"
                      disabled={busy}
                      aria-label={`Bỏ tệp ${f.name}`}
                      style={{
                        padding: "4px 8px",
                        fontSize: 12,
                        background: "none",
                        border: "none",
                        color: "var(--color-danger-btn)",
                        cursor: "pointer",
                      }}
                      onClick={() => removeFile(idx)}
                    >
                      Bỏ tệp
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {busy && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 6 }}>
                <span style={{ color: "var(--color-emerald-dark)", fontWeight: 600 }}>
                  Đang tải lên và xử lý tệp…
                </span>
                <span className="muted">Vui lòng chờ</span>
              </div>
              <div
                style={{
                  width: "100%",
                  height: 8,
                  borderRadius: "var(--radius-full)",
                  background: "#e2e8f0",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: "100%",
                    background: "linear-gradient(90deg, #34d399, #10b981)",
                    animation: "pulse 1.5s infinite ease-in-out",
                  }}
                />
              </div>
            </div>
          )}

          {error && (
            <p className="error" role="alert" style={{ marginBottom: 16 }}>
              {error}
            </p>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 20 }}>
            <button type="button" className="btn-secondary" disabled={busy} onClick={onClose}>
              Hủy
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={busy || files.length === 0 || !selectedProfileId}
            >
              {busy ? "Đang xử lý…" : "Tải lên tài liệu"}
            </button>
          </div>
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
        margin: "auto",
        maxWidth: 500,
        width: "92vw",
        borderRadius: "var(--radius-lg)",
        padding: 24,
        background: "#ffffff",
        border: "1px solid var(--border-subtle)",
        boxShadow: "var(--shadow-floating)",
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 16 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: "var(--radius-full)",
            background: "var(--color-danger-bg)",
            color: "var(--color-danger-btn)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            <line x1="10" y1="11" x2="10" y2="17" />
            <line x1="14" y1="11" x2="14" y2="17" />
          </svg>
        </div>
        <div>
          <h2 id="delete-dialog-title" style={{ margin: "0 0 8px", fontSize: 18, color: "var(--color-text-main)" }}>
            Xóa nguồn tài liệu
          </h2>
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: "var(--color-text-muted)" }}>
            Xóa nguồn tài liệu: Bạn có chắc chắn muốn xóa vĩnh viễn nguồn tài liệu này cùng toàn bộ vector chunks liên quan không? Thao tác này không thể hoàn tác.
          </p>
          <div
            style={{
              marginTop: 12,
              padding: "8px 12px",
              background: "var(--bg-app)",
              borderRadius: "var(--radius-sm)",
              fontSize: 13,
              fontWeight: 600,
              color: "var(--color-text-main)",
            }}
          >
            {source.logical_filename}
          </div>
        </div>
      </div>

      {error && (
        <p className="error" role="alert" style={{ marginBottom: 16 }}>
          {error}
        </p>
      )}

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 20 }}>
        <button type="button" className="btn-secondary" disabled={busy} onClick={onClose}>
          Giữ nguồn
        </button>
        <button
          type="button"
          className="btn-danger"
          disabled={busy}
          onClick={handleDelete}
        >
          {busy ? "Đang xóa…" : "Xóa vĩnh viễn"}
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
        margin: "auto",
        maxWidth: 780,
        width: "92vw",
        borderRadius: "var(--radius-lg)",
        padding: 28,
        background: "#ffffff",
        border: "1px solid var(--border-subtle)",
        boxShadow: "var(--shadow-floating)",
        maxHeight: "85vh",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div>
          <h2 id="preview-dialog-title" style={{ margin: "0 0 6px", fontSize: 20 }}>
            {source.logical_filename}
          </h2>
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }} className="muted">
            <span className="badge badge-pastel-green">v{source.active_version_number ?? 1} · đang dùng</span>
            <span>·</span>
            <span>{formatProfileName(source.profile_id)}</span>
          </div>
        </div>
        <button type="button" className="btn-secondary" onClick={onClose} style={{ padding: "6px 12px", fontSize: 13 }}>
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
              <p className="muted" style={{ fontSize: 13, marginBottom: 12 }}>
                Tổng cộng {data.total} đoạn trích (Trang {data.page}/
                {Math.ceil(data.total / data.page_size)})
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: 12, maxHeight: "55vh", overflowY: "auto", paddingRight: 4 }}>
                {data.items.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-sm)",
                      padding: 14,
                      background: "var(--bg-app)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        fontSize: 12,
                        marginBottom: 8,
                      }}
                    >
                      <span className="badge badge-pastel-green">
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
                        lineHeight: 1.6,
                        color: "var(--color-text-main)",
                      }}
                    >
                      {item.text}
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16, display: "flex", gap: 8, alignItems: "center", justifyContent: "flex-end" }}>
                <button
                  className="btn-secondary"
                  disabled={page <= 1 || loading}
                  onClick={() => void loadPreview(page - 1)}
                  style={{ padding: "6px 12px", fontSize: 13 }}
                >
                  Trang trước
                </button>
                <span style={{ fontSize: 13 }} className="muted">Trang {page}</span>
                <button
                  className="btn-secondary"
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
        margin: "auto",
        maxWidth: 540,
        width: "92vw",
        borderRadius: "var(--radius-lg)",
        padding: 24,
        background: "#ffffff",
        border: "1px solid var(--border-subtle)",
        boxShadow: "var(--shadow-floating)",
      }}
    >
      <h2 id="diag-title" style={{ margin: "0 0 12px", fontSize: 18, color: "var(--color-text-main)" }}>
        Chi tiết lỗi xử lý: {source.logical_filename}
      </h2>
      <p className="error" role="alert" style={{ fontSize: 14 }}>
        Không thể xử lý tệp này. Mở chi tiết để xem dòng/trường và nguyên nhân; sửa tệp rồi tải lại, hoặc chọn Thử lại nếu đây là lỗi tạm thời.
      </p>
      {source.error_message && (
        <div
          style={{
            background: "var(--color-danger-bg)",
            border: "1px solid var(--color-danger-border)",
            padding: 12,
            borderRadius: "var(--radius-sm)",
            margin: "12px 0",
            fontSize: 14,
            color: "var(--color-danger-text)",
            fontFamily: "monospace",
          }}
        >
          <strong>Nguyên nhân:</strong> {source.error_message}
        </div>
      )}
      <div style={{ marginTop: 20, textAlign: "right" }}>
        <button type="button" className="btn-secondary" onClick={onClose}>
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
  const [isDropzoneActive, setIsDropzoneActive] = useState(false);

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

  const indexingSourcesCount = sourcesData
    ? sourcesData.items.filter((s) => s.status === "processing" || s.status === "queued").length
    : 0;

  return (
    <>
      <div className="eyebrow">{admin ? "Quản trị" : "Không gian làm việc"}</div>
      <h1>Dataset</h1>

      {/* Dataset List Card */}
      <section className="card">
        {admin && (
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            <button
              className="btn-primary"
              onClick={() => setPanel(null)}
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              Tạo Dataset
            </button>
            <button
              className="btn-secondary"
              onClick={() => setGrantPanel(true)}
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <polyline points="16 11 18 13 22 9" />
              </svg>
              Cấp quyền Dataset
            </button>
          </div>
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
            <p className="muted" style={{ marginBottom: 12 }}>
              {data.total} Dataset trong phạm vi của bạn
            </p>
            <table style={{ marginBottom: 16 }}>
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
                    <td style={{ fontWeight: 600 }}>{d.name}</td>
                    <td className="muted">{d.description || "—"}</td>
                    <td>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button
                          className="btn-secondary"
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
                          <button
                            className="btn-secondary"
                            aria-label={`Chỉnh sửa ${d.name}`}
                            onClick={() => setPanel(d)}
                          >
                            Chỉnh sửa
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <button
                className="btn-secondary"
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
              <span className="muted">Trang {page}</span>{" "}
              <button
                className="btn-secondary"
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
            </div>
          </>
        )}
      </section>

      {/* Selected Dataset Detail & Sources Area */}
      {detail && (
        <section className="card" aria-label="Chi tiết Dataset" style={{ marginTop: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                <h2 style={{ margin: 0, fontSize: 22, color: "var(--color-text-main)" }}>
                  {detail.name}
                </h2>
                <span className="badge badge-pastel-green">
                  {sourcesData ? `${sourcesData.total} nguồn tài liệu` : "Đang tải…"}
                </span>
              </div>
              <p className="muted" style={{ margin: 0, fontSize: 14 }}>
                {detail.description || "Chưa có mô tả cho dataset này."}
              </p>
            </div>
            <button
              className="btn-secondary"
              onClick={() => {
                detailSequence.current++;
                selectedId.current = null;
                setDetail(null);
              }}
            >
              Đóng chi tiết
            </button>
          </div>

          <hr style={{ border: 0, borderTop: "1px solid var(--border-divider)", margin: "16px 0 20px" }} />

          {/* Ingestion Progress Bar (Active when files are indexing or queued) */}
          {indexingSourcesCount > 0 && (
            <div
              style={{
                background: "var(--color-pastel-50)",
                border: "1px solid var(--color-mint-border)",
                borderRadius: "var(--radius-md)",
                padding: "14px 18px",
                marginBottom: 20,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 600, color: "var(--color-emerald-dark)" }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: "spin 2s linear infinite" }}>
                    <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
                  </svg>
                  Đang nạp và lập chỉ mục dữ liệu ({indexingSourcesCount} tệp đang trong hàng đợi xử lý)
                </div>
                <span className="badge badge-pastel-amber">Indexing</span>
              </div>
              <div
                style={{
                  width: "100%",
                  height: 8,
                  borderRadius: "var(--radius-full)",
                  background: "#e2e8f0",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: "75%",
                    background: "linear-gradient(90deg, #34d399, #10b981)",
                    borderRadius: "var(--radius-full)",
                    transition: "width 300ms ease",
                  }}
                />
              </div>
            </div>
          )}

          {/* Upload Dropzone (Prominent Pastel Green dashed box) */}
          {admin && (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDropzoneActive(true);
              }}
              onDragLeave={() => setIsDropzoneActive(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDropzoneActive(false);
                setShowUpload(true);
              }}
              onClick={() => setShowUpload(true)}
              style={{
                border: `2px dashed ${isDropzoneActive ? "var(--color-primary-green)" : "#a7f3d0"}`,
                borderRadius: 12,
                background: isDropzoneActive ? "#dcfce7" : "#f0fdf4",
                padding: "32px 24px",
                textAlign: "center",
                marginBottom: 24,
                cursor: "pointer",
                transition: "all 150ms ease",
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: "var(--radius-full)",
                  background: "#ffffff",
                  color: "#10b981",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 14px",
                  boxShadow: "var(--shadow-soft)",
                }}
              >
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>

              <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-text-main)", marginBottom: 6 }}>
                Kéo thả tài liệu vào đây hoặc click để tải lên
              </div>

              <div className="muted" style={{ fontSize: 13, marginBottom: 14 }}>
                Hỗ trợ tải lên tài liệu quy trình SOP, phiếu hỗ trợ, nhật ký lỗi hệ thống logistics
              </div>

              {/* Supported Format Mini Tags */}
              <div style={{ display: "flex", justifyContent: "center", gap: 6, flexWrap: "wrap", marginBottom: 18 }}>
                {["PDF", "DOCX", "CSV", "XLSX", "TXT", "JSON", "LOG"].map((fmt) => (
                  <span
                    key={fmt}
                    style={{
                      background: "#ffffff",
                      color: "#047857",
                      border: "1px solid #a7f3d0",
                      borderRadius: "var(--radius-full)",
                      padding: "2px 10px",
                      fontSize: 11,
                      fontWeight: 600,
                    }}
                  >
                    {fmt}
                  </span>
                ))}
              </div>

              <button
                type="button"
                className="btn-primary"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowUpload(true);
                }}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "8px 20px",
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Tải lên tài liệu
              </button>
            </div>
          )}

          {/* Sources Section Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ margin: 0, fontSize: 18, color: "var(--color-text-main)" }}>
              Nguồn dữ liệu ({sourcesData ? sourcesData.total : 0})
            </h3>
            {admin && (
              <button
                type="button"
                className="btn-primary"
                onClick={() => setShowUpload(true)}
              >
                Tải lên tài liệu
              </button>
            )}
          </div>

          {!sourcesData ? (
            <p role="status" className="muted">Đang tải nguồn dữ liệu…</p>
          ) : sourcesData.total === 0 ? (
            <div className="empty" style={{ padding: "40px 20px", textAlign: "center" }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: "var(--radius-full)",
                  background: "var(--bg-subtle)",
                  color: "var(--color-text-muted)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 12px",
                }}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
              </div>
              <h3 style={{ fontSize: 16, margin: "0 0 6px", color: "var(--color-text-main)" }}>
                Chưa có nguồn tài liệu trong dataset này
              </h3>
              <p className="muted" style={{ maxWidth: 440, margin: "0 auto 16px", fontSize: 14 }}>
                Dataset hiện tại chưa có tài liệu nào được lập chỉ mục. Nhấn &apos;Tải lên tài liệu&apos; để bắt đầu ingestion dữ liệu vận hành.
              </p>
              {admin && (
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => setShowUpload(true)}
                >
                  Tải lên tài liệu
                </button>
              )}
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table aria-label="Danh sách nguồn dữ liệu" style={{ minWidth: 780 }}>
                <thead>
                  <tr>
                    <th>Tên tài liệu</th>
                    <th>Định dạng</th>
                    <th>Kích thước</th>
                    <th>Trạng thái</th>
                    <th>Số ảnh trích xuất</th>
                    <th>Ngày tải lên</th>
                    <th style={{ textAlign: "right" }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {sourcesData.items.map((src) => {
                    const ext = getFileExtension(src.logical_filename);
                    return (
                      <tr key={src.id}>
                        <td>
                          <div style={{ fontWeight: 600, color: "var(--color-text-main)" }}>
                            {src.logical_filename}
                          </div>
                          <div className="muted" style={{ fontSize: 12 }}>
                            {formatProfileName(src.profile_id)}
                            {src.active_version_number !== null && ` · v${src.active_version_number}`}
                          </div>
                        </td>
                        <td>
                          <span
                            className="badge badge-pastel-green"
                            style={{ fontSize: 11, padding: "2px 8px" }}
                          >
                            {ext}
                          </span>
                        </td>
                        <td className="muted" style={{ fontSize: 13 }}>
                          —
                        </td>
                        <td>
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            {renderStatusBadge(src.status)}
                            {src.status === "failed" && (
                              <button
                                type="button"
                                aria-label="Xem chi tiết lỗi"
                                onClick={() => setDiagnosticSource(src)}
                                style={{
                                  padding: "2px 6px",
                                  fontSize: 11,
                                  background: "none",
                                  border: "1px solid var(--color-danger-border)",
                                  borderRadius: "var(--radius-sm)",
                                  color: "var(--color-danger-btn)",
                                  cursor: "pointer",
                                }}
                              >
                                Chi tiết
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="muted" style={{ fontSize: 13 }}>
                          —
                        </td>
                        <td className="muted" style={{ fontSize: 13 }}>
                          {new Date(src.created_at).toLocaleDateString("vi-VN")}
                        </td>
                        <td>
                          <div style={{ display: "flex", gap: 6, justifyContent: "flex-end", alignItems: "center" }}>
                            {(src.active_version_id !== null || src.status === "ready") && (
                              <button
                                type="button"
                                className="btn-secondary"
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
                                    type="button"
                                    className="btn-secondary"
                                    disabled={sourceActionBusy}
                                    style={{ padding: "6px 12px", fontSize: 13 }}
                                    onClick={() => handleRetry(src.id)}
                                  >
                                    Thử lại
                                  </button>
                                )}
                                {(src.active_version_id !== null || src.status === "ready") && (
                                  <button
                                    type="button"
                                    className="btn-secondary"
                                    disabled={sourceActionBusy}
                                    style={{ padding: "6px 12px", fontSize: 13 }}
                                    onClick={() => handleReprocess(src.id)}
                                    title="Nạp lại nguồn tài liệu"
                                  >
                                    Nạp lại nguồn
                                  </button>
                                )}
                                <button
                                  type="button"
                                  disabled={sourceActionBusy}
                                  aria-label="Xóa nguồn tài liệu"
                                  title="Xóa nguồn tài liệu"
                                  onClick={() => setDeleteSource(src)}
                                  style={{
                                    display: "inline-flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    width: 32,
                                    height: 32,
                                    padding: 0,
                                    background: "none",
                                    border: "1px solid var(--border-subtle)",
                                    borderRadius: "var(--radius-sm)",
                                    color: "var(--color-text-muted)",
                                    cursor: "pointer",
                                    transition: "all 150ms ease",
                                  }}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.color = "var(--color-danger-btn)";
                                    e.currentTarget.style.borderColor = "var(--color-danger-border)";
                                    e.currentTarget.style.backgroundColor = "var(--color-danger-bg)";
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.color = "var(--color-text-muted)";
                                    e.currentTarget.style.borderColor = "var(--border-subtle)";
                                    e.currentTarget.style.backgroundColor = "transparent";
                                  }}
                                >
                                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="3 6 5 6 21 6" />
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                  </svg>
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {sourcesData.total > sourcesData.page_size && (
                <div style={{ marginTop: 16, display: "flex", gap: 8, alignItems: "center", justifyContent: "flex-end" }}>
                  <button
                    className="btn-secondary"
                    disabled={sourcesPage <= 1}
                    onClick={() => setSourcesPage((p) => p - 1)}
                    style={{ padding: "6px 12px", fontSize: 13 }}
                  >
                    Trang trước
                  </button>
                  <span style={{ fontSize: 13 }} className="muted">
                    Trang {sourcesPage} / {Math.ceil(sourcesData.total / sourcesData.page_size)}
                  </span>
                  <button
                    className="btn-secondary"
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

      {/* Dataset Metadata Panel */}
      {panel !== undefined && (
        <MetadataPanel
          key={panel?.id ?? "new"}
          dataset={panel}
          csrf={session.csrf_token}
          onClose={() => setPanel(undefined)}
          onSaved={refresh}
        />
      )}

      {/* Dataset Grant Panel */}
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
