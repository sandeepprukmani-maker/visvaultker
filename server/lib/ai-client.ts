import OpenAI from 'openai';
import https from 'https';
import fs from 'fs';
import { AISdkClient } from '@browserbasehq/stagehand';
import { createOpenAI } from '@ai-sdk/openai';
import { OAuthConfig, OAuthTokenFetcher } from './oauth';

let tokenFetcher: OAuthTokenFetcher | null = null;

function ensureEnvVars(): void {
  const requiredVars = [
    'OAUTH_TOKEN_URL',
    'OAUTH_CLIENT_ID',
    'OAUTH_CLIENT_SECRET',
    'OAUTH_GRANT_TYPE',
    'OAUTH_SCOPE',
    'GW_BASE_URL',
  ];

  const missing = requiredVars.filter((v) => !process.env[v]);
  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(', ')}`
    );
  }
}

function getTokenFetcher(): OAuthTokenFetcher {
  if (!tokenFetcher) {
    ensureEnvVars();

    const config: OAuthConfig = {
      tokenUrl: process.env.OAUTH_TOKEN_URL!,
      clientId: process.env.OAUTH_CLIENT_ID!,
      clientSecret: process.env.OAUTH_CLIENT_SECRET!,
      grantType: process.env.OAUTH_GRANT_TYPE!,
      scope: process.env.OAUTH_SCOPE!,
      caCertPath: process.env.CA_CERT_PATH,
    };

    tokenFetcher = new OAuthTokenFetcher(config);
  }

  return tokenFetcher;
}

function getHttpsAgent(): https.Agent | undefined {
  const caCertPath = process.env.CA_CERT_PATH;
  if (caCertPath && fs.existsSync(caCertPath)) {
    const ca = fs.readFileSync(caCertPath);
    return new https.Agent({
      ca,
      rejectUnauthorized: true,
    });
  }
  return undefined;
}

export async function getAccessToken(): Promise<string> {
  const fetcher = getTokenFetcher();
  return await fetcher.getToken();
}

export async function createAIClient(): Promise<OpenAI> {
  const token = await getAccessToken();
  const baseURL = process.env.GW_BASE_URL;

  return new OpenAI({
    apiKey: token,
    baseURL,
  });
}

export async function sendChatRequest(
  messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[],
  model: string = 'gpt-4',
  options?: Omit<OpenAI.Chat.Completions.ChatCompletionCreateParams, 'model' | 'messages' | 'stream'>
): Promise<OpenAI.Chat.Completions.ChatCompletion> {
  const client = await createAIClient();
  const response = await client.chat.completions.create({
    model,
    messages,
    stream: false,
    ...options,
  });
  return response;
}

export async function createStagehandLLMClient(modelName: string = 'gpt-4'): Promise<AISdkClient> {
  const token = await getAccessToken();
  
  const customProvider = createOpenAI({
    apiKey: token,
    baseURL: process.env.GW_BASE_URL,
  });

  const llmClient = new AISdkClient({
    model: customProvider(modelName),
  });

  return llmClient;
}
