import type { NextConfig } from "next";
const target = process.env.API_TARGET ?? "http://backend:8000";
if (!["http://backend:8000", "http://api-test:8000"].includes(target)) throw new Error("Invalid API_TARGET");
const config: NextConfig = {
  async rewrites() { return [{ source: "/api/v1/:path*", destination: `${target}/api/v1/:path*` }]; },
  async headers() { return [{ source: "/:path*", headers: [{ key: "X-Content-Type-Options", value: "nosniff" }, { key: "Referrer-Policy", value: "same-origin" }, { key: "X-Frame-Options", value: "DENY" }, { key: "Cache-Control", value: "no-store" }] }]; },
};
export default config;
