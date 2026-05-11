import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  tanstackStart: {
    server: {
      entry: "server",
    },
  },

  vite: {
    server: {
      host: "0.0.0.0",
      port: 8080,
      allowedHosts: [
        "ec2-100-31-52-198.compute-1.amazonaws.com",
      ],
    },
  },
});