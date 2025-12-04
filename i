import * as dotenv from "dotenv";
dotenv.config();

import { Stagehand } from "@browserbasehq/stagehand";
import { execFile } from "child_process";
import { promisify } from "util";

const execFileAsync = promisify(execFile);

// Config for calling the Python OAuth helper
const PYTHON_PATH = process.env.PYTHON_PATH || "python";
const OAUTH_SCRIPT = process.env.OAUTH_SCRIPT || "oauth_helper.py";

// Model name from your internal table
const MODEL_NAME =
  process.env.GW_MODEL_NAME || "us.anthropic.claude-sonnet-4-5-20250929-v1:0";

// Call Python script and parse its JSON output
async function getTokenAndUrl(): Promise<{ access_token: string; baseURL: string }> {
  const { stdout } = await execFileAsync(PYTHON_PATH, [OAUTH_SCRIPT]);
  const data = JSON.parse(stdout.trim());

  if (data.error) {
    throw new Error(`OAuth script error: ${data.error}`);
  }
  if (!data.access_token || !data.baseURL) {
    throw new Error("OAuth script did not return access_token/baseURL");
  }
  return data;
}

async function main() {
  // 1) Get fresh token + baseURL from Python OAuth helper
  const { access_token, baseURL } = await getTokenAndUrl();

  // Ensure we hit the chat-completions route
  const chatUrl = baseURL.endsWith("/chat/completions")
    ? baseURL
    : baseURL.replace(/\/$/, "") + "/chat/completions";

  // 2) Init Stagehand with your gateway model
  const stagehand = new Stagehand({
    env: "LOCAL",
    model: {
      model: MODEL_NAME,
      apiKey: access_token, // bearer token from gateway
      baseURL: chatUrl,     // your GW /chat/completions endpoint
    },
    verbose: 1,
  });

  await stagehand.init();

  const page = stagehand.context.pages()[0];
  if (!page) {
    throw new Error("No page found in Stagehand context");
  }

  await page.goto("https://www.google.com");

  // 3) Create agent using same gateway model
  const agent = stagehand.agent({
    model: {
      model: MODEL_NAME,
      apiKey: access_token,
      baseURL: chatUrl,
    },
  });

  const result = await agent.execute({
    instruction: "On Google, search for dogs.",
    maxSteps: 10,
  });

  console.log(result.message);

  await stagehand.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
