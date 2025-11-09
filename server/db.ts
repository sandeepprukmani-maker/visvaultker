import { drizzle } from "drizzle-orm/neon-serverless";
import { Pool, neonConfig } from "@neondatabase/serverless";
import * as schema from "@shared/schema";
import ws from "ws";

// Check if persistence is disabled or database is not configured
export const PERSISTENCE_ENABLED = 
  !!process.env.DATABASE_URL && 
  process.env.PERSISTENCE_DISABLED !== "true";

let db: ReturnType<typeof drizzle> | null = null;

if (PERSISTENCE_ENABLED) {
  neonConfig.webSocketConstructor = ws;
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  db = drizzle(pool, { schema });
  console.log("✅ Database persistence enabled");
} else {
  console.log("ℹ️  Database persistence disabled - history and caching unavailable");
  console.log("   Set DATABASE_URL to enable persistence features");
}

export { db };
