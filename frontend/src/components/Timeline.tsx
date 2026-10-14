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
          padding: "24px",
          textAlign: "center",
          color: "#587080",
          background: "#f8fafc",
          borderRadius: "8px",
          border: "1px dashed #cbd5e1",
        }}
      >
        Chưa có sự kiện nào được ghi nhận cho đơn hàng này.
      </div>
    );
  }

  const getSystemBadgeStyle = (system: SystemType) => {
    switch (system) {
      case "WMS":
        return {
          background: "#dbeafe",
          color: "#1e40af",
          borderColor: "#93c5fd",
        };
      case "API_GATEWAY":
        return {
          background: "#f3e8ff",
          color: "#6b21a8",
          borderColor: "#d8b4fe",
        };
      case "TMS":
        return {
          background: "#fef3c7",
          color: "#92400e",
          borderColor: "#fde68a",
        };
      case "ERP":
      case "INVENTORY":
        return {
          background: "#e0f2fe",
          color: "#0369a1",
          borderColor: "#bae6fd",
        };
      default:
        return {
          background: "#f1f5f9",
          color: "#475569",
          borderColor: "#cbd5e1",
        };
    }
  };

  const getStatusBadgeStyle = (status: string) => {
    const s = status.toUpperCase();
    if (s === "SUCCESS" || s === "OK" || s === "200") {
      return { background: "#dcfce7", color: "#166534" };
    }
    if (s === "TIMEOUT" || s === "504" || s === "500" || s === "ERROR" || s === "FATAL") {
      return { background: "#fee2e2", color: "#991b1b" };
    }
    if (s === "PENDING" || s === "WARN") {
      return { background: "#fef9c3", color: "#854d0e" };
    }
    return { background: "#f1f5f9", color: "#334155" };
  };

  const formatTimestamp = (raw: string) => {
    try {
      const d = new Date(raw);
      if (!isNaN(d.getTime())) {
        return d.toLocaleTimeString("vi-VN", { hour12: false }) + " " + d.toLocaleDateString("vi-VN");
      }
    } catch {
      // fallback
    }
    return raw;
  };

  return (
    <div style={{ position: "relative", paddingLeft: "28px" }}>
      {/* Vertical timeline line */}
      <div
        style={{
          position: "absolute",
          top: "16px",
          bottom: "16px",
          left: "11px",
          width: "2px",
          background: "#cbd5e1",
        }}
      />

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {events.map((ev, index) => {
          const sysStyle = getSystemBadgeStyle(ev.system);
          const statusStyle = getStatusBadgeStyle(ev.status);
          const isFailure = ev.is_failure_point;

          return (
            <div
              key={ev.event_id || `ev-${index}`}
              style={{
                position: "relative",
              }}
            >
              {/* Timeline dot */}
              <div
                style={{
                  position: "absolute",
                  left: "-28px",
                  top: "16px",
                  width: isFailure ? "18px" : "14px",
                  height: isFailure ? "18px" : "14px",
                  borderRadius: "50%",
                  background: isFailure ? "#ef4444" : sysStyle.color,
                  border: isFailure ? "3px solid #fee2e2" : "2px solid #ffffff",
                  boxShadow: isFailure ? "0 0 0 3px rgba(239,68,68,0.3)" : "0 1px 3px rgba(0,0,0,0.2)",
                  transform: isFailure ? "translateX(-2px)" : "none",
                  zIndex: 2,
                }}
              />

              {/* Event Card */}
              <div
                className={`event-card ${isFailure ? "border-red-500" : ""}`}
                style={{
                  background: isFailure ? "rgba(254, 242, 242, 0.7)" : "#ffffff",
                  border: isFailure ? "2px solid #ef4444" : "1px solid #e2e8f0",
                  borderRadius: "8px",
                  padding: "16px",
                  boxShadow: isFailure
                    ? "0 4px 6px -1px rgba(239, 68, 68, 0.15), 0 2px 4px -2px rgba(239, 68, 68, 0.1)"
                    : "0 1px 3px rgba(0,0,0,0.05)",
                  transition: "all 0.15s ease-in-out",
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
                      padding: "6px 12px",
                      borderRadius: "6px",
                      background: "#fee2e2",
                      color: "#b91c1c",
                      fontSize: "13px",
                      fontWeight: 700,
                      letterSpacing: "0.5px",
                    }}
                  >
                    <span>⚠️</span>
                    <span>*** ĐIỂM ĐỨT GÃY ĐỒNG BỘ PHÁT HIỆN TẠI ĐÂY ***</span>
                  </div>
                )}

                {/* Card Top: Badges & Timestamp */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "8px",
                    marginBottom: "8px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "12px",
                        fontSize: "12px",
                        fontWeight: 600,
                        border: `1px solid ${sysStyle.borderColor}`,
                        background: sysStyle.background,
                        color: sysStyle.color,
                      }}
                    >
                      {ev.system}
                    </span>
                    <span
                      style={{
                        fontSize: "14px",
                        fontWeight: 600,
                        color: "#0f172a",
                      }}
                    >
                      {ev.event_name}
                    </span>
                    <span
                      style={{
                        padding: "2px 6px",
                        borderRadius: "4px",
                        fontSize: "11px",
                        fontWeight: 600,
                        background: statusStyle.background,
                        color: statusStyle.color,
                      }}
                    >
                      {ev.status}
                    </span>
                  </div>

                  <span style={{ fontSize: "12px", color: "#64748b" }}>
                    {formatTimestamp(ev.timestamp)}
                  </span>
                </div>

                {/* Raw snippet & source info */}
                <div style={{ marginTop: "8px" }}>
                  <pre
                    style={{
                      margin: 0,
                      padding: "10px 12px",
                      background: isFailure ? "#ffffff" : "#f8fafc",
                      border: "1px solid #e2e8f0",
                      borderRadius: "6px",
                      fontSize: "12px",
                      color: "#1e293b",
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
                    marginTop: "10px",
                    fontSize: "12px",
                    color: "#64748b",
                  }}
                >
                  <span>
                    Nguồn: {ev.source_filename}
                    {ev.line_number ? ` (Dòng ${ev.line_number})` : ""}
                  </span>

                  {onSelectEvent && (
                    <button
                      type="button"
                      onClick={() => onSelectEvent(ev)}
                      style={{
                        background: "transparent",
                        border: "1px solid #cbd5e1",
                        borderRadius: "4px",
                        padding: "4px 8px",
                        fontSize: "12px",
                        cursor: "pointer",
                        color: "#0284c7",
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                      }}
                    >
                      <span>🔍 Xem trích dẫn</span>
                      {ev.citation_id && (
                        <span
                          style={{
                            background: "#e0f2fe",
                            color: "#0369a1",
                            padding: "1px 5px",
                            borderRadius: "10px",
                            fontWeight: 600,
                          }}
                        >
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
