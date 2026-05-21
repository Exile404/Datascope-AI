import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output: bundles only the deps actually used at runtime.
  // Required for our slim Docker image (saves ~450MB).
  // Outputs to .next/standalone/ during `next build`.
  output: "standalone",

  // Allow images from the backend (signed URLs, charts, etc.)
  // Empty for now; add backend host when we wire image proxying.
  images: {
    remotePatterns: [],
  },
};

export default nextConfig;
