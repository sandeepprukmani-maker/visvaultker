import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);

let cachedToken: { value: string; expiresAt: number } | null = null;
const TOKEN_CACHE_DURATION = 3000000; // 50 minutes (tokens typically expire in 1 hour)

export async function getApiToken(): Promise<string> {
  // If OAuth is configured, use Python OAuth token fetcher
  if (process.env.OAUTH_TOKEN_URL) {
    // Check cache first
    const now = Date.now();
    if (cachedToken && cachedToken.expiresAt > now) {
      return cachedToken.value;
    }

    try {
      const pythonScript = path.join(import.meta.dirname, "oauth_token_fetcher.py");
      const { stdout, stderr } = await execAsync(`python ${pythonScript}`);
      
      if (stderr) {
        console.error("OAuth token fetch warning:", stderr);
      }
      
      const token = stdout.trim();
      if (!token) {
        throw new Error("Empty token received from OAuth");
      }

      // Cache the token
      cachedToken = {
        value: token,
        expiresAt: now + TOKEN_CACHE_DURATION,
      };

      return token;
    } catch (error) {
      console.error("Failed to fetch OAuth token:", error);
      throw new Error(`OAuth token fetch failed: ${error}`);
    }
  }

  // Fallback to environment variables
  return process.env.CUSTOM_MODEL_API_KEY || process.env.GOOGLE_AI_API_KEY || "";
}

export function getModelBaseURL(): string | undefined {
  return process.env.CUSTOM_MODEL_BASE_URL || process.env.GW_BASE_URL;
}
