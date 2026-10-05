"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session } from "@/lib/contracts";
import { sessionDestination } from "@/hooks/use-session";
export default function Login() {
  const router = useRouter(); const [error,setError] = useState(""); const [busy,setBusy] = useState(false);
  return <main className="login"><div className="eyebrow">IT & Logistics · Local</div><h1>Đăng nhập</h1><form onSubmit={async e=>{e.preventDefault();setBusy(true);setError("");const data=new FormData(e.currentTarget);try{const s=await api<Session>("/auth/login",{method:"POST",body:{username:data.get("username"),password:data.get("password")}});router.replace(sessionDestination(s));}catch(err){setError(err instanceof Error?err.message:"Không thể đăng nhập");}finally{setBusy(false);}}}><label htmlFor="username">Tên đăng nhập</label><input id="username" name="username" autoComplete="username" required minLength={3} maxLength={64}/><label htmlFor="password">Mật khẩu</label><input id="password" name="password" type="password" autoComplete="current-password" required minLength={15} maxLength={128}/>{error&&<p role="alert" className="error">{error}</p>}<button disabled={busy} type="submit">{busy?"Đang đăng nhập…":"Đăng nhập"}</button></form><p className="muted">Dữ liệu lưu tại máy chạy Docker. Phần quản trị không cần cấu hình AI.</p></main>;
}
