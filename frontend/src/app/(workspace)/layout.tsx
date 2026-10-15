"use client";

import Sidebar from "@/components/Sidebar";
import { useEffect, useState, createContext, useContext } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session } from "@/lib/contracts";
import { useSessionActivity } from "@/hooks/use-session";

const SessionContext = createContext<Session | null>(null);
export const useWorkspaceSession = () => useContext(SessionContext);

export default function Workspace({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);

  useSessionActivity(session?.csrf_token);

  useEffect(() => {
    let active = true;
    api<Session>("/auth/session")
      .then((s) => {
        if (active) {
          if (s.account.must_change_password) router.replace("/change-password");
          else setSession(s);
        }
      })
      .catch(() => router.replace("/login"));

    const expired = () => {
      setSession(null);
      router.replace("/login");
    };
    window.addEventListener("session-expired", expired);
    return () => {
      active = false;
      window.removeEventListener("session-expired", expired);
    };
  }, [router]);

  if (!session) {
    return (
      <main className="main" role="status" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "50vh" }}>
        <div style={{ color: "var(--color-text-muted)", fontSize: 15 }}>Đang kiểm tra phiên đăng nhập…</div>
      </main>
    );
  }

  return (
    <SessionContext.Provider value={session}>
      {/* Mobile Top Header */}
      <header className="mobile-header">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "var(--radius-sm)",
              background: "linear-gradient(135deg, #10b981 0%, #047857 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              boxShadow: "0 1px 3px rgba(16, 185, 129, 0.25)",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
              <path d="m3.3 7 8.7 5 8.7-5" />
              <path d="M12 22V12" />
            </svg>
          </div>
          <span style={{ fontWeight: 700, fontSize: 16, color: "var(--color-text-main)" }}>Logistics RAG</span>
        </div>
        <button
          onClick={() => setMobileOpen(true)}
          aria-label="Mở menu điều hướng"
          className="btn-icon"
          style={{
            background: "none",
            border: "none",
            padding: 6,
            cursor: "pointer",
            color: "var(--color-text-main)",
            display: "flex",
            alignItems: "center",
            borderRadius: "var(--radius-sm)",
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
      </header>

      {/* Mobile Drawer Backdrop Overlay */}
      {mobileOpen && (
        <div
          className="mobile-overlay"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Main App Shell */}
      <div className="shell">
        <Sidebar
          session={session}
          error={error}
          mobileOpen={mobileOpen}
          onCloseMobile={() => setMobileOpen(false)}
          onLogout={async () => {
            try {
              await api("/auth/logout", { method: "POST", csrf: session.csrf_token });
              setSession(null);
              router.replace("/login");
            } catch (err) {
              setError(err instanceof Error ? err.message : "Không thể đăng xuất");
            }
          }}
        />
        <main className="main">{children}</main>
      </div>
    </SessionContext.Provider>
  );
}
