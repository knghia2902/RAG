"use client";
import Link from "next/link";
import { useWorkspaceSession } from "../layout";
import { useEffect,useState } from "react";
import { api } from "@/lib/api";
import type { Account,Page } from "@/lib/contracts";
import AccountPanel from "@/components/AccountPanel";
export default function Accounts(){
  const session=useWorkspaceSession();const [data,setData]=useState<Page<Account>|null>(null);const [panel,setPanel]=useState<Account|null|undefined>(undefined);const [error,setError]=useState("");const [page,setPage]=useState(1);
  const refresh=async()=>{try{setData(await api<Page<Account>>(`/admin/users?page=${page}`));setError("");}catch(err){setData(null);setError(err instanceof Error?err.message:"Không thể tải tài khoản");}};
  useEffect(()=>{let active=true;if(session?.account.role==="admin")api<Page<Account>>(`/admin/users?page=${page}`).then(d=>{if(active)setData(d);}).catch(err=>{if(active){setData(null);setError(err.message);}});return()=>{active=false;};},[page,session?.account.role]);
  if(!session)return null;if(session.account.role!=="admin")return <p role="alert">Không đủ quyền. <Link href="/datasets">Mở Dataset</Link></p>;
  return <><div className="eyebrow">Quản trị</div><h1>Tài khoản</h1><section className="card"><button onClick={()=>setPanel(null)}>Tạo tài khoản</button>{error&&<p role="alert" className="error">{error}</p>}{!data?<p role="status">Đang tải tài khoản…</p>:<><p className="muted">{data.total} tài khoản</p><table><thead><tr><th>Tên đăng nhập</th><th>Họ tên</th><th>Vai trò</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{data.items.map(account=><tr key={account.id}><td>{account.username}</td><td>{account.display_name}</td><td>{account.role==="admin"?"Admin":"Kỹ thuật viên"}</td><td>{account.active?"Hoạt động":"Vô hiệu hóa"}{account.must_change_password?" · Phải đổi mật khẩu":""}</td><td><button aria-label={`Chỉnh sửa ${account.username}`} onClick={()=>setPanel(account)}>Chỉnh sửa</button></td></tr>)}</tbody></table><button disabled={page<=1} onClick={()=>setPage(page-1)}>Trang trước</button> <span>Trang {page}</span> <button disabled={page*data.page_size>=data.total} onClick={()=>setPage(page+1)}>Trang sau</button></>}<p><Link href="/datasets">Mở không gian Dataset →</Link></p></section>{panel!==undefined&&<AccountPanel key={panel?.id??"new"} account={panel} csrf={session.csrf_token} onClose={()=>setPanel(undefined)} onSaved={refresh}/>}</>;
}
