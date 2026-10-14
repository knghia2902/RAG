"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Session } from "@/lib/contracts";

export default function Sidebar({session,onLogout,error}:{session:Session;onLogout:()=>Promise<void>;error:string}) {
  const path = usePathname();
  const links = session.account.role === "admin"
    ? [["/accounts", "Tài khoản"], ["/datasets", "Dataset"], ["/chat", "Hỏi đáp tri thức"], ["/incidents", "Phân tích sự cố"], ["/configuration", "Cấu hình"]]
    : [["/datasets", "Dataset"], ["/chat", "Hỏi đáp tri thức"], ["/incidents", "Phân tích sự cố"]];


  return <aside className="sidebar"><div className="brand">Logistics RAG</div><div>{session.account.display_name}<br/><small>{session.account.role==="admin"?"Admin":"Kỹ thuật viên"}</small></div><nav aria-label="Điều hướng">{links.map(([href,label])=><Link key={href} href={href} aria-current={path===href?"page":undefined}>{label}</Link>)}</nav><div className="status">Quản trị local · localhost</div><button onClick={onLogout}>Đăng xuất</button>{error&&<p role="alert">{error}</p>}</aside>;
}
