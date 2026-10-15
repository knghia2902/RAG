"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useWorkspaceSession } from "../layout";
import { EvidencePreview } from "@/components/EvidencePreview";
import { ImageLightboxModal } from "@/components/ImageLightboxModal";
import { api, ApiError } from "@/lib/api";
import type {
  ChatMessage,
  ChatQueryRequest,
  ChatQueryResponse,
  ChatSession,
  CitationItem,
  CitationPreviewDetail,
  Dataset,
  Page,
} from "@/lib/contracts";

function isSafeImageUrl(url: string): boolean {
  const trimmed = url.trim();
  if (trimmed.startsWith("/api/v1/datasets/")) return true;
  const lower = trimmed.toLowerCase();
  if (
    lower.startsWith("javascript:") ||
    lower.startsWith("data:") ||
    lower.startsWith("vbscript:")
  ) {
    return false;
  }
  return (
    trimmed.startsWith("/") ||
    trimmed.startsWith("http://") ||
    trimmed.startsWith("https://")
  );
}

function renderMessageContent(
  content: string,
  onImageClick: (url: string, alt?: string, caption?: string) => void,
  citations?: CitationItem[],
  onCitationClick?: (citation: CitationItem) => void
) {
  // Regex to match either markdown image: ![alt](url) OR citation: [1], [2], etc.
  const TOKEN_REGEX = /(!\[([^\]]*)\]\(([^)]+)\))|(\[(\d+)\])/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = TOKEN_REGEX.exec(content)) !== null) {
    const textBefore = content.substring(lastIndex, match.index);
    if (textBefore) {
      parts.push(
        <span key={`text-${lastIndex}`} style={{ whiteSpace: "pre-wrap" }}>
          {textBefore}
        </span>
      );
    }

    if (match[1]) {
      // It's a markdown image
      const alt = match[2];
      const url = match[3];

      if (isSafeImageUrl(url)) {
        parts.push(
          <div
            key={`img-${match.index}`}
            style={{
              margin: "12px 0",
              display: "block",
              maxWidth: "100%",
            }}
          >
            <img
              src={url}
              alt={alt || "Hình ảnh trích dẫn"}
              loading="lazy"
              onClick={() => onImageClick(url, alt, alt)}
              style={{
                maxHeight: "260px",
                maxWidth: "100%",
                objectFit: "contain",
                borderRadius: "12px",
                border: "1px solid var(--color-mint-border, #a7f3d0)",
                background: "#f8fafc",
                cursor: "zoom-in",
                boxShadow: "var(--shadow-soft)",
                display: "block",
                transition: "transform 150ms ease, box-shadow 150ms ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.01)";
                e.currentTarget.style.boxShadow = "var(--shadow-card)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.boxShadow = "var(--shadow-soft)";
              }}
            />
            {alt && (
              <div
                style={{
                  fontSize: "12px",
                  color: "var(--color-text-muted, #64748b)",
                  marginTop: "6px",
                  fontStyle: "italic",
                }}
              >
                {alt}
              </div>
            )}
          </div>
        );
      } else {
        parts.push(
          <span
            key={`unsafe-${match.index}`}
            style={{ color: "#dc2626", fontStyle: "italic", fontSize: "12px" }}
          >
            [Hình ảnh bị chặn vì lý do an toàn]
          </span>
        );
      }
    } else if (match[4]) {
      // It's a citation index like [1]
      const citIndex = parseInt(match[5], 10);
      const matchedCitation = citations?.find((c) => c.citation_index === citIndex);

      parts.push(
        <button
          key={`cit-${match.index}`}
          type="button"
          onClick={() => {
            if (matchedCitation && onCitationClick) {
              onCitationClick(matchedCitation);
            }
          }}
          title={matchedCitation ? `Xem chi tiết bằng chứng nguồn [${citIndex}]` : `Trích dẫn [${citIndex}]`}
          aria-label={`Trích dẫn số ${citIndex}`}
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "1px 7px",
            margin: "0 3px",
            borderRadius: "9999px",
            fontSize: "12px",
            fontWeight: 700,
            background: "#d1fae5",
            color: "#065f46",
            border: "1px solid #a7f3d0",
            cursor: matchedCitation ? "pointer" : "default",
            verticalAlign: "baseline",
            boxShadow: "0 1px 2px rgba(16, 185, 129, 0.15)",
            transition: "all 150ms ease",
          }}
          onMouseEnter={(e) => {
            if (matchedCitation) {
              e.currentTarget.style.transform = "translateY(-1px)";
              e.currentTarget.style.boxShadow = "0 2px 4px rgba(16, 185, 129, 0.25)";
              e.currentTarget.style.background = "#bbf7d0";
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "none";
            e.currentTarget.style.boxShadow = "0 1px 2px rgba(16, 185, 129, 0.15)";
            e.currentTarget.style.background = "#d1fae5";
          }}
        >
          [{citIndex}]
        </button>
      );
    }

    lastIndex = match.index + match[0].length;
  }

  const remaining = content.substring(lastIndex);
  if (remaining) {
    parts.push(
      <span key={`text-${lastIndex}`} style={{ whiteSpace: "pre-wrap" }}>
        {remaining}
      </span>
    );
  }

  return parts.length > 0 ? parts : <span style={{ whiteSpace: "pre-wrap" }}>{content}</span>;
}

