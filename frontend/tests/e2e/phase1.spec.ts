import { test,expect } from "@playwright/test";
test("tracer: browser login persists digest, reads dataset, logout rejects replay",async({page,request,context})=>{
  expect(process.env.TEST_API_URL).toBe("http://api-test:8000");
  const fixture=await request.post("http://api-test:8000/api/v1/_test/reset");expect(fixture.ok()).toBeTruthy();
  const credentials=await fixture.json();
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill(credentials.username);
  await page.getByLabel("Mật khẩu",{exact:true}).fill(credentials.password);
  await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();
  await expect(page).toHaveURL(/\/accounts$/);
  await expect(page.getByRole("row",{name:/browser-admin/})).toBeVisible();
  const cookies=await context.cookies();const cookie=cookies.find(c=>c.name==="rag_session");expect(cookie).toBeDefined();expect(cookie?.httpOnly).toBe(true);expect(cookie?.sameSite).toBe("Strict");expect(cookie?.secure).toBe(false);expect(cookie?.path).toBe("/");
  const proof=await request.post("http://api-test:8000/api/v1/_test/proof",{data:{token:cookie!.value}});expect(await proof.json()).toMatchObject({session_exists:true,digest_only:true,dataset_exists:true,revoked:false});
  await page.getByRole("link",{name:"Dataset",exact:true}).click();await expect(page.getByRole("cell",{name:"Browser WMS",exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Đăng xuất",exact:true}).click();await expect(page).toHaveURL(/\/login$/);
  const replay=await request.get("/api/v1/datasets",{headers:{Cookie:`rag_session=${cookie!.value}`}});expect(replay.status()).toBe(401);
  const missingOrigin=await request.post("/api/v1/auth/login",{data:credentials});expect(missingOrigin.status()).toBe(403);
});
