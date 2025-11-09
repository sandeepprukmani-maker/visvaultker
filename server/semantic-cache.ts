import { GoogleGenAI } from "@google/genai";
import { type InsertAutomationHistory, type AutomationHistory } from "@shared/schema";
import { findSimilar, createHistory } from "./api-client";

const SIMILARITY_THRESHOLD = 0.85;
const EMBEDDINGS_ENABLED = !!process.env.GOOGLE_AI_API_KEY && process.env.DISABLE_EMBEDDINGS !== "true";

let embeddingsWarningShown = false;

const ai = EMBEDDINGS_ENABLED 
  ? new GoogleGenAI({ apiKey: process.env.GOOGLE_AI_API_KEY || "" })
  : null;

export async function generateEmbedding(text: string): Promise<number[] | null> {
  if (!EMBEDDINGS_ENABLED) {
    if (!embeddingsWarningShown) {
      console.log("ℹ️  Embeddings disabled - semantic caching unavailable. Set GOOGLE_AI_API_KEY to enable.");
      embeddingsWarningShown = true;
    }
    return null;
  }

  try {
    const response = await ai!.models.embedContent({
      model: "gemini-embedding-001",
      contents: text,
      config: {
        outputDimensionality: 768,
      },
    });
    
    if (!response.embeddings || response.embeddings.length === 0) {
      throw new Error("Failed to generate embedding");
    }
    
    return response.embeddings[0].values || [];
  } catch (error) {
    console.error("Failed to generate embedding:", error);
    return null;
  }
}

export async function findSimilarAutomation(
  prompt: string,
  url?: string
): Promise<{ automation: AutomationHistory; similarity: number } | null> {
  if (!EMBEDDINGS_ENABLED) {
    return null;
  }

  const embedding = await generateEmbedding(prompt);
  
  if (!embedding) {
    return null;
  }
  
  const results = await findSimilar(embedding, SIMILARITY_THRESHOLD, 1);
  
  if (results.length === 0) {
    return null;
  }

  const result = results[0];
  
  if (url && result.detectedUrl !== url) {
    return null;
  }

  return {
    automation: result as unknown as AutomationHistory,
    similarity: result.similarity,
  };
}

export async function saveAutomation(data: InsertAutomationHistory): Promise<void> {
  // Check if persistence is enabled
  const { PERSISTENCE_ENABLED } = await import("./db.js");
  
  if (!PERSISTENCE_ENABLED) {
    // Skip database save when persistence is disabled
    console.log("📝 Skipping history save (persistence disabled)");
    return;
  }

  let embedding: number[] | null = null;
  
  try {
    embedding = await generateEmbedding(data.prompt);
  } catch (error) {
    console.error("Failed to generate embedding:", error);
  }

  await createHistory({
    prompt: data.prompt,
    prompt_embedding: embedding,
    detected_url: data.detectedUrl ?? null,
    mode: data.mode,
    model: data.model,
    success: data.success,
    session_id: data.sessionId,
    logs: data.logs,
    generated_code: data.generatedCode,
    screenshot: data.screenshot ?? null,
    error: data.error ?? null,
  });
}
