import axios from 'axios';
import https from 'https';
import fs from 'fs';

export interface OAuthConfig {
  tokenUrl: string;
  clientId: string;
  clientSecret: string;
  grantType: string;
  scope: string;
  earlyRefreshSeconds?: number;
  caCertPath?: string;
}

interface OAuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export class OAuthTokenFetcher {
  private static readonly OAUTH_HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
  };

  private config: OAuthConfig;
  private token: OAuthTokenResponse | null = null;
  private refreshAfter: number = 0;
  private httpsAgent?: https.Agent;

  constructor(config: OAuthConfig) {
    this.config = {
      ...config,
      earlyRefreshSeconds: config.earlyRefreshSeconds ?? 300,
    };

    // Configure custom CA certificate if provided
    if (config.caCertPath && fs.existsSync(config.caCertPath)) {
      const ca = fs.readFileSync(config.caCertPath);
      this.httpsAgent = new https.Agent({
        ca,
        rejectUnauthorized: true,
      });
    }
  }

  private async fetchToken(): Promise<OAuthTokenResponse> {
    const params = new URLSearchParams({
      client_id: this.config.clientId,
      client_secret: this.config.clientSecret,
      grant_type: this.config.grantType,
      scope: this.config.scope,
    });

    try {
      const response = await axios.post<OAuthTokenResponse>(
        this.config.tokenUrl,
        params.toString(),
        { 
          headers: OAuthTokenFetcher.OAUTH_HEADERS,
          httpsAgent: this.httpsAgent,
        }
      );

      this.token = response.data;
      this.refreshAfter =
        Date.now() / 1000 +
        this.token.expires_in -
        (this.config.earlyRefreshSeconds ?? 300);

      return this.token;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          `OAuth token fetch failed: ${error.response?.status} ${error.response?.statusText}`
        );
      }
      throw error;
    }
  }

  async getToken(): Promise<string> {
    if (!this.token || Date.now() / 1000 > this.refreshAfter) {
      await this.fetchToken();
    }
    return this.token!.access_token;
  }
}
