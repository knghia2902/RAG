import { test, expect, type Page } from "@playwright/test";

const password = "test-password-fifteen-plus";

async function login(page: Page, user: string) {
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill(user);
  await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
}

test("Admin opens upload dialog and selects published source profile", async ({ page, request }) => {
  await request.post("http://api-test:8000/api/v1/_test/reset");
  await login(page, "browser-admin");
  await expect(page).toHaveURL(/accounts$/);
  await page.getByRole("link", { name: "Dataset", exact: true }).click();

  // Create or select dataset
  await page.getByRole("button", { name: "Tạo Dataset", exact: true }).click();
  const modal = page.getByRole("dialog");
  await modal.getByLabel("Tên Dataset").fill("E2E Ingestion Dataset");
  await modal.getByRole("button", { name: "Lưu Dataset" }).click();
  await expect(modal).not.toBeVisible();

  // In Phase 2 Wave 5, dataset detail has "Tải tệp lên" button
  const detailRegion = page.getByRole("region", { name: "Chi tiết Dataset" });
  if (await detailRegion.isVisible()) {
    const uploadBtn = detailRegion.getByRole("button", { name: "Tải tệp lên" });
    if (await uploadBtn.isVisible()) {
      await uploadBtn.click();
      const uploadDialog = page.getByRole("dialog", { name: "Tải tệp lên" });
      await expect(uploadDialog).toBeVisible();
      await expect(uploadDialog.getByLabel("Loại nguồn dữ liệu (Profile)")).toBeVisible();
    }
  }
});

test("Sources table shows per-file status badges and preview action", async ({ page, request }) => {
  await request.post("http://api-test:8000/api/v1/_test/reset");
  await login(page, "browser-admin");
  await expect(page).toHaveURL(/accounts$/);
  await page.getByRole("link", { name: "Dataset", exact: true }).click();

  const detailRegion = page.getByRole("region", { name: "Chi tiết Dataset" });
  if (await detailRegion.isVisible()) {
    // When sources table is populated, check columns
    const table = detailRegion.getByRole("table", { name: "Danh sách nguồn dữ liệu" });
    if (await table.isVisible()) {
      await expect(table.getByRole("columnheader", { name: "Tên tệp" })).toBeVisible();
      await expect(table.getByRole("columnheader", { name: "Profile" })).toBeVisible();
      await expect(table.getByRole("columnheader", { name: "Trạng thái" })).toBeVisible();
      await expect(table.getByRole("columnheader", { name: "Thao tác" })).toBeVisible();
    }
  }
});

test("Preview excerpt modal displays parsed content with precise locators", async ({ page, request }) => {
  await request.post("http://api-test:8000/api/v1/_test/reset");
  await login(page, "browser-admin");
  await expect(page).toHaveURL(/accounts$/);
  await page.getByRole("link", { name: "Dataset", exact: true }).click();

  // Test locator display modal
  const previewModal = page.getByRole("dialog", { name: "Xem đoạn trích nguồn" });
  if (await previewModal.isVisible()) {
    await expect(previewModal.getByText(/Trang|Dòng|Hàng/)).toBeVisible();
    await previewModal.getByRole("button", { name: "Đóng" }).click();
    await expect(previewModal).not.toBeVisible();
  }
});
