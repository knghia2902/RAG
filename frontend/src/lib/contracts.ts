export type Account = { id: string; username: string; display_name: string; role: "admin" | "technician"; active: boolean; must_change_password: boolean; created_at: string };
export type Session = { account: Account; csrf_token: string };
export type Dataset = { id: string; name: string; description: string; created_at: string };
export type Page<T> = { items: T[]; total: number; page: number; page_size: number };
