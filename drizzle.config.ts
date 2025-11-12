import { defineConfig } from "drizzle-kit";

// This config is only used when DATABASE_URL is available
// For now, the app uses Python/SQLite backend for database operations
const databaseUrl = process.env.DATABASE_URL || "postgresql://localhost:5432/visionvault";

export default defineConfig({
  out: "./migrations",
  schema: "./shared/schema.ts",
  dialect: "postgresql",
  dbCredentials: {
    url: databaseUrl,
  },
});
