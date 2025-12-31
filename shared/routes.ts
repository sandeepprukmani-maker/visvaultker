import { z } from 'zod';
import { insertPostSchema, insertPosterSchema, posts, posters } from './schema';

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
  posts: {
    latest: {
      method: 'GET' as const,
      path: '/api/posts/latest',
      responses: {
        200: z.custom<typeof posts.$inferSelect>(), // Returns the latest post (upserted)
        500: errorSchemas.internal,
      },
    },
    list: {
      method: 'GET' as const,
      path: '/api/posts',
      responses: {
        200: z.array(z.custom<typeof posts.$inferSelect>()),
      },
    }
  },
  posters: {
    create: {
      method: 'POST' as const,
      path: '/api/posters',
      input: z.object({
        postId: z.number(),
      }),
      responses: {
        201: z.custom<typeof posters.$inferSelect>(),
        404: errorSchemas.notFound,
        500: errorSchemas.internal,
      },
    },
    list: {
      method: 'GET' as const,
      path: '/api/posters',
      responses: {
        200: z.array(z.custom<typeof posters.$inferSelect & { post: typeof posts.$inferSelect }>()),
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
