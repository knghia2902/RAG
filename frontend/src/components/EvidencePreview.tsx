"use client";

import React, { useEffect, useState } from "react";
import { CitationPreviewDetail } from "@/lib/contracts";

interface EvidencePreviewProps {
  citation: CitationPreviewDetail | null;
  loading: boolean;
  error: string;
  onClose: () => void;
  onImageClick?: (url: string, alt?: string, caption?: string) => void;
}

function getFileFormat(filename: string): string {
  const ext = filename.split(".").pop()?.toUpperCase();
  if (ext === "PDF") return "PDF";
  if (ext === "DOCX" || ext === "DOC") return "DOCX";
  if (ext === "LOG" || ext === "TXT") return "LOG";
  if (ext === "CSV" || ext === "XLSX" || ext === "XLS") return "SHEET";
  if (ext === "JSON" || ext === "JSONL") return "JSON";
  return ext || "DOC";
}

export function EvidencePreview({
  citation,
  loading,
  error,
  onClose,
  onImageClick,
}: EvidencePreviewProps) {
  const [imageError, setImageError] = useState<boolean>(false);

  useEffect(() => {
    setImageError(false);
  }, [citation?.image_url, citation?.locator?.image_url]);

  // Handle ESC key to close drawer
  useEffect(() => {
    if (!citation && !loading && !error) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [citation, loading, error, onClose]);

  // If nothing is requested to be previewed, do not render the drawer
  if (!citation && !loading && !error) {
    return null;
  }

  const imageUrl = citation?.image_url || citation?.locator?.image_url;
  const fileFormat = citation ? getFileFormat(citation.logical_filename) : "";

  return (
    <>
      {/* 1. Backdrop Overlay */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(15, 23, 42, 0.35)",
          backdropFilter: "blur(2px)",
          WebkitBackdropFilter: "blur(2px)",
          zIndex: 40,
          transition: "opacity 200ms ease",
        }}
      />

      {/* 2. Slide-over Drawer */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Chi tiết Bằng chứng Nguồn"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "480px",
          maxWidth: "92vw",
          background: "#ffffff",
          zIndex: 50,
          boxShadow: "-4px 0 24px rgba(0, 0, 0, 0.12)",
          display: "flex",
          flexDirection: "column",
          transition: "transform 300ms cubic-bezier(0.16, 1, 0.3, 1)",
          overflow: "hidden",
        }}
      >
        {/* Drawer Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid var(--border-subtle, #e2e8f0)",
            background: "#ffffff",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                background: "var(--color-pastel-mint, #ecfdf5)",
                border: "1px solid var(--color-mint-border, #a7f3d0)",
                color: "var(--color-emerald-dark, #047857)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </div>
            <div style={{ minWidth: 0 }}>
              <h3
                style={{
                  margin: 0,
                  fontSize: "16px",
                  fontWeight: 600,
                  color: "var(--color-text-main, #0f172a)",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                Chi tiết Bằng chứng Nguồn
              </h3>
              <div style={{ fontSize: "12px", color: "var(--color-text-muted, #64748b)", marginTop: "2px" }}>
                {citation ? `Đối chiếu trích dẫn [${citation.citation_index}]` : "Đang xử lý yêu cầu..."}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng bảng xem trước bằng chứng"
            title="Đóng bảng xem trước bằng chứng"
            style={{
              background: "transparent",
              border: "none",
              color: "var(--color-text-muted, #64748b)",
              cursor: "pointer",
              padding: "8px",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 150ms ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "var(--bg-subtle, #f1f5f9)";
              e.currentTarget.style.color = "var(--color-text-main, #0f172a)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
              e.currentTarget.style.color = "var(--color-text-muted, #64748b)";
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        {/* Drawer Body */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          {/* Loading state */}
          {loading && (
            <div
              role="status"
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "64px 20px",
                gap: "12px",
                color: "var(--color-emerald-dark, #047857)",
              }}
            >
              <div
                style={{
                  width: "32px",
                  height: "32px",
                  border: "3px solid var(--color-mint-border, #a7f3d0)",
                  borderTopColor: "var(--color-primary-green, #10b981)",
                  borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }}
              />
              <span style={{ fontSize: "14px", fontWeight: 500 }}>
                Đang tải chi tiết bằng chứng nguồn...
              </span>
            </div>
          )}

          {/* Revocation / Error state (Live Scope Recheck) */}
          {error && !loading && (
            <div
              role="alert"
              style={{
                background: "var(--color-danger-bg, #fef2f2)",
                border: "1px solid var(--color-danger-border, #fecaca)",
                color: "var(--color-danger-text, #b91c1c)",
                padding: "16px",
                borderRadius: "10px",
                fontSize: "13px",
                lineHeight: "1.5",
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
                <span>⛔</span>
                <span>Quyền truy cập bị từ chối hoặc thu hồi</span>
              </div>
              <div>{error}</div>
            </div>
          )}

          {/* Citation Content */}
          {citation && !loading && !error && (
            <>
              {/* Document Metadata Card */}
              <div
                style={{
                  background: "var(--bg-app, #f8fafc)",
                  border: "1px solid var(--border-subtle, #e2e8f0)",
                  borderRadius: "12px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "10px" }}>
                  <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-text-main, #0f172a)", wordBreak: "break-word" }}>
                    {citation.logical_filename}
                  </div>
                  <span
                    style={{
                      background: "#e0f2fe",
                      color: "#0369a1",
                      border: "1px solid #bae6fd",
                      borderRadius: "6px",
                      padding: "2px 8px",
                      fontSize: "11px",
                      fontWeight: 700,
                      flexShrink: 0,
                    }}
                  >
                    {fileFormat}
                  </span>
                </div>

                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", fontSize: "12px" }}>
                  <span
                    style={{
                      background: "var(--color-pastel-mint, #ecfdf5)",
                      color: "var(--color-emerald-deep, #065f46)",
                      border: "1px solid var(--color-mint-border, #a7f3d0)",
                      padding: "3px 10px",
                      borderRadius: "9999px",
                      fontWeight: 600,
                    }}
                  >
                    v{citation.version_number} · đang dùng
                  </span>
                  <span
                    style={{
                      background: "var(--bg-subtle, #f1f5f9)",
                      color: "var(--color-text-muted, #64748b)",
                      border: "1px solid var(--border-subtle, #e2e8f0)",
                      padding: "3px 10px",
                      borderRadius: "9999px",
                    }}
                  >
                    Dataset: {citation.dataset_name}
                  </span>
                </div>
              </div>

              {/* Provenance Locator Pills */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted, #64748b)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Vị trí trong tài liệu
                </div>
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "8px",
                  }}
                >
                  {citation.locator.page && (
                    <span
                      style={{
                        background: "var(--color-pastel-50, #f0fdf4)",
                        color: "var(--color-emerald-dark, #047857)",
                        border: "1px solid var(--color-mint-border, #a7f3d0)",
                        borderRadius: "8px",
                        padding: "4px 10px",
                        fontSize: "13px",
                        fontWeight: 600,
                      }}
                    >
                      📄 Trang {citation.locator.page}
                    </span>
                  )}
                  {citation.locator.section && (
                    <span
                      style={{
                        background: "var(--bg-subtle, #f1f5f9)",
                        color: "var(--color-text-main, #0f172a)",
                        border: "1px solid var(--border-subtle, #e2e8f0)",
                        borderRadius: "8px",
                        padding: "4px 10px",
                        fontSize: "13px",
                        fontWeight: 500,
                      }}
                    >
                      Mục: {citation.locator.section}
                    </span>
                  )}
                  {citation.locator.sheet && (
                    <span
                      style={{
                        background: "var(--bg-subtle, #f1f5f9)",
                        color: "var(--color-text-main, #0f172a)",
                        border: "1px solid var(--border-subtle, #e2e8f0)",
                        borderRadius: "8px",
                        padding: "4px 10px",
                        fontSize: "13px",
                        fontWeight: 500,
                      }}
                    >
                      Sheet: {citation.locator.sheet}
                    </span>
                  )}
                  {citation.locator.row && (
                    <span
                      style={{
                        background: "var(--bg-subtle, #f1f5f9)",
                        color: "var(--color-text-main, #0f172a)",
                        border: "1px solid var(--border-subtle, #e2e8f0)",
                        borderRadius: "8px",
                        padding: "4px 10px",
                        fontSize: "13px",
                        fontWeight: 500,
                      }}
                    >
                      Hàng: {citation.locator.row}
                    </span>
                  )}
                  {citation.locator.line_start && (
                    <span
                      style={{
                        background: "var(--color-pastel-50, #f0fdf4)",
                        color: "var(--color-emerald-dark, #047857)",
                        border: "1px solid var(--color-mint-border, #a7f3d0)",
                        borderRadius: "8px",
                        padding: "4px 10px",
                        fontSize: "13px",
                        fontWeight: 600,
                      }}
                    >
                      Dòng {citation.locator.line_start}
                      {citation.locator.line_end ? ` - ${citation.locator.line_end}` : ""}
                    </span>
                  )}
                  {citation.locator.json_path && (
                    <span
                      style={{
                        background: "var(--bg-subtle, #f1f5f9)",
                        color: "var(--color-text-main, #0f172a)",
                        border: "1px solid var(--border-subtle, #e2e8f0)",
                        borderRadius: "8px",
                        padding: "4px 10px",
                        fontSize: "12px",
                        fontFamily: "monospace",
                      }}
                    >
                      {citation.locator.json_path}
                    </span>
                  )}
                  {!citation.locator.page &&
                    !citation.locator.sheet &&
                    !citation.locator.line_start &&
                    !citation.locator.json_path && (
                      <span
                        style={{
                          background: "var(--bg-subtle, #f1f5f9)",
                          color: "var(--color-text-muted, #64748b)",
                          border: "1px solid var(--border-subtle, #e2e8f0)",
                          borderRadius: "8px",
                          padding: "4px 10px",
                          fontSize: "12px",
                        }}
                      >
                        Bản ghi văn bản đã chuẩn hóa
                      </span>
                    )}
                </div>
              </div>

              {/* Cited Image Container */}
              {imageUrl && (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted, #64748b)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {citation.locator?.page
                      ? `Hình ảnh tại trang ${citation.locator.page}`
                      : "Hình ảnh trích dẫn"}
                  </div>

                  {imageError ? (
                    <div
                      role="alert"
                      style={{
                        background: "var(--color-danger-bg, #fef2f2)",
                        border: "1px solid var(--color-danger-border, #fecaca)",
                        color: "var(--color-danger-text, #b91c1c)",
                        padding: "12px",
                        borderRadius: "8px",
                        fontSize: "13px",
                      }}
                    >
                      ⚠️ Không thể tải hình ảnh trích dẫn (tệp không tồn tại hoặc quyền truy cập đã thay đổi).
                    </div>
                  ) : (
                    <div
                      style={{
                        background: "var(--color-pastel-50, #f0fdf4)",
                        border: "1px solid var(--color-mint-border, #a7f3d0)",
                        borderRadius: "12px",
                        padding: "12px",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: "10px",
                        boxShadow: "var(--shadow-soft)",
                      }}
                    >
                      <img
                        src={imageUrl}
                        alt={citation.logical_filename || "Hình ảnh trích dẫn"}
                        loading="lazy"
                        onError={() => setImageError(true)}
                        onClick={() => {
                          if (onImageClick) {
                            onImageClick(
                              imageUrl,
                              citation.logical_filename,
                              citation.locator?.page
                                ? `Trang ${citation.locator.page} - ${citation.logical_filename}`
                                : citation.logical_filename
                            );
                          }
                        }}
                        style={{
                          maxHeight: "260px",
                          maxWidth: "100%",
                          objectFit: "contain",
                          cursor: "zoom-in",
                          borderRadius: "8px",
                          background: "#ffffff",
                          transition: "transform 150ms ease",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = "scale(1.02)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = "none";
                        }}
                      />
                      <button
                        type="button"
                        aria-label="Phóng to ảnh sơ đồ kỹ thuật"
                        onClick={() => {
                          if (onImageClick) {
                            onImageClick(
                              imageUrl,
                              citation.logical_filename,
                              citation.locator?.page
                                ? `Trang ${citation.locator.page} - ${citation.logical_filename}`
                                : citation.logical_filename
                            );
                          }
                        }}
                        style={{
                          background: "#ffffff",
                          border: "1px solid var(--border-subtle, #e2e8f0)",
                          color: "var(--color-emerald-dark, #047857)",
                          borderRadius: "8px",
                          padding: "6px 14px",
                          fontSize: "13px",
                          fontWeight: 600,
                          cursor: "pointer",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          boxShadow: "var(--shadow-soft)",
                          transition: "all 150ms ease",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderColor = "var(--color-primary-green, #10b981)";
                          e.currentTarget.style.color = "var(--color-primary-green, #10b981)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderColor = "var(--border-subtle, #e2e8f0)";
                          e.currentTarget.style.color = "var(--color-emerald-dark, #047857)";
                        }}
                      >
                        🔍 Phóng to xem chi tiết sơ đồ
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Source Excerpt Card */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted, #64748b)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Đoạn trích nguyên bản
                </div>
                <div
                  style={{
                    background: "var(--color-pastel-50, #f0fdf4)",
                    border: "1px solid var(--border-subtle, #e2e8f0)",
                    borderLeft: "4px solid var(--color-primary-green, #10b981)",
                    borderRadius: "8px",
                    padding: "16px",
                    fontSize: "13px",
                    fontFamily: "monospace",
                    lineHeight: "1.65",
                    whiteSpace: "pre-wrap",
                    color: "var(--color-text-main, #0f172a)",
                    maxHeight: "360px",
                    overflowY: "auto",
                    boxShadow: "var(--shadow-soft)",
                  }}
                >
                  {citation.excerpt_text}
                </div>
              </div>
            </>
          )}
        </div>
      </aside>
    </>
  );
}
