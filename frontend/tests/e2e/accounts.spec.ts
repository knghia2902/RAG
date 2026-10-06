import { test,expect, type Page } from "@playwright/test";
const temporary="short123",changed="newpass8";
async function login(page:Page,username:string,password:string){await page.goto("/login");await page.getByLabel("Tên đăng nhập").fill(username);const passwordField=page.getByLabel("Mật khẩu",{exact:true});await passwordField.fill("short77");expect(await passwordField.evaluate((field:HTMLInputElement)=>field.checkValidity())).toBe(false);await passwordField.fill(password);await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();}
for(const failedRequest of [false,true])test(`review CR-02 metadata save works after ${failedRequest?"failed API":"invalid empty"} reset`,async({page,request})=>{
  await request.post("http://api-test:8000/api/v1/_test/reset");await login(page,"browser-admin",temporary);await expect(page).toHaveURL(/accounts$/);
  await page.getByRole("button",{name:"Chỉnh sửa browser-admin"}).click();const panel=page.getByRole("dialog");
  if(failedRequest){await page.route("**/reset-password",route=>route.fulfill({status:503,contentType:"application/json",body:JSON.stringify({detail:"Reset unavailable"})}));await panel.getByLabel("Mật khẩu tạm").fill(temporary);}
  await panel.getByRole("button",{name:"Đặt lại mật khẩu",exact:true}).click();
  if(failedRequest)await expect(panel.getByRole("alert")).toHaveText("Reset unavailable");
  await expect(panel.getByLabel("Mật khẩu tạm")).toHaveValue("");
  await panel.getByLabel("Họ tên").fill("Metadata after reset");
  await panel.getByRole("button",{name:"Lưu tài khoản"}).click();
  await expect(panel).not.toBeVisible();await expect(page.getByRole("row",{name:/browser-admin/})).toContainText("Metadata after reset");
});
test("narrow viewport retains navigation, account table and accessible right panel",async({page,request})=>{
  await request.post("http://api-test:8000/api/v1/_test/reset");await page.setViewportSize({width:390,height:844});await login(page,"browser-admin",temporary);
  await expect(page).toHaveURL(/accounts$/);await expect(page.getByRole("table")).toBeVisible();
  await expect(page.getByRole("navigation",{name:"Điều hướng"})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.getByRole("button",{name:"Tạo tài khoản",exact:true}).click();const panel=page.getByRole("dialog");
  const bounds=await panel.boundingBox();expect(bounds).not.toBeNull();expect(bounds!.x).toBeGreaterThanOrEqual(0);expect(bounds!.x+bounds!.width).toBeLessThanOrEqual(390);
  await page.screenshot({path:"test-results/phase1-narrow.png",fullPage:true});
  await page.keyboard.press("Escape");await expect(panel).not.toBeVisible();await expect(page.getByRole("button",{name:"Tạo tài khoản",exact:true})).toBeFocused();
});
test("Admin panel creates user; forced change rotates cookie and reset disables second client",async({page,request,browser})=>{
  await request.post("http://api-test:8000/api/v1/_test/reset");await login(page,"browser-admin",temporary);await expect(page).toHaveURL(/accounts$/);
  await page.getByRole("button",{name:"Tạo tài khoản",exact:true}).click();const dialog=page.getByRole("dialog");await expect(dialog.getByLabel("Tên đăng nhập")).toBeFocused();
  await dialog.getByLabel("Tên đăng nhập").fill("browser-tech");await dialog.getByLabel("Họ tên").fill("Kỹ thuật viên mới");const temporaryField=dialog.getByLabel("Mật khẩu tạm");await temporaryField.fill("short77");expect(await temporaryField.evaluate((field:HTMLInputElement)=>field.checkValidity())).toBe(false);await temporaryField.fill(temporary);await dialog.getByRole("button",{name:"Lưu tài khoản"}).click();await expect(dialog).not.toBeVisible();await expect(page.getByRole("row",{name:/browser-tech/})).toBeVisible();
  const second=await browser.newContext();const tech=await second.newPage();await login(tech,"browser-tech",temporary);await expect(tech).toHaveURL(/change-password$/);const before=(await second.cookies()).find(c=>c.name==="rag_session")!.value;
  const oldCsrf=(await (await second.request.get("http://next-test:3000/api/v1/auth/session")).json()).csrf_token;
  const denied=await second.request.get("http://next-test:3000/api/v1/datasets");expect(denied.status()).toBe(403);
  await tech.getByLabel("Mật khẩu hiện tại").fill(temporary);const newPasswordField=tech.getByLabel("Mật khẩu mới",{exact:true});await newPasswordField.fill("short77");expect(await newPasswordField.evaluate((field:HTMLInputElement)=>field.checkValidity())).toBe(false);await newPasswordField.fill(changed);await tech.getByLabel("Nhập lại mật khẩu mới").fill(changed);await tech.getByRole("button",{name:"Đổi mật khẩu"}).click();await expect(tech).toHaveURL(/datasets$/);expect((await second.cookies()).find(c=>c.name==="rag_session")!.value).not.toBe(before);
  expect((await request.get("/api/v1/datasets",{headers:{Cookie:`rag_session=${before}`}})).status()).toBe(401);
  expect((await second.request.post("http://next-test:3000/api/v1/auth/activity",{data:{},headers:{Origin:"http://next-test:3000","X-Requested-With":"RAG-Web","X-CSRF-Token":oldCsrf}})).status()).toBe(403);
  await page.getByRole("button",{name:"Chỉnh sửa browser-tech"}).click();await page.getByRole("dialog").getByLabel("Mật khẩu tạm").fill(temporary);await page.getByRole("button",{name:"Đặt lại mật khẩu",exact:true}).click();await expect(page.getByRole("dialog")).not.toBeVisible();await tech.reload();await expect(tech).toHaveURL(/login$/);
  await login(tech,"browser-tech",temporary);await expect(tech).toHaveURL(/change-password$/);
  await page.getByRole("button",{name:"Chỉnh sửa browser-tech"}).click();await page.getByRole("dialog").getByLabel("Đang hoạt động").uncheck();await page.getByRole("button",{name:"Lưu tài khoản"}).click();await expect(page.getByRole("dialog")).not.toBeVisible();await tech.reload();await expect(tech).toHaveURL(/login$/);await second.close();
});
