import { test,expect } from "@playwright/test";
test("ui-smoke: real role landing, labelled panel, keyboard and logout",async({page,request})=>{
  const start=performance.now();
  const fixture=await request.post("http://api-test:8000/api/v1/_test/reset");expect(fixture.ok()).toBeTruthy();
  const credentials=await fixture.json();
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill(credentials.username);
  await page.getByLabel("Mật khẩu",{exact:true}).fill(credentials.password);
  await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();
  await expect(page).toHaveURL(/\/accounts$/);
  await expect(page.getByRole("navigation",{name:"Điều hướng"})).toBeVisible();
  await page.screenshot({path:"test-results/phase1-desktop.png",fullPage:true});
  const opener=page.getByRole("button",{name:"Tạo tài khoản",exact:true});await opener.focus();await page.keyboard.press("Enter");
  const panel=page.getByRole("dialog",{name:"Tạo tài khoản"});
  await expect(panel.getByLabel("Tên đăng nhập")).toBeFocused();
  await expect(panel).toHaveAttribute("aria-busy","false");
  await panel.getByRole("button",{name:"Đóng",exact:true}).focus();await page.keyboard.press("Tab");
  await expect(panel.getByLabel("Tên đăng nhập")).toBeFocused();
  await page.keyboard.press("Escape");await expect(panel).not.toBeVisible();await expect(opener).toBeFocused();
  await page.getByRole("button",{name:"Đăng xuất",exact:true}).click();await expect(page).toHaveURL(/\/login$/);
  const elapsed=performance.now()-start;console.log(`ui-smoke warm execution: ${elapsed.toFixed(0)}ms`);expect(elapsed).toBeLessThanOrEqual(30000);
});

test("passive browser polling preserves idle and exact idle/absolute cutoff clears content",async({page,request})=>{
  await page.clock.install();
  for(const kind of ["idle","absolute"]){
    await request.post("http://api-test:8000/api/v1/_test/reset");
    const clock=await request.post("http://api-test:8000/api/v1/_test/clock",{data:{offset_seconds:0}});expect(clock.ok()).toBeTruthy();
    await page.goto("/login");await page.getByLabel("Tên đăng nhập").fill("browser-admin");await page.getByLabel("Mật khẩu",{exact:true}).fill("test-password-fifteen-plus");await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();
    await expect(page).toHaveURL(/accounts$/);await page.getByRole("link",{name:"Dataset",exact:true}).click();await expect(page.getByRole("cell",{name:"Browser WMS",exact:true})).toBeVisible();
    const token=(await page.context().cookies()).find(c=>c.name==="rag_session")!.value;
    const before=await (await request.post("http://api-test:8000/api/v1/_test/session-time",{data:{token}})).json();
    let polls=0,heartbeats=0;const record=(request:import("@playwright/test").Request)=>{if(request.url().includes("/api/v1/datasets")&&request.method()==="GET")polls++;if(request.url().endsWith("/auth/activity"))heartbeats++;};page.on("request",record);
    await page.clock.runFor(15000);
    await expect.poll(()=>polls).toBeGreaterThanOrEqual(3);expect(heartbeats).toBe(0);page.off("request",record);
    const after=await (await request.post("http://api-test:8000/api/v1/_test/session-time",{data:{token}})).json();expect(after.last_activity_at).toBe(before.last_activity_at);
    // Test-only DB clock is controlled; no host-clock change or real long sleeps.
    const set=await request.post("http://api-test:8000/api/v1/_test/clock",{data:{token,cutoff:kind}});expect(set.ok()).toBeTruthy();
    await page.clock.runFor(5000);await expect(page).toHaveURL(/login$/);
    await expect(page.getByText("Browser WMS",{exact:true})).not.toBeVisible();
  }
  await request.post("http://api-test:8000/api/v1/_test/reset");
});
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
