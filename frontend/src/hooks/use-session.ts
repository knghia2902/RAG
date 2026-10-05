"use client";
import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import type { Session } from "@/lib/contracts";

export function sessionDestination(session: Session) {
  return session.account.must_change_password ? "/change-password" : session.account.role === "admin" ? "/accounts" : "/datasets";
}

// Only real visible user interaction renews idle; no timer-based heartbeat.
export function useSessionActivity(csrf: string | undefined) {
  const path = usePathname();
  const lastSent = useRef(0);
  useEffect(() => {
    if (!csrf) return;
    const touch = (event?: Event) => {
      if (document.visibilityState !== "visible" || (event && !event.isTrusted)) return;
      const now = Date.now();
      if (now - lastSent.current < 60000) return;
      lastSent.current = now;
      void api("/auth/activity", { method: "POST", csrf }).catch(() => {});
    };
    touch(); // Navigation into an authenticated visible page counts as activity.
    for (const name of ["pointerdown", "keydown"]) document.addEventListener(name, touch, { passive: true });
    return () => { for (const name of ["pointerdown", "keydown"]) document.removeEventListener(name, touch); };
  }, [csrf, path]);
}

// Passive reads reconcile current scope without sending activity heartbeats.
export function useDatasetRefresh(refresh:()=>Promise<void>,clear:()=>void) {
  const path=usePathname();
  useEffect(()=>{
    const reconcile=()=>{if(document.visibilityState==="visible")void refresh();};
    const rejected=()=>{clear();};
    const timer=window.setInterval(reconcile,5000);
    window.addEventListener("focus",reconcile);document.addEventListener("visibilitychange",reconcile);
    window.addEventListener("dataset-access-changed",rejected);
    return()=>{window.clearInterval(timer);window.removeEventListener("focus",reconcile);document.removeEventListener("visibilitychange",reconcile);window.removeEventListener("dataset-access-changed",rejected);};
  },[refresh,clear,path]);
}
