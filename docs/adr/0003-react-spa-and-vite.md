# 0003 — React SPA and Vite

Status: Accepted. Date: 2026-11-04.

Context: The initial product is an authenticated learning application without a demonstrated SSR requirement.

Decision: React 19, Vite 8, TypeScript, Node 24, pnpm 11, TanStack Router/Query, Tailwind, and a minimal shadcn/ui component convention. Feature folders own their components. Use React Hook Form and Zod when forms are added. Generate types from OpenAPI and use openapi-fetch rather than duplicating API models.

Consequences: A simple static frontend can use a same-origin API proxy. Server state stays in Query. Static hosting must provide SPA fallback routing. Pin the TypeScript major supported by both ESLint tooling and OpenAPI generation rather than selecting an incompatible newest compiler.
