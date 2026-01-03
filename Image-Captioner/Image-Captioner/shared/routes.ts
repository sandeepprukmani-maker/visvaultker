import { z } from 'zod';
import { insertQuoteSchema, quotes } from './schema';

export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  notFound: z.object({
    message: z.string(),
  }),
  internal: z.object({
    message: z.string(),
  }),
};

export const api = {
  quotes: {
    generate: {
      method: 'POST' as const,
      path: '/api/quotes/generate',
      input: z.object({
        postId: z.number().int().positive().default(1)
      }),
      responses: {
        201: z.custom<typeof quotes.$inferSelect>(),
        500: errorSchemas.internal,
      },
    },
    list: {
      method: 'GET' as const,
      path: '/api/quotes',
      responses: {
        200: z.array(z.custom<typeof quotes.$inferSelect>()),
      },
    },
  },
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}

export type QuoteInput = z.infer<typeof api.quotes.generate.input>;
export type QuoteResponse = z.infer<typeof api.quotes.generate.responses[201]>;
