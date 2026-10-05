import {test,expect,type Page} from "@playwright/test";
const password="test-password-fifteen-plus";
async function login(page:Page,user:string){await page.goto("/login");await page.getByLabel("Tên đăng nhập").fill(user);await page.getByLabel("Mật khẩu",{exact:true}).fill(password);await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();}
test("Admin grants per item and an open technician page reconciles grant and revocation",async({page,request,browser})=>{
  await request.post("http://api-test:8000/api/v1/_test/reset");await login(page,"browser-admin");await expect(page).toHaveURL(/accounts$/);
  const session=await (await page.request.get("/api/v1/auth/session")).json();
  const headers={Origin:"http://next-test:3000","X-Requested-With":"RAG-Web","X-CSRF-Token":session.csrf_token};
  const user=await (await page.request.post("/api/v1/admin/users",{data:{username:"grant-tech",display_name:"Grant Tech",role:"technician",temporary_password:password},headers})).json();
  await page.getByRole("link",{name:"Dataset",exact:true}).click();
  await page.getByRole("button",{name:"Tạo Dataset",exact:true}).click();const metadata=page.getByRole("dialog");await expect(metadata.getByLabel("Tên Dataset")).toBeFocused();
  await metadata.getByLabel("Tên Dataset").fill("Grant WMS");await metadata.getByLabel("Mô tả").fill("Nguồn giới hạn quyền");await metadata.getByRole("button",{name:"Lưu Dataset"}).click();await expect(metadata).not.toBeVisible();
  const datasets=await (await page.request.get("/api/v1/datasets")).json();const dataset=datasets.items.find((d:{name:string})=>d.name==="Grant WMS");
  const context=await browser.newContext();const tech=await context.newPage();await login(tech,"grant-tech");await expect(tech).toHaveURL(/change-password$/);
  await tech.getByLabel("Mật khẩu hiện tại").fill(password);await tech.getByLabel("Mật khẩu mới",{exact:true}).fill("changed-password-long-enough");await tech.getByLabel("Nhập lại mật khẩu mới").fill("changed-password-long-enough");await tech.getByRole("button",{name:"Đổi mật khẩu"}).click();await expect(tech).toHaveURL(/datasets$/);await expect(tech.getByText(/Liên hệ Admin/)).toBeVisible();
  await page.getByRole("button",{name:"Cấp quyền Dataset"}).click();const panel=page.getByRole("dialog");await panel.getByLabel("Kỹ thuật viên").selectOption(user.id);await expect(panel.getByLabel("Grant WMS",{exact:true})).not.toBeChecked();await panel.getByLabel("Grant WMS",{exact:true}).check();await panel.getByRole("button",{name:"Lưu quyền"}).click();await expect(panel.getByRole("status")).toHaveText("Đã lưu quyền Dataset");
  await expect(tech.getByRole("row",{name:/Grant WMS/})).toBeVisible({timeout:15000});await tech.getByRole("button",{name:"Xem Grant WMS"}).click();await expect(tech.getByRole("region",{name:"Chi tiết Dataset"})).toBeVisible();
  await panel.getByLabel("Grant WMS",{exact:true}).uncheck();await panel.getByRole("button",{name:"Lưu quyền"}).click();await expect(panel.getByRole("status")).toHaveText("Đã lưu quyền Dataset");
  expect((await context.request.get(`http://next-test:3000/api/v1/datasets/${dataset.id}`)).status()).toBe(404);
  await expect(tech.getByText(/Liên hệ Admin/)).toBeVisible({timeout:15000});await expect(tech.getByRole("region",{name:"Chi tiết Dataset"})).not.toBeVisible();await expect(tech.getByText("Nguồn giới hạn quyền")).not.toBeVisible();
  await page.route(`**/api/v1/admin/users/${user.id}/datasets/${dataset.id}`,async route=>{if(route.request().method()==="PUT")await route.fulfill({status:503,contentType:"application/json",body:JSON.stringify({detail:"Không thể lưu mục này"})});else await route.continue();});
  await panel.getByLabel("Browser WMS",{exact:true}).check();await panel.getByLabel("Grant WMS",{exact:true}).check();await panel.getByRole("button",{name:"Lưu quyền"}).click();await expect(panel.getByRole("alert")).toContainText("Một số quyền chưa được lưu");await expect(panel.getByLabel("Browser WMS",{exact:true})).toBeChecked();await expect(panel.getByLabel("Grant WMS",{exact:true})).not.toBeChecked();await expect(panel.getByText("Đã lưu quyền Dataset")).not.toBeVisible();
  await panel.getByRole("button",{name:"Đóng",exact:true}).click();await expect(page.getByRole("button",{name:"Cấp quyền Dataset"})).toBeFocused();await context.close();
});
