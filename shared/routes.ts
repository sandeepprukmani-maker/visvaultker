import { z } from 'zod';
import { 
  tokenRequestSchema, tokenResponseSchema, errorResponseSchema,
  layoutRequestSchema, layoutResponseSchema,
  mortgageQuoteRequestSchema, helocQuoteRequestSchema, quoteResponseSchema,
  scenarios
} from './schema';

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
  unauthorized: z.object({
    message: z.string(),
  })
};

export const api = {
  auth: {
    token: {
      method: 'POST' as const,
      path: '/adfs/oauth2/token' as const,
      input: tokenRequestSchema,
      responses: {
        200: tokenResponseSchema,
        400: errorResponseSchema,
      },
    },
  },
  layouts: {
    mortgage: {
      method: 'POST' as const,
      path: '/api/uwm/instantpricequote/v1/mortgagepricinglayout' as const,
      input: layoutRequestSchema,
      responses: {
        200: layoutResponseSchema,
        401: errorSchemas.unauthorized,
      },
    },
    heloc: {
      method: 'POST' as const,
      path: '/api/uwm/instantpricequote/v1/heloclayout' as const,
      input: layoutRequestSchema,
      responses: {
        200: layoutResponseSchema,
        401: errorSchemas.unauthorized,
      },
    },
  },
  quotes: {
    mortgage: {
      method: 'POST' as const,
      path: '/api/uwm/instantpricequote/v1/pricequote' as const,
      input: mortgageQuoteRequestSchema,
      responses: {
        200: quoteResponseSchema,
        400: errorSchemas.validation,
        401: errorSchemas.unauthorized,
      },
    },
    heloc: {
      method: 'POST' as const,
      path: '/api/uwm/instantpricequote/v1/helocquote' as const,
      input: helocQuoteRequestSchema,
      responses: {
        200: quoteResponseSchema,
        400: errorSchemas.validation,
        401: errorSchemas.unauthorized,
      },
    },
  },
  scenarios: {
    list: {
      method: 'GET' as const,
      path: '/api/uwm/instantpricequote/v1/scenarios' as const,
      responses: {
        200: z.array(z.custom<typeof scenarios.$inferSelect>()),
        401: errorSchemas.unauthorized,
      },
    },
    get: {
      method: 'GET' as const,
      path: '/api/uwm/instantpricequote/v1/scenarios/:id' as const,
      responses: {
        200: z.custom<typeof scenarios.$inferSelect>(),
        404: errorSchemas.notFound,
        401: errorSchemas.unauthorized,
      },
    },
    delete: {
      method: 'DELETE' as const,
      path: '/api/uwm/instantpricequote/v1/scenarios/:id' as const,
      responses: {
        204: z.void(),
        404: errorSchemas.notFound,
        401: errorSchemas.unauthorized,
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
