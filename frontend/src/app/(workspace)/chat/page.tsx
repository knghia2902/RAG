"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useWorkspaceSession } from "../layout";
import { EvidencePreview } from "@/components/EvidencePreview";
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

export default function ChatPage() {
  const session = useWorkspaceSession();

  // State: Sessions
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [loadingSessions, setLoadingSessions] = useState<boolean>(true);

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

  // State: Citation preview panel (Right column)
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

  // Preview citation with Live Scope Recheck (D-05)
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
    <div style={{ display: "flex", gap: "20px", height: "calc(100vh - 120px)", minHeight: "600px" }}>
      {/* 1. Left Column: Chat Sessions Sidebar */}
      <aside
        style={{
          width: "260px",
          background: "#ffffff",
          border: "1px solid #d7e1e8",
          borderRadius: "8px",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
        }}
      >
        <div style={{ padding: "16px", borderBottom: "1px solid #e0e8ed" }}>
          <button
            type="button"
            onClick={handleCreateSession}
            style={{
              width: "100%",
              background: "#075b79",
              color: "#ffffff",
              fontWeight: "bold",
              border: "1px solid #075b79",
              borderRadius: "6px",
              padding: "10px",
              cursor: "pointer",
            }}
          >
            + Tạo cuộc trò chuyện mới
          </button>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "8px" }}>
          {loadingSessions ? (
            <div style={{ padding: "16px", textAlign: "center", color: "#527080", fontSize: "14px" }}>
              Đang tải danh sách...
            </div>
          ) : sessions.length === 0 ? (
            <div style={{ padding: "24px 16px", textAlign: "center", color: "#587080", fontSize: "13px" }}>
              <strong>Chưa có cuộc trò chuyện</strong>
              <p style={{ margin: "8px 0 0", color: "#8195a4" }}>
                Bấm nút Tạo cuộc trò chuyện mới để bắt đầu phiên hỏi đáp đầu tiên.
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
                      borderRadius: "6px",
                      marginBottom: "4px",
                      cursor: "pointer",
                      background: isActive ? "#e9f3f8" : "transparent",
                      borderLeft: isActive ? "4px solid #075b79" : "4px solid transparent",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div
                        style={{
                          fontSize: "14px",
                          fontWeight: isActive ? "bold" : "normal",
                          color: "#172b3a",
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
                      style={{
                        background: "none",
                        border: "none",
                        color: "#8195a4",
                        fontSize: "12px",
                        padding: "2px 6px",
                        cursor: "pointer",
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
          border: "1px solid #d7e1e8",
          borderRadius: "8px",
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
        }}
      >
        {/* Scope Filter Bar (RAG-03, D-03) */}
        <div
          style={{
            borderBottom: "1px solid #e0e8ed",
            padding: "12px 16px",
            background: "#fafbfc",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "13px", fontWeight: "bold", color: "#527080" }}>
              {selectedDatasetId || selectedProfileId || startTime || endTime
                ? "Bộ lọc phạm vi: Đang lọc tùy chỉnh"
                : "Bộ lọc phạm vi (Tất cả dataset được cấp quyền)"}
            </span>
            <button
              type="button"
              onClick={() => setFilterExpanded(!filterExpanded)}
              style={{
                background: "none",
                border: "none",
                color: "#075b79",
                fontSize: "13px",
                cursor: "pointer",
                padding: "2px 6px",
                fontWeight: "bold",
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
                borderTop: "1px solid #e2e8f0",
              }}
            >
              <div>
                <label style={{ fontSize: "12px", color: "#527080" }}>Dataset:</label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  style={{ width: "100%", margin: "4px 0 0", padding: "6px" }}
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
                <label style={{ fontSize: "12px", color: "#527080" }}>Loại hồ sơ:</label>
                <select
                  value={selectedProfileId}
                  onChange={(e) => setSelectedProfileId(e.target.value)}
                  style={{ width: "100%", margin: "4px 0 0", padding: "6px" }}
                >
                  <option value="">Tất cả hồ sơ</option>
                  <option value="sop">Quy trình SOP</option>
                  <option value="text_log">Nhật ký Log</option>
                  <option value="ticket">Phiếu Ticket</option>
                  <option value="ops_table">Bảng vận hành</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: "12px", color: "#527080" }}>Từ ngày:</label>
                <input
                  type="date"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  style={{ margin: "4px 0 0", padding: "6px" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "12px", color: "#527080" }}>Đến ngày:</label>
                <input
                  type="date"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  style={{ margin: "4px 0 0", padding: "6px" }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Message Stream */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
          {loadingMessages ? (
            <div style={{ textAlign: "center", color: "#527080", padding: "40px" }}>
              Đang tải tin nhắn...
            </div>
          ) : messages.length === 0 ? (
            <div style={{ textAlign: "center", color: "#587080", padding: "60px 20px" }}>
              <h3 style={{ margin: "0 0 8px", fontSize: "18px", color: "#172b3a" }}>
                Bắt đầu tra cứu tri thức
              </h3>
              <p style={{ margin: 0, fontSize: "14px", maxWidth: "480px", marginInline: "auto", lineHeight: "1.6" }}>
                Nhập câu hỏi bằng tiếng Việt để tìm kiếm quy trình SOP, nhật ký log, ticket hoặc dữ liệu vận hành từ các Dataset được cấp quyền.
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
                    maxWidth: "85%",
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                  }}
                >
                  <span style={{ fontSize: "12px", fontWeight: "bold", color: "#527080" }}>
                    {isUser ? "Bạn" : "Trợ lý tri thức Logistics"}
                  </span>

                  <div
                    style={{
                      background: isUser ? "#e9f3f8" : "#ffffff",
                      border: "1px solid #d7e1e8",
                      borderRadius: "8px",
                      padding: "14px 16px",
                      fontSize: "14px",
                      lineHeight: "1.6",
                      color: "#172b3a",
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {/* Visual Warning Banners (RAG-05, D-04) */}
                    {!isUser && m.has_uncertainty && (
                      <div
                        role="alert"
                        style={{
                          background: "#fef3c7",
                          border: "1px solid #fcd34d",
                          color: "#b45309",
                          padding: "8px 12px",
                          borderRadius: "4px",
                          fontSize: "12px",
                          fontWeight: "bold",
                          marginBottom: "10px",
                        }}
                      >
                        ⚠ Cảnh báo: Thiếu dữ liệu xác thực cho một số nội dung.
                      </div>
                    )}

                    {!isUser && m.has_conflict && (
                      <div
                        role="alert"
                        style={{
                          background: "#fef3c7",
                          border: "1px solid #fcd34d",
                          color: "#b45309",
                          padding: "8px 12px",
                          borderRadius: "4px",
                          fontSize: "12px",
                          fontWeight: "bold",
                          marginBottom: "10px",
                        }}
                      >
                        ⚠ Cảnh báo: Phát hiện mâu thuẫn giữa các nguồn tài liệu trích dẫn.
                      </div>
                    )}

                    {/* Content */}
                    <div>{m.content}</div>

                    {/* Citations list pills */}
                    {!isUser && m.citations && m.citations.length > 0 && (
                      <div style={{ marginTop: "12px", paddingTop: "8px", borderTop: "1px solid #edf2f7" }}>
                        <div style={{ fontSize: "12px", fontWeight: "bold", color: "#527080", marginBottom: "6px" }}>
                          Nguồn trích dẫn:
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                          {m.citations.map((c) => (
                            <button
                              key={c.citation_index}
                              type="button"
                              onClick={() => handleCitationClick(c)}
                              style={{
                                background: "#e9f3f8",
                                color: "#075b79",
                                border: "1px solid #8195a4",
                                borderRadius: "4px",
                                padding: "3px 8px",
                                fontSize: "12px",
                                fontWeight: "bold",
                                cursor: "pointer",
                              }}
                            >
                              [{c.citation_index}] Xem nguồn
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {queryError && (
            <div
              role="alert"
              style={{
                background: "#fdf2f2",
                border: "1px solid #f8b4b4",
                color: "#a22a28",
                padding: "12px",
                borderRadius: "6px",
                fontSize: "14px",
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
            borderTop: "1px solid #e0e8ed",
            padding: "16px",
            background: "#ffffff",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          {sendingQuery && (
            <div role="status" style={{ fontSize: "13px", color: "#527080" }}>
              Đang truy xuất và tổng hợp câu trả lời...
            </div>
          )}
          <div style={{ display: "flex", gap: "10px" }}>
            <textarea
              rows={2}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Nhập câu hỏi bằng tiếng Việt về quy trình, log, ticket, sự cố..."
              style={{
                flex: 1,
                padding: "10px",
                border: "1px solid #8195a4",
                borderRadius: "6px",
                fontSize: "14px",
                resize: "none",
                fontFamily: "inherit",
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
                background: "#075b79",
                color: "#ffffff",
                border: "1px solid #075b79",
                borderRadius: "6px",
                padding: "0 24px",
                fontWeight: "bold",
                cursor: !question.trim() || sendingQuery ? "not-allowed" : "pointer",
              }}
            >
              Gửi câu hỏi
            </button>
          </div>
        </form>
      </section>

      {/* 3. Right Column: Evidence Preview Panel (D-01) */}
      <div style={{ width: "360px", flexShrink: 0 }}>
        <EvidencePreview
          citation={previewCitation}
          loading={previewLoading}
          error={previewError}
          onClose={() => {
            setPreviewCitation(null);
            setPreviewError("");
          }}
        />
      </div>
    </div>
  );
}
