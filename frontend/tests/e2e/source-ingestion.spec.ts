import { test, expect, type Page } from "@playwright/test";

const password = "test-password-fifteen-plus";

async function login(page: Page, user: string) {
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill(user);
  await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
}

test.describe("Source Lifecycle and Ingestion Workspace E2E", () => {
  test.beforeEach(async ({ request }) => {
    try {
      await request.post("http://api-test:8000/api/v1/_test/reset");
    } catch {
      // In offline or standalone test run without api-test container, route mocks will be used
    }
  });

  test("1. Admin opens upload dialog, selects published profile, previews schema and uploads log file", async ({
    page,
  }) => {
    // Mock routes for end-to-end predictability
    let uploaded = false;
    const mockSource = {
      id: "source-log-001",
      dataset_id: "dataset-wms-001",
      logical_filename: "system_audit.log",
      profile_id: "log",
      active_version_id: "ver-001",
      active_version_number: 1,
      status: "ready",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await page.route("**/api/v1/datasets*", async (route) => {
      const url = route.request().url();
      if (route.request().method() === "GET" && url.includes("/sources/profiles")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: "log",
              name: "Nhật ký hệ thống (Log)",
              description: "Nhật ký máy chủ và dịch vụ",
              supported_formats: [".log", ".txt", ".jsonl"],
              expected_fields: ["timestamp", "system", "severity"],
              optional_fields: ["trace_id", "message"],
            },
          ]),
        });
      }
      if (route.request().method() === "GET" && url.includes("/sources?")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            items: uploaded ? [mockSource] : [],
            total: uploaded ? 1 : 0,
            page: 1,
            page_size: 25,
          }),
        });
      }
      if (route.request().method() === "GET" && !url.includes("/sources")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            items: [{ id: "dataset-wms-001", name: "Browser WMS", description: "Kho trung tâm" }],
            total: 1,
            page: 1,
            page_size: 25,
          }),
        });
      }
      return route.continue();
    });

    await page.route("**/api/v1/admin/datasets/*/sources/upload", async (route) => {
      uploaded = true;
      return route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              filename: "system_audit.log",
              source_id: "source-log-001",
              version_number: 1,
              status: "ready",
              job_id: "job-001",
              is_duplicate: false,
              message: "Tải lên thành công",
            },
          ],
        }),
      });
    });

    await login(page, "browser-admin");
    await page.goto("/datasets");

    // Open dataset detail
    await page.getByRole("button", { name: "Xem Browser WMS" }).click();
    const detailRegion = page.getByRole("region", { name: "Chi tiết Dataset" });
    await expect(detailRegion).toBeVisible();

    // Verify initial empty state
    await expect(detailRegion.getByText("Chưa có nguồn dữ liệu")).toBeVisible();
    await expect(
      detailRegion.getByText("Tải tệp đầu tiên lên để bắt đầu quản lý dữ liệu trong Dataset này.")
    ).toBeVisible();

    // Click "Tải tệp lên" to open dialog
    await detailRegion.getByRole("button", { name: "Tải tệp lên" }).click();
    const uploadDialog = page.getByRole("dialog");
    await expect(uploadDialog).toBeVisible();
    await expect(uploadDialog.getByRole("heading", { name: "Tải tệp lên" })).toBeVisible();

    // Verify profile selector and schema details
    await expect(uploadDialog.getByLabel("Loại nguồn dữ liệu (Profile)")).toBeVisible();
    await expect(uploadDialog.getByText(/Trường bắt buộc: timestamp, system, severity/)).toBeVisible();

    // Select files and verify selection list
    const logContent = "2026-10-07T12:00:00Z [INFO] [TMS] status=DELIVERED trace_id=tr-102";
    await uploadDialog.locator("#upload-files").setInputFiles({
      name: "system_audit.log",
      mimeType: "text/plain",
      buffer: Buffer.from(logContent),
    });
    await expect(uploadDialog.getByText("system_audit.log")).toBeVisible();

    // Submit upload
    await uploadDialog.getByRole("button", { name: "Xác nhận tải lên" }).click();

    // Verify batch result presentation
    await expect(uploadDialog.getByText("Kết quả tải lên")).toBeVisible();
    await expect(uploadDialog.getByText("Sẵn sàng")).toBeVisible();
    await expect(uploadDialog.getByText("Tải lên thành công")).toBeVisible();

    // Close upload dialog
    await uploadDialog.getByRole("button", { name: "Đóng" }).click();
    await expect(uploadDialog).not.toBeVisible();

    // Verify table updated to ready state
    const table = detailRegion.getByRole("table", { name: "Danh sách nguồn dữ liệu" });
    await expect(table).toBeVisible();
    await expect(table.getByRole("columnheader", { name: "Tên tệp" })).toBeVisible();
    await expect(table.getByRole("columnheader", { name: "Profile" })).toBeVisible();
    await expect(table.getByRole("columnheader", { name: "Phiên bản" })).toBeVisible();
    await expect(table.getByRole("columnheader", { name: "Trạng thái" })).toBeVisible();
    await expect(table.getByRole("columnheader", { name: "Thao tác" })).toBeVisible();

    await expect(table.getByText("system_audit.log")).toBeVisible();
    await expect(table.getByText("v1 · đang dùng")).toBeVisible();
    await expect(table.getByText("Sẵn sàng")).toBeVisible();
  });

  test("2. Preview excerpt modal displays parsed content with precise format-specific locators", async ({
    page,
  }) => {
    const mockSource = {
      id: "source-preview-001",
      dataset_id: "dataset-wms-001",
      logical_filename: "sop_logistics.pdf",
      profile_id: "document",
      active_version_id: "ver-001",
      active_version_number: 1,
      status: "ready",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await page.route("**/api/v1/datasets*", async (route) => {
      const url = route.request().url();
      if (url.includes("/preview")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            source_id: "source-preview-001",
            version_number: 1,
            items: [
              {
                id: "chunk-01",
                position: 1,
                text: "Quy trình kiểm tra an toàn kho bãi trước giờ xuất kho.",
                locator: {
                  source_id: "source-preview-001",
                  source_version: 1,
                  page: 3,
                  section: "Chương II: An toàn",
                },
                metadata: { system: "WMS", category: "SOP" },
              },
            ],
            total: 1,
            page: 1,
            page_size: 25,
          }),
        });
      }
      if (url.includes("/sources?")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            items: [mockSource],
            total: 1,
            page: 1,
            page_size: 25,
          }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [{ id: "dataset-wms-001", name: "Browser WMS", description: "Kho trung tâm" }],
          total: 1,
          page: 1,
          page_size: 25,
        }),
      });
    });

    await login(page, "browser-admin");
    await page.goto("/datasets");
    await page.getByRole("button", { name: "Xem Browser WMS" }).click();

    // Click "Xem đoạn trích"
    const detailRegion = page.getByRole("region", { name: "Chi tiết Dataset" });
    await detailRegion.getByRole("button", { name: "Xem đoạn trích sop_logistics.pdf" }).click();

    // Verify Preview Modal
    const previewModal = page.getByRole("dialog");
    await expect(previewModal).toBeVisible();
    await expect(previewModal.getByRole("heading", { name: "sop_logistics.pdf" })).toBeVisible();
    await expect(previewModal.getByText("v1 · đang dùng")).toBeVisible();
    await expect(previewModal.getByText("Tài liệu chung")).toBeVisible();

    // Verify format-specific locator tags
    await expect(previewModal.getByText(/Trang 3/)).toBeVisible();
    await expect(previewModal.getByText(/Mục: Chương II: An toàn/)).toBeVisible();
    await expect(
      previewModal.getByText("Quy trình kiểm tra an toàn kho bãi trước giờ xuất kho.")
    ).toBeVisible();

    // Close preview modal
    await previewModal.getByRole("button", { name: "Đóng" }).click();
    await expect(previewModal).not.toBeVisible();
  });

  test("3. Permitted Technician can view sources and excerpts but CANNOT see Admin upload/mutation controls", async ({
    page,
  }) => {
    const mockSource = {
      id: "source-tech-001",
      dataset_id: "dataset-wms-001",
      logical_filename: "inventory.csv",
      profile_id: "operations_table",
      active_version_id: "ver-001",
      active_version_number: 1,
      status: "ready",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    // Mock session as technician
    await page.route("**/api/v1/auth/session", async (route) => {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          account: {
            id: "user-tech-01",
            username: "browser-tech",
            display_name: "Technician User",
            role: "technician",
            active: true,
            must_change_password: false,
            created_at: new Date().toISOString(),
          },
          csrf_token: "mock-csrf-tech",
        }),
      });
    });

    await page.route("**/api/v1/datasets*", async (route) => {
      const url = route.request().url();
      if (url.includes("/preview")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            source_id: "source-tech-001",
            version_number: 1,
            items: [
              {
                id: "row-01",
                position: 1,
                text: "SKU-9901 | Pallet A | Status: AVAILABLE",
                locator: {
                  source_id: "source-tech-001",
                  source_version: 1,
                  sheet: "Sheet1",
                  row: 5,
                },
                metadata: { sku: "SKU-9901" },
              },
            ],
            total: 1,
            page: 1,
            page_size: 25,
          }),
        });
      }
      if (url.includes("/sources?")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            items: [mockSource],
            total: 1,
            page: 1,
            page_size: 25,
          }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [{ id: "dataset-wms-001", name: "Permitted WMS", description: "Kho được cấp" }],
          total: 1,
          page: 1,
          page_size: 25,
        }),
      });
    });

    await page.goto("/datasets");
    await page.getByRole("button", { name: "Xem Permitted WMS" }).click();

    const detailRegion = page.getByRole("region", { name: "Chi tiết Dataset" });
    await expect(detailRegion).toBeVisible();

    // Verify technician can see "Xem đoạn trích"
    await expect(
      detailRegion.getByRole("button", { name: "Xem đoạn trích inventory.csv" })
    ).toBeVisible();

    // CRITICAL: Technician MUST NOT see admin controls
    await expect(detailRegion.getByRole("button", { name: "Tải tệp lên" })).not.toBeVisible();
    await expect(detailRegion.getByRole("button", { name: "Thử lại" })).not.toBeVisible();
    await expect(detailRegion.getByRole("button", { name: "Nạp lại nguồn" })).not.toBeVisible();
    await expect(detailRegion.getByRole("button", { name: "Xóa nguồn" })).not.toBeVisible();

    // Technician opens excerpt preview
    await detailRegion.getByRole("button", { name: "Xem đoạn trích inventory.csv" }).click();
    const previewModal = page.getByRole("dialog");
    await expect(previewModal).toBeVisible();
    await expect(previewModal.getByText(/Sheet: Sheet1, Hàng: 5/)).toBeVisible();
    await previewModal.getByRole("button", { name: "Đóng" }).click();
  });

  test("4. Admin deletes source with confirmation dialog and source is removed from workspace", async ({
    page,
  }) => {
    let deleted = false;
    const mockSource = {
      id: "source-del-001",
      dataset_id: "dataset-wms-001",
      logical_filename: "obsolete_sop.txt",
      profile_id: "document",
      active_version_id: "ver-001",
      active_version_number: 1,
      status: "ready",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await page.route("**/api/v1/datasets*", async (route) => {
      const url = route.request().url();
      if (url.includes("/sources?")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            items: deleted ? [] : [mockSource],
            total: deleted ? 0 : 1,
            page: 1,
            page_size: 25,
          }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [{ id: "dataset-wms-001", name: "Browser WMS", description: "Kho trung tâm" }],
          total: 1,
          page: 1,
          page_size: 25,
        }),
      });
    });

    await page.route("**/api/v1/admin/datasets/*/sources/*", async (route) => {
      if (route.request().method() === "DELETE") {
        deleted = true;
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ message: "Đã xóa nguồn dữ liệu thành công" }),
        });
      }
      return route.continue();
    });

    await login(page, "browser-admin");
    await page.goto("/datasets");
    await page.getByRole("button", { name: "Xem Browser WMS" }).click();

    const detailRegion = page.getByRole("region", { name: "Chi tiết Dataset" });
    await expect(detailRegion.getByText("obsolete_sop.txt")).toBeVisible();

    // Click "Xóa nguồn" button
    await detailRegion.getByRole("button", { name: "Xóa nguồn" }).click();

    // Verify confirmation modal
    const deleteModal = page.getByRole("dialog");
    await expect(deleteModal).toBeVisible();
    await expect(
      deleteModal.getByText(/Xóa nguồn “obsolete_sop.txt”\? Nguồn sẽ không còn hiển thị/)
    ).toBeVisible();

    // Click "Giữ nguồn" first -> modal closes, source still present
    await deleteModal.getByRole("button", { name: "Giữ nguồn" }).click();
    await expect(deleteModal).not.toBeVisible();
    await expect(detailRegion.getByText("obsolete_sop.txt")).toBeVisible();

    // Click "Xóa nguồn" again, then confirm delete
    await detailRegion.getByRole("button", { name: "Xóa nguồn" }).click();
    await deleteModal.getByRole("button", { name: "Xóa nguồn" }).click();
    await expect(deleteModal).not.toBeVisible();

    // Verify source disappeared and empty state rendered
    await expect(detailRegion.getByText("Chưa có nguồn dữ liệu")).toBeVisible();
  });

  test("5. Diagnostic error dialog shows detailed row and reason when ingestion fails", async ({
    page,
  }) => {
    const failedSource = {
      id: "source-fail-001",
      dataset_id: "dataset-wms-001",
      logical_filename: "invalid_orders.csv",
      profile_id: "operations_table",
      active_version_id: null,
      active_version_number: null,
      status: "failed",
      error_message: "Xác thực lược đồ thất bại (Hàng 2: thiếu trường entity_id)",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await page.route("**/api/v1/datasets*", async (route) => {
      const url = route.request().url();
      if (url.includes("/sources?")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            items: [failedSource],
            total: 1,
            page: 1,
            page_size: 25,
          }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [{ id: "dataset-wms-001", name: "Browser WMS", description: "Kho trung tâm" }],
          total: 1,
          page: 1,
          page_size: 25,
        }),
      });
    });

    await login(page, "browser-admin");
    await page.goto("/datasets");
    await page.getByRole("button", { name: "Xem Browser WMS" }).click();

    const detailRegion = page.getByRole("region", { name: "Chi tiết Dataset" });
    await expect(detailRegion.getByText("Thất bại")).toBeVisible();
    await expect(detailRegion.getByRole("button", { name: "Thử lại" })).toBeVisible();

    // Click "Chi tiết lỗi"
    await detailRegion.getByRole("button", { name: "Chi tiết lỗi" }).click();

    const diagModal = page.getByRole("dialog");
    await expect(diagModal).toBeVisible();
    await expect(
      diagModal.getByText(
        "Không thể xử lý tệp này. Mở chi tiết để xem dòng/trường và nguyên nhân; sửa tệp rồi tải lại, hoặc chọn Thử lại nếu đây là lỗi tạm thời."
      )
    ).toBeVisible();
    await expect(diagModal.getByText(/Hàng 2: thiếu trường entity_id/)).toBeVisible();

    await diagModal.getByRole("button", { name: "Đóng" }).click();
    await expect(diagModal).not.toBeVisible();
  });
});
