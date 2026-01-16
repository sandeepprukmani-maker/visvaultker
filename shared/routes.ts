import { z } from 'zod';
import { insertAutomationSchema, automations, automationLogs } from './schema';

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
  automations: {
    list: {
      method: 'GET' as const,
      path: '/api/automations',
      responses: {
        200: z.array(z.custom<typeof automations.$inferSelect>()),
      },
    },
    get: {
      method: 'GET' as const,
      path: '/api/automations/:id',
      responses: {
        200: z.custom<typeof automations.$inferSelect & { logs: typeof automationLogs.$inferSelect[] }>(),
        404: errorSchemas.notFound,
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/automations',
      input: insertAutomationSchema,
      responses: {
        201: z.custom<typeof automations.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
    logs: {
      method: 'GET' as const,
      path: '/api/automations/:id/logs',
      responses: {
        200: z.array(z.custom<typeof automationLogs.$inferSelect>()),
        404: errorSchemas.notFound,
      },
    }
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
