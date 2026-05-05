---
name: ai-sdk-v3-typescript-debug
description: Debug AI SDK 3.x TypeScript integration errors in monorepo setups — provider API changes, chunk type mismatches, module resolution issues, and duplicate export conflicts
category: software-development
tags: [typescript, ai-sdk, debugging, monorepo]
---

# AI SDK 3.x TypeScript Integration Debugging

## Context
When integrating AI SDK 3.x (`ai`, `@ai-sdk/openai`, `@ai-sdk/anthropic`, `@ai-sdk/google`) in a monorepo with shared TypeScript code, multiple TypeScript errors arise due to API differences between SDK 2.x and 3.x, and cross-package type resolution issues.

## Common Errors and Fixes

### 1. `Cannot find module 'ai'` / Module has no exported member
**Cause**: shared/ directory has no tsconfig.json, and AI SDK packages are only in web/node_modules.  
**Fix**: Create root `package.json` with workspaces, `pnpm-workspace.yaml`, and `shared/package.json` so npm/pnpm can hoist dependencies.

### 2. `Property 'languageModel' does not exist` on provider
**Cause**: SDK 2.x API used `provider.languageModel(modelId)`.  
**Fix**: SDK 3.x uses `provider(modelId)` — provider is a callable that returns the language model directly.

```typescript
// Wrong (2.x API)
const model = provider.languageModel("gpt-4o-mini");

// Correct (3.x API)
const model = provider("gpt-4o-mini");
```

### 3. `Property 'fullStream' does not exist` on `Promise<StreamTextResult>`
**Cause**: `streamText()` in 3.x returns `Promise<StreamTextResult>` — must await first.  
**Fix**: 
```typescript
// Wrong
const stream = streamText({ model, messages });
for await (const chunk of stream.fullStream) {}

// Correct
const streamResult = await streamText({ model, messages });
for await (const chunk of streamResult.fullStream) {}
```

### 4. `tool-delta` type not assignable
**Cause**: SDK 3.x renamed `tool-delta` → `tool-call-delta` and changed property `textDelta` → `argsTextDelta`.  
**Fix**:
```typescript
// Wrong (2.x)
case 'tool-delta':
  yield { type: 'tool_delta', toolName: chunk.toolName, toolArgs: chunk.textDelta };

// Correct (3.x)
case 'tool-call-delta':
  yield { type: 'tool_delta', toolName: chunk.toolName, toolArgs: chunk.argsTextDelta };
```

### 5. `error` chunk type incompatible
**Cause**: SDK 3.x `error` chunk has `error: unknown`, not `error: string`.  
**Fix**: Cast with `String(chunk.error)`.

### 6. Duplicate export `PROVIDERS` — Export declaration conflicts
**Cause**: `export { PROVIDERS }` appears before PROVIDERS is declared. TypeScript falsely reports "Cannot redeclare exported variable" because it can't find the binding yet.  
**Fix**: Move all `export { ... }` statements to AFTER the actual declaration. PROVIDERS declared via `export const PROVIDERS: ...` doesn't need a separate re-export.

```typescript
// Wrong
export { PROVIDERS };  // line 9 - not yet declared!
export const PROVIDERS: ...  // line 15

// Correct
export const PROVIDERS: ...  // line 15 - declared and exported
// ... rest of file ...
// Export functions at the END
export { resolveProviderType, resolveModelId };
```

### 7. `async_hooks` module not found in browser
**Cause**: `thinking-context.ts` imported `AsyncLocalStorage` from `async_hooks` (Node.js only).  
**Fix**: Replace with browser-compatible global stack:
```typescript
const CONTEXT_STACK: ThinkingContext[] = [];
export function runWithThinkingContext<T>(context: ThinkingContext, fn: () => T): T {
  CONTEXT_STACK.push(context);
  try { return fn(); }
  finally { CONTEXT_STACK.pop(); }
}
export function getThinkingContext(): ThinkingContext | undefined {
  return CONTEXT_STACK[CONTEXT_STACK.length - 1];
}
```

### 8. `baseUrl` deprecated in TypeScript 6+
**Cause**: `tsconfig.app.json` has `"baseUrl": "."` which is deprecated.  
**Fix**: Remove `ignoreDeprecations: "6.0"` (unsupported by older tsc versions) and instead accept the deprecation warning, OR migrate to jsconfig.json path mappings. The warning doesn't block builds in practice.

## Build Verification Command
```bash
cd web && npm run build 2>&1 | grep -E "^error" | head -20
```

## SDK Version Check
```bash
cat node_modules/ai/package.json | grep '"version"'
# Should be 3.x (e.g., 3.4.33)
```

## Provider API Surface (3.x)
```typescript
const openai = createOpenAI({ apiKey, baseURL });
const anthropic = createAnthropic({ apiKey });
const google = createGoogleGenerativeAI({ apiKey });

// All three are callable — pass the result to generateText/streamText
const model = provider(modelId);  // e.g., openai("gpt-4o-mini")
generateText({ model, messages });
```
