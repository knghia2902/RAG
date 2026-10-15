"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session } from "@/lib/contracts";

export default function ChangePassword() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Session>("/auth/session")
      .then(setSession)
      .catch(() => router.replace("/login"));

    const expired = () => {
      setSession(null);
      router.replace("/login");
    };
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, [router]);

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
        {/* Brand / Security Header */}
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
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
          <div className="eyebrow" style={{ justifyContent: "center", marginBottom: 4 }}>
            Bảo mật tài khoản
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: "6px 0 8px", color: "var(--color-text-main)" }}>
            Đổi mật khẩu
          </h1>
          <p className="muted" style={{ margin: 0, fontSize: 14 }}>
            Đổi mật khẩu tạm để tiếp tục làm việc. Mật khẩu có 8–128 ký tự.
          </p>
        </div>

        {/* Form */}
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const data = new FormData(e.currentTarget);
            setError("");
            if (data.get("new_password") !== data.get("confirmation")) {
              setError("Mật khẩu nhập lại không khớp");
              return;
            }
            setBusy(true);
            try {
              const result = await api<Session>("/auth/change-password", {
                method: "POST",
                csrf: session?.csrf_token,
                body: {
                  current_password: data.get("current_password"),
                  new_password: data.get("new_password"),
                },
              });
              router.replace(result.account.role === "admin" ? "/accounts" : "/datasets");
            } catch (err) {
              setError(err instanceof Error ? err.message : "Không thể đổi mật khẩu");
            } finally {
              setBusy(false);
            }
          }}
          style={{ display: "flex", flexDirection: "column", gap: 16 }}
        >
          <div>
            <label htmlFor="current">Mật khẩu hiện tại</label>
            <input
              id="current"
              name="current_password"
              type="password"
              autoComplete="current-password"
              placeholder="Nhập mật khẩu hiện tại..."
              required
              minLength={8}
              maxLength={128}
            />
          </div>

          <div>
            <label htmlFor="new">Mật khẩu mới</label>
            <input
              id="new"
              name="new_password"
              type="password"
              autoComplete="new-password"
              placeholder="Nhập mật khẩu mới..."
              required
              minLength={8}
              maxLength={128}
            />
          </div>

          <div>
            <label htmlFor="confirmation">Nhập lại mật khẩu mới</label>
            <input
              id="confirmation"
              name="confirmation"
              type="password"
              autoComplete="new-password"
              placeholder="Nhập lại mật khẩu mới..."
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
            disabled={busy || !session}
            type="submit"
            className="btn-primary"
            style={{
              width: "100%",
              padding: "12px",
              fontSize: 15,
              marginTop: 4,
            }}
          >
            {busy ? "Đang xử lý…" : "Đổi mật khẩu"}
          </button>
        </form>
      </main>
    </div>
  );
}
