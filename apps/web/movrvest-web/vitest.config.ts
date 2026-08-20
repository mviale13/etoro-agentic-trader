import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

/**
 * The `@/` alias Next resolves from tsconfig paths. Vitest needs it
 * told explicitly, otherwise any test that reaches a module importing
 * `@/...` fails to load rather than failing an assertion.
 */
export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./", import.meta.url)),
    },
  },
});
