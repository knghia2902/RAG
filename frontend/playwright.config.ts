import { defineConfig } from "@playwright/test";
const baseURL=process.env.PLAYWRIGHT_BASE_URL;
if(baseURL!=="http://next-test:3000")throw new Error("E2E requires isolated next-test");
export default defineConfig({testDir:"./tests/e2e",fullyParallel:false,workers:1,retries:0,timeout:30000,use:{baseURL,browserName:"chromium",trace:"retain-on-failure"},reporter:"list"});
