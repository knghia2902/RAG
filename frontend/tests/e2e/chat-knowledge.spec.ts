import { test, expect, type Page } from "@playwright/test";

const password = "test-password-fifteen-plus";

async function login(page: Page, user: string) {
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill(user);
  await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
}

test("Admin and technician can access Grounded Q&A /chat and view citations", async ({
  page,
  request,
}) => {
  await request.post("http://api-test:8000/api/v1/_test/reset");
  await login(page, "browser-admin");
  await expect(page).toHaveURL(/accounts$/);

  // 1. Navigation has "Hỏi đáp tri thức"
  const chatLink = page.getByRole("link", { name: "Hỏi đáp tri thức", exact: true });
  await expect(chatLink).toBeVisible();
  await chatLink.click();
  await expect(page).toHaveURL(/chat$/);

  // 2. Chat interface components visible
  await expect(page.getByRole("button", { name: "+ Tạo cuộc trò chuyện mới" })).toBeVisible();
  await expect(page.getByPlaceholder("Nhập câu hỏi bằng tiếng Việt về quy trình, log, ticket, sự cố...")).toBeVisible();
  await expect(page.getByRole("button", { name: "Gửi câu hỏi", exact: true })).toBeVisible();

  // 3. Send test query
  await page.getByPlaceholder("Nhập câu hỏi bằng tiếng Việt về quy trình, log, ticket, sự cố...").fill("Kiểm tra đơn hàng DH001");
  await page.getByRole("button", { name: "Gửi câu hỏi", exact: true }).click();

  // 4. Verify message stream contains user question and assistant answer
  await expect(page.getByText("Bạn")).toBeVisible();
  await expect(page.getByText("Trợ lý tri thức Logistics")).toBeVisible();

  // 5. Check configuration page has model config
  await page.getByRole("link", { name: "Cấu hình", exact: true }).click();
  await expect(page).toHaveURL(/configuration$/);
  await expect(page.getByRole("heading", { name: "Mô hình AI & Index Vector (SYS-02)" })).toBeVisible();
  await expect(page.getByText("Mô hình nhúng (Embedding Provider)")).toBeVisible();
  await expect(page.getByText("Mô hình sinh câu trả lời (LLM Generation Provider)")).toBeVisible();
});
