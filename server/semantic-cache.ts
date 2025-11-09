import { GoogleGenAI } from "@google/genai";
import { db } from "./db";
import { automationHistory, type InsertAutomationHistory, type AutomationHistory } from "@shared/schema";
import { sql } from "drizzle-orm";

// Using Gemini embeddings - gemini-embedding-001 is the latest model
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });

const SIMILARITY_THRESHOLD = 0.85;

export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await ai.models.embedContent({
    model: "gemini-embedding-001",
    contents: text,
    config: {
      outputDimensionality: 768, // Use 768 dimensions for efficiency
    },
  });
  
  if (!response.embeddings || response.embeddings.length === 0) {
    throw new Error("Failed to generate embedding");
  }
  
  return response.embeddings[0].values || [];
}

export async function findSimilarAutomation(
  prompt: string,
  url?: string
): Promise<{ automation: AutomationHistory; similarity: number } | null> {
  const embedding = await generateEmbedding(prompt);
  const embeddingString = `[${embedding.join(",")}]`;

  const results = await db.execute<AutomationHistory & { similarity: number }>(sql`
    SELECT 
      *,
      1 - (prompt_embedding <=> ${embeddingString}::vector) as similarity
    FROM automation_history
    WHERE 
      success = true
      ${url ? sql`AND detected_url = ${url}` : sql``}
      AND prompt_embedding IS NOT NULL
      AND 1 - (prompt_embedding <=> ${embeddingString}::vector) > ${SIMILARITY_THRESHOLD}
    ORDER BY similarity DESC
    LIMIT 1
  `);

  if (results.rows.length === 0) {
    return null;
  }

  const result = results.rows[0];
  return {
    automation: result,
    similarity: result.similarity,
  };
}

export async function saveAutomation(data: InsertAutomationHistory): Promise<void> {
  let embedding: number[] | null = null;
  
  try {
    embedding = await generateEmbedding(data.prompt);
  } catch (error) {
    console.error("Failed to generate embedding:", error);
  }

  await db.insert(automationHistory).values({
    ...data,
    promptEmbedding: embedding ? `[${embedding.join(",")}]` : null,
  });
}
