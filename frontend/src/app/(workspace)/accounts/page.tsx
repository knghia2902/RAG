"use client";
import Link from "next/link";
import { useWorkspaceSession } from "../layout";
export default function Accounts(){const session=useWorkspaceSession();if(!session)return null;if(session.account.role!=="admin")return <p role="alert">Không đủ quyền. <Link href="/datasets">Mở Dataset</Link></p>;return <><div className="eyebrow">Quản trị</div><h1>Tài khoản</h1><section className="card"><h2>Tài khoản đang đăng nhập</h2><table><thead><tr><th>Tên đăng nhập</th><th>Họ tên</th><th>Vai trò</th></tr></thead><tbody><tr><td>{session.account.username}</td><td>{session.account.display_name}</td><td>Admin</td></tr></tbody></table><p><Link href="/datasets">Mở không gian Dataset →</Link></p></section></>;}
