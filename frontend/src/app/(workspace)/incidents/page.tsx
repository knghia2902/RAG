"use client";

import React, { useState } from "react";
import Timeline from "@/components/Timeline";
import {
  IncidentAnalysisDetail,
  SeverityType,
  SystemType,
  TimelineEvent,
} from "@/lib/contracts";

export default function IncidentsPage() {
  const [activeTab, setActiveTab] = useState<"quick_form" | "upload_ticket">("quick_form");

  // Form states
  const [orderId, setOrderId] = useState("");
  const [description, setDescription] = useState("");
  const [selectedSystem, setSelectedSystem] = useState<string>("");
  const [ticketFile, setTicketFile] = useState<File | null>(null);

  // Execution states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Array<{ line: number; field?: string; message: string }>>([]);

  // Result state
  const [analysis, setAnalysis] = useState<IncidentAnalysisDetail | null>(null);

  // Citation preview modal state
  const [selectedCitation, setSelectedCitation] = useState<{
    title: string;
    source: string;
    line?: number;
    timestamp?: string;
    snippet: string;
    citation_id?: number | string;
  } | null>(null);

  const getCsrfToken = () => {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : "";
  };

  const handleAnalyzeQuickForm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderId.trim()) return;

    setLoading(true);
    setError(null);
    setValidationErrors([]);
    setAnalysis(null);

    try {
      const csrf = getCsrfToken();
      const res = await fetch("/api/v1/incidents/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "RAG-Web",
          ...(csrf ? { "X-CSRF-Token": csrf } : {}),
        },
        body: JSON.stringify({
          order_id: orderId.trim(),
          description: description.trim() || undefined,
          system: selectedSystem || undefined,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Lỗi khi phân tích sự cố");
      }

      const data = await res.json();
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message || "Đã xảy ra lỗi ngoài ý muốn");
    } finally {
      setLoading(false);
    }
  };

  const handleUploadTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketFile) return;

    setLoading(true);
    setError(null);
    setValidationErrors([]);
    setAnalysis(null);

    try {
      const csrf = getCsrfToken();
      const formData = new FormData();
      formData.append("file", ticketFile);

      const res = await fetch("/api/v1/incidents/upload-ticket", {
        method: "POST",
        headers: {
          "X-Requested-With": "RAG-Web",
          ...(csrf ? { "X-CSRF-Token": csrf } : {}),
        },
        body: formData,
      });

      if (res.status === 422) {
        const errData = await res.json();
        setValidationErrors(errData.detail?.errors || []);
        throw new Error(errData.detail?.message || "Tệp ticket sai quy cách cấu trúc.");
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Lỗi khi tải lên và phân tích ticket");
      }

      const data = await res.json();
      setAnalysis(data.analysis);
    } catch (err: any) {
      setError(err.message || "Đã xảy ra lỗi ngoài ý muốn");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectEvent = (event: TimelineEvent) => {
    setSelectedCitation({
      title: `${event.system} - ${event.event_name}`,
      source: event.source_filename,
      line: event.line_number,
      timestamp: event.timestamp,
      snippet: event.raw_snippet,
      citation_id: event.citation_id,
    });
  };

  const renderPriorityBadge = (priority: SeverityType | string) => {
    switch (priority) {
      case "P1":
        return <span className="badge badge-pastel-rose">Mức ưu tiên: P1 Critical</span>;
      case "P2":
        return <span className="badge badge-pastel-amber">Mức ưu tiên: P2 Medium</span>;
      case "P3":
        return <span className="badge badge-pastel-green">Mức ưu tiên: P3 Low</span>;
      case "P4":
        return <span className="badge badge-pastel-slate">Mức ưu tiên: P4 Info</span>;
      default:
        return <span className="badge badge-pastel-slate">Mức ưu tiên: {priority}</span>;
    }
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
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
          ĐỐI SOÁT LOG IT & LOGISTICS
        </div>
        <h1 style={{ margin: "0 0 8px 0" }}>
          Phân tích sự cố Logistics IT (WMS-TMS)
        </h1>
        <p className="muted" style={{ margin: 0 }}>
          Đối soát luồng log đa hệ thống theo mã đơn hàng, định vị điểm gãy đồng bộ và đề xuất bước xử lý theo chuẩn SOP.
        </p>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          marginBottom: "20px",
          background: "var(--bg-subtle)",
          padding: "4px",
          borderRadius: "10px",
          width: "fit-content",
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab("quick_form")}
          style={{
            padding: "8px 18px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            borderRadius: "8px",
            border: activeTab === "quick_form" ? "1px solid var(--color-mint-border)" : "1px solid transparent",
            backgroundColor: activeTab === "quick_form" ? "#ffffff" : "transparent",
            color: activeTab === "quick_form" ? "var(--color-emerald-dark)" : "var(--color-text-muted)",
            boxShadow: activeTab === "quick_form" ? "var(--shadow-soft)" : "none",
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
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <span>Tra cứu theo Mã đơn hàng (Order ID)</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("upload_ticket")}
          style={{
            padding: "8px 18px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            borderRadius: "8px",
            border: activeTab === "upload_ticket" ? "1px solid var(--color-mint-border)" : "1px solid transparent",
            backgroundColor: activeTab === "upload_ticket" ? "#ffffff" : "transparent",
            color: activeTab === "upload_ticket" ? "var(--color-emerald-dark)" : "var(--color-text-muted)",
            boxShadow: activeTab === "upload_ticket" ? "var(--shadow-soft)" : "none",
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
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <span>Phân tích theo Ticket sự cố</span>
        </button>
      </div>

      {/* Input Section Card */}
      <div className="card-soft" style={{ marginBottom: "28px" }}>
        {activeTab === "quick_form" ? (
          <form onSubmit={handleAnalyzeQuickForm}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px", marginBottom: "20px" }}>
              <div>
                <label htmlFor="order-id-input">
                  Mã đơn hàng (Order ID) *
                </label>
                <div style={{ display: "flex", gap: "8px" }}>
                  <input
                    id="order-id-input"
                    type="text"
                    placeholder="Ví dụ: DH001"
                    value={orderId}
                    onChange={(e) => setOrderId(e.target.value)}
                    required
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    onClick={() => setOrderId("DH001")}
                    className="btn-secondary"
                    style={{ whiteSpace: "nowrap", fontSize: "13px", padding: "8px 12px" }}
                    title="Điền nhanh mã đơn hàng mẫu DH001"
                  >
                    Mẫu DH001
                  </button>
                </div>
              </div>

              <div>
                <label htmlFor="system-select">
                  Hệ thống liên quan
                </label>
                <select
                  id="system-select"
                  value={selectedSystem}
                  onChange={(e) => setSelectedSystem(e.target.value)}
                >
                  <option value="">Tất cả hệ thống (WMS · Gateway · TMS)</option>
                  <option value="WMS">WMS (Kho Sóng Thần)</option>
                  <option value="API_GATEWAY">API Gateway</option>
                  <option value="TMS">TMS (Điều phối vận tải)</option>
                </select>
              </div>

              <div>
                <label htmlFor="incident-desc-input">
                  Mô tả vắn tắt sự cố (Tùy chọn)
                </label>
                <input
                  id="incident-desc-input"
                  type="text"
                  placeholder="Ví dụ: Đơn đóng gói nhưng chưa thấy tài xế..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "12px" }}>
              <button
                type="submit"
                disabled={loading || !orderId.trim()}
                className="btn-primary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "10px 22px",
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
                    <span>Đang phân tích...</span>
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
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    <span>Phân tích sự cố</span>
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleUploadTicket}>
            <div
              style={{
                border: "2px dashed var(--color-mint-border)",
                borderRadius: "12px",
                backgroundColor: "var(--color-pastel-50)",
                padding: "28px",
                textAlign: "center",
                marginBottom: "20px",
                cursor: "pointer",
                transition: "all 150ms ease",
              }}
            >
              <div
                style={{
                  width: "48px",
                  height: "48px",
                  borderRadius: "50%",
                  backgroundColor: "#ffffff",
                  color: "var(--color-emerald-dark)",
                  boxShadow: "var(--shadow-soft)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 12px",
                }}
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>

              <label
                htmlFor="ticket-file-input"
                style={{
                  fontSize: "15px",
                  fontWeight: 600,
                  color: "var(--color-text-main)",
                  cursor: "pointer",
                  marginBottom: "4px",
                }}
              >
                {ticketFile ? ticketFile.name : "Chọn tệp Ticket (.json hoặc .csv) *"}
              </label>

              <p className="muted" style={{ fontSize: "13px", margin: "4px 0 14px" }}>
                Hỗ trợ tệp JSON danh sách hoặc CSV với các cột: <code>ticket_id</code>, <code>order_id</code>, <code>timestamp</code>, <code>system</code>, <code>severity</code>, <code>description</code>. Tối đa 5MB.
              </p>

              <input
                id="ticket-file-input"
                type="file"
                accept=".json,.csv"
                onChange={(e) => setTicketFile(e.target.files?.[0] || null)}
                required
                style={{ display: "none" }}
              />

              <button
                type="button"
                onClick={() => document.getElementById("ticket-file-input")?.click()}
                className="btn-secondary"
                style={{ fontSize: "13px" }}
              >
                {ticketFile ? "Thay đổi tệp khác" : "Duyệt tìm tệp trên máy tính"}
              </button>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="submit"
                disabled={loading || !ticketFile}
                className="btn-primary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "10px 22px",
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
                    <span>Đang tải lên...</span>
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
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                    <span>Phân tích sự cố</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {/* Global Error Banner */}
        {error && (
          <div role="alert" className="error" style={{ marginTop: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <svg
                width="16"
                height="16"
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
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Validation Errors Table (422) */}
        {validationErrors.length > 0 && (
          <div style={{ marginTop: "16px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: 700, color: "var(--color-danger-text)", margin: "0 0 8px 0" }}>
              Chi tiết lỗi kiểm định dòng tệp ticket:
            </h4>
            <div style={{ overflowX: "auto", border: "1px solid var(--color-danger-border)", borderRadius: "8px" }}>
              <table>
                <thead>
                  <tr style={{ backgroundColor: "var(--color-danger-bg)", color: "var(--color-danger-text)" }}>
                    <th style={{ width: "80px" }}>Dòng</th>
                    <th style={{ width: "160px" }}>Trường vi phạm</th>
                    <th>Mô tả lỗi</th>
                  </tr>
                </thead>
                <tbody>
                  {validationErrors.map((err, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>{err.line}</td>
                      <td style={{ color: "var(--color-text-muted)" }}>{err.field || "-"}</td>
                      <td style={{ color: "var(--color-danger-text)" }}>{err.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Empty State when no analysis yet */}
      {!analysis && !loading && (
        <div
          className="card-soft"
          style={{
            textAlign: "center",
            padding: "56px 24px",
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
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </div>
          <h2 style={{ fontSize: "20px", fontWeight: 600, color: "var(--color-text-main)", margin: "0 0 8px 0" }}>
            Chưa có sự cố nào được phân tích
          </h2>
          <p className="muted" style={{ maxWidth: "540px", margin: "0 auto 20px", fontSize: "15px" }}>
            Nhập mã đơn hàng (ví dụ: DH001) hoặc tải file ticket để hệ thống đối chiếu log WMS/TMS và đề xuất hướng xử lý.
          </p>
          <button
            type="button"
            onClick={() => {
              setOrderId("DH001");
              // Trigger quick search
              const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
              setOrderId("DH001");
            }}
            className="btn-secondary"
            style={{ fontSize: "13px" }}
          >
            Thử phân tích ngay đơn hàng DH001
          </button>
        </div>
      )}

      {/* 4-Block Incident Dashboard */}
      {analysis && (
        <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
          {/* KHỐI 1: Tổng quan & Phân loại sự cố */}
          <div className="card-soft">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
              <div>
                <div className="eyebrow" style={{ marginBottom: "4px" }}>
                  KHỐI 1 · TỔNG QUAN & PHÂN LOẠI SỰ CỐ
                </div>
                <h2 style={{ fontSize: "20px", fontWeight: 600, color: "var(--color-text-main)", margin: "4px 0 0 0" }}>
                  {analysis.title}
                </h2>
              </div>

              {/* Priority & Confidence Badges */}
              <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                {renderPriorityBadge(analysis.classification.suggested_priority)}
                <span className="badge badge-pastel-slate">
                  Độ tin cậy: {Math.round(analysis.classification.confidence * 100)}%
                </span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px", marginBottom: "16px", flexWrap: "wrap" }}>
              <span className="badge badge-pastel-slate" style={{ padding: "4px 10px" }}>
                <strong style={{ marginRight: "4px" }}>Nhóm lỗi:</strong> {analysis.classification.error_group}
              </span>
              <span className="badge badge-pastel-green" style={{ padding: "4px 10px" }}>
                <strong style={{ marginRight: "4px" }}>Hệ thống chính:</strong> {analysis.classification.primary_system}
              </span>
              {analysis.ticket_id && (
                <span className="badge badge-pastel-amber" style={{ padding: "4px 10px" }}>
                  <strong style={{ marginRight: "4px" }}>Phiếu Ticket:</strong> {analysis.ticket_id}
                </span>
              )}
            </div>

            <p style={{ margin: 0, fontSize: "15px", lineHeight: "1.6", color: "var(--color-text-main)" }}>
              {analysis.summary}
            </p>
          </div>

          {/* KHỐI 2: Trục dòng thời gian đa hệ thống */}
          <div className="card-soft">
            <div style={{ marginBottom: "20px" }}>
              <div className="eyebrow" style={{ marginBottom: "4px" }}>
                KHỐI 2 · TRỤC THỜI GIAN ĐỐI SOÁT ĐA HỆ THỐNG
              </div>
              <h3 style={{ fontSize: "18px", fontWeight: 600, color: "var(--color-text-main)", margin: "4px 0 0 0" }}>
                Chuỗi sự kiện theo thứ tự thời gian (WMS → API Gateway → TMS)
              </h3>
            </div>

            <Timeline events={analysis.timeline} onSelectEvent={handleSelectEvent} />
          </div>

          {/* KHỐI 3: Giả thuyết nguyên nhân gốc rễ & Dữ liệu còn thiếu */}
          <div className="card-soft">
            <div style={{ marginBottom: "20px" }}>
              <div className="eyebrow" style={{ marginBottom: "4px" }}>
                KHỐI 3 · GIẢ THUYẾT NGUYÊN NHÂN & CẢNH BÁO THIẾU THÔNG TIN
              </div>
              <h3 style={{ fontSize: "18px", fontWeight: 600, color: "var(--color-text-main)", margin: "4px 0 0 0" }}>
                Nguyên nhân gốc rễ đề xuất
              </h3>
            </div>

            {/* Hypotheses List */}
            <div style={{ display: "flex", flexDirection: "column", gap: "14px", marginBottom: "20px" }}>
              {analysis.hypotheses.map((h, idx) => {
                const isConfirmed = Boolean(h.is_confirmed);
                return (
                  <div
                    key={idx}
                    style={{
                      padding: "16px 20px",
                      borderRadius: "10px",
                      backgroundColor: isConfirmed ? "var(--color-pastel-50)" : "#fffbeb",
                      border: isConfirmed ? "1px solid var(--color-mint-border)" : "1px solid #fde68a",
                      transition: "all 150ms ease",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px", flexWrap: "wrap" }}>
                      <span className={`badge ${isConfirmed ? "badge-pastel-green" : "badge-pastel-amber"}`}>
                        {isConfirmed ? "ĐÃ XÁC NHẬN TỪ LOG" : "GIẢ THUYẾT NGUYÊN NHÂN"}
                      </span>
                      <span style={{ fontSize: "12.5px", color: "var(--color-text-muted)" }}>
                        Độ tin cậy: <strong>{h.confidence_level}</strong>
                      </span>
                      {h.supporting_evidence_citations.length > 0 && (
                        <div style={{ display: "flex", alignItems: "center", gap: "4px", marginLeft: "auto" }}>
                          <span style={{ fontSize: "12.5px", color: "var(--color-emerald-dark)", fontWeight: 500 }}>
                            Trích dẫn:
                          </span>
                          {h.supporting_evidence_citations.map((c) => (
                            <span key={c} className="badge badge-pastel-green" style={{ padding: "1px 6px", fontSize: "11px" }}>
                              #{c}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <p style={{ margin: 0, fontSize: "14.5px", color: "var(--color-text-main)", lineHeight: "1.6" }}>
                      {h.hypothesis}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Missing Information Yellow Banner (RAG-05) */}
            {analysis.missing_information.length > 0 && (
              <div
                style={{
                  padding: "16px 20px",
                  borderRadius: "10px",
                  backgroundColor: "#fefce8",
                  border: "1px solid #fef08a",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px", color: "#854d0e" }}>
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
                  <strong style={{ fontSize: "14px" }}>Cảnh báo dữ liệu còn thiếu / chưa đầy đủ (RAG-05):</strong>
                </div>
                <ul style={{ margin: 0, paddingLeft: "24px", fontSize: "13.5px", color: "#713f12", lineHeight: "1.6" }}>
                  {analysis.missing_information.map((item, idx) => (
                    <li key={idx} style={{ marginBottom: "4px" }}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* KHỐI 4: Khuyến nghị & Quy trình xử lý theo SOP */}
          <div className="card-soft">
            <div style={{ marginBottom: "20px" }}>
              <div className="eyebrow" style={{ marginBottom: "4px" }}>
                KHỐI 4 · CÁC BƯỚC XỬ LÝ THEO QUY TRÌNH CHUẨN (SOP)
              </div>
              <h3 style={{ fontSize: "18px", fontWeight: 600, color: "var(--color-text-main)", margin: "4px 0 0 0" }}>
                Hướng dẫn kiểm tra và khắc phục có thể kiểm tra nguồn
              </h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {analysis.recommended_actions.map((act) => (
                <div
                  key={act.step_number}
                  style={{
                    display: "flex",
                    gap: "16px",
                    padding: "16px 20px",
                    backgroundColor: "var(--bg-card)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "10px",
                    boxShadow: "var(--shadow-soft)",
                    alignItems: "flex-start",
                  }}
                >
                  {/* Step number badge */}
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      backgroundColor: "var(--color-primary-green)",
                      color: "#ffffff",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                      fontSize: "14px",
                      flexShrink: 0,
                    }}
                  >
                    {act.step_number}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px", flexWrap: "wrap" }}>
                      <span className="badge badge-pastel-green">
                        Quy trình: {act.sop_reference}
                      </span>
                    </div>

                    <p style={{ margin: "0 0 8px 0", fontSize: "15px", fontWeight: 600, color: "var(--color-text-main)" }}>
                      {act.action}
                    </p>

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "13px",
                        color: "var(--color-emerald-dark)",
                      }}
                    >
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
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>
                        <strong>Kết quả kỳ vọng:</strong> {act.expected_outcome}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Citation Preview Modal */}
      {selectedCitation && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="citation-modal-title"
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
              maxWidth: "640px",
              width: "100%",
              padding: "24px",
              boxShadow: "var(--shadow-floating)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h3 id="citation-modal-title" style={{ margin: 0, fontSize: "17px", fontWeight: 600, color: "var(--color-text-main)" }}>
                  {selectedCitation.title}
                </h3>
                {selectedCitation.citation_id && (
                  <span className="badge badge-pastel-green">
                    #{selectedCitation.citation_id}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => setSelectedCitation(null)}
                aria-label="Đóng bảng xem trước trích dẫn"
                style={{
                  background: "transparent",
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

            <div
              style={{
                display: "flex",
                gap: "8px",
                flexWrap: "wrap",
                fontSize: "12.5px",
                color: "var(--color-text-muted)",
                marginBottom: "16px",
              }}
            >
              <span className="badge badge-pastel-slate">
                Tệp nguồn: {selectedCitation.source}
              </span>
              {selectedCitation.line && (
                <span className="badge badge-pastel-slate">
                  Dòng: {selectedCitation.line}
                </span>
              )}
              {selectedCitation.timestamp && (
                <span className="badge badge-pastel-slate">
                  Thời gian: {selectedCitation.timestamp}
                </span>
              )}
            </div>

            <pre
              style={{
                margin: 0,
                padding: "14px 16px",
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "10px",
                fontSize: "13px",
                lineHeight: "1.5",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                maxHeight: "320px",
                overflowY: "auto",
                fontFamily: "ui-monospace, SFMono-Regular, monospace",
                color: "var(--color-text-main)",
              }}
            >
              {selectedCitation.snippet}
            </pre>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "20px" }}>
              <button
                type="button"
                onClick={() => setSelectedCitation(null)}
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
