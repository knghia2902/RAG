import {test,expect,type Page} from "@playwright/test";
const password="test-password-fifteen-plus";
async function login(page:Page,user:string){await page.goto("/login");await page.getByLabel("Tên đăng nhập").fill(user);await page.getByLabel("Mật khẩu",{exact:true}).fill(password);await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();}
test("review CR-03 busy metadata save blocks Escape and finishes before reopening",async({page,request})=>{
  await request.post("http://api-test:8000/api/v1/_test/reset");await login(page,"browser-admin");await expect(page).toHaveURL(/accounts$/);await page.getByRole("link",{name:"Dataset",exact:true}).click();
  let release!:()=>void;const held=new Promise<void>(resolve=>{release=resolve;});let entered!:()=>void;const pending=new Promise<void>(resolve=>{entered=resolve;});
  await page.route("**/api/v1/admin/datasets",async route=>{if(route.request().method()!=="POST")return route.continue();const response=await route.fetch();entered();await held;await route.fulfill({response});});
  try{await page.getByRole("button",{name:"Tạo Dataset",exact:true}).click();const panel=page.getByRole("dialog");await panel.getByLabel("Tên Dataset").fill("Held metadata");await panel.getByRole("button",{name:"Lưu Dataset"}).click();await pending;await page.keyboard.press("Escape");await expect(panel).toBeVisible();await expect(panel).toHaveAttribute("aria-busy","true");release();await expect(panel).not.toBeVisible();await page.getByRole("button",{name:"Tạo Dataset",exact:true}).click();await panel.getByLabel("Tên Dataset").fill("New unsaved edits");await expect(panel.getByLabel("Tên Dataset")).toHaveValue("New unsaved edits");}finally{release();}
});
test("review CR-03 obsolete metadata completion cannot dismiss a replacement dialog",async({page,request})=>{
  await request.post("http://api-test:8000/api/v1/_test/reset");await login(page,"browser-admin");await expect(page).toHaveURL(/accounts$/);await page.getByRole("link",{name:"Dataset",exact:true}).click();
  let release!:()=>void;const held=new Promise<void>(resolve=>{release=resolve;});let entered!:()=>void;const pending=new Promise<void>(resolve=>{entered=resolve;});
  await page.route("**/api/v1/admin/datasets",async route=>{if(route.request().method()!=="POST")return route.continue();const response=await route.fetch();entered();await held;await route.fulfill({response});});
  try{await page.getByRole("button",{name:"Tạo Dataset",exact:true}).click();const panel=page.getByRole("dialog");await panel.getByLabel("Tên Dataset").fill("Obsolete save");await panel.getByRole("button",{name:"Lưu Dataset"}).click();await pending;await page.evaluate(()=>window.dispatchEvent(new Event("dataset-access-changed")));await expect(panel).not.toBeVisible();await page.getByRole("button",{name:"Tạo Dataset",exact:true}).click();await panel.getByLabel("Tên Dataset").fill("Replacement edits");const completed=page.waitForResponse(response=>response.url().endsWith("/admin/datasets")&&response.request().method()==="POST");release();await completed;await expect(panel).toBeVisible();await expect(panel.getByLabel("Tên Dataset")).toHaveValue("Replacement edits");await expect(page.getByRole("row",{name:/Obsolete save/})).toBeVisible({timeout:15000});await expect(panel.getByLabel("Tên Dataset")).toHaveValue("Replacement edits");}finally{release();}
});
for(const listFirst of [true,false])test(`review CR-04 authorized detail survives passive list response ${listFirst?"before":"after"} detail`,async({page,request})=>{
  await request.post("http://api-test:8000/api/v1/_test/reset");await login(page,"browser-admin");await expect(page).toHaveURL(/accounts$/);await page.getByRole("link",{name:"Dataset",exact:true}).click();await expect(page.getByRole("button",{name:"Xem Browser WMS"})).toBeVisible();
  let releaseList!:()=>void,releaseDetail!:()=>void,listEntered!:()=>void,detailEntered!:()=>void;
  const heldList=new Promise<void>(r=>{releaseList=r;}),heldDetail=new Promise<void>(r=>{releaseDetail=r;}),listPending=new Promise<void>(r=>{listEntered=r;}),detailPending=new Promise<void>(r=>{detailEntered=r;});
  await page.route("**/api/v1/datasets?*",async route=>{const response=await route.fetch();listEntered();await heldList;await route.fulfill({response});});
  await page.route(/\/api\/v1\/datasets\/[0-9a-f-]+$/,async route=>{const response=await route.fetch();detailEntered();await heldDetail;await route.fulfill({response});});
  try{await page.evaluate(()=>window.dispatchEvent(new Event("focus")));await listPending;await page.getByRole("button",{name:"Xem Browser WMS"}).click();await detailPending;
    const detail=page.getByRole("region",{name:"Chi tiết Dataset"});
    if(listFirst){const response=page.waitForResponse(r=>r.url().includes("/datasets?")&&r.request().method()==="GET");releaseList();await response;await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));releaseDetail();}else{releaseDetail();await expect(detail).toBeVisible();releaseList();}
    await expect(detail).toBeVisible();await expect(detail).toContainText("Browser WMS");
  }finally{releaseList();releaseDetail();}
});
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
  await expect(panel).toHaveAttribute("aria-busy","false");await panel.getByRole("button",{name:"Đóng",exact:true}).focus();await page.keyboard.press("Tab");await expect(panel.getByLabel("Kỹ thuật viên")).toBeFocused();
  await page.keyboard.press("Escape");await expect(panel).not.toBeVisible();await expect(page.getByRole("button",{name:"Cấp quyền Dataset"})).toBeFocused();await context.close();
});
