import { defineConfig } from "drizzle-kit";

// Only require DATABASE_URL when actually running drizzle-kit commands
// This allows the app to run without a database
if (!process.env.DATABASE_URL) {
  console.warn("⚠️  DATABASE_URL not set - drizzle-kit commands will not work");
  console.warn("   This is OK if you're running without database persistence");
}

export default defineConfig({
  out: "./migrations",
  schema: "./shared/schema.ts",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL || "postgresql://localhost/dummy",
  },
});
