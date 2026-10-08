"use client";

import React from "react";
import { CitationPreviewDetail } from "@/lib/contracts";

interface EvidencePreviewProps {
  citation: CitationPreviewDetail | null;
  loading: boolean;
  error: string;
  onClose: () => void;
}

export function EvidencePreview({
  citation,
  loading,
  error,
  onClose,
}: EvidencePreviewProps) {
  if (!citation && !loading && !error) {
    return (
      <aside
        style={{
          background: "#ffffff",
          border: "1px solid #d7e1e8",
          borderRadius: "8px",
          padding: "24px",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          color: "#587080",
        }}
      >
        <p style={{ margin: 0, fontSize: "14px", lineHeight: "1.5" }}>
          Nhấp vào thẻ trích dẫn [1], [2] trong câu trả lời để xem chi tiết bằng chứng nguồn và vị trí tài liệu.
        </p>
      </aside>
    );
  }

  return (
    <aside
      style={{
        background: "#ffffff",
        border: "1px solid #d7e1e8",
        borderRadius: "8px",
        padding: "24px",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        overflowY: "auto",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #e0e8ed",
          paddingBottom: "12px",
        }}
      >
        <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "bold", color: "#172b3a" }}>
          {citation ? `Bằng chứng trích dẫn [${citation.citation_index}]` : "Xem trước trích dẫn"}
        </h3>
        <button
          type="button"
          onClick={onClose}
          aria-label="Đóng bảng trích dẫn"
          style={{
            background: "none",
            border: "none",
            color: "#527080",
            cursor: "pointer",
            fontSize: "14px",
            padding: "4px 8px",
          }}
        >
          ✕ Đóng
        </button>
      </div>

      {/* Loading state */}
      {loading && (
        <div role="status" style={{ color: "#527080", fontSize: "14px", padding: "16px 0" }}>
          Đang tải chi tiết bằng chứng nguồn...
        </div>
      )}

      {/* Revocation / Error state (Live Scope Recheck D-05) */}
      {error && !loading && (
        <div
          role="alert"
          style={{
            background: "#fdf2f2",
            border: "1px solid #f8b4b4",
            color: "#a22a28",
            padding: "12px",
            borderRadius: "6px",
            fontSize: "13px",
            lineHeight: "1.5",
          }}
        >
          <strong>Truy cập bị từ chối:</strong> {error}
        </div>
      )}

      {/* Content display */}
      {citation && !loading && !error && (
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {/* Metadata badges */}
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <div style={{ fontSize: "14px", fontWeight: "bold", color: "#172b3a" }}>
              {citation.logical_filename}
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", fontSize: "12px" }}>
              <span
                style={{
                  background: "#e9f3f8",
                  color: "#075b79",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  fontWeight: "bold",
                }}
              >
                v{citation.version_number} · đang dùng
              </span>
              <span
                style={{
                  background: "#f3f6f8",
                  color: "#527080",
                  padding: "2px 8px",
                  borderRadius: "4px",
                }}
              >
                Dataset: {citation.dataset_name}
              </span>
            </div>
          </div>

          {/* Provenance Locator */}
          <div
            style={{
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: "4px",
              padding: "8px 12px",
              fontSize: "12px",
              color: "#334155",
            }}
          >
            <strong>Tọa độ nguồn: </strong>
            {citation.locator.page && `Trang: ${citation.locator.page} `}
            {citation.locator.section && `Mục: ${citation.locator.section} `}
            {citation.locator.sheet && `Sheet: ${citation.locator.sheet} `}
            {citation.locator.row && `Hàng: ${citation.locator.row} `}
            {citation.locator.line_start && (
              `Dòng: ${citation.locator.line_start}` +
              (citation.locator.line_end ? ` - ${citation.locator.line_end}` : "") + " "
            )}
            {citation.locator.json_path && `Đường dẫn JSON: ${citation.locator.json_path}`}
            {!citation.locator.page &&
              !citation.locator.sheet &&
              !citation.locator.line_start &&
              !citation.locator.json_path &&
              "Bản ghi văn bản đã chuẩn hóa"}
          </div>

          {/* Excerpt Container */}
          <div>
            <div style={{ fontSize: "12px", fontWeight: "bold", color: "#527080", marginBottom: "6px" }}>
              Đoạn trích nguyên bản:
            </div>
            <div
              style={{
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: "6px",
                padding: "12px",
                fontSize: "13px",
                fontFamily: "monospace",
                lineHeight: "1.6",
                whiteSpace: "pre-wrap",
                color: "#1e293b",
                maxHeight: "360px",
                overflowY: "auto",
              }}
            >
              {citation.excerpt_text}
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
