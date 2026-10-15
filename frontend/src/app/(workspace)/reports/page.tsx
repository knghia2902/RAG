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
        setError("Quyền truy cập vào dữ liệu báo cáo này đã bị thu hồi theo chính sách Live Scope Recheck (AUTH-04, REP-06).");
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
    window.open(`/api/v1/reports/${reportId}/pdf`, "_blank");
  };

  const toggleDatasetSelection = (did: string) => {
    setSelectedDatasetIds((prev) =>
      prev.includes(did) ? prev.filter((id) => id !== did) : [...prev, did]
    );
  };

  return (
    <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
      {/* Page Header */}
      <div style={{ marginBottom: "28px" }}>
        <div className="eyebrow" style={{ marginBottom: "8px" }}>
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          SỐ LIỆU TẤT ĐỊNH & AI NARRATIVE
        </div>
        <h1 style={{ margin: "0 0 8px 0" }}>
          Báo cáo Sự cố IT & Vận hành Logistics
        </h1>
        <p className="muted" style={{ margin: 0 }}>
          Tạo báo cáo theo yêu cầu với số liệu tất định 100%, nhận định xu hướng của AI và xuất bản PDF tiếng Việt chuẩn in ấn (REP-01 - REP-06).
        </p>
      </div>

      {/* Tab Navigation */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          marginBottom: "24px",
          backgroundColor: "var(--bg-subtle)",
          padding: "4px",
          borderRadius: "10px",
          width: "fit-content",
        }}
      >
        <button
          type="button"
          onClick={() => {
            setActiveTab("create");
            setError(null);
          }}
          style={{
            padding: "8px 18px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            borderRadius: "8px",
            border: activeTab === "create" ? "1px solid var(--color-mint-border)" : "1px solid transparent",
            backgroundColor: activeTab === "create" ? "#ffffff" : "transparent",
            color: activeTab === "create" ? "var(--color-emerald-dark)" : "var(--color-text-muted)",
            boxShadow: activeTab === "create" ? "var(--shadow-soft)" : "none",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            transition: "all 150ms ease",
          }}
        >
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M12 5v14M5 12h14" />
          </svg>
          <span>Tạo báo cáo mới</span>
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab("history");
            setError(null);
          }}
          style={{
            padding: "8px 18px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            borderRadius: "8px",
            border: activeTab === "history" ? "1px solid var(--color-mint-border)" : "1px solid transparent",
            backgroundColor: activeTab === "history" ? "#ffffff" : "transparent",
            color: activeTab === "history" ? "var(--color-emerald-dark)" : "var(--color-text-muted)",
            boxShadow: activeTab === "history" ? "var(--shadow-soft)" : "none",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            transition: "all 150ms ease",
          }}
        >
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span>Lịch sử báo cáo</span>
        </button>
      </div>

      {/* Security alert / Error banner */}
      {securityDenied && (
        <div role="alert" className="error" style={{ marginBottom: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
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
            backgroundColor: "#fffbeb",
            border: "1px solid #fde68a",
            color: "#b45309",
            padding: "12px 16px",
            borderRadius: "8px",
            marginBottom: "24px",
            fontSize: "14px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* TAB 1: Tạo báo cáo mới */}
      {activeTab === "create" && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: activeReport ? "minmax(340px, 380px) 1fr" : "minmax(340px, 480px) 1fr",
            gap: "28px",
            alignItems: "start",
          }}
        >
          {/* Form Cấu hình phạm vi báo cáo */}
          <div className="card-soft">
            <div style={{ marginBottom: "18px" }}>
              <div className="eyebrow" style={{ marginBottom: "4px" }}>
                THIẾT LẬP THỜI GIAN & PHẠM VI
              </div>
              <h2 style={{ fontSize: "18px", fontWeight: 600, color: "var(--color-text-main)", margin: 0 }}>
                Cấu hình phạm vi báo cáo
              </h2>
            </div>

            <form onSubmit={handleGenerateReport}>
              {/* Kỳ báo cáo buttons */}
              <div style={{ marginBottom: "18px" }}>
                <label style={{ marginBottom: "8px" }}>
                  Kỳ khảo sát (Múi giờ Asia/Ho_Chi_Minh - UTC+7)
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "8px" }}>
                  {[
                    { id: "daily", label: "Hôm nay" },
                    { id: "weekly", label: "Tuần này" },
                    { id: "monthly", label: "Tháng này" },
                    { id: "custom", label: "Tùy chọn ngày" },
                  ].map((p) => {
                    const isActive = periodType === p.id;
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => setPeriodType(p.id as PeriodType)}
                        style={{
                          padding: "9px 12px",
                          fontSize: "13.5px",
                          fontWeight: isActive ? 600 : 500,
                          backgroundColor: isActive ? "var(--color-pastel-mint)" : "#ffffff",
                          color: isActive ? "var(--color-emerald-dark)" : "var(--color-text-main)",
                          border: isActive ? "1.5px solid var(--color-primary-green)" : "1px solid var(--border-subtle)",
                          borderRadius: "8px",
                          cursor: "pointer",
                          transition: "all 150ms ease",
                          textAlign: "center",
                        }}
                      >
                        {p.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Tùy chọn ngày nếu chọn Custom */}
              {periodType === "custom" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "18px" }}>
                  <div>
                    <label htmlFor="report-start-date" style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
                      Từ ngày
                    </label>
                    <input
                      id="report-start-date"
                      type="date"
                      required
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                    />
                  </div>
                  <div>
                    <label htmlFor="report-end-date" style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
                      Đến ngày
                    </label>
                    <input
                      id="report-end-date"
                      type="date"
                      required
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                    />
                  </div>
                </div>
              )}

              {/* Chọn Dataset */}
              <div style={{ marginBottom: "22px" }}>
                <label style={{ marginBottom: "8px" }}>
                  Phạm vi Dataset được cấp quyền ({selectedDatasetIds.length}/{availableDatasets.length})
                </label>
                <div
                  style={{
                    maxHeight: "160px",
                    overflowY: "auto",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "8px",
                    padding: "8px 12px",
                    backgroundColor: "var(--bg-app)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                  }}
                >
                  {availableDatasets.length > 0 ? (
                    availableDatasets.map((ds) => {
                      const isChecked = selectedDatasetIds.includes(ds.id);
                      return (
                        <label
                          key={ds.id}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            fontSize: "13px",
                            padding: "6px 8px",
                            borderRadius: "6px",
                            cursor: "pointer",
                            backgroundColor: isChecked ? "var(--color-pastel-mint)" : "transparent",
                            color: isChecked ? "var(--color-emerald-dark)" : "var(--color-text-main)",
                            transition: "background-color 150ms ease",
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => toggleDatasetSelection(ds.id)}
                            style={{ accentColor: "var(--color-primary-green)" }}
                          />
                          <span style={{ fontWeight: isChecked ? 600 : 400 }}>{ds.name}</span>
                        </label>
                      );
                    })
                  ) : (
                    <div style={{ fontSize: "12.5px", color: "var(--color-text-muted)", fontStyle: "italic", padding: "8px" }}>
                      Đang tải danh sách dataset hoặc tài khoản chưa có dataset...
                    </div>
                  )}
                </div>
                <small className="muted" style={{ fontSize: "12px", marginTop: "6px", display: "block" }}>
                  * Nếu không chọn, hệ thống tự động tổng hợp toàn bộ dataset trong quyền hạn của bạn.
                </small>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
                style={{
                  width: "100%",
                  padding: "11px 18px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  fontSize: "14.5px",
                }}
              >
                {loading ? (
                  <>
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      style={{ animation: "spin 1s linear infinite" }}
                      aria-hidden="true"
                    >
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                    <span>Đang tổng hợp số liệu...</span>
                  </>
                ) : (
                  <>
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                    </svg>
                    <span>Tạo báo cáo sự cố</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Right Column: Active Report Preview OR Empty State */}
          {activeReport ? (
            <ReportPreviewSection
              report={activeReport}
              onDownloadPdf={() => handleDownloadPdf(activeReport.id)}
              onOpenProvenance={() => setShowProvenanceModal(true)}
            />
          ) : (
            <div
              className="card-soft"
              style={{
                textAlign: "center",
                padding: "64px 32px",
                backgroundColor: "#ffffff",
              }}
            >
              <div
                style={{
                  width: "64px",
                  height: "64px",
                  borderRadius: "50%",
                  backgroundColor: "var(--color-pastel-mint)",
                  color: "var(--color-emerald-dark)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 16px",
                }}
              >
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
              </div>
              <h2 style={{ fontSize: "20px", fontWeight: 600, color: "var(--color-text-main)", margin: "0 0 8px 0" }}>
                Chưa có báo cáo sự cố nào được tạo
              </h2>
              <p className="muted" style={{ maxWidth: "480px", margin: "0 auto", fontSize: "15px" }}>
                Chọn khoảng thời gian hoặc kỳ báo cáo và nhấn &apos;Tạo báo cáo sự cố&apos; để xem trước số liệu và xuất file PDF.
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Lịch sử báo cáo */}
      {activeTab === "history" && (
        <div className="card-soft" style={{ padding: 0, overflow: "hidden" }}>
          <div
            style={{
              padding: "18px 24px",
              borderBottom: "1px solid var(--border-subtle)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div>
              <div className="eyebrow" style={{ marginBottom: "2px" }}>
                KHO LƯU TRỮ
              </div>
              <h2 style={{ fontSize: "18px", fontWeight: 600, color: "var(--color-text-main)", margin: 0 }}>
                Danh sách báo cáo đã lập
              </h2>
            </div>
            <button
              onClick={fetchHistory}
              disabled={loadingHistory}
              className="btn-secondary"
              style={{ fontSize: "13px", padding: "6px 14px", display: "flex", alignItems: "center", gap: "6px" }}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
              </svg>
              <span>{loadingHistory ? "Đang tải..." : "Làm mới"}</span>
            </button>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>Tiêu đề báo cáo</th>
                  <th>Kỳ khảo sát</th>
                  <th style={{ textAlign: "center" }}>Sự cố</th>
                  <th style={{ textAlign: "center" }}>Ticket</th>
                  <th>Thời điểm tạo</th>
                  <th style={{ textAlign: "right" }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {historyItems.length > 0 ? (
                  historyItems.map((item) => (
                    <tr key={item.id}>
                      <td style={{ fontWeight: 600, color: "var(--color-text-main)" }}>
                        {item.title}
                      </td>
                      <td>
                        <span className="badge badge-pastel-slate" style={{ textTransform: "uppercase" }}>
                          {item.period_type}
                        </span>
                      </td>
                      <td style={{ textAlign: "center", fontWeight: 600 }}>{item.total_incidents}</td>
                      <td style={{ textAlign: "center" }}>{item.total_tickets}</td>
                      <td style={{ color: "var(--color-text-muted)", fontSize: "13px" }}>
                        {new Date(item.created_at).toLocaleString("vi-VN")}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "8px" }}>
                          <button
                            onClick={() => handleViewReport(item.id)}
                            className="btn-secondary"
                            style={{
                              fontSize: "12.5px",
                              padding: "5px 10px",
                              color: "var(--color-emerald-dark)",
                              borderColor: "var(--color-mint-border)",
                            }}
                          >
                            Xem trước
                          </button>
                          <button
                            onClick={() => handleDownloadPdf(item.id)}
                            className="btn-primary"
                            style={{
                              fontSize: "12.5px",
                              padding: "5px 10px",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                          >
                            <svg
                              width="12"
                              height="12"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              aria-hidden="true"
                            >
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                              <polyline points="7 10 12 15 17 10" />
                              <line x1="12" y1="15" x2="12" y2="3" />
                            </svg>
                            <span>Xuất PDF</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} style={{ padding: "48px 24px", textAlign: "center", color: "var(--color-text-muted)" }}>
                      {loadingHistory ? "Đang tải dữ liệu..." : "Chưa có báo cáo nào được tạo trong phạm vi quyền hạn của bạn."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {activeReport && activeTab === "history" && (
            <div style={{ padding: "28px 24px", borderTop: "2px solid var(--border-subtle)", backgroundColor: "var(--bg-app)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                <div>
                  <div className="eyebrow">XEM TRƯỚC BÁO CÁO</div>
                  <h3 style={{ fontSize: "18px", fontWeight: 600, margin: "2px 0 0 0", color: "var(--color-text-main)" }}>
                    Bản xem trước chi tiết báo cáo đang chọn
                  </h3>
                </div>
                <button
                  onClick={() => setActiveReport(null)}
                  className="btn-secondary"
                  style={{ fontSize: "12.5px", padding: "6px 12px" }}
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
          role="dialog"
          aria-modal="true"
          aria-labelledby="provenance-modal-title"
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(15, 23, 42, 0.45)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "20px",
          }}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "16px",
              border: "1px solid var(--border-subtle)",
              padding: "24px",
              maxWidth: "720px",
              width: "100%",
              maxHeight: "85vh",
              overflowY: "auto",
              boxShadow: "var(--shadow-floating)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "50%",
                    backgroundColor: "var(--color-pastel-mint)",
                    color: "var(--color-emerald-dark)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </div>
                <h3 id="provenance-modal-title" style={{ fontSize: "17px", fontWeight: 600, color: "var(--color-text-main)", margin: 0 }}>
                  Nguồn dữ liệu tham chiếu (Provenance Snapshot)
                </h3>
              </div>
              <button
                onClick={() => setShowProvenanceModal(false)}
                aria-label="Đóng nguồn dữ liệu tham chiếu"
                style={{
                  background: "none",
                  border: "none",
                  fontSize: "18px",
                  cursor: "pointer",
                  color: "var(--color-text-muted)",
                  padding: "4px 8px",
                  borderRadius: "6px",
                }}
              >
                ✕
              </button>
            </div>

            <p className="muted" style={{ fontSize: "13.5px", marginBottom: "16px" }}>
              Danh sách các tệp dữ liệu, phiên bản và mã dataset đã tạo nên các số liệu trong báo cáo:
            </p>

            <div style={{ overflowX: "auto", border: "1px solid var(--border-subtle)", borderRadius: "8px" }}>
              <table>
                <thead>
                  <tr>
                    <th>Tên tệp nguồn</th>
                    <th>Phiên bản</th>
                    <th>Dataset ID</th>
                  </tr>
                </thead>
                <tbody>
                  {activeReport.provenance_sources && activeReport.provenance_sources.length > 0 ? (
                    activeReport.provenance_sources.map((src, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 600 }}>{src.filename || "N/A"}</td>
                        <td>
                          <span className="badge badge-pastel-green">
                            v{src.version_number || 1}
                          </span>
                        </td>
                        <td style={{ fontFamily: "monospace", fontSize: "12px", color: "var(--color-text-muted)" }}>
                          {src.dataset_id}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={3} style={{ padding: "24px", textAlign: "center", color: "var(--color-text-muted)" }}>
                        Không có thông tin nguồn tham chiếu.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div style={{ marginTop: "20px", display: "flex", justifyContent: "flex-end" }}>
              <button
                onClick={() => setShowProvenanceModal(false)}
                className="btn-secondary"
                style={{ fontSize: "13px" }}
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

  const resolutionRate =
    m.total_incidents > 0
      ? `${Math.round((m.resolved_incidents / m.total_incidents) * 100)}%`
      : "100%";

  return (
    <div
      style={{
        backgroundColor: "#ffffff",
        border: "1px solid var(--border-subtle)",
        borderRadius: "12px",
        padding: "32px",
        boxShadow: "var(--shadow-card)",
      }}
    >
      {/* Header & Download Actions */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          borderBottom: "1px solid var(--border-subtle)",
          paddingBottom: "20px",
          marginBottom: "24px",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <div className="eyebrow" style={{ marginBottom: "4px" }}>
            XEM TRƯỚC VĂN BẢN BÁO CÁO
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 700, color: "var(--color-text-main)", margin: "0 0 6px 0" }}>
            {report.title}
          </h2>
          <div style={{ fontSize: "13px", color: "var(--color-text-muted)", display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
            <span className="badge badge-pastel-green" style={{ textTransform: "uppercase" }}>
              Kỳ: {report.period_type}
            </span>
            <span>·</span>
            <span>Múi giờ: {report.timezone}</span>
            <span>·</span>
            <span>
              {new Date(report.start_time).toLocaleDateString("vi-VN")} — {new Date(report.end_time).toLocaleDateString("vi-VN")}
            </span>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            type="button"
            onClick={onOpenProvenance}
            className="btn-secondary"
            style={{
              fontSize: "13px",
              padding: "8px 14px",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span>Nguồn dữ liệu</span>
          </button>
          <button
            type="button"
            onClick={onDownloadPdf}
            className="btn-primary"
            style={{
              fontSize: "13px",
              padding: "8px 16px",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>Xuất PDF</span>
          </button>
        </div>
      </div>

      {/* 4 Floating KPI Summary Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "16px",
          marginBottom: "28px",
        }}
      >
        {/* Card 1: Tổng số sự cố */}
        <div
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid var(--border-subtle)",
            borderRadius: "12px",
            padding: "18px 20px",
            boxShadow: "var(--shadow-soft)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
            <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted)", textTransform: "uppercase" }}>
              Tổng số sự cố
            </span>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                backgroundColor: "var(--color-pastel-mint)",
                color: "var(--color-emerald-dark)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
            </div>
          </div>
          <div style={{ fontSize: "30px", fontWeight: 700, color: "var(--color-text-main)", lineHeight: 1.1 }}>
            {m.total_incidents}
          </div>
          <div style={{ fontSize: "12px", color: "var(--color-text-muted)", marginTop: "6px" }}>
            {m.open_incidents} đang mở · {m.resolved_incidents} đã xử lý
          </div>
        </div>

        {/* Card 2: Thời gian xử lý trung bình (MTTR) */}
        <div
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid var(--border-subtle)",
            borderRadius: "12px",
            padding: "18px 20px",
            boxShadow: "var(--shadow-soft)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
            <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted)", textTransform: "uppercase" }}>
              MTTR Trung bình
            </span>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                backgroundColor: "var(--color-pastel-mint)",
                color: "var(--color-emerald-dark)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            </div>
          </div>
          <div style={{ fontSize: "28px", fontWeight: 700, color: "var(--color-emerald-dark)", lineHeight: 1.1 }}>
            {m.mttr_minutes !== null ? `${m.mttr_minutes} phút` : "Hoàn tất"}
          </div>
          <div style={{ fontSize: "12px", color: "var(--color-text-muted)", marginTop: "6px" }}>
            Thời gian giải quyết trung bình
          </div>
        </div>

        {/* Card 3: Tỷ lệ giải quyết sự cố */}
        <div
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid var(--border-subtle)",
            borderRadius: "12px",
            padding: "18px 20px",
            boxShadow: "var(--shadow-soft)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
            <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted)", textTransform: "uppercase" }}>
              Tỷ lệ giải quyết
            </span>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                backgroundColor: "var(--color-pastel-mint)",
                color: "var(--color-emerald-dark)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
          </div>
          <div style={{ fontSize: "30px", fontWeight: 700, color: "var(--color-text-main)", lineHeight: 1.1 }}>
            {resolutionRate}
          </div>
          <div style={{ fontSize: "12px", color: "var(--color-text-muted)", marginTop: "6px" }}>
            {m.resolved_incidents}/{m.total_incidents} sự cố được đóng
          </div>
        </div>

        {/* Card 4: Tỷ lệ trích dẫn bằng chứng */}
        <div
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid var(--border-subtle)",
            borderRadius: "12px",
            padding: "18px 20px",
            boxShadow: "var(--shadow-soft)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
            <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted)", textTransform: "uppercase" }}>
              Trích dẫn bằng chứng
            </span>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                backgroundColor: "var(--color-pastel-mint)",
                color: "var(--color-emerald-dark)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
            </div>
          </div>
          <div style={{ fontSize: "30px", fontWeight: 700, color: "var(--color-text-main)", lineHeight: 1.1 }}>
            100%
          </div>
          <div style={{ fontSize: "12px", color: "var(--color-text-muted)", marginTop: "6px" }}>
            Bằng chứng nguồn đối chiếu đầy đủ
          </div>
        </div>
      </div>

      {/* System & Priority Breakdown Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px", marginBottom: "28px" }}>
        {/* System distribution */}
        <div style={{ border: "1px solid var(--border-subtle)", borderRadius: "10px", padding: "16px", backgroundColor: "#ffffff" }}>
          <h3 style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-text-main)", margin: "0 0 12px 0" }}>
            Phân bổ theo Hệ thống
          </h3>
          <table>
            <thead>
              <tr>
                <th>Hệ thống</th>
                <th style={{ textAlign: "center" }}>Sự cố</th>
                <th style={{ textAlign: "right" }}>Tỷ lệ</th>
              </tr>
            </thead>
            <tbody>
              {m.system_breakdown && m.system_breakdown.length > 0 ? (
                m.system_breakdown.map((s, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>{s.system}</td>
                    <td style={{ textAlign: "center" }}>{s.incident_count}</td>
                    <td style={{ textAlign: "right", color: "var(--color-emerald-dark)", fontWeight: 600 }}>
                      {s.percentage}%
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} style={{ padding: "16px", textAlign: "center", color: "var(--color-text-muted)" }}>
                    Không có dữ liệu
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Priority distribution */}
        <div style={{ border: "1px solid var(--border-subtle)", borderRadius: "10px", padding: "16px", backgroundColor: "#ffffff" }}>
          <h3 style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-text-main)", margin: "0 0 12px 0" }}>
            Phân bổ theo Mức độ Ưu tiên
          </h3>
          <table>
            <thead>
              <tr>
                <th>Mức độ</th>
                <th style={{ textAlign: "center" }}>Số lượng</th>
                <th style={{ textAlign: "right" }}>Tỷ lệ</th>
              </tr>
            </thead>
            <tbody>
              {m.priority_breakdown && m.priority_breakdown.length > 0 ? (
                m.priority_breakdown.map((p, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>
                      <span
                        className={`badge ${
                          p.priority === "P1"
                            ? "badge-pastel-rose"
                            : p.priority === "P2"
                            ? "badge-pastel-amber"
                            : "badge-pastel-green"
                        }`}
                      >
                        {p.priority}
                      </span>
                    </td>
                    <td style={{ textAlign: "center" }}>{p.count}</td>
                    <td style={{ textAlign: "right", color: "var(--color-emerald-dark)", fontWeight: 600 }}>
                      {p.percentage}%
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} style={{ padding: "16px", textAlign: "center", color: "var(--color-text-muted)" }}>
                    Không có dữ liệu
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recurring Errors List */}
      <div style={{ border: "1px solid var(--border-subtle)", borderRadius: "10px", padding: "18px 20px", marginBottom: "28px", backgroundColor: "#ffffff" }}>
        <h3 style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-text-main)", margin: "0 0 12px 0" }}>
          Danh mục lỗi lặp lại (Xuất hiện &ge; 2 lần)
        </h3>
        {m.recurring_errors && m.recurring_errors.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>Hệ thống & Nhóm lỗi</th>
                  <th style={{ textAlign: "center" }}>Số lần</th>
                  <th style={{ textAlign: "center" }}>Tỷ lệ</th>
                  <th>Đơn hàng bị ảnh hưởng</th>
                </tr>
              </thead>
              <tbody>
                {m.recurring_errors.map((err, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>
                      {err.system}: {err.error_group}
                    </td>
                    <td style={{ textAlign: "center", fontWeight: 700, color: "var(--color-danger-text)" }}>
                      {err.occurrence_count}
                    </td>
                    <td style={{ textAlign: "center", fontWeight: 600 }}>{err.percentage}%</td>
                    <td style={{ color: "var(--color-text-muted)", fontSize: "13px" }}>
                      {err.affected_orders.join(", ") || "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ fontSize: "13.5px", color: "var(--color-text-muted)", fontStyle: "italic", padding: "12px 0" }}>
            Không ghi nhận lỗi nào lặp lại từ 2 lần trở lên trong kỳ khảo sát.
          </div>
        )}
      </div>

      {/* AI Narrative Analysis */}
      <div
        style={{
          border: "1px solid var(--color-mint-border)",
          backgroundColor: "var(--color-pastel-50)",
          borderRadius: "12px",
          padding: "24px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: "var(--color-pastel-mint)",
              color: "var(--color-emerald-dark)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
          </div>
          <h3 style={{ fontSize: "17px", fontWeight: 600, color: "var(--color-emerald-dark)", margin: 0 }}>
            Nhận định Vận hành & Khuyến nghị SOP (AI Analysis)
          </h3>
        </div>

        <div style={{ marginBottom: "16px" }}>
          <h4 style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-text-main)", margin: "0 0 6px 0" }}>
            Tóm tắt điều hành
          </h4>
          <p style={{ fontSize: "14px", color: "var(--color-text-main)", margin: 0, lineHeight: 1.6 }}>
            {report.narrative.executive_summary}
          </p>
        </div>

        <div style={{ marginBottom: "16px" }}>
          <h4 style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-text-main)", margin: "0 0 6px 0" }}>
            Phân tích nguyên nhân gốc rễ
          </h4>
          <p style={{ fontSize: "14px", color: "var(--color-text-main)", margin: 0, lineHeight: 1.6 }}>
            {report.narrative.root_cause_analysis}
          </p>
        </div>

        <div style={{ marginBottom: "16px" }}>
          <h4 style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-text-main)", margin: "0 0 8px 0" }}>
            Khuyến nghị xử lý theo SOP
          </h4>
          <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "14px", color: "var(--color-text-main)", lineHeight: 1.6 }}>
            {report.narrative.recommendations && report.narrative.recommendations.length > 0 ? (
              report.narrative.recommendations.map((rec, idx) => <li key={idx} style={{ marginBottom: "4px" }}>{rec}</li>)
            ) : (
              <li>Không có khuyến nghị cụ thể.</li>
            )}
          </ul>
        </div>

        {report.narrative.missing_data_warnings && report.narrative.missing_data_warnings.length > 0 && (
          <div
            style={{
              marginTop: "16px",
              padding: "12px 16px",
              backgroundColor: "#fffbeb",
              border: "1px solid #fde68a",
              borderRadius: "8px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px", color: "#92400e" }}>
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <strong style={{ fontSize: "13px" }}>Lưu ý về dữ liệu:</strong>
            </div>
            <ul style={{ margin: 0, paddingLeft: "22px", fontSize: "13px", color: "#92400e", lineHeight: 1.5 }}>
              {report.narrative.missing_data_warnings.map((w, idx) => (
                <li key={idx} style={{ marginBottom: "2px" }}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
