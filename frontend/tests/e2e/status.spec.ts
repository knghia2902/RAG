import {test,expect,type Page} from "@playwright/test";
const password="test-password-fifteen-plus";
async function login(page:Page,user:string){await page.goto("/login");await page.getByLabel("Tên đăng nhập").fill(user);await page.getByLabel("Mật khẩu",{exact:true}).fill(password);await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();}
test("Admin sees safe no-key configuration and technician has no configuration authority",async({page,request,browser})=>{
  await request.post("http://api-test:8000/api/v1/_test/reset");await login(page,"browser-admin");await expect(page).toHaveURL(/accounts$/);
  await page.getByRole("link",{name:"Cấu hình",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Cấu hình",exact:true})).toBeVisible();
  await expect(page.getByText("Chưa cấu hình AI",{exact:true})).toBeVisible();
  await expect(page.getByText("Sẵn sàng",{exact:true})).toBeVisible();
  await expect(page.locator("input")).toHaveCount(0);
  await expect(page.getByRole("link",{name:"Cấu hình",exact:true})).toHaveAttribute("aria-current","page");
  const response=await page.request.get("/api/v1/status");expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({database_ready:true,provider_configured:false});
  await page.route("**/api/v1/status",route=>route.fulfill({status:503,contentType:"application/json",body:JSON.stringify({detail:"Không thể tải trạng thái"})}));
  await page.getByRole("button",{name:"Làm mới trạng thái"}).click();await expect(page.getByRole("region",{name:"Trạng thái cấu hình"}).getByRole("alert")).toContainText("Không thể tải trạng thái");
  await expect(page.getByText("Chưa cấu hình AI",{exact:true})).not.toBeVisible();
  await page.unroute("**/api/v1/status");await page.getByRole("button",{name:"Thử lại"}).click();await expect(page.getByText("Chưa cấu hình AI",{exact:true})).toBeVisible();
  await page.route("**/api/v1/status",route=>route.fulfill({status:403,contentType:"application/json",body:JSON.stringify({detail:"Quyền đã thay đổi"})}));
  await page.getByRole("button",{name:"Làm mới trạng thái"}).click();await expect(page.getByRole("region",{name:"Trạng thái cấu hình"}).getByRole("alert")).toContainText("Quyền đã thay đổi");await expect(page.getByText("Chưa cấu hình AI",{exact:true})).not.toBeVisible();
  await page.unroute("**/api/v1/status");await page.getByRole("button",{name:"Thử lại"}).click();await expect(page.getByText("Chưa cấu hình AI",{exact:true})).toBeVisible();
  await page.getByRole("link",{name:"Quay lại Dataset"}).click();await expect(page).toHaveURL(/datasets$/);await page.goBack();await expect(page).toHaveURL(/configuration$/);
  const session=await (await page.request.get("/api/v1/auth/session")).json();const headers={Origin:"http://next-test:3000","X-Requested-With":"RAG-Web","X-CSRF-Token":session.csrf_token};
  await page.request.post("/api/v1/admin/users",{data:{username:"status-tech",display_name:"Status Tech",role:"technician",temporary_password:password},headers});
  const context=await browser.newContext();const tech=await context.newPage();await login(tech,"status-tech");await expect(tech).toHaveURL(/change-password$/);
  await tech.getByLabel("Mật khẩu hiện tại").fill(password);await tech.getByLabel("Mật khẩu mới",{exact:true}).fill("changed-password-long-enough");await tech.getByLabel("Nhập lại mật khẩu mới").fill("changed-password-long-enough");await tech.getByRole("button",{name:"Đổi mật khẩu"}).click();await expect(tech).toHaveURL(/datasets$/);
  await expect(tech.getByRole("link",{name:"Cấu hình",exact:true})).toHaveCount(0);expect((await context.request.get("http://next-test:3000/api/v1/status")).status()).toBe(403);
  await tech.goto("/configuration");await expect(tech.getByRole("alert").filter({hasText:"Không đủ quyền"})).toBeVisible();await expect(tech.getByText("Chưa cấu hình AI",{exact:true})).not.toBeVisible();await context.close();
});
