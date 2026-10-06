"use client";
import Sidebar from "@/components/Sidebar";
import { useEffect, useState, createContext, useContext } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session } from "@/lib/contracts";
import { useSessionActivity } from "@/hooks/use-session";
const SessionContext=createContext<Session|null>(null);
export const useWorkspaceSession=()=>useContext(SessionContext);
export default function Workspace({children}:{children:React.ReactNode}) {
  const router=useRouter(); const [session,setSession]=useState<Session|null>(null); const [error,setError]=useState("");
  useSessionActivity(session?.csrf_token);
  useEffect(()=>{let active=true;api<Session>("/auth/session").then(s=>{if(active){if(s.account.must_change_password)router.replace("/change-password");else setSession(s);}}).catch(()=>router.replace("/login"));const expired=()=>{setSession(null);router.replace("/login");};window.addEventListener("session-expired",expired);return()=>{active=false;window.removeEventListener("session-expired",expired);};},[router]);
  if(!session)return <main className="main" role="status">Đang kiểm tra phiên đăng nhập…</main>;
  return <SessionContext.Provider value={session}><div className="shell"><Sidebar session={session} error={error} onLogout={async()=>{try{await api("/auth/logout",{method:"POST",csrf:session.csrf_token});setSession(null);router.replace("/login");}catch(err){setError(err instanceof Error?err.message:"Không thể đăng xuất");}}}/><main className="main">{children}</main></div></SessionContext.Provider>;
}
