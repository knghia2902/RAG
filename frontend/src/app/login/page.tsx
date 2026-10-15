"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session } from "@/lib/contracts";
import { sessionDestination } from "@/hooks/use-session";

export default function Login() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "var(--bg-app)",
        padding: "24px 16px",
      }}
    >
      <main
        className="card-soft"
        style={{
          width: "100%",
          maxWidth: 440,
          padding: "36px 32px",
          boxShadow: "var(--shadow-card)",
          borderRadius: "var(--radius-lg)",
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, #10b981 0%, #047857 100%)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              boxShadow: "0 4px 10px rgba(16, 185, 129, 0.25)",
              marginBottom: 12,
            }}
          >
            <svg
              width="26"
              height="26"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
              <path d="m3.3 7 8.7 5 8.7-5" />
              <path d="M12 22V12" />
            </svg>
          </div>
          <div className="eyebrow" style={{ justifyContent: "center", marginBottom: 4 }}>
            IT &amp; Logistics · Local Security
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: "6px 0 8px", color: "var(--color-text-main)" }}>
            Đăng nhập hệ thống
          </h1>
          <p className="muted" style={{ margin: 0, fontSize: 14 }}>
            Tra cứu SOP, đối chiếu log sự cố và tạo báo cáo vận hành
          </p>
        </div>

        {/* Login Form */}
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            const data = new FormData(e.currentTarget);
            try {
              const s = await api<Session>("/auth/login", {
                method: "POST",
                body: {
                  username: data.get("username"),
                  password: data.get("password"),
                },
              });
              router.replace(sessionDestination(s));
            } catch (err) {
              setError(err instanceof Error ? err.message : "Không thể đăng nhập");
            } finally {
              setBusy(false);
            }
          }}
          style={{ display: "flex", flexDirection: "column", gap: 16 }}
        >
          <div>
            <label htmlFor="username">Tên đăng nhập</label>
            <input
              id="username"
              name="username"
              autoComplete="username"
              placeholder="Nhập tên đăng nhập..."
              required
              minLength={3}
              maxLength={64}
            />
          </div>

          <div>
            <label htmlFor="password">Mật khẩu</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="Nhập mật khẩu..."
              required
              minLength={8}
              maxLength={128}
            />
          </div>

          {error && (
            <p role="alert" className="error" style={{ margin: 0 }}>
              {error}
            </p>
          )}

          <button
            disabled={busy}
            type="submit"
            className="btn-primary"
            aria-label="Đăng nhập"
            style={{
              width: "100%",
              padding: "12px",
              fontSize: 15,
              marginTop: 4,
            }}
          >
            {busy ? "Đang đăng nhập…" : "Đăng nhập hệ thống"}
          </button>
        </form>

        <div
          style={{
            marginTop: 24,
            paddingTop: 16,
            borderTop: "1px solid var(--border-divider)",
            textAlign: "center",
          }}
        >
          <p className="muted" style={{ margin: 0, fontSize: 13 }}>
            Dữ liệu lưu tại máy chạy Docker. Phần quản trị không cần cấu hình AI.
          </p>
        </div>
      </main>
    </div>
  );
}
