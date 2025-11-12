import { GoogleGenAI } from "@google/genai";
import { type InsertAutomationHistory, type AutomationHistory } from "@shared/schema";
import { findSimilar, createHistory } from "./api-client";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });

const SIMILARITY_THRESHOLD = 0.85;

export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await ai.models.embedContent({
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
}

export async function findSimilarAutomation(
  prompt: string,
  url?: string
): Promise<{ automation: AutomationHistory; similarity: number } | null> {
  const embedding = await generateEmbedding(prompt);
  
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
