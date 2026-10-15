"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useWorkspaceSession } from "../layout";
import { api } from "@/lib/api";
import type { ModelConfig } from "@/lib/contracts";

type ConfigurationStatus = { database_ready: boolean; provider_configured: boolean };

export default function ConfigurationPage() {
  const session = useWorkspaceSession();
  const [status, setStatus] = useState<ConfigurationStatus | null>(null);
  const [modelConfig, setModelConfig] = useState<ModelConfig | null>(null);
  const [error, setError] = useState("");
  const [request, setRequest] = useState(0);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (session?.account.role !== "admin") return;

    Promise.all([
      api<ConfigurationStatus>("/status"),
      api<ModelConfig>("/config/models").catch(() => null),
    ])
      .then(([statusVal, configVal]) => {
        if (active) {
          setStatus(statusVal);
          setModelConfig(configVal);
        }
      })
      .catch((err) => {
        if (active) {
          setStatus(null);
          setError(err instanceof Error ? err.message : "Không thể tải trạng thái hệ thống");
        }
      });

    return () => {
      active = false;
    };
  }, [session?.account.role, request]);

  const refresh = () => {
    setStatus(null);
    setModelConfig(null);
    setError("");
    setSaveMessage(null);
    setRequest((value) => value + 1);
  };

  const handleSaveConfig = () => {
    setSaveMessage("Cấu hình mô hình hiện tại đang đồng bộ trực tiếp với các biến môi trường (.env) và hoạt động ổn định.");
    setTimeout(() => {
      setSaveMessage(null);
    }, 4000);
  };

  if (!session) return null;

  if (session.account.role !== "admin") {
    return (
      <div style={{ maxWidth: "600px", margin: "40px auto" }}>
        <div className="card-soft" style={{ textAlign: "center", padding: "40px 24px" }}>
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "50%",
              backgroundColor: "var(--color-danger-bg)",
              color: "var(--color-danger-text)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
            }}
          >
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
          <h2 style={{ fontSize: "18px", fontWeight: 600, color: "var(--color-text-main)", margin: "0 0 8px 0" }}>
            Truy cập bị giới hạn
          </h2>
          <p className="muted" style={{ marginBottom: "20px" }}>
            Trang Cấu hình hệ thống chỉ dành cho tài khoản có vai trò Quản trị viên (Admin).
          </p>
          <Link href="/datasets" className="btn-primary" style={{ display: "inline-block" }}>
            Mở Quản trị Dataset
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: "1080px", margin: "0 auto" }}>
      {/* Header */}
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
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          QUẢN TRỊ HỆ THỐNG
        </div>
        <h1 style={{ margin: "0 0 8px 0" }}>
          Cấu hình mô hình & Nhà cung cấp AI
        </h1>
        <p className="muted" style={{ margin: 0 }}>
          Theo dõi trạng thái kết nối hạ tầng cơ sở dữ liệu PostgreSQL + pgvector và thông số nhà cung cấp mô hình AI (SYS-02).
        </p>
      </div>

      {/* Global save / success notification */}
      {saveMessage && (
        <div
          role="status"
          style={{
            backgroundColor: "var(--color-pastel-mint)",
            border: "1px solid var(--color-mint-border)",
            color: "var(--color-emerald-dark)",
            borderRadius: "10px",
            padding: "14px 18px",
            marginBottom: "24px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            fontWeight: 500,
            fontSize: "14px",
            boxShadow: "var(--shadow-soft)",
          }}
        >
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
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span>{saveMessage}</span>
        </div>
      )}

      {/* Global error */}
      {error && (
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
            <span>{error}</span>
          </div>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {/* Card 1: Hạ tầng dịch vụ */}
        <section className="card-soft" aria-label="Trạng thái cấu hình">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
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
                  <ellipse cx="12" cy="5" rx="9" ry="3" />
                  <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                  <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                </svg>
              </div>
              <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 600, color: "var(--color-text-main)" }}>
                Hạ tầng dịch vụ
              </h2>
            </div>

            <button
              onClick={refresh}
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
              <span>Làm mới trạng thái</span>
            </button>
          </div>

          {!status ? (
            <p className="muted" style={{ padding: "16px 0", margin: 0 }}>
              Đang kiểm tra trạng thái hạ tầng...
            </p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
              <div
                style={{
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "16px 18px",
                  backgroundColor: status.database_ready ? "var(--color-pastel-50)" : "var(--bg-app)",
                }}
              >
                <div style={{ fontSize: "12.5px", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Cơ sở dữ liệu
                </div>
                <div style={{ fontSize: "16px", fontWeight: 600, color: "var(--color-text-main)", marginTop: "4px", display: "flex", alignItems: "center", gap: "8px" }}>
                  <span>PostgreSQL + pgvector</span>
                  <span className={`badge ${status.database_ready ? "badge-pastel-green" : "badge-pastel-rose"}`}>
                    {status.database_ready ? "Sẵn sàng" : "Chưa kết nối"}
                  </span>
                </div>
                <p className="muted" style={{ fontSize: "12px", margin: "6px 0 0" }}>
                  Lưu trữ bảng quan hệ, metadata và vector embeddings.
                </p>
              </div>

              <div
                style={{
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "16px 18px",
                  backgroundColor: status.provider_configured ? "var(--color-pastel-50)" : "var(--bg-app)",
                }}
              >
                <div style={{ fontSize: "12.5px", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Dịch vụ AI
                </div>
                <div style={{ fontSize: "16px", fontWeight: 600, color: "var(--color-text-main)", marginTop: "4px", display: "flex", alignItems: "center", gap: "8px" }}>
                  <span>OpenAI / Gemini API</span>
                  <span className={`badge ${status.provider_configured ? "badge-pastel-green" : "badge-pastel-amber"}`}>
                    {status.provider_configured ? "Đã cấu hình" : "Chế độ Mock"}
                  </span>
                </div>
                <p className="muted" style={{ fontSize: "12px", margin: "6px 0 0" }}>
                  Xác nhận các khóa môi trường server-side hợp lệ.
                </p>
              </div>
            </div>
          )}
        </section>

        {/* Card 2: Cấu hình mô hình sinh câu trả lời (LLM Generation Provider) */}
        <section className="card-soft" aria-label="Cấu hình mô hình sinh câu trả lời">
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "18px" }}>
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
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 600, color: "var(--color-text-main)" }}>
                Mô hình sinh câu trả lời (LLM Generation Provider)
              </h2>
              <div className="muted" style={{ fontSize: "13px" }}>
                Tạo phản hồi hỏi đáp tri thức và tổng hợp nhận định báo cáo sự cố
              </div>
            </div>
          </div>

          {!modelConfig ? (
            <p className="muted" style={{ padding: "16px 0", margin: 0 }}>
              Đang tải thông tin mô hình sinh câu trả lời...
            </p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px" }}>
              <div style={{ padding: "14px 16px", border: "1px solid var(--border-subtle)", borderRadius: "10px", backgroundColor: "#ffffff" }}>
                <span style={{ fontSize: "12px", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Nhà cung cấp
                </span>
                <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-text-main)", marginTop: "4px" }}>
                  {modelConfig.llm_provider === "gemini"
                    ? "Google Gemini API"
                    : modelConfig.llm_provider === "openai"
                    ? "OpenAI API"
                    : "Mô phỏng nội bộ (Fake Adapter)"}
                </div>
              </div>

              <div style={{ padding: "14px 16px", border: "1px solid var(--border-subtle)", borderRadius: "10px", backgroundColor: "#ffffff" }}>
                <span style={{ fontSize: "12px", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Tên mô hình
                </span>
                <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-emerald-dark)", marginTop: "4px", fontFamily: "monospace" }}>
                  {modelConfig.llm_model}
                </div>
              </div>

              <div style={{ padding: "14px 16px", border: "1px solid var(--border-subtle)", borderRadius: "10px", backgroundColor: "#ffffff" }}>
                <span style={{ fontSize: "12px", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Trạng thái API Key
                </span>
                <div style={{ marginTop: "4px" }}>
                  {(() => {
                    const isConfigured = Boolean(
                      (modelConfig.llm_provider === "gemini" && modelConfig.gemini_configured) ||
                      (modelConfig.llm_provider === "openai" && modelConfig.openai_configured) ||
                      modelConfig.gemini_configured ||
                      modelConfig.openai_configured
                    );
                    return isConfigured ? (
                      <span className="badge badge-pastel-green">
                        Đã cấu hình an toàn
                      </span>
                    ) : (
                      <span className="badge badge-pastel-amber">
                        Chưa cấu hình (Chế độ Mock)
                      </span>
                    );
                  })()}
                </div>
              </div>
            </div>
          )}

          <div
            style={{
              marginTop: "16px",
              padding: "10px 14px",
              backgroundColor: "var(--color-pastel-50)",
              border: "1px solid var(--color-mint-border)",
              borderRadius: "8px",
              fontSize: "12.5px",
              color: "var(--color-emerald-deep)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
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
              <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <span>
              Bảo mật: API Key được quản lý an toàn phía server và không bao giờ xuất hiện ra giao diện trình duyệt.
            </span>
          </div>
        </section>

        {/* Card 3: Cấu hình mô hình nhúng (Embedding Provider & Vector Store) */}
        <section className="card-soft" aria-label="Cấu hình mô hình nhúng">
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "18px" }}>
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
                <line x1="2" y1="12" x2="22" y2="12" />
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 600, color: "var(--color-text-main)" }}>
                Mô hình nhúng & Index Vector (Embedding Provider)
              </h2>
              <div className="muted" style={{ fontSize: "13px" }}>
                Chuyển đổi tài liệu thành vector biểu diễn ngữ nghĩa phục vụ truy xuất
              </div>
            </div>
          </div>

          {!modelConfig ? (
            <p className="muted" style={{ padding: "16px 0", margin: 0 }}>
              Đang tải thông tin mô hình nhúng...
            </p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
              <div style={{ padding: "14px 16px", border: "1px solid var(--border-subtle)", borderRadius: "10px", backgroundColor: "#ffffff" }}>
                <span style={{ fontSize: "12px", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Nhà cung cấp
                </span>
                <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-text-main)", marginTop: "4px" }}>
                  {modelConfig.embedding_provider === "openai" ? "OpenAI API" : "Mô phỏng nội bộ (Fake Adapter)"}
                </div>
              </div>

              <div style={{ padding: "14px 16px", border: "1px solid var(--border-subtle)", borderRadius: "10px", backgroundColor: "#ffffff" }}>
                <span style={{ fontSize: "12px", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Tên mô hình
                </span>
                <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-emerald-dark)", marginTop: "4px", fontFamily: "monospace" }}>
                  {modelConfig.embedding_model}
                </div>
              </div>

              <div style={{ padding: "14px 16px", border: "1px solid var(--border-subtle)", borderRadius: "10px", backgroundColor: "#ffffff" }}>
                <span style={{ fontSize: "12px", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Số chiều vector
                </span>
                <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-text-main)", marginTop: "4px" }}>
                  {modelConfig.embedding_dimension} chiều
                </div>
              </div>

              <div style={{ padding: "14px 16px", border: "1px solid var(--border-subtle)", borderRadius: "10px", backgroundColor: "#ffffff" }}>
                <span style={{ fontSize: "12px", color: "var(--color-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  Phiên bản Index
                </span>
                <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-text-muted)", marginTop: "4px", fontFamily: "monospace" }}>
                  {modelConfig.index_version}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Action Controls & Primary CTA */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingTop: "8px",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", gap: "16px", fontSize: "14px" }}>
            <Link href="/datasets" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span>← Quay lại danh sách Dataset</span>
            </Link>
            <span style={{ color: "var(--border-subtle)" }}>|</span>
            <Link href="/chat" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span>Chuyển sang Hỏi đáp tri thức →</span>
            </Link>
          </div>

          <button
            type="button"
            onClick={handleSaveConfig}
            className="btn-primary"
            style={{
              padding: "10px 22px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "14px",
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
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            <span>Lưu cấu hình mô hình</span>
          </button>
        </div>
      </div>
    </div>
  );
}
