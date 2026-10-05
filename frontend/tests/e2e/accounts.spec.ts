import { test,expect, type Page } from "@playwright/test";
const temporary="test-password-fifteen-plus",changed="new-password-long-enough";
async function login(page:Page,username:string,password:string){await page.goto("/login");await page.getByLabel("Tên đăng nhập").fill(username);await page.getByLabel("Mật khẩu",{exact:true}).fill(password);await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();}
test("Admin panel creates user; forced change rotates cookie and reset disables second client",async({page,request,browser})=>{
  await request.post("http://api-test:8000/api/v1/_test/reset");await login(page,"browser-admin",temporary);await expect(page).toHaveURL(/accounts$/);
  await page.getByRole("button",{name:"Tạo tài khoản",exact:true}).click();const dialog=page.getByRole("dialog");await expect(dialog.getByLabel("Tên đăng nhập")).toBeFocused();
  await dialog.getByLabel("Tên đăng nhập").fill("browser-tech");await dialog.getByLabel("Họ tên").fill("Kỹ thuật viên mới");await dialog.getByLabel("Mật khẩu tạm").fill(temporary);await dialog.getByRole("button",{name:"Lưu tài khoản"}).click();await expect(dialog).not.toBeVisible();await expect(page.getByRole("row",{name:/browser-tech/})).toBeVisible();
  const second=await browser.newContext();const tech=await second.newPage();await login(tech,"browser-tech",temporary);await expect(tech).toHaveURL(/change-password$/);const before=(await second.cookies()).find(c=>c.name==="rag_session")!.value;
  const denied=await second.request.get("http://next-test:3000/api/v1/datasets");expect(denied.status()).toBe(403);
  await tech.getByLabel("Mật khẩu hiện tại").fill(temporary);await tech.getByLabel("Mật khẩu mới",{exact:true}).fill(changed);await tech.getByLabel("Nhập lại mật khẩu mới").fill(changed);await tech.getByRole("button",{name:"Đổi mật khẩu"}).click();await expect(tech).toHaveURL(/datasets$/);expect((await second.cookies()).find(c=>c.name==="rag_session")!.value).not.toBe(before);
  expect((await request.get("/api/v1/datasets",{headers:{Cookie:`rag_session=${before}`}})).status()).toBe(401);
  await page.getByRole("button",{name:"Chỉnh sửa browser-tech"}).click();await page.getByRole("dialog").getByLabel("Mật khẩu tạm").fill(temporary);await page.getByRole("button",{name:"Đặt lại mật khẩu",exact:true}).click();await expect(page.getByRole("dialog")).not.toBeVisible();await tech.reload();await expect(tech).toHaveURL(/login$/);
  await login(tech,"browser-tech",temporary);await expect(tech).toHaveURL(/change-password$/);
  await page.getByRole("button",{name:"Chỉnh sửa browser-tech"}).click();await page.getByRole("dialog").getByLabel("Đang hoạt động").uncheck();await page.getByRole("button",{name:"Lưu tài khoản"}).click();await expect(page.getByRole("dialog")).not.toBeVisible();await tech.reload();await expect(tech).toHaveURL(/login$/);await second.close();
});
