import dotenv from "dotenv";
dotenv.config();

console.log("Loaded DB URL in db.ts:", process.env.DATABASE_URL); // DEBUG

import { drizzle } from "drizzle-orm/neon-http";
import { neon } from "@neondatabase/serverless";
import * as schema from "@shared/schema";

const dbUrl = process.env.DATABASE_URL;

if (!dbUrl) {
  throw new Error("DATABASE_URL is missing! Check your .env file.");
}

const sql = neon(dbUrl);
export const db = drizzle(sql, { schema });
