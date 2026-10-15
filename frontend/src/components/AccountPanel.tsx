"use client";
import { useEffect, useRef, useState } from "react";
import type { Account } from "@/lib/contracts";
import { api } from "@/lib/api";

export default function AccountPanel({
  account,
  csrf,
  onClose,
  onSaved,
}: {
  account: Account | null;
  csrf: string;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const form = useRef<HTMLFormElement>(null);
  const usernameInputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const el = dialog.current;
    const opener = document.activeElement as HTMLElement | null;
    el?.showModal();
    if (!account) {
      usernameInputRef.current?.focus();
    }
    return () => {
      el?.close();
      opener?.focus();
    };
  }, [account]);

  const save = async (reset = false) => {
    const data = new FormData(form.current!);
    setError("");
    setBusy(true);
    try {
      if (reset && account) {
        await api(`/admin/users/${account.id}/reset-password`, {
          method: "POST",
          csrf,
          body: { temporary_password: data.get("temporary_password") },
        });
      } else {
        await api(account ? `/admin/users/${account.id}` : "/admin/users", {
          method: account ? "PATCH" : "POST",
          csrf,
          body: account
            ? {
                display_name: data.get("display_name"),
                role: data.get("role"),
                active: data.get("active") === "on",
              }
            : {
                username: data.get("username"),
                display_name: data.get("display_name"),
                role: data.get("role"),
                temporary_password: data.get("temporary_password"),
              },
        });
      }
      form.current?.reset();
      await onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể lưu tài khoản");
      const input = form.current?.elements.namedItem("temporary_password") as HTMLInputElement | null;
      if (input) input.value = "";
    } finally {
      setBusy(false);
    }
  };

  return (
    <dialog
      ref={dialog}
      onKeyDown={(event) => {
        if (event.key !== "Tab") return;
        const controls = Array.from(
          event.currentTarget.querySelectorAll<HTMLElement>(
            "input:not([disabled]),select:not([disabled]),textarea:not([disabled]),button:not([disabled]),a[href]"
          )
        ).filter((el) => el.getClientRects().length > 0);
        const first = controls[0],
          last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }}
      aria-labelledby="panel-title"
      aria-busy={busy}
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else onClose();
      }}
      style={{
        margin: "auto",
        maxWidth: "min(480px, calc(100vw - 32px))",
        width: "100%",
        borderRadius: "var(--radius-lg)",
        padding: 24,
        background: "#ffffff",
        border: "1px solid var(--border-subtle)",
        boxShadow: "var(--shadow-floating)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 18,
        }}
      >
        <h2 id="panel-title" style={{ margin: 0, fontSize: 18, color: "var(--color-text-main)" }}>
          {account ? "Chỉnh sửa tài khoản" : "Tạo tài khoản mới"}
        </h2>
        <button
          type="button"
          aria-label="Đóng hộp thoại"
          onClick={() => {
            form.current?.reset();
            onClose();
          }}
          disabled={busy}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--color-text-muted)",
            padding: 4,
          }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <form
        ref={form}
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <div style={{ marginBottom: 14 }}>
          <label
            htmlFor="panel-username"
            style={{ display: "block", marginBottom: 6, fontWeight: 600, fontSize: 13 }}
          >
            Tên đăng nhập
          </label>
          <input
            ref={usernameInputRef}
            id="panel-username"
            name="username"
            defaultValue={account?.username ?? ""}
            disabled={!!account}
            required
            minLength={3}
            maxLength={64}
            autoComplete="off"
            placeholder="Ví dụ: nva_tech"
          />
        </div>

        <div style={{ marginBottom: 14 }}>
          <label
            htmlFor="panel-name"
            style={{ display: "block", marginBottom: 6, fontWeight: 600, fontSize: 13 }}
          >
            Họ tên
          </label>
          <input
            id="panel-name"
            name="display_name"
            defaultValue={account?.display_name ?? ""}
            required
            maxLength={128}
            placeholder="Ví dụ: Nguyễn Văn A"
          />
        </div>

        <div style={{ marginBottom: 14 }}>
          <label
            htmlFor="panel-role"
            style={{ display: "block", marginBottom: 6, fontWeight: 600, fontSize: 13 }}
          >
            Vai trò
          </label>
          <select
            id="panel-role"
            name="role"
            defaultValue={account?.role ?? "technician"}
            style={{
              width: "100%",
              padding: "9px 12px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
              fontSize: 14,
            }}
          >
            <option value="technician">Kỹ thuật viên</option>
            <option value="admin">Quản trị viên (Admin)</option>
          </select>
        </div>

        {account && (
          <div style={{ margin: "14px 0" }}>
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                cursor: "pointer",
                fontWeight: 500,
                fontSize: 14,
              }}
            >
              <input
                name="active"
                type="checkbox"
                defaultChecked={account.active}
                style={{ width: "auto", accentColor: "#10b981", cursor: "pointer" }}
              />
              <span>Đang hoạt động</span>
            </label>
          </div>
        )}

        <div style={{ marginBottom: 14 }}>
          <label
            htmlFor="panel-password"
            style={{ display: "block", marginBottom: 6, fontWeight: 600, fontSize: 13 }}
          >
            Mật khẩu tạm
          </label>
          <input
            id="panel-password"
            name="temporary_password"
            type="password"
            required={!account}
            minLength={8}
            maxLength={128}
            autoComplete="new-password"
            placeholder="Tối thiểu 8 ký tự"
          />
          <p className="muted" style={{ fontSize: 12, marginTop: 4, marginBottom: 0 }}>
            Tài khoản mới hoặc đặt lại mật khẩu phải đổi mật khẩu trước khi làm việc.
          </p>
        </div>

        {error && (
          <p role="alert" className="error" style={{ margin: "12px 0" }}>
            {error}
          </p>
        )}

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            gap: 8,
            marginTop: 20,
            flexWrap: "wrap",
          }}
        >
          <button
            type="button"
            className="btn-secondary"
            disabled={busy}
            onClick={() => {
              form.current?.reset();
              onClose();
            }}
          >
            Đóng
          </button>

          {account && (
            <button
              disabled={busy}
              type="button"
              className="btn-secondary"
              onClick={() => {
                const field = form.current?.elements.namedItem("temporary_password") as HTMLInputElement;
                const required = field.required;
                try {
                  field.required = true;
                  if (field.reportValidity()) void save(true);
                } finally {
                  field.required = required;
                }
              }}
            >
              Đặt lại mật khẩu
            </button>
          )}

          <button
            disabled={busy}
            type="submit"
            className="btn-primary"
            aria-label="Lưu tài khoản"
            style={{ backgroundColor: "#10b981", borderColor: "#10b981" }}
          >
            {account ? "Lưu tài khoản" : "Tạo tài khoản"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
