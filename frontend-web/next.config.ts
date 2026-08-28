import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Autorise l'accès au serveur de dev via 127.0.0.1 en plus de localhost
  // (utile en conteneur/CI où l'un ou l'autre peut être utilisé).
  allowedDevOrigins: ["localhost", "127.0.0.1"],
};

export default nextConfig;
