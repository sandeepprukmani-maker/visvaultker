import { type InsertAutomationHistory, type AutomationHistory } from "@shared/schema";
import { findSimilar, createHistory } from "./api-client";
import https from "https";
import { spawn } from "child_process";

const SIMILARITY_THRESHOLD = 0.85;

async function fetchOAuthToken(): Promise<string> {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn("python", ["fetch_token.py"]);
    let output = "";
    let errorOutput = "";
    
    pythonProcess.stdout.on("data", (data) => {
      output += data.toString();
    });
    
    pythonProcess.stderr.on("data", (data) => {
      errorOutput += data.toString();
    });
    
    pythonProcess.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`Python script failed: ${errorOutput}`));
      } else {
        try {
          const result = JSON.parse(output.trim());
          if (result.error) {
            reject(new Error(`OAuth error: ${result.error}`));
          } else {
            resolve(result.access_token);
          }
        } catch (e) {
          reject(new Error(`Failed to parse OAuth response: ${output}`));
        }
      }
    });
  });
}

export async function generateEmbedding(text: string): Promise<number[]> {
  try {
    const token = await fetchOAuthToken();
    const embeddingEndpoint = process.env.OPENAI_EMBEDDING_ENDPOINT || "https://api.openai.com/v1/embeddings";
    const embeddingModel = process.env.OPENAI_EMBEDDING_MODEL || "text-embedding-3-small";
    
    const requestPayload = {
      input: text,
      model: embeddingModel,
      encoding_format: "float"
    };
    
    const requestBody = JSON.stringify(requestPayload);
    
    return new Promise((resolve, reject) => {
      const url = new URL(embeddingEndpoint);
      
      const options = {
        hostname: url.hostname,
        port: url.port || 443,
        path: url.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "Content-Length": Buffer.byteLength(requestBody),
        },
      };
      
      const req = https.request(options, (res) => {
        let responseData = "";
        
        res.on("data", (chunk) => {
          responseData += chunk;
        });
        
        res.on("end", () => {
          if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
            try {
              const data = JSON.parse(responseData);
              const embedding = data.data?.[0]?.embedding;
              
              if (!embedding || !Array.isArray(embedding)) {
                reject(new Error("Invalid embedding response"));
                return;
              }
              
              resolve(embedding);
            } catch (e) {
              reject(new Error(`Failed to parse embedding response: ${responseData}`));
            }
          } else {
            reject(new Error(`Embedding API request failed with status ${res.statusCode}: ${responseData}`));
          }
        });
      });
      
      req.on("error", (error) => {
        reject(error);
      });
      
      req.write(requestBody);
      req.end();
    });
  } catch (error) {
    console.error("Error generating embedding:", error);
    return [];
  }
}

export async function findSimilarAutomation(
  prompt: string,
  url?: string
): Promise<{ automation: AutomationHistory; similarity: number } | null> {
  try {
    const embedding = await generateEmbedding(prompt);
    
    if (!embedding || embedding.length === 0) {
      console.log("No embedding generated, skipping similarity search");
      return null;
    }
    
    const results = await findSimilar(embedding, SIMILARITY_THRESHOLD, 10);
    
    if (results && results.length > 0) {
      const topResult = results[0];
      
      if (topResult.similarity >= SIMILARITY_THRESHOLD) {
        console.log(`Found similar automation with similarity: ${topResult.similarity}`);
        
        const automationHistory: AutomationHistory = {
          id: topResult.id,
          prompt: topResult.prompt,
          promptEmbedding: topResult.promptEmbedding,
          detectedUrl: topResult.detectedUrl,
          mode: topResult.mode,
          model: topResult.model,
          success: topResult.success,
          sessionId: topResult.sessionId,
          logs: topResult.logs,
          generatedCode: topResult.generatedCode,
          screenshot: topResult.screenshot,
          error: topResult.error,
          createdAt: new Date(topResult.createdAt),
        };
        
        return {
          automation: automationHistory,
          similarity: topResult.similarity
        };
      }
    }
    
    return null;
  } catch (error) {
    console.error("Error finding similar automation:", error);
    return null;
  }
}

export async function saveAutomation(data: InsertAutomationHistory): Promise<void> {
  try {
    const embedding = await generateEmbedding(data.prompt);
    
    await createHistory({
      prompt: data.prompt,
      prompt_embedding: embedding.length > 0 ? embedding : null,
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
    
    console.log(`Saved automation with embedding (${embedding.length} dimensions)`);
  } catch (error) {
    console.error("Error saving automation:", error);
    throw error;
  }
}
