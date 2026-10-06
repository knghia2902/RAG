"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { useWorkspaceSession } from "../layout";
import { api } from "@/lib/api";

type ConfigurationStatus={database_ready:boolean;provider_configured:boolean};

export default function Configuration(){
  const session=useWorkspaceSession();
  const [status,setStatus]=useState<ConfigurationStatus|null>(null);
  const [error,setError]=useState("");const [request,setRequest]=useState(0);
  useEffect(()=>{
    let active=true;
    if(session?.account.role!=="admin")return;
    api<ConfigurationStatus>("/status").then(value=>{if(active)setStatus(value);}).catch(err=>{if(active){setStatus(null);setError(err instanceof Error?err.message:"Không thể tải trạng thái");}});
    return()=>{active=false;};
  },[session?.account.role,request]);
  const refresh=()=>{setStatus(null);setError("");setRequest(value=>value+1);};
  if(!session)return null;
  if(session.account.role!=="admin")return <p role="alert">Không đủ quyền. <Link href="/datasets">Mở Dataset</Link></p>;
  return <><div className="eyebrow">Quản trị</div><h1>Cấu hình</h1><section className="card" aria-label="Trạng thái cấu hình">
    {error?<><p role="alert" className="error">{error}</p><button onClick={refresh}>Thử lại</button></>:!status?<p role="status">Đang tải trạng thái…</p>:<><dl><dt>Database</dt><dd>{status.database_ready?"Sẵn sàng":"Chưa sẵn sàng"}</dd><dt>AI</dt><dd>{status.provider_configured?"Đã cấu hình AI":"Chưa cấu hình AI"}</dd></dl><p className="muted">Cấu hình tại máy chạy Docker bằng .env. Trạng thái AI chỉ xác nhận có cấu hình, chưa kiểm tra kết nối provider.</p><button onClick={refresh}>Làm mới trạng thái</button></>}
    <p><Link href="/datasets">Quay lại Dataset</Link></p>
  </section></>;
}
