"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Account, Dataset, DatasetGrants, Page } from "@/lib/contracts";

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

export default function DatasetGrantPanel({
  csrf,
  onClose,
  onSaved,
}: {
  csrf: string;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const revision = useRef(0);
  const [users, setUsers] = useState<Account[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [target, setTarget] = useState("");
  const [committed, setCommitted] = useState<string[] | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");

  useEffect(() => {
    const el = dialog.current;
    const opener = document.activeElement as HTMLElement | null;
    el?.showModal();
    let active = true;

    const loadPages = async <T,>(path: string) => {
      const all: T[] = [];
      let page = 1;
      while (true) {
        const result = await api<Page<T>>(`${path}?page=${page}&page_size=100`);
        all.push(...result.items);
        if (all.length >= result.total) return all;
        page++;
      }
    };

    void Promise.all([loadPages<Account>("/admin/users"), loadPages<Dataset>("/datasets")])
      .then(([accounts, rows]) => {
        if (active) {
          setUsers(accounts.filter((a) => a.role === "technician"));
          setDatasets(rows);
        }
      })
      .catch((err) => {
        if (active) setError(err.message);
      });

    return () => {
      active = false;
      revision.current++;
      el?.close();
      opener?.focus();
    };
  }, []);

  const load = useCallback(async (id: string) => {
    const current = ++revision.current;
    setCommitted(null);
    setSelected([]);
    if (!id) return false;
    try {
      const state = await api<DatasetGrants>(`/admin/users/${id}/datasets`);
      if (current === revision.current) {
        setCommitted(state.dataset_ids);
        setSelected(state.dataset_ids);
        return true;
      }
    } catch (err) {
      if (current === revision.current)
        setError(err instanceof Error ? err.message : "Không thể tải quyền");
    }
    return false;
  }, []);

  const save = async () => {
    if (!committed || !target) return;
    setBusy(true);
    setError("");
    setSaved("");
    let failed = false;

    for (const dataset of datasets) {
      const before = committed.includes(dataset.id);
      const after = selected.includes(dataset.id);
      if (before === after) continue;
      try {
        await api(`/admin/users/${target}/datasets/${dataset.id}`, {
          method: after ? "PUT" : "DELETE",
          csrf,
        });
      } catch (err) {
        failed = true;
        setError(
          `Một số quyền chưa được lưu. ${err instanceof Error ? err.message : "Vui lòng thử lại"}`
        );
        break;
      }
    }

    try {
      const loaded = await load(target);
      await onSaved();
      if (!failed && loaded) setSaved("Đã lưu quyền Dataset");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể cập nhật trạng thái quyền");
    } finally {
      setBusy(false);
    }
  };

  const targetUser = users.find((u) => u.id === target);

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
      aria-labelledby="grants-title"
      aria-busy={busy}
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else onClose();
      }}
      style={{
        margin: "auto",
        maxWidth: 520,
        width: "92vw",
        borderRadius: "var(--radius-lg)",
        padding: 24,
        background: "#ffffff",
        border: "1px solid var(--border-subtle)",
        boxShadow: "var(--shadow-floating)",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 18,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <h2 id="grants-title" style={{ margin: 0, fontSize: 18, color: "var(--color-text-main)" }}>
            Phân quyền truy cập Dataset
          </h2>
          <span className="badge badge-pastel-green">Phân quyền</span>
        </div>
        <button
          type="button"
          aria-label="Đóng"
          onClick={onClose}
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

      {/* Technician Selector */}
      <div style={{ marginBottom: 12 }}>
        <label
          htmlFor="grant-user"
          style={{ display: "block", marginBottom: 6, fontWeight: 600, fontSize: 13 }}
        >
          Kỹ thuật viên
        </label>
        <select
          id="grant-user"
          value={target}
          disabled={busy}
          onChange={(e) => {
            setTarget(e.target.value);
            setError("");
            setSaved("");
            void load(e.target.value);
          }}
          style={{
            width: "100%",
            padding: "9px 12px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--border-subtle)",
            fontSize: 14,
          }}
        >
          <option value="">Chọn Kỹ thuật viên</option>
          {users.map((user) => (
            <option value={user.id} key={user.id}>
              {user.display_name} ({user.username})
            </option>
          ))}
        </select>
      </div>

      {/* Selected Technician Card */}
      {targetUser && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "10px 14px",
            borderRadius: "var(--radius-sm)",
            background: "var(--bg-app)",
            border: "1px solid var(--border-subtle)",
            marginBottom: 16,
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "var(--radius-full)",
              background: "var(--color-pastel-mint)",
              color: "var(--color-emerald-dark)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: 13,
              flexShrink: 0,
            }}
          >
            {getInitials(targetUser.display_name)}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontWeight: 600,
                fontSize: 14,
                color: "var(--color-text-main)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {targetUser.display_name}
            </div>
            <div className="muted" style={{ fontSize: 12 }}>
              @{targetUser.username}
            </div>
          </div>
          <span className="badge badge-pastel-green">Kỹ thuật viên</span>
        </div>
      )}

      {/* Dataset Checkbox List */}
      {target && committed === null ? (
        <div style={{ padding: "20px 0", textAlign: "center" }}>
          <p role="status" className="muted" style={{ margin: 0 }}>
            Đang tải quyền Dataset…
          </p>
        </div>
      ) : target && datasets.length === 0 ? (
        <div style={{ padding: "16px 0", textAlign: "center" }}>
          <p className="muted" style={{ margin: 0 }}>
            Chưa có Dataset để cấp quyền.
          </p>
        </div>
      ) : target && (
        <fieldset
          disabled={busy}
          style={{
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-sm)",
            padding: "14px 16px",
            margin: "0 0 16px",
            background: "#ffffff",
          }}
        >
          <legend
            style={{
              fontWeight: 600,
              fontSize: 13,
              color: "var(--color-text-main)",
              padding: "0 6px",
            }}
          >
            Dataset được cấp
          </legend>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 8,
              maxHeight: "36vh",
              overflowY: "auto",
              paddingRight: 2,
            }}
          >
            {datasets.map((dataset) => {
              const isChecked = selected.includes(dataset.id);
              return (
                <label
                  key={dataset.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "8px 12px",
                    borderRadius: "var(--radius-sm)",
                    border: `1px solid ${isChecked ? "var(--color-mint-border)" : "var(--border-divider)"}`,
                    backgroundColor: isChecked ? "var(--color-pastel-50)" : "#ffffff",
                    cursor: "pointer",
                    transition: "all 150ms ease",
                    margin: 0,
                  }}
                >
                  <input
                    type="checkbox"
                    style={{
                      width: "auto",
                      accentColor: "#10b981",
                      cursor: "pointer",
                    }}
                    checked={isChecked}
                    onChange={(e) => {
                      setSaved("");
                      setSelected((old) =>
                        e.target.checked
                          ? [...old, dataset.id]
                          : old.filter((id) => id !== dataset.id)
                      );
                    }}
                  />
                  {dataset.name}
                </label>
              );
            })}
          </div>
        </fieldset>
      )}

      {error && (
        <p className="error" role="alert" style={{ margin: "12px 0" }}>
          {error}
        </p>
      )}

      {saved && (
        <p
          role="status"
          style={{
            color: "var(--color-emerald-dark)",
            fontWeight: 600,
            fontSize: 14,
            margin: "12px 0",
          }}
        >
          {saved}
        </p>
      )}

      {/* Modal Footer */}
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: 8,
          marginTop: 20,
        }}
      >
        <button
          type="button"
          className="btn-secondary"
          disabled={busy}
          onClick={onClose}
        >
          Đóng
        </button>
        <button
          type="button"
          className="btn-primary"
          aria-label="Lưu quyền"
          style={{ backgroundColor: "#10b981", borderColor: "#10b981" }}
          disabled={busy || !target || committed === null}
          onClick={() => void save()}
        >
          {busy ? "Đang lưu…" : "Lưu phân quyền"}
        </button>
      </div>
    </dialog>
  );
}
