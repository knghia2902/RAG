"use client";

import React, { useEffect, useState } from "react";
import {
  Dataset,
  PeriodType,
  ReportDetail,
  ReportFilter,
  ReportHistoryItem,
} from "@/lib/contracts";

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<"create" | "history">("create");

  // Form state
  const [periodType, setPeriodType] = useState<PeriodType>("daily");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [availableDatasets, setAvailableDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetIds, setSelectedDatasetIds] = useState<string[]>([]);

  // Execution & loading states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [securityDenied, setSecurityDenied] = useState(false);

  // Result / Preview state
  const [activeReport, setActiveReport] = useState<ReportDetail | null>(null);
  const [historyItems, setHistoryItems] = useState<ReportHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showProvenanceModal, setShowProvenanceModal] = useState(false);

  const getCsrfToken = () => {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : "";
  };

  // Fetch datasets and history on initial load
  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    if (activeTab === "history") {
      fetchHistory();
    }
  }, [activeTab]);

  const fetchDatasets = async () => {
    try {
      const res = await fetch("/api/v1/datasets", {
        headers: { "X-Requested-With": "RAG-Web" },
      });
      if (res.ok) {
        const data = await res.json();
        const datasets = Array.isArray(data) ? data : data.items || [];
        setAvailableDatasets(datasets);
      }
    } catch {
      // Ignore background fetch error
    }
  };

  const fetchHistory = async () => {
    setLoadingHistory(true);
    setError(null);
    setSecurityDenied(false);
    try {
      const res = await fetch("/api/v1/reports/history", {
        headers: { "X-Requested-With": "RAG-Web" },
      });
      if (res.status === 403) {
        setSecurityDenied(true);
        setError("Quyền truy cập vào dữ liệu báo cáo đã bị thu hồi hoặc bạn không có quyền xem báo cáo.");
        setHistoryItems([]);
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setHistoryItems(data);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Không thể tải lịch sử báo cáo");
      }
    } catch (err: any) {
      setError(err.message || "Lỗi kết nối khi tải lịch sử báo cáo");
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSecurityDenied(false);

    const payload: ReportFilter = {
      period_type: periodType,
      start_date: periodType === "custom" && startDate ? startDate : undefined,
      end_date: periodType === "custom" && endDate ? endDate : undefined,
      dataset_ids: selectedDatasetIds,
    };

    try {
      const csrf = getCsrfToken();
      const res = await fetch("/api/v1/reports/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "RAG-Web",
          ...(csrf ? { "X-CSRF-Token": csrf } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (res.status === 403) {
        setSecurityDenied(true);
        setActiveReport(null);
        setError("Quyền truy cập vào một hoặc nhiều dataset đã bị thu hồi hoặc bạn không có quyền tạo báo cáo.");
        return;
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Không thể tạo báo cáo sự cố");
        return;
      }

      const reportDetail: ReportDetail = await res.json();
      setActiveReport(reportDetail);
    } catch (err: any) {
      setError(err.message || "Lỗi kết nối hệ thống khi tạo báo cáo");
    } finally {
      setLoading(false);
    }
  };

  const handleViewReport = async (reportId: string) => {
    setLoading(true);
    setError(null);
    setSecurityDenied(false);

    try {
      const res = await fetch(`/api/v1/reports/${reportId}`, {
        headers: { "X-Requested-With": "RAG-Web" },
      });

      if (res.status === 403) {
        setSecurityDenied(true);
        setActiveReport(null);
        setError("Quyền truy cập vào dữ liệu báo cáo này đã bị thu hồi theo chính sách Live Scope Recheck (AUTH-04, REP-06).");
        return;
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Không thể tải chi tiết báo cáo");
        return;
      }

      const reportDetail: ReportDetail = await res.json();
      setActiveReport(reportDetail);
    } catch (err: any) {
      setError(err.message || "Lỗi khi lấy chi tiết báo cáo");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = (reportId: string) => {
    // Direct browser download
    window.open(`/api/v1/reports/${reportId}/pdf`, "_blank");
  };

  const toggleDatasetSelection = (did: string) => {
    setSelectedDatasetIds((prev) =>
      prev.includes(did) ? prev.filter((id) => id !== did) : [...prev, did]
    );
  };

  return (
    <div className="workspace-container" style={{ padding: "24px 32px", maxWidth: "1280px", margin: "0 auto" }}>
      <header style={{ marginBottom: "20px" }}>
        <h1 style={{ fontSize: "24px", fontWeight: "bold", color: "#0f172a", marginBottom: "6px" }}>
          Báo cáo Sự cố IT & Vận hành Logistics
        </h1>
        <p style={{ color: "#64748b", fontSize: "14px", margin: 0 }}>
          Tạo báo cáo theo yêu cầu với số liệu tất định 100%, nhận định xu hướng của AI và xuất bản PDF tiếng Việt chuẩn in ấn (REP-01 - REP-06).
        </p>
      </header>

      {/* Tab Navigation */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid #e2e8f0", marginBottom: "20px" }}>
        <button
          type="button"
          onClick={() => { setActiveTab("create"); setError(null); }}
          style={{
            padding: "10px 18px",
            fontSize: "14px",
            fontWeight: activeTab === "create" ? "600" : "normal",
            color: activeTab === "create" ? "#2563eb" : "#64748b",
            borderBottom: activeTab === "create" ? "2px solid #2563eb" : "2px solid transparent",
            background: "none",
            borderTop: "none",
            borderLeft: "none",
            borderRight: "none",
            cursor: "pointer",
          }}
        >
          Tạo báo cáo mới
        </button>
        <button
          type="button"
          onClick={() => { setActiveTab("history"); setError(null); }}
          style={{
            padding: "10px 18px",
            fontSize: "14px",
            fontWeight: activeTab === "history" ? "600" : "normal",
            color: activeTab === "history" ? "#2563eb" : "#64748b",
            borderBottom: activeTab === "history" ? "2px solid #2563eb" : "2px solid transparent",
            background: "none",
            borderTop: "none",
            borderLeft: "none",
            borderRight: "none",
            cursor: "pointer",
          }}
        >
          Lịch sử báo cáo
        </button>
      </div>

      {/* Security alert / Error banner */}
      {securityDenied && (
        <div
          role="alert"
          style={{
            background: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#b91c1c",
            padding: "14px 18px",
            borderRadius: "6px",
            marginBottom: "20px",
            fontWeight: "500",
            fontSize: "14px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "18px" }}>⚠</span>
            <span>
              <strong>Lỗi Phân Quyền (HTTP 403 Forbidden):</strong> {error}
            </span>
          </div>
        </div>
      )}

      {error && !securityDenied && (
        <div
          role="alert"
          style={{
            background: "#fffbeb",
            border: "1px solid #fde68a",
            color: "#b45309",
            padding: "12px 16px",
            borderRadius: "6px",
            marginBottom: "20px",
            fontSize: "14px",
          }}
        >
          {error}
        </div>
      )}

      {/* TAB 1: Tạo báo cáo mới */}
      {activeTab === "create" && (
        <div style={{ display: "grid", gridTemplateColumns: activeReport ? "420px 1fr" : "1fr", gap: "24px" }}>
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "20px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
            }}
          >
            <h2 style={{ fontSize: "16px", fontWeight: "600", color: "#1e293b", marginBottom: "16px" }}>
              Cấu hình phạm vi báo cáo
            </h2>

            <form onSubmit={handleGenerateReport}>
              {/* Kỳ báo cáo */}
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "500", color: "#475569", marginBottom: "8px" }}>
                  Kỳ khảo sát (Múi giờ Asia/Ho_Chi_Minh - UTC+7)
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "8px" }}>
                  {[
                    { id: "daily", label: "Hôm nay" },
                    { id: "weekly", label: "Tuần này" },
                    { id: "monthly", label: "Tháng này" },
                    { id: "custom", label: "Tùy chọn" },
                  ].map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setPeriodType(p.id as PeriodType)}
                      style={{
                        padding: "8px 12px",
                        fontSize: "13px",
                        fontWeight: periodType === p.id ? "600" : "normal",
                        background: periodType === p.id ? "#eff6ff" : "#f8fafc",
                        color: periodType === p.id ? "#1d4ed8" : "#475569",
                        border: periodType === p.id ? "1px solid #3b82f6" : "1px solid #cbd5e1",
                        borderRadius: "6px",
                        cursor: "pointer",
                      }}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tùy chọn ngày nếu chọn Custom */}
              {periodType === "custom" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "16px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>
                      Từ ngày
                    </label>
                    <input
                      type="date"
                      required
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px 10px",
                        border: "1px solid #cbd5e1",
                        borderRadius: "6px",
                        fontSize: "13px",
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>
                      Đến ngày
                    </label>
                    <input
                      type="date"
                      required
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px 10px",
                        border: "1px solid #cbd5e1",
                        borderRadius: "6px",
                        fontSize: "13px",
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Chọn Dataset */}
              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "500", color: "#475569", marginBottom: "8px" }}>
                  Phạm vi Dataset được cấp quyền ({selectedDatasetIds.length}/{availableDatasets.length})
                </label>
                <div
                  style={{
                    maxHeight: "150px",
                    overflowY: "auto",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    padding: "8px 12px",
                    background: "#f8fafc",
                  }}
                >
                  {availableDatasets.length > 0 ? (
                    availableDatasets.map((ds) => (
                      <label
                        key={ds.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "8px",
                          fontSize: "13px",
                          padding: "4px 0",
                          cursor: "pointer",
                          color: "#334155",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={selectedDatasetIds.includes(ds.id)}
                          onChange={() => toggleDatasetSelection(ds.id)}
                        />
                        <span>{ds.name}</span>
                      </label>
                    ))
                  ) : (
                    <div style={{ fontSize: "12px", color: "#94a3b8", fontStyle: "italic" }}>
                      Đang tải danh sách dataset hoặc tài khoản chưa có dataset...
                    </div>
                  )}
                </div>
                <small style={{ fontSize: "11.5px", color: "#94a3b8", marginTop: "4px", display: "block" }}>
                  * Nếu không chọn, hệ thống sẽ tự động tổng hợp toàn bộ dataset trong quyền hạn của bạn.
                </small>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: "100%",
                  padding: "10px 16px",
                  fontSize: "14px",
                  fontWeight: "600",
                  color: "#ffffff",
                  background: loading ? "#94a3b8" : "#2563eb",
                  border: "none",
                  borderRadius: "6px",
                  cursor: loading ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                }}
              >
                {loading ? "Đang tổng hợp số liệu..." : "Tạo báo cáo ngay"}
              </button>
            </form>
          </div>

          {/* Result Preview Container */}
          {activeReport && (
            <ReportPreviewSection
              report={activeReport}
              onDownloadPdf={() => handleDownloadPdf(activeReport.id)}
              onOpenProvenance={() => setShowProvenanceModal(true)}
            />
          )}
        </div>
      )}

      {/* TAB 2: Lịch sử báo cáo */}
      {activeTab === "history" && (
        <div
          style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            overflow: "hidden",
            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          }}
        >
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #e2e8f0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "16px", fontWeight: "600", color: "#1e293b", margin: 0 }}>
              Danh sách báo cáo đã lập
            </h2>
            <button
              onClick={fetchHistory}
              disabled={loadingHistory}
              style={{
                fontSize: "13px",
                padding: "6px 12px",
                background: "#f1f5f9",
                border: "1px solid #cbd5e1",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              {loadingHistory ? "Đang tải..." : "Làm mới"}
            </button>
          </div>

          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13.5px" }}>
            <thead>
              <tr style={{ background: "#f8fafc", textAlign: "left", color: "#475569" }}>
                <th style={{ padding: "10px 16px", borderBottom: "1px solid #e2e8f0" }}>Tiêu đề báo cáo</th>
                <th style={{ padding: "10px 16px", borderBottom: "1px solid #e2e8f0" }}>Kỳ</th>
                <th style={{ padding: "10px 16px", borderBottom: "1px solid #e2e8f0" }}>Sự cố</th>
                <th style={{ padding: "10px 16px", borderBottom: "1px solid #e2e8f0" }}>Ticket</th>
                <th style={{ padding: "10px 16px", borderBottom: "1px solid #e2e8f0" }}>Thời điểm tạo</th>
                <th style={{ padding: "10px 16px", borderBottom: "1px solid #e2e8f0", textAlign: "right" }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {historyItems.length > 0 ? (
                historyItems.map((item) => (
                  <tr key={item.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    <td style={{ padding: "12px 16px", fontWeight: "500", color: "#1e293b" }}>{item.title}</td>
                    <td style={{ padding: "12px 16px", textTransform: "uppercase", fontSize: "12px", color: "#64748b" }}>
                      {item.period_type}
                    </td>
                    <td style={{ padding: "12px 16px" }}>{item.total_incidents}</td>
                    <td style={{ padding: "12px 16px" }}>{item.total_tickets}</td>
                    <td style={{ padding: "12px 16px", color: "#64748b", fontSize: "12.5px" }}>
                      {new Date(item.created_at).toLocaleString("vi-VN")}
                    </td>
                    <td style={{ padding: "12px 16px", textAlign: "right" }}>
                      <button
                        onClick={() => handleViewReport(item.id)}
                        style={{
                          marginRight: "8px",
                          padding: "6px 10px",
                          fontSize: "12.5px",
                          background: "#eff6ff",
                          color: "#1d4ed8",
                          border: "1px solid #bfdbfe",
                          borderRadius: "4px",
                          cursor: "pointer",
                        }}
                      >
                        Xem trước
                      </button>
                      <button
                        onClick={() => handleDownloadPdf(item.id)}
                        style={{
                          padding: "6px 10px",
                          fontSize: "12.5px",
                          background: "#f0fdf4",
                          color: "#15803d",
                          border: "1px solid #bbf7d0",
                          borderRadius: "4px",
                          cursor: "pointer",
                        }}
                      >
                        Tải PDF
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "#94a3b8" }}>
                    {loadingHistory ? "Đang tải dữ liệu..." : "Chưa có báo cáo nào được tạo trong phạm vi quyền hạn của bạn."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {activeReport && activeTab === "history" && (
            <div style={{ padding: "20px", borderTop: "2px solid #e2e8f0" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h3 style={{ fontSize: "16px", fontWeight: "600", margin: 0, color: "#0f172a" }}>
                  Bản xem trước chi tiết báo cáo đang chọn
                </h3>
                <button
                  onClick={() => setActiveReport(null)}
                  style={{
                    fontSize: "12px",
                    background: "none",
                    border: "none",
                    color: "#64748b",
                    cursor: "pointer",
                  }}
                >
                  ✕ Đóng bản xem trước
                </button>
              </div>
              <ReportPreviewSection
                report={activeReport}
                onDownloadPdf={() => handleDownloadPdf(activeReport.id)}
                onOpenProvenance={() => setShowProvenanceModal(true)}
              />
            </div>
          )}
        </div>
      )}

      {/* Provenance Modal */}
      {showProvenanceModal && activeReport && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(15, 23, 42, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: "#ffffff",
              borderRadius: "8px",
              padding: "24px",
              maxWidth: "700px",
              width: "90%",
              maxHeight: "80vh",
              overflowY: "auto",
              boxShadow: "0 10px 25px rgba(0,0,0,0.2)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: "600", color: "#0f172a", margin: 0 }}>
                Nguồn dữ liệu tham chiếu (Provenance Snapshot)
              </h3>
              <button
                onClick={() => setShowProvenanceModal(false)}
                style={{ background: "none", border: "none", fontSize: "18px", cursor: "pointer", color: "#64748b" }}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: "13px", color: "#475569", marginBottom: "14px" }}>
              Danh sách các tệp dữ liệu, phiên bản và mã dataset đã tạo nên các số liệu trong báo cáo:
            </p>

            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ background: "#f8fafc", textAlign: "left" }}>
                  <th style={{ padding: "8px 12px", borderBottom: "1px solid #e2e8f0" }}>Tên tệp nguồn</th>
                  <th style={{ padding: "8px 12px", borderBottom: "1px solid #e2e8f0" }}>Phiên bản</th>
                  <th style={{ padding: "8px 12px", borderBottom: "1px solid #e2e8f0" }}>Dataset ID</th>
                </tr>
              </thead>
              <tbody>
                {activeReport.provenance_sources && activeReport.provenance_sources.length > 0 ? (
                  activeReport.provenance_sources.map((src, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "8px 12px", fontWeight: "500" }}>{src.filename || "N/A"}</td>
                      <td style={{ padding: "8px 12px" }}>v{src.version_number || 1}</td>
                      <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: "12px", color: "#64748b" }}>
                        {src.dataset_id}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} style={{ padding: "16px", textAlign: "center", color: "#94a3b8" }}>
                      Không có thông tin nguồn tham chiếu.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            <div style={{ marginTop: "20px", textAlign: "right" }}>
              <button
                onClick={() => setShowProvenanceModal(false)}
                style={{
                  padding: "8px 16px",
                  fontSize: "13px",
                  background: "#e2e8f0",
                  color: "#334155",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ReportPreviewSection({
  report,
  onDownloadPdf,
  onOpenProvenance,
}: {
  report: ReportDetail;
  onDownloadPdf: () => void;
  onOpenProvenance: () => void;
}) {
  const m = report.metrics;

  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "8px",
        padding: "24px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      {/* Header & Download Button */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          borderBottom: "1px solid #e2e8f0",
          paddingBottom: "16px",
          marginBottom: "20px",
        }}
      >
        <div>
          <h2 style={{ fontSize: "18px", fontWeight: "bold", color: "#0f172a", margin: "0 0 6px 0" }}>
            {report.title}
          </h2>
          <div style={{ fontSize: "12.5px", color: "#64748b" }}>
            <span>Kỳ: <strong>{report.period_type.toUpperCase()}</strong></span> ·{" "}
            <span>
              Múi giờ: {report.timezone} ({new Date(report.start_time).toLocaleDateString("vi-VN")} -{" "}
              {new Date(report.end_time).toLocaleDateString("vi-VN")})
            </span>
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            type="button"
            onClick={onOpenProvenance}
            style={{
              padding: "8px 14px",
              fontSize: "13px",
              background: "#f8fafc",
              color: "#334155",
              border: "1px solid #cbd5e1",
              borderRadius: "6px",
              cursor: "pointer",
            }}
          >
            Nguồn dữ liệu
          </button>
          <button
            type="button"
            onClick={onDownloadPdf}
            style={{
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: "600",
              background: "#16a34a",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            Tải PDF tiếng Việt
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5, 1fr)",
          gap: "12px",
          marginBottom: "24px",
        }}
      >
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", padding: "12px", borderRadius: "6px", textAlign: "center" }}>
          <div style={{ fontSize: "20px", fontWeight: "bold", color: "#0f172a" }}>{m.total_incidents}</div>
          <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Tổng sự cố</div>
        </div>
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", padding: "12px", borderRadius: "6px", textAlign: "center" }}>
          <div style={{ fontSize: "20px", fontWeight: "bold", color: "#0f172a" }}>{m.total_tickets}</div>
          <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Ticket IT</div>
        </div>
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", padding: "12px", borderRadius: "6px", textAlign: "center" }}>
          <div style={{ fontSize: "20px", fontWeight: "bold", color: "#dc2626" }}>{m.open_incidents}</div>
          <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Đang mở</div>
        </div>
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", padding: "12px", borderRadius: "6px", textAlign: "center" }}>
          <div style={{ fontSize: "20px", fontWeight: "bold", color: "#16a34a" }}>{m.resolved_incidents}</div>
          <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Đã giải quyết</div>
        </div>
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", padding: "12px", borderRadius: "6px", textAlign: "center" }}>
          <div style={{ fontSize: "20px", fontWeight: "bold", color: "#2563eb" }}>
            {m.mttr_minutes !== null ? `${m.mttr_minutes}m` : "Chưa hoàn tất"}
          </div>
          <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>MTTR TB</div>
        </div>
      </div>

      {/* System & Priority Breakdown Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginBottom: "24px" }}>
        {/* System distribution */}
        <div style={{ border: "1px solid #e2e8f0", borderRadius: "6px", padding: "14px" }}>
          <h3 style={{ fontSize: "14px", fontWeight: "600", color: "#1e293b", marginTop: 0, marginBottom: "10px" }}>
            Phân bổ theo Hệ thống
          </h3>
          <table style={{ width: "100%", fontSize: "12.5px", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ color: "#64748b", textAlign: "left", borderBottom: "1px solid #e2e8f0" }}>
                <th style={{ padding: "6px 0" }}>Hệ thống</th>
                <th style={{ padding: "6px 0", textAlign: "center" }}>Sự cố</th>
                <th style={{ padding: "6px 0", textAlign: "right" }}>Tỷ lệ</th>
              </tr>
            </thead>
            <tbody>
              {m.system_breakdown && m.system_breakdown.length > 0 ? (
                m.system_breakdown.map((s, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #f8fafc" }}>
                    <td style={{ padding: "6px 0", fontWeight: "500" }}>{s.system}</td>
                    <td style={{ padding: "6px 0", textAlign: "center" }}>{s.incident_count}</td>
                    <td style={{ padding: "6px 0", textAlign: "right", color: "#2563eb" }}>{s.percentage}%</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} style={{ padding: "8px 0", textAlign: "center", color: "#94a3b8" }}>
                    Không có dữ liệu
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Priority distribution */}
        <div style={{ border: "1px solid #e2e8f0", borderRadius: "6px", padding: "14px" }}>
          <h3 style={{ fontSize: "14px", fontWeight: "600", color: "#1e293b", marginTop: 0, marginBottom: "10px" }}>
            Phân bổ theo Mức độ Ưu tiên
          </h3>
          <table style={{ width: "100%", fontSize: "12.5px", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ color: "#64748b", textAlign: "left", borderBottom: "1px solid #e2e8f0" }}>
                <th style={{ padding: "6px 0" }}>Mức độ</th>
                <th style={{ padding: "6px 0", textAlign: "center" }}>Số lượng</th>
                <th style={{ padding: "6px 0", textAlign: "right" }}>Tỷ lệ</th>
              </tr>
            </thead>
            <tbody>
              {m.priority_breakdown && m.priority_breakdown.length > 0 ? (
                m.priority_breakdown.map((p, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #f8fafc" }}>
                    <td style={{ padding: "6px 0", fontWeight: "bold" }}>{p.priority}</td>
                    <td style={{ padding: "6px 0", textAlign: "center" }}>{p.count}</td>
                    <td style={{ padding: "6px 0", textAlign: "right", color: "#2563eb" }}>{p.percentage}%</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} style={{ padding: "8px 0", textAlign: "center", color: "#94a3b8" }}>
                    Không có dữ liệu
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recurring Errors List */}
      <div style={{ border: "1px solid #e2e8f0", borderRadius: "6px", padding: "16px", marginBottom: "24px" }}>
        <h3 style={{ fontSize: "14px", fontWeight: "600", color: "#1e293b", marginTop: 0, marginBottom: "10px" }}>
          Danh mục lỗi lặp lại (Xuất hiện &ge; 2 lần)
        </h3>
        {m.recurring_errors && m.recurring_errors.length > 0 ? (
          <table style={{ width: "100%", fontSize: "13px", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8fafc", textAlign: "left", color: "#475569" }}>
                <th style={{ padding: "8px 12px", borderBottom: "1px solid #e2e8f0" }}>Hệ thống & Nhóm lỗi</th>
                <th style={{ padding: "8px 12px", borderBottom: "1px solid #e2e8f0", textAlign: "center" }}>Số lần</th>
                <th style={{ padding: "8px 12px", borderBottom: "1px solid #e2e8f0", textAlign: "center" }}>Tỷ lệ</th>
                <th style={{ padding: "8px 12px", borderBottom: "1px solid #e2e8f0" }}>Đơn hàng bị ảnh hưởng</th>
              </tr>
            </thead>
            <tbody>
              {m.recurring_errors.map((err, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                  <td style={{ padding: "8px 12px", fontWeight: "500" }}>{err.system}: {err.error_group}</td>
                  <td style={{ padding: "8px 12px", textAlign: "center", fontWeight: "bold", color: "#dc2626" }}>
                    {err.occurrence_count}
                  </td>
                  <td style={{ padding: "8px 12px", textAlign: "center" }}>{err.percentage}%</td>
                  <td style={{ padding: "8px 12px", color: "#475569" }}>
                    {err.affected_orders.join(", ") || "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ fontSize: "13px", color: "#64748b", fontStyle: "italic", padding: "8px 0" }}>
            Không ghi nhận lỗi nào lặp lại từ 2 lần trở lên trong kỳ khảo sát.
          </div>
        )}
      </div>

      {/* AI Narrative Analysis */}
      <div style={{ border: "1px solid #bfdbfe", background: "#f8fafc", borderRadius: "6px", padding: "18px" }}>
        <h3 style={{ fontSize: "15px", fontWeight: "600", color: "#1d4ed8", marginTop: 0, marginBottom: "12px" }}>
          Nhận định Vận hành & Khuyến nghị SOP (AI Analysis)
        </h3>

        <div style={{ marginBottom: "14px" }}>
          <h4 style={{ fontSize: "13px", fontWeight: "600", color: "#334155", margin: "0 0 4px 0" }}>
            Tóm tắt điều hành
          </h4>
          <p style={{ fontSize: "13.5px", color: "#1e293b", margin: 0, lineHeight: 1.5 }}>
            {report.narrative.executive_summary}
          </p>
        </div>

        <div style={{ marginBottom: "14px" }}>
          <h4 style={{ fontSize: "13px", fontWeight: "600", color: "#334155", margin: "0 0 4px 0" }}>
            Phân tích nguyên nhân gốc rễ
          </h4>
          <p style={{ fontSize: "13.5px", color: "#1e293b", margin: 0, lineHeight: 1.5 }}>
            {report.narrative.root_cause_analysis}
          </p>
        </div>

        <div style={{ marginBottom: "14px" }}>
          <h4 style={{ fontSize: "13px", fontWeight: "600", color: "#334155", margin: "0 0 6px 0" }}>
            Khuyến nghị xử lý theo SOP
          </h4>
          <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "13px", color: "#1e293b", lineHeight: 1.6 }}>
            {report.narrative.recommendations && report.narrative.recommendations.length > 0 ? (
              report.narrative.recommendations.map((rec, idx) => <li key={idx}>{rec}</li>)
            ) : (
              <li>Không có khuyến nghị cụ thể.</li>
            )}
          </ul>
        </div>

        {report.narrative.missing_data_warnings && report.narrative.missing_data_warnings.length > 0 && (
          <div style={{ marginTop: "12px", padding: "8px 12px", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: "4px" }}>
            <strong style={{ fontSize: "12px", color: "#92400e" }}>Lưu ý về dữ liệu:</strong>
            <ul style={{ margin: "4px 0 0 0", paddingLeft: "18px", fontSize: "12px", color: "#92400e" }}>
              {report.narrative.missing_data_warnings.map((w, idx) => <li key={idx}>{w}</li>)}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
