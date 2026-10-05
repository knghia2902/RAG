export class ApiError extends Error { constructor(public status: number, message: string) { super(message); } }
export async function api<T>(path: string, options: { method?: string; body?: unknown; csrf?: string } = {}): Promise<T> {
  const method = options.method ?? "GET";
  const response = await fetch(`/api/v1${path}`, { method, credentials: "same-origin", cache: "no-store", headers: method === "GET" ? {} : { "Content-Type": "application/json", "X-Requested-With": "RAG-Web", ...(options.csrf ? { "X-CSRF-Token": options.csrf } : {}) }, ...(method !== "GET" ? { body: JSON.stringify(options.body ?? {}) } : {}) });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (response.status === 401 && !path.endsWith("/login")) { window.dispatchEvent(new Event("session-expired")); }
    if (response.status===401 || (method==="GET"&&path.startsWith("/datasets")&&[403,404].includes(response.status))) { window.dispatchEvent(new Event("dataset-access-changed")); }
    throw new ApiError(response.status, typeof body.detail === "string" ? body.detail : "Không thể hoàn tất yêu cầu");
  }
  return response.status === 204 ? undefined as T : response.json();
}
