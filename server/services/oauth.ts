interface OAuthConfig {
  tokenUrl: string;
  clientId: string;
  clientSecret: string;
  grantType: string;
  scope: string;
  earlyRefreshSeconds: number;
}

class OAuthTokenFetcher {
  private token: string | null = null;
  private refreshAfter: Date | null = null;
  private config: OAuthConfig;
  private readonly OAUTH_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
  };

  constructor(config: OAuthConfig) {
    this.config = config;
  }

  private async fetchToken(): Promise<void> {
    const params = new URLSearchParams();
    params.append("client_id", this.config.clientId);
    params.append("client_secret", this.config.clientSecret);
    params.append("grant_type", this.config.grantType);
    params.append("scope", this.config.scope);

    const response = await fetch(this.config.tokenUrl, {
      method: "POST",
      headers: this.OAUTH_HEADERS,
      body: params.toString(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch OAuth token: ${response.statusText}`);
    }

    const data = await response.json();
    this.token = data.access_token;
    
    const expiresIn = data.expires_in || 3600;
    this.refreshAfter = new Date(
      Date.now() + (expiresIn - this.config.earlyRefreshSeconds) * 1000
    );
  }

  async getToken(): Promise<string> {
    if (!this.token || !this.refreshAfter || Date.now() >= this.refreshAfter.getTime()) {
      await this.fetchToken();
    }
    return this.token!;
  }
}

function ensureEnvVarsForOAuth(): void {
  const requiredEnvVars = [
    "OAUTH_TOKEN_URL",
    "OAUTH_CLIENT_ID",
    "OAUTH_CLIENT_SECRET",
    "OAUTH_GRANT_TYPE",
    "OAUTH_SCOPE",
    "GW_BASE_URL",
  ];

  const missing = requiredEnvVars.filter((v) => !process.env[v]);
  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(", ")}`
    );
  }
}

let tokenFetcher: OAuthTokenFetcher | null = null;

export function getTokenFetcher(): OAuthTokenFetcher {
  if (!tokenFetcher) {
    ensureEnvVarsForOAuth();
    
    const config: OAuthConfig = {
      tokenUrl: process.env.OAUTH_TOKEN_URL!,
      clientId: process.env.OAUTH_CLIENT_ID!,
      clientSecret: process.env.OAUTH_CLIENT_SECRET!,
      grantType: process.env.OAUTH_GRANT_TYPE!,
      scope: process.env.OAUTH_SCOPE!,
      earlyRefreshSeconds: 300,
    };

    tokenFetcher = new OAuthTokenFetcher(config);
  }
  
  return tokenFetcher;
}

export async function getAccessToken(): Promise<string> {
  const fetcher = getTokenFetcher();
  return await fetcher.getToken();
}
