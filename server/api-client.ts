const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://localhost:8000";

interface ApiHistory {
  id: number;
  prompt: string;
  promptEmbedding: number[] | null;
  detectedUrl: string | null;
  mode: string;
  model: string;
  success: boolean;
  sessionId: string;
  logs: any[];
  generatedCode: {
    typescript?: string;
    cached?: string;
    agent?: string;
    locators?: string;
  };
  screenshot: string | null;
  error: string | null;
  createdAt: string;
}

export async function fetchAllHistory(): Promise<ApiHistory[]> {
  const response = await fetch(`${PYTHON_API_URL}/api/history`);
  if (!response.ok) {
    throw new Error(`Failed to fetch history: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchHistoryById(id: number): Promise<ApiHistory> {
  const response = await fetch(`${PYTHON_API_URL}/api/history/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch history: ${response.statusText}`);
  }
  return response.json();
}

export async function createHistory(data: {
  prompt: string;
  prompt_embedding: number[] | null;
  detected_url: string | null;
  mode: string;
  model: string;
  success: boolean;
  session_id: string;
  logs: any[];
  generated_code: any;
  screenshot: string | null;
  error: string | null;
}): Promise<{ id: number; message: string }> {
  const response = await fetch(`${PYTHON_API_URL}/api/history`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create history: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteHistory(id: number): Promise<{ message: string }> {
  const response = await fetch(`${PYTHON_API_URL}/api/history/${id}`, {
    method: "DELETE",
  });
  
  if (!response.ok) {
    throw new Error(`Failed to delete history: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteAllHistory(): Promise<{ message: string }> {
  const response = await fetch(`${PYTHON_API_URL}/api/history`, {
    method: "DELETE",
  });
  
  if (!response.ok) {
    throw new Error(`Failed to delete all history: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchCache(): Promise<ApiHistory[]> {
  const response = await fetch(`${PYTHON_API_URL}/api/cache`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cache: ${response.statusText}`);
  }
  return response.json();
}

export async function findSimilar(
  embedding: number[],
  threshold: number = 0.85,
  limit: number = 10
): Promise<(ApiHistory & { similarity: number })[]> {
  const response = await fetch(`${PYTHON_API_URL}/api/similarity-search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ embedding, threshold, limit }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to search similar: ${response.statusText}`);
  }
  return response.json();
}
