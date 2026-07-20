import type { NextConfig } from "next";

const isDevelopment = process.env.NODE_ENV === "development";
const apiProxy = process.env.API_PROXY_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = isDevelopment
  ? {
      async rewrites() {
        return [{ source: "/api/:path*", destination: `${apiProxy}/api/:path*` }];
      },
    }
  : {
      output: "export",
      trailingSlash: true,
    };

export default nextConfig;
