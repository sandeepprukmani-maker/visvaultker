import { z } from 'zod';

// Error schemas
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

// RSS Item schema
export const rssItemSchema = z.object({
  title: z.string(),
  description: z.string(),
  link: z.string(),
  pubDate: z.string(),
});

// Video schema
export const videoSchema = z.object({
  id: z.number(),
  videoId: z.string(),
  status: z.string(),
  videoUrl: z.string().nullable(),
  thumbnailUrl: z.string().nullable(),
  originalTitle: z.string(),
  originalDescription: z.string(),
  marketingScript: z.string(),
  createdAt: z.string(),
});

// API Contract
export const api = {
  rss: {
    getLatest: {
      method: 'GET' as const,
      path: '/api/rss/latest',
      responses: {
        200: rssItemSchema,
        500: errorSchemas.internal,
      },
    },
    rephrase: {
      method: 'POST' as const,
      path: '/api/rss/rephrase',
      input: z.object({
        title: z.string(),
        description: z.string(),
      }),
      responses: {
        200: z.object({
          marketingScript: z.string(),
        }),
        400: errorSchemas.validation,
        500: errorSchemas.internal,
      },
    },
  },
  videos: {
    list: {
      method: 'GET' as const,
      path: '/api/videos',
      responses: {
        200: z.array(videoSchema),
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/videos',
      input: z.object({
        originalTitle: z.string(),
        originalDescription: z.string(),
        marketingScript: z.string(),
      }),
      responses: {
        201: videoSchema,
        400: errorSchemas.validation,
        500: errorSchemas.internal,
      },
    },
    getStatus: {
      method: 'GET' as const,
      path: '/api/videos/:id/status',
      responses: {
        200: z.object({
          status: z.string(),
          videoUrl: z.string().nullable(),
          thumbnailUrl: z.string().nullable(),
        }),
        404: errorSchemas.notFound,
        500: errorSchemas.internal,
      },
    },
  },
};

// URL builder helper
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

// Type exports
export type RSSItem = z.infer<typeof rssItemSchema>;
export type VideoResponse = z.infer<typeof videoSchema>;
export type RephraseInput = z.infer<typeof api.rss.rephrase.input>;
export type CreateVideoInput = z.infer<typeof api.videos.create.input>;
