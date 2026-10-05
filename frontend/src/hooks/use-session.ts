"use client";
import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";

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
