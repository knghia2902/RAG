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
  const [selectedCitation, setSelectedCitation] = useState<any | null>(null);
  const [citationError, setCitationError] = useState<string | null>(null);

  const getCsrfToken = () => {
    // Read csrf token from document cookie or local storage if applicable
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
    setCitationError(null);
  };

  const getPriorityBadge = (priority: SeverityType | string) => {
    switch (priority) {
      case "P1":
        return { bg: "#fee2e2", text: "#991b1b", border: "#fca5a5" };
      case "P2":
        return { bg: "#ffedd5", text: "#9a3412", border: "#fdba74" };
      case "P3":
        return { bg: "#fef9c3", text: "#854d0e", border: "#fde047" };
      case "P4":
        return { bg: "#e0f2fe", text: "#0369a1", border: "#7dd3fc" };
      default:
        return { bg: "#f1f5f9", text: "#334155", border: "#cbd5e1" };
    }
  };

  return (
    <div style={{ padding: "24px 32px", maxWidth: "1280px", margin: "0 auto" }}>
      {/* Page Header */}
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ fontSize: "24px", fontWeight: 700, color: "#0f172a", margin: "0 0 6px 0" }}>
          Phân tích sự cố Logistics IT (WMS-TMS)
        </h1>
        <p style={{ margin: 0, color: "#64748b", fontSize: "14px" }}>
          Đối soát luồng log đa hệ thống theo mã đơn hàng, định vị điểm gãy đồng bộ và đề xuất bước xử lý theo chuẩn SOP.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "12px", borderBottom: "1px solid #e2e8f0", marginBottom: "20px" }}>
        <button
          type="button"
          onClick={() => setActiveTab("quick_form")}
          style={{
            padding: "10px 18px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            border: "none",
            borderBottom: activeTab === "quick_form" ? "2px solid #0284c7" : "2px solid transparent",
            color: activeTab === "quick_form" ? "#0284c7" : "#64748b",
            background: "transparent",
          }}
        >
          Nhập nhanh Order ID
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("upload_ticket")}
          style={{
            padding: "10px 18px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            border: "none",
            borderBottom: activeTab === "upload_ticket" ? "2px solid #0284c7" : "2px solid transparent",
            color: activeTab === "upload_ticket" ? "#0284c7" : "#64748b",
            background: "transparent",
          }}
        >
          Tải tệp Ticket (JSON / CSV)
        </button>
      </div>

      {/* Input Section Card */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "8px",
          padding: "20px",
          marginBottom: "28px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
        }}
      >
        {activeTab === "quick_form" ? (
          <form onSubmit={handleAnalyzeQuickForm}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px", marginBottom: "16px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                  Mã đơn hàng (Order ID) *
                </label>
                <input
                  type="text"
                  placeholder="Ví dụ: DH001"
                  value={orderId}
                  onChange={(e) => setOrderId(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    fontSize: "14px",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                  Hệ thống liên quan
                </label>
                <select
                  value={selectedSystem}
                  onChange={(e) => setSelectedSystem(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    fontSize: "14px",
                    background: "#ffffff",
                  }}
                >
                  <option value="">Tất cả hệ thống</option>
                  <option value="WMS">WMS (Kho Sóng Thần)</option>
                  <option value="API_GATEWAY">API Gateway</option>
                  <option value="TMS">TMS (Điều phối vận tải)</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                  Mô tả vắn tắt sự cố (Tùy chọn)
                </label>
                <input
                  type="text"
                  placeholder="Đơn đóng gói nhưng chưa thấy tài xế..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    fontSize: "14px",
                  }}
                />
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="submit"
                disabled={loading || !orderId.trim()}
                style={{
                  background: loading ? "#94a3b8" : "#0284c7",
                  color: "#ffffff",
                  padding: "10px 24px",
                  borderRadius: "6px",
                  border: "none",
                  fontSize: "14px",
                  fontWeight: 600,
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                {loading ? "Đang phân tích..." : "Phân tích sự cố"}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleUploadTicket}>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                Chọn tệp Ticket (.json hoặc .csv) *
              </label>
              <input
                type="file"
                accept=".json,.csv"
                onChange={(e) => setTicketFile(e.target.files?.[0] || null)}
                required
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "1px dashed #cbd5e1",
                  background: "#f8fafc",
                  fontSize: "14px",
                }}
              />
              <span style={{ fontSize: "12px", color: "#64748b", marginTop: "4px", display: "block" }}>
                Hỗ trợ tệp JSON danh sách hoặc CSV với các cột: ticket_id, order_id, timestamp, system, severity, description. Dung lượng tối đa 5MB.
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="submit"
                disabled={loading || !ticketFile}
                style={{
                  background: loading ? "#94a3b8" : "#0284c7",
                  color: "#ffffff",
                  padding: "10px 24px",
                  borderRadius: "6px",
                  border: "none",
                  fontSize: "14px",
                  fontWeight: 600,
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                {loading ? "Đang tải lên..." : "Tải lên & Phân tích"}
              </button>
            </div>
          </form>
        )}

        {/* Global Error Banner */}
        {error && (
          <div
            style={{
              marginTop: "16px",
              padding: "12px 16px",
              borderRadius: "6px",
              background: "#fef2f2",
              border: "1px solid #fecaca",
              color: "#b91c1c",
              fontSize: "14px",
            }}
          >
            {error}
          </div>
        )}

        {/* Validation Errors Table (422) */}
        {validationErrors.length > 0 && (
          <div style={{ marginTop: "16px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: 700, color: "#b91c1c", margin: "0 0 8px 0" }}>
              Chi tiết lỗi kiểm định dòng tệp ticket:
            </h4>
            <div style={{ overflowX: "auto", border: "1px solid #fee2e2", borderRadius: "6px" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                <thead>
                  <tr style={{ background: "#fef2f2", color: "#991b1b", textAlign: "left" }}>
                    <th style={{ padding: "8px 12px" }}>Dòng</th>
                    <th style={{ padding: "8px 12px" }}>Trường vi phạm</th>
                    <th style={{ padding: "8px 12px" }}>Mô tả lỗi</th>
                  </tr>
                </thead>
                <tbody>
                  {validationErrors.map((err, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid #fee2e2" }}>
                      <td style={{ padding: "8px 12px", fontWeight: 600 }}>{err.line}</td>
                      <td style={{ padding: "8px 12px", color: "#64748b" }}>{err.field || "-"}</td>
                      <td style={{ padding: "8px 12px", color: "#b91c1c" }}>{err.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* 4-Block Incident Dashboard */}
      {analysis && (
        <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
          {/* KHỐI 1: Tổng quan & Phân loại sự cố */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "20px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px" }}>
              <div>
                <span style={{ fontSize: "12px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                  KHỐI 1 · TỔNG QUAN & PHÂN LOẠI SỰ CỐ
                </span>
                <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#0f172a", margin: "4px 0 0 0" }}>
                  {analysis.title}
                </h2>
              </div>

              {/* Priority & Confidence Badges */}
              <div style={{ display: "flex", gap: "8px" }}>
                {(() => {
                  const pBadge = getPriorityBadge(analysis.classification.suggested_priority);
                  return (
                    <span
                      style={{
                        padding: "4px 10px",
                        borderRadius: "16px",
                        fontSize: "12px",
                        fontWeight: 700,
                        background: pBadge.bg,
                        color: pBadge.text,
                        border: `1px solid ${pBadge.border}`,
                      }}
                    >
                      Mức ưu tiên: {analysis.classification.suggested_priority}
                    </span>
                  );
                })()}

                <span
                  style={{
                    padding: "4px 10px",
                    borderRadius: "16px",
                    fontSize: "12px",
                    fontWeight: 600,
                    background: "#f1f5f9",
                    color: "#475569",
                  }}
                >
                  Độ tin cậy: {Math.round(analysis.classification.confidence * 100)}%
                </span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "12px", marginBottom: "16px", flexWrap: "wrap" }}>
              <span style={{ padding: "4px 10px", background: "#f8fafc", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "13px" }}>
                <strong>Nhóm lỗi:</strong> {analysis.classification.error_group}
              </span>
              <span style={{ padding: "4px 10px", background: "#f8fafc", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "13px" }}>
                <strong>Hệ thống chính:</strong> {analysis.classification.primary_system}
              </span>
              {analysis.ticket_id && (
                <span style={{ padding: "4px 10px", background: "#f8fafc", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "13px" }}>
                  <strong>Phiếu Ticket:</strong> {analysis.ticket_id}
                </span>
              )}
            </div>

            <p style={{ margin: 0, fontSize: "14px", lineHeight: "1.6", color: "#334155" }}>
              {analysis.summary}
            </p>
          </div>

          {/* KHỐI 2: Trục dòng thời gian đa hệ thống */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "20px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
            }}
          >
            <div style={{ marginBottom: "16px" }}>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                KHỐI 2 · TRỤC THỜI GIAN ĐỐI SOÁT ĐA HỆ THỐNG
              </span>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#0f172a", margin: "4px 0 0 0" }}>
                Chuỗi sự kiện theo thứ tự thời gian (WMS → API Gateway → TMS)
              </h3>
            </div>

            <Timeline events={analysis.timeline} onSelectEvent={handleSelectEvent} />
          </div>

          {/* KHỐI 3: Giả thuyết nguyên nhân gốc rễ & Dữ liệu còn thiếu */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "20px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
            }}
          >
            <div style={{ marginBottom: "16px" }}>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                KHỐI 3 · GIẢ THUYẾT NGUYÊN NHÂN & CẢNH BÁO THIẾU THÔNG TIN
              </span>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#0f172a", margin: "4px 0 0 0" }}>
                Nguyên nhân gốc rễ đề xuất
              </h3>
            </div>

            {/* Hypotheses List */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "20px" }}>
              {analysis.hypotheses.map((h, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: "12px 16px",
                    borderRadius: "6px",
                    background: h.is_confirmed ? "#f0fdf4" : "#f8fafc",
                    border: `1px solid ${h.is_confirmed ? "#bbf7d0" : "#e2e8f0"}`,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "12px",
                        fontSize: "11px",
                        fontWeight: 700,
                        background: h.is_confirmed ? "#22c55e" : "#64748b",
                        color: "#ffffff",
                      }}
                    >
                      {h.is_confirmed ? "ĐÃ XÁC NHẬN TỪ LOG" : "GIẢ THUYẾT"}
                    </span>
                    <span style={{ fontSize: "12px", color: "#64748b" }}>
                      Độ tin cậy: {h.confidence_level}
                    </span>
                    {h.supporting_evidence_citations.length > 0 && (
                      <span style={{ fontSize: "12px", color: "#0284c7" }}>
                        Trích dẫn: {h.supporting_evidence_citations.map((c) => `#${c}`).join(", ")}
                      </span>
                    )}
                  </div>
                  <p style={{ margin: 0, fontSize: "14px", color: "#1e293b", lineHeight: "1.5" }}>
                    {h.hypothesis}
                  </p>
                </div>
              ))}
            </div>

            {/* Missing Information Yellow Banner (RAG-05) */}
            {analysis.missing_information.length > 0 && (
              <div
                style={{
                  padding: "14px 18px",
                  borderRadius: "6px",
                  background: "#fefce8",
                  border: "1px solid #fef08a",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px", color: "#854d0e" }}>
                  <span>⚠️</span>
                  <strong style={{ fontSize: "13px" }}>Cảnh báo dữ liệu còn thiếu / chưa đầy đủ (RAG-05):</strong>
                </div>
                <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "13px", color: "#713f12" }}>
                  {analysis.missing_information.map((item, idx) => (
                    <li key={idx} style={{ marginBottom: "4px" }}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* KHỐI 4: Khuyến nghị & Quy trình xử lý theo SOP */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "20px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
            }}
          >
            <div style={{ marginBottom: "16px" }}>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                KHỐI 4 · CÁC BƯỚC XỬ LÝ THEO QUY TRÌNH CHUẨN (SOP)
              </span>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#0f172a", margin: "4px 0 0 0" }}>
                Hướng dẫn kiểm tra và khắc phục có thể kiểm tra nguồn
              </h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {analysis.recommended_actions.map((act) => (
                <div
                  key={act.step_number}
                  style={{
                    display: "flex",
                    gap: "14px",
                    padding: "12px 16px",
                    background: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                  }}
                >
                  <div
                    style={{
                      width: "28px",
                      height: "28px",
                      borderRadius: "50%",
                      background: "#0284c7",
                      color: "#ffffff",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                      fontSize: "13px",
                      flexShrink: 0,
                    }}
                  >
                    {act.step_number}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px", flexWrap: "wrap" }}>
                      <span
                        style={{
                          background: "#e0f2fe",
                          color: "#0369a1",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "12px",
                          fontWeight: 600,
                        }}
                      >
                        Quy trình: {act.sop_reference}
                      </span>
                    </div>

                    <p style={{ margin: "0 0 6px 0", fontSize: "14px", fontWeight: 500, color: "#0f172a" }}>
                      {act.action}
                    </p>

                    <div style={{ fontSize: "13px", color: "#166534" }}>
                      <strong>Kết quả kỳ vọng:</strong> {act.expected_outcome}
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
            zIndex: 100,
            padding: "20px",
          }}
        >
          <div
            style={{
              background: "#ffffff",
              borderRadius: "8px",
              maxWidth: "600px",
              width: "100%",
              padding: "20px",
              boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "#0f172a" }}>
                {selectedCitation.title} {selectedCitation.citation_id ? `[#${selectedCitation.citation_id}]` : ""}
              </h3>
              <button
                type="button"
                onClick={() => setSelectedCitation(null)}
                style={{ background: "transparent", border: "none", fontSize: "18px", cursor: "pointer", color: "#64748b" }}
              >
                ✕
              </button>
            </div>

            <div style={{ fontSize: "13px", color: "#64748b", marginBottom: "12px" }}>
              Tệp nguồn: <strong>{selectedCitation.source}</strong>
              {selectedCitation.line ? ` · Dòng: ${selectedCitation.line}` : ""}
              {selectedCitation.timestamp ? ` · Thời gian: ${selectedCitation.timestamp}` : ""}
            </div>

            <pre
              style={{
                margin: 0,
                padding: "12px",
                background: "#f8fafc",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                fontSize: "13px",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                maxHeight: "300px",
                overflowY: "auto",
                fontFamily: "ui-monospace, SFMono-Regular, monospace",
              }}
            >
              {selectedCitation.snippet}
            </pre>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
              <button
                type="button"
                onClick={() => setSelectedCitation(null)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  background: "#e2e8f0",
                  border: "none",
                  fontWeight: 600,
                  fontSize: "13px",
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
