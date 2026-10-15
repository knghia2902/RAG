"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useWorkspaceSession } from "../layout";
import { api } from "@/lib/api";
import type { ModelConfig } from "@/lib/contracts";

type ConfigurationStatus = { database_ready: boolean; provider_configured: boolean };

export default function Configuration() {
  const session = useWorkspaceSession();
  const [status, setStatus] = useState<ConfigurationStatus | null>(null);
  const [modelConfig, setModelConfig] = useState<ModelConfig | null>(null);
  const [error, setError] = useState("");
  const [request, setRequest] = useState(0);

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
          setError(err instanceof Error ? err.message : "Không thể tải trạng thái");
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
    setRequest((value) => value + 1);
  };

  if (!session) return null;
  if (session.account.role !== "admin")
    return (
      <p role="alert">
        Không đủ quyền. <Link href="/datasets">Mở Dataset</Link>
      </p>
    );

  return (
    <>
      <div className="eyebrow">Quản trị</div>
      <h1>Cấu hình hệ thống</h1>

      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {/* Card 1: System Status */}
        <section className="card" aria-label="Trạng thái cấu hình">
          <h2 style={{ margin: "0 0 16px", fontSize: "18px" }}>Hạ tầng dịch vụ</h2>
          {error ? (
            <>
              <p role="alert" className="error">
                {error}
              </p>
              <button onClick={refresh}>Thử lại</button>
            </>
          ) : !status ? (
            <p role="status">Đang tải trạng thái…</p>
          ) : (
            <>
              <dl>
                <dt>Database</dt>
                <dd>{status.database_ready ? "Sẵn sàng (PostgreSQL + pgvector)" : "Chưa sẵn sàng"}</dd>
                <dt>AI Services</dt>
                <dd>{status.provider_configured ? "Đã cấu hình AI" : "Chưa cấu hình AI"}</dd>
              </dl>
              <p className="muted">
                Cấu hình tại máy chạy Docker bằng .env. Trạng thái AI xác nhận các khóa môi trường cục bộ.
              </p>
              <button onClick={refresh}>Làm mới trạng thái</button>
            </>
          )}
        </section>

        {/* Card 2: Model Configuration (SYS-02) */}
        <section className="card" aria-label="Cấu hình mô hình AI">
          <h2 style={{ margin: "0 0 16px", fontSize: "18px" }}>Mô hình AI & Index Vector (SYS-02)</h2>
          {!modelConfig ? (
            <p role="status">Đang tải thông tin mô hình…</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <h3 style={{ fontSize: "14px", fontWeight: "bold", margin: "0 0 8px", color: "#527080" }}>
                  Mô hình nhúng (Embedding Provider)
                </h3>
                <dl style={{ margin: 0 }}>
                  <dt>Nhà cung cấp:</dt>
                  <dd>
                    {modelConfig.embedding_provider === "openai" ? "OpenAI API" : "Mô phỏng nội bộ (Fake Adapter)"}
                  </dd>
                  <dt>Tên mô hình:</dt>
                  <dd>{modelConfig.embedding_model}</dd>
                  <dt>Số chiều vector (Dimension):</dt>
                  <dd>{modelConfig.embedding_dimension} chiều</dd>
                  <dt>Index Version hiện tại:</dt>
                  <dd style={{ fontFamily: "monospace", fontSize: "13px" }}>{modelConfig.index_version}</dd>
                </dl>
              </div>

              <div style={{ borderTop: "1px solid #e0e8ed", paddingTop: "16px" }}>
                <h3 style={{ fontSize: "14px", fontWeight: "bold", margin: "0 0 8px", color: "#527080" }}>
                  Mô hình sinh câu trả lời (LLM Generation Provider)
                </h3>
                <dl style={{ margin: 0 }}>
                  <dt>Nhà cung cấp:</dt>
                  <dd>
                    {modelConfig.llm_provider === "gemini"
                      ? "Google Gemini API"
                      : modelConfig.llm_provider === "openai"
                      ? "OpenAI API"
                      : "Mô phỏng nội bộ (Fake Adapter)"}
                  </dd>
                  <dt>Tên mô hình:</dt>
                  <dd>{modelConfig.llm_model}</dd>
                  <dt>Trạng thái API Key:</dt>
                  <dd>
                    {(() => {
                      const isConfigured = Boolean(
                        (modelConfig.llm_provider === "gemini" && modelConfig.gemini_configured) ||
                        (modelConfig.llm_provider === "openai" && modelConfig.openai_configured) ||
                        modelConfig.gemini_configured ||
                        modelConfig.openai_configured
                      );
                      return (
                        <span
                          style={{
                            background: isConfigured ? "#dcfce7" : "#fee2e2",
                            color: isConfigured ? "#15803d" : "#b91c1c",
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontWeight: "bold",
                            fontSize: "12px",
                          }}
                        >
                          {isConfigured ? "Đã cấu hình" : "Chưa cấu hình (dùng Mock)"}
                        </span>
                      );
                    })()}
                  </dd>
                </dl>
              </div>

              <p className="muted" style={{ fontSize: "13px", margin: 0 }}>
                Lưu ý: API Key được bảo vệ an toàn phía server và không bao giờ xuất hiện ra giao diện trình duyệt.
              </p>
            </div>
          )}
        </section>

        <p>
          <Link href="/datasets">Quay lại danh sách Dataset</Link> ·{" "}
          <Link href="/chat">Chuyển sang Hỏi đáp tri thức</Link>
        </p>
      </div>
    </>
  );
}
