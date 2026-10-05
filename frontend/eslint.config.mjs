import { defineConfig, globalIgnores } from "eslint/config";
import typescript from "typescript-eslint";
export default defineConfig([...typescript.configs.recommended, globalIgnores([".next/**", "next-env.d.ts", "test-results/**", "playwright-report/**"])]);
