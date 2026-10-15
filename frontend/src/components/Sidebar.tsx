"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Session } from "@/lib/contracts";

interface SidebarProps {
  session: Session;
  onLogout: () => Promise<void>;
  error: string;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export default function Sidebar({
  session,
  onLogout,
  error,
  mobileOpen = false,
  onCloseMobile,
}: SidebarProps) {
  const path = usePathname();

  const links =
    session.account.role === "admin"
      ? [
          { href: "/accounts", label: "Tài khoản", icon: "accounts" },
          { href: "/datasets", label: "Dataset", icon: "datasets" },
          { href: "/chat", label: "Hỏi đáp tri thức", icon: "chat" },
          { href: "/incidents", label: "Phân tích sự cố", icon: "incidents" },
          { href: "/reports", label: "Báo cáo sự cố", icon: "reports" },
          { href: "/configuration", label: "Cấu hình", icon: "configuration" },
        ]
      : [
          { href: "/datasets", label: "Dataset", icon: "datasets" },
          { href: "/chat", label: "Hỏi đáp tri thức", icon: "chat" },
          { href: "/incidents", label: "Phân tích sự cố", icon: "incidents" },
          { href: "/reports", label: "Báo cáo sự cố", icon: "reports" },
        ];

  // Initials for avatar circle
  const initials = session.account.display_name
    ? session.account.display_name
        .trim()
        .split(/\s+/)
        .map((w) => w[0])
        .slice(-2)
        .join("")
        .toUpperCase() || "ND"
    : "ND";

  const renderIcon = (iconName: string) => {
    switch (iconName) {
      case "chat":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        );
      case "datasets":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          </svg>
        );
      case "incidents":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        );
      case "reports":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
        );
      case "configuration":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <line x1="4" y1="21" x2="4" y2="14" />
            <line x1="4" y1="10" x2="4" y2="3" />
            <line x1="12" y1="21" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12" y2="3" />
            <line x1="20" y1="21" x2="20" y2="16" />
            <line x1="20" y1="12" x2="20" y2="3" />
            <line x1="1" y1="14" x2="7" y2="14" />
            <line x1="9" y1="8" x2="15" y2="8" />
            <line x1="17" y1="16" x2="23" y2="16" />
          </svg>
        );
      case "accounts":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`}>
      {/* Brand & Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          paddingBottom: 16,
          borderBottom: "1px solid var(--border-divider)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: "var(--radius-sm)",
              background: "linear-gradient(135deg, #10b981 0%, #047857 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              boxShadow: "0 2px 4px rgba(16, 185, 129, 0.25)",
              flexShrink: 0,
            }}
          >
            <svg
              width="22"
              height="22"
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
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span className="brand" style={{ fontSize: 16, fontWeight: 700, color: "var(--color-text-main)", letterSpacing: "-0.01em" }}>
                Logistics RAG
              </span>
              <span className="badge badge-pastel-green" style={{ fontSize: 10, padding: "1px 6px" }}>
                v1.0
              </span>
            </div>
            <div style={{ fontSize: 11, color: "var(--color-text-muted)" }}>Hệ thống Hỗ trợ Kỹ thuật</div>
          </div>
        </div>

        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            aria-label="Đóng thanh điều hướng"
            className="mobile-close-btn"
            style={{
              display: "none",
              background: "none",
              border: "none",
              padding: 6,
              color: "var(--color-text-muted)",
              cursor: "pointer",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav" aria-label="Điều hướng">
        {links.map(({ href, label, icon }) => {
          const isActive = path === href;
          return (
            <Link
              key={href}
              href={href}
              className="sidebar-link"
              aria-current={isActive ? "page" : undefined}
              onClick={onCloseMobile}
            >
              <span className="sidebar-link-icon">{renderIcon(icon)}</span>
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Profile Card */}
      <div
        style={{
          marginTop: "auto",
          paddingTop: 16,
          borderTop: "1px solid var(--border-divider)",
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 10px",
            backgroundColor: "var(--bg-subtle)",
            borderRadius: "var(--radius-sm)",
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "50%",
              backgroundColor: "var(--color-pastel-mint)",
              color: "var(--color-emerald-dark)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: 13,
              border: "1px solid var(--color-mint-border)",
              flexShrink: 0,
            }}
          >
            {initials}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: "var(--color-text-main)",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
              title={session.account.display_name}
            >
              {session.account.display_name}
            </div>
            <div style={{ marginTop: 2 }}>
              <span
                className={session.account.role === "admin" ? "badge badge-pastel-green" : "badge badge-pastel-slate"}
                style={{ fontSize: 11, padding: "1px 6px" }}
              >
                {session.account.role === "admin" ? "Quản trị viên" : "Kỹ thuật viên"}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
          <div className="status" style={{ border: "none", padding: 0, fontSize: 11, color: "var(--color-text-light)" }}>
            Local · localhost
          </div>
          <button
            onClick={onLogout}
            className="btn-secondary"
            style={{
              padding: "4px 10px",
              fontSize: 12,
              borderRadius: "var(--radius-sm)",
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Đăng xuất
          </button>
        </div>
        {error && (
          <p role="alert" className="error" style={{ margin: 0, padding: "6px 10px", fontSize: 12 }}>
            {error}
          </p>
        )}
      </div>
    </aside>
  );
}