export default function ChatPage() {
  const session = useWorkspaceSession();

  // State: Sessions
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [loadingSessions, setLoadingSessions] = useState<boolean>(true);

  // State: Lightbox modal
  const [lightboxImage, setLightboxImage] = useState<{
    url: string;
    alt?: string;
    caption?: string;
  } | null>(null);

  // State: Messages
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState<boolean>(false);

  // State: Query input & loading
  const [question, setQuestion] = useState<string>("");
  const [sendingQuery, setSendingQuery] = useState<boolean>(false);
  const [queryError, setQueryError] = useState<string>("");

  // State: Datasets for scope filter
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [filterExpanded, setFilterExpanded] = useState<boolean>(false);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [selectedProfileId, setSelectedProfileId] = useState<string>("");
  const [startTime, setStartTime] = useState<string>("");
  const [endTime, setEndTime] = useState<string>("");

  // State: Citation preview panel (Slide-over drawer)
  const [previewCitation, setPreviewCitation] = useState<CitationPreviewDetail | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [previewError, setPreviewError] = useState<string>("");

  // 1. Fetch sessions
  const fetchSessions = useCallback(async () => {
    try {
      setLoadingSessions(true);
      const data = await api<ChatSession[]>("/chat/sessions");
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        setActiveSessionId(data[0].id);
      }
    } catch {
      // Ignore or log error
    } finally {
      setLoadingSessions(false);
    }
  }, [activeSessionId]);

  // 2. Fetch datasets for filter
  useEffect(() => {
    api<Page<Dataset>>("/datasets?page=1&page_size=100")
      .then((res) => setDatasets(res.items))
      .catch(() => {});
  }, []);

  // 3. Initial load of sessions
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // 4. Fetch messages when active session changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }
    setLoadingMessages(true);
    setQueryError("");
    setPreviewCitation(null);
    setPreviewError("");

    api<ChatMessage[]>(`/chat/sessions/${activeSessionId}/messages`)
      .then((data) => setMessages(data))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          setActiveSessionId(null);
        }
      })
      .finally(() => setLoadingMessages(false));
  }, [activeSessionId]);

  // Create new session
  const handleCreateSession = async () => {
    if (!session) return;
    try {
      const newSession = await api<ChatSession>("/chat/sessions", {
        method: "POST",
        csrf: session.csrf_token,
      });
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]);
      setPreviewCitation(null);
    } catch (err) {
      setQueryError(err instanceof Error ? err.message : "Không thể tạo cuộc trò chuyện mới");
    }
  };

  // Delete session
  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!session) return;
    if (!window.confirm("Bạn có chắc chắn muốn xóa cuộc trò chuyện này?")) return;

    try {
      await api(`/chat/sessions/${sessionId}`, {
        method: "DELETE",
        csrf: session.csrf_token,
      });
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        const remaining = sessions.filter((s) => s.id !== sessionId);
        setActiveSessionId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Không thể xóa cuộc trò chuyện");
    }
  };

  // Send query
  const handleSendQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || sendingQuery || !session) return;

    const currentQ = question.trim();
    setQuestion("");
    setSendingQuery(true);
    setQueryError("");

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: "temp-" + Date.now(),
      role: "user",
      content: currentQ,
      citations: [],
      has_uncertainty: false,
      has_conflict: false,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    const payload: ChatQueryRequest = {
      question: currentQ,
      session_id: activeSessionId || undefined,
      dataset_ids: selectedDatasetId ? [selectedDatasetId] : undefined,
      profile_id: selectedProfileId || undefined,
      start_time: startTime ? new Date(startTime).toISOString() : undefined,
      end_time: endTime ? new Date(endTime).toISOString() : undefined,
    };

    try {
      const res = await api<ChatQueryResponse>("/chat/query", {
        method: "POST",
        body: payload,
        csrf: session.csrf_token,
      });

      if (!activeSessionId) {
        setActiveSessionId(res.session_id);
        fetchSessions();
      }

      setMessages((prev) => [...prev, res.message]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Không thể hoàn thành truy xuất do lỗi kết nối.";
      setQueryError(msg);
      // Remove optimistic message on failure
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
      setQuestion(currentQ);
    } finally {
      setSendingQuery(false);
    }
  };

  // Preview citation with Live Scope Recheck
  const handleCitationClick = async (citation: CitationItem) => {
    setPreviewLoading(true);
    setPreviewError("");
    try {
      const url = `/chat/citations/preview?dataset_id=${citation.dataset_id}&source_id=${citation.source_id}&citation_index=${citation.citation_index}`;
      const data = await api<CitationPreviewDetail>(url);
      setPreviewCitation(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setPreviewError("Quyền truy cập nguồn dữ liệu đã thay đổi hoặc bị thu hồi. Liên hệ Quản trị viên để được cấp lại quyền.");
      } else {
        setPreviewError(err instanceof Error ? err.message : "Không thể tải chi tiết trích dẫn.");
      }
      setPreviewCitation(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", gap: "24px", height: "calc(100vh - 110px)", minHeight: "600px", position: "relative" }}>
      {/* 1. Left Column: Chat Sessions Sidebar */}
      <aside
        style={{
          width: "270px",
          background: "#ffffff",
          border: "1px solid var(--border-subtle, #e2e8f0)",
          borderRadius: "16px",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
          boxShadow: "var(--shadow-soft)",
          overflow: "hidden",
        }}
      >
        <div style={{ padding: "16px", borderBottom: "1px solid var(--border-subtle, #e2e8f0)" }}>
          <button
            type="button"
            onClick={handleCreateSession}
            style={{
              width: "100%",
              backgroundColor: "var(--color-primary-green, #10b981)",
              color: "#ffffff",
              fontWeight: 600,
              fontSize: "14px",
              border: "1px solid var(--color-primary-green, #10b981)",
              borderRadius: "8px",
              padding: "10px 14px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              boxShadow: "0 1px 2px rgba(16, 185, 129, 0.2)",
              transition: "all 150ms ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "var(--color-primary-hover, #059669)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "var(--color-primary-green, #10b981)";
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            + Tạo cuộc trò chuyện mới
          </button>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "10px" }}>
          {loadingSessions ? (
            <div style={{ padding: "24px 16px", textAlign: "center", color: "var(--color-text-muted, #64748b)", fontSize: "14px" }}>
              Đang tải danh sách...
            </div>
          ) : sessions.length === 0 ? (
            <div style={{ padding: "32px 16px", textAlign: "center", color: "var(--color-text-muted, #64748b)", fontSize: "13px" }}>
              <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: "var(--color-pastel-mint, #ecfdf5)", color: "var(--color-emerald-dark, #047857)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 10px" }}>
                💬
              </div>
              <strong style={{ display: "block", color: "var(--color-text-main, #0f172a)" }}>Chưa có cuộc trò chuyện</strong>
              <p style={{ margin: "6px 0 0", color: "var(--color-text-muted, #64748b)", fontSize: "12px", lineHeight: "1.5" }}>
                Bấm nút trên để bắt đầu phiên hỏi đáp tri thức đầu tiên.
              </p>
            </div>
          ) : (
            <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {sessions.map((s) => {
                const isActive = s.id === activeSessionId;
                return (
                  <li
                    key={s.id}
                    onClick={() => setActiveSessionId(s.id)}
                    aria-current={isActive ? "true" : undefined}
                    style={{
                      padding: "10px 12px",
                      borderRadius: "8px",
                      marginBottom: "6px",
                      cursor: "pointer",
                      background: isActive ? "var(--color-pastel-mint, #ecfdf5)" : "transparent",
                      border: isActive ? "1px solid var(--color-mint-border, #a7f3d0)" : "1px solid transparent",
                      borderLeft: isActive ? "3px solid var(--color-primary-green, #10b981)" : "1px solid transparent",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      transition: "all 150ms ease",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = "var(--color-pastel-50, #f0fdf4)";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = "transparent";
                      }
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1, paddingRight: "8px" }}>
                      <div
                        style={{
                          fontSize: "14px",
                          fontWeight: isActive ? 600 : 400,
                          color: isActive ? "var(--color-emerald-deep, #065f46)" : "var(--color-text-main, #0f172a)",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {s.title}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteSession(s.id, e)}
                      title="Xóa cuộc trò chuyện"
                      aria-label="Xóa cuộc trò chuyện"
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--color-text-light, #94a3b8)",
                        fontSize: "13px",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        cursor: "pointer",
                        transition: "color 150ms ease",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.color = "#dc2626";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.color = "var(--color-text-light, #94a3b8)";
                      }}
                    >
                      ✕
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </aside>

      {/* 2. Center Column: Chat Conversation Stream & Input */}
      <section
        style={{
          flex: 1,
          background: "#ffffff",
          border: "1px solid var(--border-subtle, #e2e8f0)",
          borderRadius: "16px",
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          boxShadow: "var(--shadow-soft)",
          overflow: "hidden",
        }}
      >
        {/* Scope Filter Bar */}
        <div
          style={{
            borderBottom: "1px solid var(--border-subtle, #e2e8f0)",
            padding: "12px 20px",
            background: "#fafbfc",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor: selectedDatasetId || selectedProfileId || startTime || endTime ? "#10b981" : "#94a3b8",
                  display: "inline-block",
                }}
              />
              <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-text-main, #0f172a)" }}>
                {selectedDatasetId || selectedProfileId || startTime || endTime
                  ? "Bộ lọc phạm vi: Đang lọc tùy chỉnh"
                  : "Bộ lọc phạm vi: Tất cả dataset được cấp quyền"}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setFilterExpanded(!filterExpanded)}
              style={{
                background: "none",
                border: "none",
                color: "var(--color-emerald-dark, #047857)",
                fontSize: "13px",
                cursor: "pointer",
                padding: "4px 8px",
                fontWeight: 600,
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              {filterExpanded ? "Đóng bộ lọc ▲" : "Tùy chỉnh bộ lọc ▼"}
            </button>
          </div>

          {filterExpanded && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "12px",
                marginTop: "12px",
                paddingTop: "12px",
                borderTop: "1px solid var(--border-subtle, #e2e8f0)",
              }}
            >
              <div>
                <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted, #64748b)", marginBottom: "4px" }}>
                  Dataset:
                </label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-subtle, #e2e8f0)",
                    fontSize: "13px",
                  }}
                >
                  <option value="">Tất cả dataset được cấp quyền</option>
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted, #64748b)", marginBottom: "4px" }}>
                  Loại hồ sơ:
                </label>
                <select
                  value={selectedProfileId}
                  onChange={(e) => setSelectedProfileId(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-subtle, #e2e8f0)",
                    fontSize: "13px",
                  }}
                >
                  <option value="">Tất cả hồ sơ</option>
                  <option value="sop">Quy trình SOP</option>
                  <option value="text_log">Nhật ký Log</option>
                  <option value="ticket">Phiếu Ticket</option>
                  <option value="ops_table">Bảng vận hành</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted, #64748b)", marginBottom: "4px" }}>
                  Từ ngày:
                </label>
                <input
                  type="date"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-subtle, #e2e8f0)",
                    fontSize: "13px",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-text-muted, #64748b)", marginBottom: "4px" }}>
                  Đến ngày:
                </label>
                <input
                  type="date"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-subtle, #e2e8f0)",
                    fontSize: "13px",
                  }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Message Stream */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px 28px",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
            backgroundColor: "var(--bg-app, #f8fafc)",
          }}
        >
          {loadingMessages ? (
            <div style={{ textAlign: "center", color: "var(--color-text-muted, #64748b)", padding: "48px 0", fontSize: "14px" }}>
              Đang tải tin nhắn...
            </div>
          ) : messages.length === 0 ? (
            <div style={{ textAlign: "center", padding: "64px 20px", margin: "auto" }}>
              <div
                style={{
                  width: "56px",
                  height: "56px",
                  borderRadius: "50%",
                  background: "var(--color-pastel-mint, #ecfdf5)",
                  border: "1px solid var(--color-mint-border, #a7f3d0)",
                  color: "var(--color-emerald-dark, #047857)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 16px",
                  boxShadow: "0 2px 6px rgba(16, 185, 129, 0.12)",
                }}
              >
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <h3 style={{ margin: "0 0 8px", fontSize: "20px", fontWeight: 600, color: "var(--color-text-main, #0f172a)" }}>
                Bắt đầu cuộc hội thoại mới
              </h3>
              <p
                style={{
                  margin: 0,
                  fontSize: "14px",
                  color: "var(--color-text-muted, #64748b)",
                  maxWidth: "480px",
                  marginInline: "auto",
                  lineHeight: "1.6",
                }}
              >
                Đặt câu hỏi về quy trình logistics, tra cứu SOP hoặc sự cố đơn hàng để nhận phân tích kèm bằng chứng trích dẫn.
              </p>
            </div>
          ) : (
            messages.map((m) => {
              const isUser = m.role === "user";
              return (
                <div
                  key={m.id}
                  style={{
                    alignSelf: isUser ? "flex-end" : "flex-start",
                    maxWidth: isUser ? "80%" : "85%",
                    display: "flex",
                    flexDirection: isUser ? "column" : "row",
                    gap: isUser ? "4px" : "12px",
                    alignItems: isUser ? "flex-end" : "flex-start",
                  }}
                >
                  {/* AI Avatar */}
                  {!isUser && (
                    <div
                      style={{
                        width: "36px",
                        height: "36px",
                        borderRadius: "50%",
                        background: "var(--color-pastel-mint, #ecfdf5)",
                        border: "1px solid var(--color-mint-border, #a7f3d0)",
                        color: "var(--color-emerald-dark, #047857)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                        marginTop: "2px",
                        boxShadow: "0 1px 3px rgba(16, 185, 129, 0.1)",
                      }}
                      title="Trợ lý tri thức Logistics"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="11" width="18" height="10" rx="2"></rect>
                        <circle cx="12" cy="5" r="2"></circle>
                        <path d="M12 7v4"></path>
                        <line x1="8" y1="16" x2="8" y2="16"></line>
                        <line x1="16" y1="16" x2="16" y2="16"></line>
                      </svg>
                    </div>
                  )}

                  <div style={{ display: "flex", flexDirection: "column", gap: "4px", width: "100%" }}>
                    {/* Role header */}
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        justifyContent: isUser ? "flex-end" : "flex-start",
                      }}
                    >
                      <span
                        style={{
                          fontSize: "12px",
                          fontWeight: 600,
                          color: isUser ? "var(--color-emerald-dark, #047857)" : "var(--color-emerald-deep, #065f46)",
                        }}
                      >
                        {isUser ? "Bạn" : "Trợ lý tri thức Logistics"}
                      </span>
                      {!isUser && (
                        <span
                          style={{
                            fontSize: "11px",
                            padding: "1px 6px",
                            borderRadius: "9999px",
                            background: "var(--color-pastel-mint, #ecfdf5)",
                            color: "var(--color-emerald-dark, #047857)",
                            border: "1px solid var(--color-mint-border, #a7f3d0)",
                            fontWeight: 600,
                          }}
                        >
                          AI RAG
                        </span>
                      )}
                    </div>

                    {/* Bubble */}
                    <div
                      style={{
                        background: isUser ? "var(--color-pastel-mint, #ecfdf5)" : "#ffffff",
                        border: isUser
                          ? "1px solid var(--color-mint-border, #a7f3d0)"
                          : "1px solid var(--border-subtle, #e2e8f0)",
                        borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                        padding: "14px 18px",
                        fontSize: "15px",
                        lineHeight: "1.6",
                        color: "var(--color-text-main, #0f172a)",
                        boxShadow: isUser ? "0 1px 2px rgba(16, 185, 129, 0.08)" : "var(--shadow-soft)",
                      }}
                    >
                      {/* Visual Warning Banners */}
                      {!isUser && m.has_uncertainty && (
                        <div
                          role="alert"
                          style={{
                            background: "#fffbeb",
                            border: "1px solid #fde68a",
                            color: "#b45309",
                            padding: "8px 12px",
                            borderRadius: "8px",
                            fontSize: "12px",
                            fontWeight: 600,
                            marginBottom: "10px",
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                          }}
                        >
                          <span>⚠</span>
                          <span>Cảnh báo: Thiếu dữ liệu xác thực cho một số nội dung.</span>
                        </div>
                      )}

                      {!isUser && m.has_conflict && (
                        <div
                          role="alert"
                          style={{
                            background: "#fffbeb",
                            border: "1px solid #fde68a",
                            color: "#b45309",
                            padding: "8px 12px",
                            borderRadius: "8px",
                            fontSize: "12px",
                            fontWeight: 600,
                            marginBottom: "10px",
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                          }}
                        >
                          <span>⚠</span>
                          <span>Cảnh báo: Phát hiện mâu thuẫn giữa các nguồn tài liệu trích dẫn.</span>
                        </div>
                      )}

                      {/* Content */}
                      <div>
                        {isUser
                          ? m.content
                          : renderMessageContent(
                              m.content,
                              (url, alt, caption) => setLightboxImage({ url, alt, caption }),
                              m.citations,
                              (cit) => handleCitationClick(cit)
                            )}
                      </div>

                      {/* Cited Images Gallery */}
                      {!isUser &&
                        m.citations &&
                        m.citations.some((c) => c.image_url && !m.content.includes(c.image_url)) && (
                          <div
                            style={{
                              marginTop: "14px",
                              paddingTop: "12px",
                              borderTop: "1px solid var(--border-divider, #f1f5f9)",
                            }}
                          >
                            <div
                              style={{
                                fontSize: "12px",
                                fontWeight: 600,
                                color: "var(--color-emerald-deep, #065f46)",
                                marginBottom: "8px",
                                display: "flex",
                                alignItems: "center",
                                gap: "6px",
                              }}
                            >
                              📷 Sơ đồ & Hình ảnh trích dẫn:
                            </div>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                              {m.citations
                                .filter((c) => c.image_url && !m.content.includes(c.image_url))
                                .map((imgCit, idx) => (
                                  <div
                                    key={`cited-img-${imgCit.citation_index}-${idx}`}
                                    style={{
                                      background: "var(--color-pastel-50, #f0fdf4)",
                                      border: "1px solid var(--color-mint-border, #a7f3d0)",
                                      borderRadius: "12px",
                                      padding: "8px",
                                      display: "flex",
                                      flexDirection: "column",
                                      alignItems: "center",
                                      maxWidth: "240px",
                                      boxShadow: "var(--shadow-soft)",
                                    }}
                                  >
                                    <img
                                      src={imgCit.image_url}
                                      alt={
                                        imgCit.caption ||
                                        `Hình ảnh trích dẫn [${imgCit.citation_index}]`
                                      }
                                      loading="lazy"
                                      onClick={() =>
                                        imgCit.image_url &&
                                        setLightboxImage({
                                          url: imgCit.image_url,
                                          alt:
                                            imgCit.caption ||
                                            `Trích dẫn [${imgCit.citation_index}]`,
                                          caption:
                                            imgCit.caption ||
                                            (imgCit.locator.page
                                              ? `Trang ${imgCit.locator.page}`
                                              : undefined),
                                        })
                                      }
                                      style={{
                                        maxHeight: "160px",
                                        maxWidth: "100%",
                                        objectFit: "contain",
                                        borderRadius: "8px",
                                        cursor: "zoom-in",
                                        transition: "transform 150ms ease",
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.transform = "scale(1.02)";
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.transform = "none";
                                      }}
                                    />
                                    <span
                                      style={{
                                        fontSize: "11px",
                                        fontWeight: 600,
                                        color: "var(--color-emerald-deep, #065f46)",
                                        marginTop: "6px",
                                        textAlign: "center",
                                      }}
                                    >
                                      Trích dẫn [{imgCit.citation_index}]
                                      {imgCit.locator.page
                                        ? ` · Trang ${imgCit.locator.page}`
                                        : ""}
                                    </span>
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}

                      {/* Citations list pills */}
                      {!isUser && m.citations && m.citations.length > 0 && (
                        <div
                          style={{
                            marginTop: "14px",
                            paddingTop: "10px",
                            borderTop: "1px solid var(--border-divider, #f1f5f9)",
                          }}
                        >
                          <div
                            style={{
                              fontSize: "12px",
                              fontWeight: 600,
                              color: "var(--color-emerald-deep, #065f46)",
                              marginBottom: "8px",
                              display: "flex",
                              alignItems: "center",
                              gap: "6px",
                            }}
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                            </svg>
                            Nguồn trích dẫn đối chiếu ({m.citations.length}):
                          </div>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                            {m.citations.map((c) => (
                              <button
                                key={c.citation_index}
                                type="button"
                                onClick={() => handleCitationClick(c)}
                                title={`Xem bằng chứng trích dẫn [${c.citation_index}]`}
                                style={{
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: "6px",
                                  background: "var(--color-pastel-50, #f0fdf4)",
                                  border: "1px solid var(--border-subtle, #e2e8f0)",
                                  borderRadius: "8px",
                                  padding: "4px 10px",
                                  fontSize: "12px",
                                  color: "var(--color-text-main, #0f172a)",
                                  cursor: "pointer",
                                  transition: "all 150ms ease",
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.transform = "translateY(-1px)";
                                  e.currentTarget.style.borderColor = "var(--color-mint-border, #a7f3d0)";
                                  e.currentTarget.style.boxShadow = "var(--shadow-soft)";
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.transform = "none";
                                  e.currentTarget.style.borderColor = "var(--border-subtle, #e2e8f0)";
                                  e.currentTarget.style.boxShadow = "none";
                                }}
                              >
                                <span
                                  style={{
                                    background: "#d1fae5",
                                    color: "#065f46",
                                    borderRadius: "9999px",
                                    padding: "1px 6px",
                                    fontWeight: 700,
                                    fontSize: "11px",
                                  }}
                                >
                                  [{c.citation_index}]
                                </span>
                                <span style={{ fontWeight: 500 }}>
                                  {c.locator?.page
                                    ? `Trang ${c.locator.page}`
                                    : c.locator?.line_start
                                    ? `Dòng ${c.locator.line_start}${c.locator.line_end ? `-${c.locator.line_end}` : ""}`
                                    : c.locator?.section
                                    ? `Mục ${c.locator.section}`
                                    : "Chi tiết nguồn"}
                                </span>
                                {c.image_url && (
                                  <span style={{ fontSize: "11px" }}>📷</span>
                                )}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {queryError && (
            <div
              role="alert"
              style={{
                background: "var(--color-danger-bg, #fef2f2)",
                border: "1px solid var(--color-danger-border, #fecaca)",
                color: "var(--color-danger-text, #b91c1c)",
                padding: "12px 16px",
                borderRadius: "8px",
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              {queryError}
            </div>
          )}
        </div>

        {/* Input Form at bottom */}
        <form
          onSubmit={handleSendQuery}
          style={{
            borderTop: "1px solid var(--border-subtle, #e2e8f0)",
            padding: "16px 20px",
            background: "#ffffff",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          {sendingQuery && (
            <div role="status" style={{ fontSize: "13px", color: "var(--color-emerald-dark, #047857)", fontWeight: 500, display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ display: "inline-block", animation: "spin 1s linear infinite" }}>🔄</span>
              Đang truy xuất và tổng hợp câu trả lời...
            </div>
          )}
          <div style={{ display: "flex", gap: "12px", alignItems: "flex-end" }}>
            <textarea
              rows={2}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Nhập câu hỏi bằng tiếng Việt về quy trình, log, ticket, sự cố..."
              style={{
                flex: 1,
                padding: "12px 14px",
                border: "1px solid var(--border-subtle, #e2e8f0)",
                borderRadius: "10px",
                fontSize: "14px",
                lineHeight: "1.5",
                resize: "none",
                fontFamily: "inherit",
                color: "var(--color-text-main, #0f172a)",
                outline: "none",
                transition: "border-color 150ms ease, box-shadow 150ms ease",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--color-primary-green, #10b981)";
                e.currentTarget.style.boxShadow = "0 0 0 3px rgba(16, 185, 129, 0.15)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--border-subtle, #e2e8f0)";
                e.currentTarget.style.boxShadow = "none";
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendQuery(e);
                }
              }}
            />
            <button
              type="submit"
              disabled={!question.trim() || sendingQuery}
              style={{
                backgroundColor: "var(--color-primary-green, #10b981)",
                color: "#ffffff",
                border: "1px solid var(--color-primary-green, #10b981)",
                borderRadius: "10px",
                padding: "0 24px",
                height: "48px",
                fontWeight: 600,
                fontSize: "14px",
                cursor: !question.trim() || sendingQuery ? "not-allowed" : "pointer",
                opacity: !question.trim() || sendingQuery ? 0.6 : 1,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                boxShadow: "0 1px 2px rgba(16, 185, 129, 0.2)",
                transition: "all 150ms ease",
                whiteSpace: "nowrap",
              }}
              onMouseEnter={(e) => {
                if (question.trim() && !sendingQuery) {
                  e.currentTarget.style.backgroundColor = "var(--color-primary-hover, #059669)";
                }
              }}
              onMouseLeave={(e) => {
                if (question.trim() && !sendingQuery) {
                  e.currentTarget.style.backgroundColor = "var(--color-primary-green, #10b981)";
                }
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
              Gửi câu hỏi
            </button>
          </div>
        </form>
      </section>

      {/* 3. Evidence Preview Slide-over Drawer (Task 08-02-02) */}
      <EvidencePreview
        citation={previewCitation}
        loading={previewLoading}
        error={previewError}
        onClose={() => {
          setPreviewCitation(null);
          setPreviewError("");
        }}
        onImageClick={(url, alt, caption) =>
          setLightboxImage({ url, alt, caption })
        }
      />

      {/* Lightbox Modal (Task 08-02-03) */}
      {lightboxImage && (
        <ImageLightboxModal
          isOpen={!!lightboxImage}
          imageUrl={lightboxImage.url}
          altText={lightboxImage.alt}
          caption={lightboxImage.caption}
          onClose={() => setLightboxImage(null)}
        />
      )}
    </div>
  );
}
