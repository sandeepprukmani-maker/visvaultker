import { type InsertAutomationHistory, type AutomationHistory } from "@shared/schema";
import { findSimilar, createHistory } from "./api-client";

const SIMILARITY_THRESHOLD = 0.85;

export async function generateEmbedding(text: string): Promise<number[]> {
  return [];
}

export async function findSimilarAutomation(
  prompt: string,
  url?: string
): Promise<{ automation: AutomationHistory; similarity: number } | null> {
  return null;
}

export async function saveAutomation(data: InsertAutomationHistory): Promise<void> {
  await createHistory({
    prompt: data.prompt,
    prompt_embedding: null,
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
