"use client";
import Link from "next/link";
import { useWorkspaceSession } from "../layout";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Account, Page } from "@/lib/contracts";
import AccountPanel from "@/components/AccountPanel";

export default function Accounts() {
  const session = useWorkspaceSession();
  const [data, setData] = useState<Page<Account> | null>(null);
  const [panel, setPanel] = useState<Account | null | undefined>(undefined);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);

  const refresh = async () => {
    try {
      setData(await api<Page<Account>>(`/admin/users?page=${page}`));
      setError("");
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Không thể tải tài khoản");
    }
  };

  useEffect(() => {
    let active = true;
    if (session?.account.role === "admin") {
      api<Page<Account>>(`/admin/users?page=${page}`)
        .then((d) => {
          if (active) setData(d);
        })
        .catch((err) => {
          if (active) {
            setData(null);
            setError(err.message);
          }
        });
    }
    return () => {
      active = false;
    };
  }, [page, session?.account.role]);

  if (!session) return null;
  if (session.account.role !== "admin") {
    return (
      <div className="card" style={{ maxWidth: 500, margin: "40px auto", textAlign: "center" }}>
        <p role="alert" className="error">
          Bạn không có quyền quản trị tài khoản hệ thống.
        </p>
        <Link href="/datasets" className="btn-primary" style={{ display: "inline-block", marginTop: 12 }}>
          Mở Dataset
        </Link>
      </div>
    );
  }

  return (
    <>
      <div className="eyebrow">Quản trị hệ thống</div>
      <h1>Tài khoản</h1>

      <section className="card">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 12,
            marginBottom: 20,
          }}
        >
          <div>
            <h2 style={{ margin: "0 0 4px", fontSize: 20, color: "var(--color-text-main)" }}>
              Danh sách tài khoản người dùng
            </h2>
            <p className="muted" style={{ margin: 0, fontSize: 14 }}>
              {data ? `${data.total} tài khoản trong hệ thống` : "Đang tải dữ liệu…"}
            </p>
          </div>
          <button
            className="btn-primary"
            onClick={() => setPanel(null)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Tạo tài khoản
          </button>
        </div>

        {error && (
          <p role="alert" className="error" style={{ marginBottom: 16 }}>
            {error}
          </p>
        )}

        {!data ? (
          <p role="status" className="muted">
            Đang tải tài khoản…
          </p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table aria-label="Bảng tài khoản" style={{ minWidth: 680, marginBottom: 16 }}>
              <thead>
                <tr>
                  <th>Tên đăng nhập</th>
                  <th>Họ tên</th>
                  <th>Vai trò</th>
                  <th>Trạng thái</th>
                  <th>Ngày tạo</th>
                  <th style={{ textAlign: "right" }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((account) => (
                  <tr key={account.id}>
                    <td>
                      <div style={{ fontWeight: 600, color: "var(--color-text-main)" }}>
                        {account.username}
                      </div>
                    </td>
                    <td style={{ color: "var(--color-text-main)" }}>
                      {account.display_name}
                    </td>
                    <td>
                      {account.role === "admin" ? (
                        <span className="badge badge-pastel-slate">Quản trị viên</span>
                      ) : (
                        <span className="badge badge-pastel-green">Kỹ thuật viên</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        {account.active ? (
                          <span className="badge badge-pastel-green">Hoạt động</span>
                        ) : (
                          <span className="badge badge-pastel-rose">Vô hiệu hóa</span>
                        )}
                        {account.must_change_password && (
                          <span className="badge badge-pastel-amber" title="Phải đổi mật khẩu ở lần đăng nhập tới">
                            Đổi mật khẩu
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="muted" style={{ fontSize: 13 }}>
                      {new Date(account.created_at).toLocaleDateString("vi-VN")}
                    </td>
                    <td>
                      <div style={{ display: "flex", justifyContent: "flex-end" }}>
                        <button
                          className="btn-secondary"
                          aria-label={`Chỉnh sửa ${account.username}`}
                          onClick={() => setPanel(account)}
                          style={{
                            padding: "6px 12px",
                            fontSize: 13,
                            display: "inline-flex",
                            alignItems: "center",
                            gap: 4,
                          }}
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
                          >
                            <path d="M12 20h9" />
                            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                          </svg>
                          Chỉnh sửa
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: 12,
                marginTop: 8,
              }}
            >
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <button
                  className="btn-secondary"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  style={{ padding: "6px 14px", fontSize: 13 }}
                >
                  Trang trước
                </button>
                <span className="muted" style={{ fontSize: 13 }}>
                  Trang {page} / {Math.ceil(data.total / data.page_size) || 1}
                </span>
                <button
                  className="btn-secondary"
                  disabled={page * data.page_size >= data.total}
                  onClick={() => setPage(page + 1)}
                  style={{ padding: "6px 14px", fontSize: 13 }}
                >
                  Trang sau
                </button>
              </div>

              <div>
                <Link
                  href="/datasets"
                  style={{
                    fontSize: 14,
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4,
                    fontWeight: 500,
                  }}
                >
                  Mở không gian Dataset →
                </Link>
              </div>
            </div>
          </div>
        )}
      </section>

      {panel !== undefined && (
        <AccountPanel
          key={panel?.id ?? "new"}
          account={panel}
          csrf={session.csrf_token}
          onClose={() => setPanel(undefined)}
          onSaved={refresh}
        />
      )}
    </>
  );
}
