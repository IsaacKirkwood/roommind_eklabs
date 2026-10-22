import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    lib: {
      entry: resolve(import.meta.dirname, "src/house-status-card.ts"),
      name: "RoomMindHouseStatusCard",
      formats: ["iife"],
      fileName: () => "roommind-house-status-card.js",
    },
    outDir: "../custom_components/roommind_eklabs/frontend",
    emptyOutDir: false,
  },
});
