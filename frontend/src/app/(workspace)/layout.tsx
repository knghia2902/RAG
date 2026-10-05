"use client";
import Link from "next/link";
import { useEffect, useState, createContext, useContext } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session } from "@/lib/contracts";
const SessionContext=createContext<Session|null>(null);
export const useWorkspaceSession=()=>useContext(SessionContext);
export default function Workspace({children}:{children:React.ReactNode}) {
  const router=useRouter(); const [session,setSession]=useState<Session|null>(null); const [error,setError]=useState("");
  useEffect(()=>{let active=true;api<Session>("/auth/session").then(s=>{if(active)setSession(s);}).catch(()=>router.replace("/login"));const expired=()=>{setSession(null);router.replace("/login");};window.addEventListener("session-expired",expired);return()=>{active=false;window.removeEventListener("session-expired",expired);};},[router]);
  if(!session)return <main className="main" role="status">Đang kiểm tra phiên đăng nhập…</main>;
  return <SessionContext.Provider value={session}><div className="shell"><aside className="sidebar"><div className="brand">Logistics RAG</div><div>{session.account.display_name}<br/><small>{session.account.role==="admin"?"Admin":"Kỹ thuật viên"}</small></div><nav aria-label="Điều hướng">{session.account.role==="admin"&&<Link href="/accounts">Tài khoản</Link>}<Link href="/datasets">Dataset</Link></nav><div className="status">Quản trị local · localhost</div><button onClick={async()=>{try{await api("/auth/logout",{method:"POST",csrf:session.csrf_token});setSession(null);router.replace("/login");}catch(err){setError(err instanceof Error?err.message:"Không thể đăng xuất");}}}>Đăng xuất</button>{error&&<p role="alert">{error}</p>}</aside><main className="main">{children}</main></div></SessionContext.Provider>;
}
