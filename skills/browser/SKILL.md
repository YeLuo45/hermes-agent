---
name: browser-vision-screenshot-workaround
description: Workaround when browser_vision cannot analyze its own screenshots in headless mode
---
# Browser Vision Screenshot Workaround

## Problem
`browser_vision` tool returns a `screenshot_path` but cannot analyze its own screenshots. The tool consistently reports "I don't see any screenshot attached" even when working in a headless browser context. Similarly, `vision_analyze` cannot read local PNG files from the screenshot cache.

## Workaround: Use browser_console for state verification

Instead of visual screenshot analysis, use JavaScript in the page context to verify state:

```javascript
// Check canvas exists
browser_console(expression: "JSON.stringify({ canvas: !!document.querySelector('canvas'), canvasCount: document.querySelectorAll('canvas').length, title: document.title })")

// Check game state
browser_console(expression: "document.body.innerText")

// Get specific game elements
browser_console(expression: "JSON.stringify({ pieces: document.querySelectorAll('.piece-class').length, turn: document.querySelector('.turn-indicator')?.textContent })")
```

## Alternative: Read source code directly

For verifying code changes (colors, UI elements), read source files directly:
```bash
read_file(path: "src/components/Board/Board.jsx", offset: 1, limit: 50)
```

## When visual verification is truly needed

1. Navigate to page with `browser_navigate`
2. Use `browser_vision` only for initial page description (it can describe what's on screen)
3. Don't expect to analyze the screenshot path it returns — treat it as fire-and-forget

## Root cause

The `screenshot_path` returned by browser tools points to a local file, but the `vision_analyze` tool cannot access files outside its allowed paths. The browser_vision tool itself has internal image analysis that fails when it tries to look at its own output.

## Verified environments

- WSL2 with headless Edge/Chrome via Playwright
- This limitation appears consistent across sessions
