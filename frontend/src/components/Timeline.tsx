"use client";

import React from "react";
import { SystemType, TimelineEvent } from "@/lib/contracts";

interface TimelineProps {
  events: TimelineEvent[];
  onSelectEvent?: (event: TimelineEvent) => void;
}

export default function Timeline({ events, onSelectEvent }: TimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div
        style={{
          padding: "32px 24px",
          textAlign: "center",
          color: "var(--color-text-muted)",
          backgroundColor: "var(--color-pastel-50)",
          borderRadius: "12px",
          border: "1px dashed var(--color-mint-border)",
          fontSize: "14px",
        }}
      >
        Chưa có sự kiện nào được ghi nhận cho đơn hàng này.
      </div>
    );
  }

  const renderSystemIcon = (system: SystemType, isFailure: boolean) => {
    if (isFailure) {
      return (
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
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      );
    }

    switch (system) {
      case "WMS":
        // Warehouse box icon
        return (
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
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
        );
      case "API_GATEWAY":
        // Server / gateway icon
        return (
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
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
            <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
            <line x1="6" y1="6" x2="6.01" y2="6" />
            <line x1="6" y1="18" x2="6.01" y2="18" />
          </svg>
        );
      case "TMS":
        // Delivery truck icon
        return (
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
            <rect x="1" y="3" width="15" height="13" />
            <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
            <circle cx="5.5" cy="18.5" r="2.5" />
            <circle cx="18.5" cy="18.5" r="2.5" />
          </svg>
        );
      default:
        // Activity pulse icon
        return (
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
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
        );
    }
  };

  const getSystemBadgeClass = (system: SystemType) => {
    switch (system) {
      case "WMS":
        return "badge-pastel-green";
      case "API_GATEWAY":
        return "badge-pastel-slate";
      case "TMS":
        return "badge-pastel-amber";
      default:
        return "badge-pastel-slate";
    }
  };

  const getStatusBadgeClass = (status: string) => {
    const s = status.toUpperCase();
    if (s === "SUCCESS" || s === "OK" || s === "200") {
      return "badge-pastel-green";
    }
    if (s === "TIMEOUT" || s === "504" || s === "500" || s === "ERROR" || s === "FATAL") {
      return "badge-pastel-rose";
    }
    if (s === "PENDING" || s === "WARN") {
      return "badge-pastel-amber";
    }
    return "badge-pastel-slate";
  };

  const formatTimestamp = (raw: string) => {
    try {
      const d = new Date(raw);
      if (!isNaN(d.getTime())) {
        return `${d.toLocaleTimeString("vi-VN", { hour12: false })} · ${d.toLocaleDateString("vi-VN")}`;
      }
    } catch {
      // fallback
    }
    return raw;
  };

  return (
    <div style={{ position: "relative", paddingLeft: "44px" }}>
      {/* Vertical timeline track: 2px solid #d1fae5 */}
      <div
        style={{
          position: "absolute",
          top: "20px",
          bottom: "20px",
          left: "15px",
          width: "2px",
          backgroundColor: "#d1fae5",
        }}
      />

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {events.map((ev, index) => {
          const isFailure = Boolean(ev.is_failure_point);

          return (
            <div
              key={ev.event_id || `ev-${index}`}
              style={{
                position: "relative",
              }}
            >
              {/* Event node: 32px diameter circle */}
              <div
                style={{
                  position: "absolute",
                  left: "-44px",
                  top: "16px",
                  width: "32px",
                  height: "32px",
                  borderRadius: "50%",
                  backgroundColor: isFailure ? "var(--color-danger-bg)" : "var(--color-pastel-mint)",
                  border: isFailure ? "2px solid #ef4444" : "2px solid var(--color-primary-green)",
                  color: isFailure ? "var(--color-danger-text)" : "var(--color-emerald-dark)",
                  boxShadow: isFailure
                    ? "0 0 0 4px rgba(239, 68, 68, 0.2)"
                    : "0 1px 3px rgba(16, 185, 129, 0.2)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  zIndex: 2,
                  transition: "all 150ms ease",
                }}
              >
                {renderSystemIcon(ev.system, isFailure)}
              </div>

              {/* Event Card */}
              <div
                style={{
                  backgroundColor: isFailure ? "#fffafa" : "#ffffff",
                  border: isFailure ? "1.5px solid #fca5a5" : "1px solid var(--border-subtle)",
                  borderRadius: "12px",
                  padding: "18px 20px",
                  boxShadow: isFailure
                    ? "0 4px 12px -2px rgba(239, 68, 68, 0.15), 0 2px 4px -2px rgba(239, 68, 68, 0.08)"
                    : "var(--shadow-soft)",
                  transition: "all 150ms ease",
                }}
              >
                {/* Failure Banner */}
                {isFailure && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      marginBottom: "12px",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      backgroundColor: "var(--color-danger-bg)",
                      border: "1px solid var(--color-danger-border)",
                      color: "var(--color-danger-text)",
                      fontSize: "13px",
                      fontWeight: 600,
                      letterSpacing: "0.02em",
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
                    <span>*** ĐIỂM ĐỨT GÃY ĐỒNG BỘ PHÁT HIỆN TẠI ĐÂY ***</span>
                  </div>
                )}

                {/* Card Top: System Badges, Event Name & Timestamp */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "10px",
                    marginBottom: "10px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                    <span className={`badge ${getSystemBadgeClass(ev.system)}`}>
                      {ev.system}
                    </span>
                    <span
                      style={{
                        fontSize: "15px",
                        fontWeight: 600,
                        color: "var(--color-text-main)",
                      }}
                    >
                      {ev.event_name}
                    </span>
                    <span className={`badge ${getStatusBadgeClass(ev.status)}`}>
                      {ev.status}
                    </span>
                  </div>

                  <span
                    style={{
                      fontSize: "13px",
                      color: "var(--color-text-muted)",
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
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
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                    {formatTimestamp(ev.timestamp)}
                  </span>
                </div>

                {/* Raw snippet & source info */}
                <div style={{ marginTop: "10px" }}>
                  <pre
                    style={{
                      margin: 0,
                      padding: "10px 14px",
                      backgroundColor: isFailure ? "#ffffff" : "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "8px",
                      fontSize: "12.5px",
                      lineHeight: 1.5,
                      color: "var(--color-text-main)",
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-all",
                      fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                    }}
                  >
                    {ev.raw_snippet}
                  </pre>
                </div>

                {/* Footer action / Citation info */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginTop: "12px",
                    paddingTop: "8px",
                    borderTop: "1px solid var(--border-divider)",
                    fontSize: "12.5px",
                    color: "var(--color-text-muted)",
                    flexWrap: "wrap",
                    gap: "8px",
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
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
                    Nguồn: <strong style={{ color: "var(--color-text-main)" }}>{ev.source_filename}</strong>
                    {ev.line_number ? ` (Dòng ${ev.line_number})` : ""}
                  </span>

                  {onSelectEvent && (
                    <button
                      type="button"
                      onClick={() => onSelectEvent(ev)}
                      aria-label={`Xem trích dẫn cho sự kiện ${ev.event_name}`}
                      style={{
                        background: "#ffffff",
                        border: "1px solid var(--border-subtle)",
                        borderRadius: "8px",
                        padding: "5px 10px",
                        fontSize: "12.5px",
                        fontWeight: 500,
                        cursor: "pointer",
                        color: "var(--color-emerald-dark)",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        transition: "all 150ms ease",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = "var(--color-pastel-50)";
                        e.currentTarget.style.borderColor = "var(--color-mint-border)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = "#ffffff";
                        e.currentTarget.style.borderColor = "var(--border-subtle)";
                      }}
                    >
                      <svg
                        width="13"
                        height="13"
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
                      <span>Xem trích dẫn</span>
                      {ev.citation_id && (
                        <span className="badge badge-pastel-green" style={{ padding: "1px 6px", fontSize: "11px" }}>
                          #{ev.citation_id}
                        </span>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
