import { drizzle } from "drizzle-orm/neon-serverless";
import { Pool, neonConfig } from "@neondatabase/serverless";
import * as schema from "@shared/schema";
import ws from "ws";

// Database is optional - used only if DATABASE_URL is provided
// The Python API server handles database operations for history and caching
let db: ReturnType<typeof drizzle> | null = null;

if (process.env.DATABASE_URL) {
  neonConfig.webSocketConstructor = ws;
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  db = drizzle(pool, { schema });
}

export { db };
