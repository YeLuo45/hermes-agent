---
name: llm-design-dev
description: OpenMAIC 多智能体交互课堂的大模型设计能力 — Provider架构、LLM调用层、LangGraph编排、JSON流式解析、动作系统。用于复刻该能力到其他项目。
category: software-development
---

# OpenMAIC 大模型设计能力沉淀

> 来源：PRJ-20260424-001 OpenMAIC 项目分析
> 用途：其他项目复刻该多智能体交互课堂的大模型能力

---

## 核心能力概览

OpenMAIC 是一套**多智能体交互课堂**框架，核心是让多个 AI Agent 在课堂场景中协作：
- **Director Agent**：负责任务分发，决定哪个 Agent 说话
- **角色 Agent**：Teacher / Assistant / Student，各有不同权限和行为准则
- **白板控制**：Agent 可以操作白板元素（文字、形状、LaTeX、代码、表格等）
- **流式输出**：通过 SSE 流式推送文本和动作事件

---

## 一、Provider 架构（多后端适配）

### 1.1 核心文件
- `lib/ai/providers.ts` — Provider 注册表（所有模型配置）
- `lib/ai/llm.ts` — 统一 LLM 调用层（callLLM / streamLLM）
- `lib/ai/thinking-context.ts` — AsyncLocalStorage 携带 per-request ThinkingConfig

### 1.2 Provider 类型定义（lib/types/provider.ts）
```typescript
type ProviderType = 'openai' | 'anthropic' | 'google' | 'openai-compatible';

// 模型能力标志
interface ModelCapabilities {
  streaming?: boolean;
  tools?: boolean;
  vision?: boolean;
  thinking?: ThinkingCapability; // 推理能力配置
}

interface ThinkingCapability {
  toggleable: boolean;      // 是否可关闭
  budgetAdjustable: boolean; // 预算是否可调
  defaultEnabled: boolean;   // 默认是否启用
}
```

### 1.3 支持的 Provider

| Provider | 类型标识 | BaseUrl | 代表模型 |
|----------|---------|---------|---------|
| OpenAI | `openai` | `https://api.openai.com/v1` | GPT-5.4, o4-mini, o3 |
| Anthropic | `anthropic` | `https://api.anthropic.com/v1` | Claude Opus 4.6, Sonnet 4.6 |
| Google | `google` | `https://generativelanguage.googleapis.com/v1beta` | Gemini 3.1 Pro, 2.5 Flash |
| GLM (智谱) | `openai` | `https://open.bigmodel.cn/api/paas/v4` | GLM-5.1, GLM-5 |
| MiniMax | `anthropic-compatible` | MiniMax 官方 | abab6.5s |
| DeepSeek | `openai-compatible` | `https://api.deepseek.com/v1` | DeepSeek Chat |
| Kimi (Moonshot) | `openai-compatible` | `https://api.moonshot.cn/v1` | Kimi Turbo |
| Qwen (通义) | `openai-compatible` | 阿里云 DashScope | Qwen Max |
| SiliconFlow | `openai-compatible` | `https://api.siliconflow.cn/v1` | 聚合模型 |
| Doubao (豆包) | `openai-compatible` | 火山引擎 | Doubao Pro |

### 1.4 Provider 注册表示例
```typescript
export const PROVIDERS: Record<ProviderId, ProviderConfig> = {
  openai: {
    id: 'openai',
    type: 'openai',
    defaultBaseUrl: 'https://api.openai.com/v1',
    requiresApiKey: true,
    models: [
      {
        id: 'gpt-5.4',
        contextWindow: 1000000,
        outputWindow: 128000,
        capabilities: {
          streaming: true,
          tools: true,
          vision: true,
          thinking: {
            toggleable: true,
            budgetAdjustable: true,
            defaultEnabled: false,
          },
        },
      },
      // ...更多模型
    ],
  },
  // OpenAI兼容Provider示例
  deepseek: {
    id: 'deepseek',
    type: 'openai',
    defaultBaseUrl: 'https://api.deepseek.com/v1',
    requiresApiKey: true,
    models: [...],
  },
};
```

### 1.5 添加新 Provider 的步骤

1. 在 `lib/types/provider.ts` 添加 `ProviderId` 类型
2. 在 `lib/ai/providers.ts` 的 `PROVIDERS` 对象中添加配置
3. 如果 Provider 使用非标准 BaseUrl，需要在 `resolveModel()` 中处理

---

## 二、LLM 调用层设计

### 2.1 核心函数（lib/ai/llm.ts）

```typescript
// 统一调用接口
export async function callLLM<T extends GenerateTextParams>(
  params: T,
  source: string,           // 日志标签
  retryOptions?: LLMRetryOptions,  // 重试配置
  thinking?: ThinkingConfig, // 推理配置（覆盖全局）
): Promise<GenerateTextResult<any, any>>

export function streamLLM<T extends StreamTextParams>(
  params: T,
  source: string,
  thinking?: ThinkingConfig,
): StreamTextResult<any, any>
```

### 2.2 重试机制
```typescript
export interface LLMRetryOptions {
  retries?: number;  // 最大重试次数（默认0）
  validate?: (text: string) => boolean; // 验证函数，默认检查非空
}
```

### 2.3 Thinking/推理配置适配

**关键设计**：为不同 Provider 适配推理参数，避免"一刀切"。

| Provider | 启用方式 | 关闭方式 | 预算参数 |
|----------|---------|---------|---------|
| OpenAI | 不注入（用模型默认） | `reasoningEffort: 'none'` | 无（离散级别） |
| Anthropic | `type: 'enabled'` + `budgetTokens` | `type: 'disabled'` | `budgetTokens: 10240` |
| Google Gemini 2.5 | `thinkingBudget: 128~24576` | `thinkingBudget: 0` | `thinkingBudget` |
| Google Gemini 3.x | `thinkingLevel: 'high'` | `thinkingLevel: 'minimal'` | 无（级别） |
| OpenAI兼容 | 不支持（会被schema过滤） | — | — |

```typescript
function buildThinkingProviderOptions(
  modelId: string,
  config: ThinkingConfig,
): ProviderOptions | undefined {
  // 根据模型类型注入对应的 providerOptions
  switch (providerType) {
    case 'openai':
      return { openai: { reasoningEffort: 'none' } };
    case 'anthropic':
      return { anthropic: { thinking: { type: 'disabled' } } };
    case 'google':
      return { google: { thinkingConfig: { thinkingBudget: 0 } } };
  }
}
```

### 2.4 AsyncLocalStorage 传递 ThinkingConfig

**问题**：LLM 调用经过多层（route → stateless-generate → director-graph → ai-sdk-adapter → callLLM），需要在每一层都能访问到请求级别的 thinking 配置。

**方案**：`thinkingContext = new AsyncLocalStorage<ThinkingConfig | undefined>()`

在 `callLLM` 中用 `thinkingContext.run(config, () => generateText(...))` 包装，使得底层 `providers.ts` 的自定义 fetch 可以通过 `AsyncLocalStorage.get()`

**注意**：`thinking-context.ts` 使用 `node:async_hooks`，是**纯 Server 模块**，不能被 Client 代码 import（通过 `globalThis.__thinkingContext` 间接访问）。

---

## 三、多智能体编排（LangGraph）

### 3.1 核心文件
- `lib/orchestration/director-graph.ts` — LangGraph StateGraph 定义
- `lib/orchestration/stateless-generate.ts` — 流式生成入口 + JSON 解析器
- `lib/orchestration/ai-sdk-adapter.ts` — AI SDK → LangGraph 适配器
- `lib/orchestration/prompt-builder.ts` — System Prompt 构建
- `lib/orchestration/director-prompt.ts` — Director Agent 的决策 Prompt
- `lib/orchestration/tool-schemas.ts` — 动作描述

### 3.2 图结构

```
START → director ──(shouldEnd?)──→ END
              │
              └──(next)──→ agent_generate ──→ director (loop)
```

**Director Node**：决定下一个 Agent（Single Agent 用代码逻辑，Multi Agent 用 LLM）

**Agent Generate Node**：运行单个 Agent 的生成，流式输出事件

### 3.3 LangGraph State 定义
```typescript
const OrchestratorState = Annotation.Root({
  // 输入（每个请求设置一次）
  messages: Annotation<StatelessChatRequest['messages']>,
  storeState: Annotation<StatelessChatRequest['storeState']>,
  availableAgentIds: Annotation<string[]>,
  maxTurns: Annotation<number>,
  languageModel: Annotation<LanguageModel>,
  thinkingConfig: Annotation<ThinkingConfig | null>,
  discussionContext: Annotation<{ topic: string; prompt?: string } | null>,
  triggerAgentId: Annotation<string | null>,
  userProfile: Annotation<{ nickname?: string; bio?: string } | null>,
  agentConfigOverrides: Annotation<Record<string, AgentConfig>>,

  // 内部状态（节点间更新）
  currentAgentId: Annotation<string | null>,
  turnCount: Annotation<number>,
  agentResponses: Annotation<AgentTurnSummary[]>,  // 累加reducer
  whiteboardLedger: Annotation<WhiteboardActionRecord[]>,  // 累加reducer
  shouldEnd: Annotation<boolean>,
  totalActions: Annotation<number>,
});
```

### 3.4 Director 决策逻辑

**Single Agent 模式**（代码逻辑，零 LLM 调用）：
- turn 0：派发 Agent
- turn 1+：cue user（等待用户输入）

**Multi Agent 模式**（LLM 决策）：
- turn 0 + triggerAgentId：派发 trigger agent（跳过 LLM）
- 其他：LLM 决定 next agent / USER / END

### 3.5 AISDK-LangGraph 适配器

```typescript
export class AISdkLangGraphAdapter extends BaseChatModel {
  constructor(languageModel: LanguageModel, thinking?: ThinkingConfig) {
    super({});
    this.languageModel = languageModel;
    this.thinking = thinking;
  }

  async _generate(messages: BaseMessage[]): Promise<ChatResult> {
    const result = await callLLM({
      model: this.languageModel,
      messages: this.convertMessages(messages),  // LangChain → AI SDK格式
    }, 'chat-adapter', undefined, this.thinking);
    return {
      generations: [{ text: result.text, message: new AIMessage(result.text) }],
    };
  }

  async *streamGenerate(messages: BaseMessage[]) {
    const result = streamLLM({ model: this.languageModel, messages });
    for await (const chunk of result.textStream) {
      yield { type: 'delta', content: chunk };
    }
  }
}
```

---

## 四、结构化输出解析

### 4.1 输出格式

Agent 输出是**JSON Array**，包含 `text` 和 `action` 两种对象：

```json
[
  {"type": "action", "name": "spotlight", "params": {"elementId": "img_1"}},
  {"type": "text", "content": "同学们好，请看这张图..."},
  {"type": "action", "name": "wb_draw_latex", "params": {"latex": "E=mc^2", "x": 100, "y": 50, "height": 60}},
  {"type": "text", "content": "这是质能方程"}
]
```

### 4.2 流式 JSON 解析（stateless-generate.ts）

**挑战**：LLM 流式输出 JSON 不完整，需要增量解析。

**方案**：使用 `partial-json` + `jsonrepair` 双保险

```typescript
export function parseStructuredChunk(chunk: string, state: ParserState): ParseResult {
  state.buffer += chunk;

  // 1. 找到开始的 `[`
  if (!state.jsonStarted) {
    const idx = state.buffer.indexOf('[');
    if (idx === -1) return result;  // 还没到JSON
    state.buffer = state.buffer.slice(idx);
    state.jsonStarted = true;
  }

  // 2. 增量解析
  try {
    const repaired = jsonrepair(state.buffer);
    parsed = JSON.parse(repaired);
  } catch {
    parsed = parsePartialJson(state.buffer, Allow.ARR | ...);
  }

  // 3. 发出已完成的item，流式推送最后一个text item的增量
  // 4. 检查是否闭合（以 `]` 结尾）
}
```

### 4.3 容错机制

当模型输出纯文本（非 JSON）：
```typescript
export function finalizeParser(state: ParserState): ParseResult {
  if (!state.jsonStarted) {
    // 从未出现 `[`，整个buffer作为纯文本发出
    result.textChunks.push(state.buffer.trim());
  }
  // ...
}
```

---

## 五、动作系统（Tool Schemas）

### 5.1 动作类型（lib/types/action.ts）
- **Slide 动作**：`spotlight`, `laser`, `play_video`
- **Whiteboard 动作**：`wb_open`, `wb_close`, `wb_draw_text`, `wb_draw_shape`, `wb_draw_chart`, `wb_draw_latex`, `wb_draw_table`, `wb_draw_line`, `wb_draw_code`, `wb_edit_code`, `wb_clear`, `wb_delete`

### 5.2 角色-动作映射（lib/orchestration/registry/types.ts）
```typescript
export const ROLE_ACTIONS: Record<string, string[]> = {
  teacher: [...SLIDE_ACTIONS, ...WHITEBOARD_ACTIONS],  // 全动作
  assistant: [...WHITEBOARD_ACTIONS],  // 无slide控制
  student: [...WHITEBOARD_ACTIONS],    // 白板只读（被动邀请）
};
```

### 5.3 场景过滤
```typescript
export function getEffectiveActions(allowedActions: string[], sceneType?: string): string[] {
  if (!sceneType || sceneType === 'slide') return allowedActions;
  // 非slide场景过滤掉spotlight/laser
  return allowedActions.filter(a => !SLIDE_ONLY_ACTIONS.includes(a));
}
```

### 5.4 动作白板互斥
- **Whiteboard 打开时**：Slide Canvas 隐藏，spotlight/laser 失效
- **Spotlight/Laser 使用前**：需要先 `wb_close`

---

## 六、Agent 配置

### 6.1 AgentConfig 结构（lib/orchestration/registry/types.ts）
```typescript
export interface AgentConfig {
  id: string;
  name: string;           // 显示名（中文）
  role: string;          // teacher | assistant | student
  persona: string;       // 系统Prompt（人格描述）
  avatar: string;        // Emoji或图片URL
  color: string;         // UI主题色（hex）
  allowedActions: string[];
  priority: number;      // Director决策优先级(1-10)
  voiceConfig?: {        // TTS配置
    providerId: TTSProviderId;
    modelId?: string;
    voiceId: string;
  };
  isGenerated?: boolean; // 是否LLM生成
  boundStageId?: string; // 绑定的stage ID
}
```

### 6.2 Prompt 构建（lib/orchestration/prompt-builder.ts）

核心变量替换：
```typescript
const vars = {
  agentName: agentConfig.name,
  persona: agentConfig.persona,
  roleGuideline: ROLE_GUIDELINES[agentConfig.role],
  studentProfileSection: buildStudentProfileSection(userProfile),
  peerContext: buildPeerContextSection(agentResponses, agentConfig.name),
  languageConstraint: buildLanguageConstraint(storeState.stage?.languageDirective),
  formatExample: hasSlideActions ? FORMAT_EXAMPLE_SLIDE : FORMAT_EXAMPLE_WB,
  actionDescriptions: getActionDescriptions(effectiveActions),
  stateContext: buildStateContext(storeState),
  virtualWhiteboardContext: buildVirtualWhiteboardContext(storeState, whiteboardLedger),
  lengthGuidelines: buildLengthGuidelines(agentConfig.role),
  whiteboardGuidelines: buildWhiteboardGuidelines(agentConfig.role),
};
```

### 6.3 角色行为准则

**Teacher**：
- 100字左右 speech text
- 可用所有动作
- 控制课堂节奏，提问引导学生
- 白板布局：1000×562px，20px边距，30px间距

**Assistant**：
- 80字左右 speech text
- 支持角色，不抢戏
- 最多1-2个小元素

**Student**：
- 50字左右 speech text
- 不主动使用白板
- 快速，自然反应

---

## 七、前端循环（Agent Loop）

### 7.1 核心文件
- `lib/chat/agent-loop.ts` — 纯异步循环逻辑（frontend 和 eval 共用）
- `components/chat/use-chat-sessions.ts` — React Hook（调用 agent-loop）

### 7.2 循环流程

```
用户发消息
  → runAgentLoop()
    → POST /api/chat { messages, storeState, config, directorState }
    → 解析 SSE 事件（agent_start, text_delta, action, agent_end, cue_user, done）
    → onEvent() 处理每个事件
    → onIterationEnd() 检查退出条件
    → 退出条件：cue_user | end | max_turns | empty_turns
    → 循环或结束
```

### 7.3 退出条件
```typescript
type ExitReason = 'end' | 'cue_user' | 'max_turns' | 'aborted' | 'empty_turns' | 'no_done';
```

- `cue_user`：Director 让用户输入（对话轮次）
- `empty_turns`：连续2次 Agent 无输出
- `max_turns`：达到上限

---

## 八、API 层

### 8.1 Chat API（app/api/chat/route.ts）

```typescript
// 请求体
interface StatelessChatRequest {
  messages: UIMessage[];
  storeState: {
    stage: unknown;
    scenes: unknown[];
    currentSceneId: string | null;
    mode: string;
    whiteboardOpen: boolean;
  };
  config: {
    agentIds: string[];
    sessionType?: string;
  };
  directorState?: DirectorState;  // 跨请求累积状态
  apiKey: string;
  baseUrl?: string;
  model?: string;
  providerType?: string;
}

// SSE事件类型
type StatelessEvent =
  | { type: 'thinking'; data: { stage: string; agentId?: string } }
  | { type: 'agent_start'; data: AgentStartData }
  | { type: 'text_delta'; data: { content: string; messageId: string } }
  | { type: 'action'; data: ActionData }
  | { type: 'agent_end'; data: { messageId: string; agentId: string } }
  | { type: 'cue_user'; data: { fromAgentId?: string } }
  | { type: 'done'; data: DirectorState }
  | { type: 'error'; data: { message: string } };
```

### 8.2 心跳保活
```typescript
const HEARTBEAT_INTERVAL_MS = 15_000;
setInterval(() => {
  writer.write(encoder.encode(`:heartbeat\n\n`));
}, HEARTBEAT_INTERVAL_MS);
```

---

## 九、复刻清单

### 9.1 必做（核心能力）

| 步骤 | 文件 | 说明 |
|------|------|------|
| 1 | `lib/types/provider.ts` | 定义 ProviderId, ModelInfo, ThinkingConfig 类型 |
| 2 | `lib/ai/providers.ts` | 构建 PROVIDERS 注册表 |
| 3 | `lib/ai/llm.ts` | 实现 callLLM / streamLLM（含重试、thinking适配） |
| 4 | `lib/ai/thinking-context.ts` | AsyncLocalStorage + globalThis 暴露（纯server） |
| 5 | `lib/orchestration/director-graph.ts` | LangGraph StateGraph |
| 6 | `lib/orchestration/stateless-generate.ts` | 流式JSON解析器 |
| 7 | `lib/orchestration/ai-sdk-adapter.ts` | AI SDK → LangChain 适配器 |
| 8 | `lib/orchestration/prompt-builder.ts` | System Prompt 构建 |
| 9 | `lib/orchestration/tool-schemas.ts` | 动作描述 |
| 10 | `lib/orchestration/registry/types.ts` | AgentConfig 定义 + 角色动作映射 |
| 11 | `lib/chat/agent-loop.ts` | 前端循环逻辑 |
| 12 | `app/api/chat/route.ts` | SSE API 端点 |

### 9.2 依赖安装

```bash
pnpm add ai @ai-sdk/openai @ai-sdk/anthropic @ai-sdk/google @langchain/langgraph
pnpm add partial-json jsonrepair
```

### 9.3 关键陷阱

1. **thinking-context 是纯 Server 模块**：不能被 Client 代码 import，通过 `globalThis.__thinkingContext` 间接访问
2. **OpenAI 兼容 Provider 不支持 thinking 参数**：会被 Vercel AI SDK 的 Zod schema 过滤掉
3. **JSON 流式解析要用 partial-json + jsonrepair 双保险**：直接 JSON.parse 会因不完整而失败
4. **Whiteboard 布局是 1000×562**：Agent 的坐标计算基于此画布尺寸
5. **Director State 跨请求累积**：前端需要把 `directorState` 带回每次请求

---

## 十、扩展方向

- **多模态**：支持图像/视频生成（需要额外 Adapter）
- **PBL 场景**：Project-Based Learning 的 Issue Board 模式
- **Quiz 模式**：自动出题、自动评分
- **课堂录制/回放**：Playback Engine

---

## 十一、UI/UX 设计系统

> 来源：PRJ-20260424-001 OpenMAIC 前端组件分析
> 用途：复刻多智能体交互课堂的 UI 交互模式

### 11.1 设计哲学

| 原则 | 实现 |
|------|------|
| **AI 优先** | UI 为 AI Agent 流式输出服务，消息逐字显现而非整块渲染 |
| **沉浸感** | 最小化 UI 干扰，最大化内容呈现；演讲模式隐藏侧边栏 |
| **双模态** | Playback（回放预生成内容）vs Autonomous（实时生成讨论）两种交互模式 |
| **可访问性** | 完整 dark mode，backdrop-blur 毛玻璃效果，无障碍色对比 |
| **流畅反馈** | 所有状态变化有动效，无白屏跳转，异步操作有明确 loading 态 |

### 11.2 布局架构

```
Stage（主容器）
├── Header（顶栏：标题、设置、主题切换）
├── SceneSidebar（场景导航侧边栏，可折叠）
├── CanvasArea（中央内容区）
│   ├── SlideRenderer（幻灯片 + spotlight/laser 效果）
│   ├── Whiteboard（白板浮层，spring 动画弹出）
│   └── Roundtable（底部讨论区）
├── ChatArea（右侧面板，drag-to-resize）
│   ├── Tabs: Lecture Notes | Chat Sessions
│   └── InlineActionTag（气泡内动作徽章）
└── AgentBar（智能体选择顶栏）
```

**尺寸规范**：
- ChatArea 默认宽度：340px，最小 240px，最大 560px
- Whiteboard 弹出：`inset: 4`（全屏减 4 单位），圆角 3xl
- 白板画布：1000×562px（Agent 坐标计算基于此尺寸）
- 场景列表项间距：mb-3（12px）

### 11.3 核心组件

#### ChatArea（`components/chat/chat-area.tsx`）

右侧面板，含两个 Tab：

| Tab | 内容 | 空状态 |
|-----|------|--------|
| Lecture Notes | 从 scenes 实时推导的课堂笔记，自动跟随当前 scene | BookOpen 图标 + "开始上课后笔记会出现在这里" |
| Chat Sessions | 讨论/QA 会话列表，可展开折叠 | MessageSquare 图标 + "还没有对话" |

**交互细节**：
- Drag handle 在左侧边缘，hover 时显示紫色竖线
- 折叠按钮在 Tab header 右侧
- Chat Tab 有活跃会话时在 Lecture Tab 上显示 amber 脉冲点

#### MessageBubble（`components/chat/chat-session.tsx`）

消息气泡，根据角色变色：

| 角色 | 背景 | 边框 | 文本色 |
|------|------|------|--------|
| User | `from-purple-600 to-purple-700` 渐变 | ring-purple-500/20 | 白色 |
| Teacher | `bg-white dark:bg-gray-800` | `border-gray-100 dark:border-gray-700` | `text-gray-700 dark:text-gray-200` |
| 其他 Agent | `bg-indigo-50 dark:bg-indigo-900/20` | `border-indigo-100/50` | `text-indigo-900 dark:text-indigo-200` |

**流式状态**：
- Agent 开始说话但无内容时：显示 3 个脉冲点（200ms 间隔递增动画）
- 流式输出中：文字末尾有 `animate-pulse` 光标
- 被中断：红色方点替代光标

**Inline Action Badge**：在文字流式完成前不显示，StreamBuffer 到达该动作时才插入。

#### InlineActionTag（`components/chat/inline-action-tag.tsx`）

气泡内的动作徽章，固定宽度 pill：

| 动作族 | 配色 |
|--------|------|
| Spotlight/Play | Yellow 系：`bg-yellow-50`，`border-yellow-300/40` |
| Laser | Red 系：`bg-red-50`，`border-red-300/40` |
| Whiteboard 动作 | Violet 系：`bg-violet-50`，带 `PenLine` 小芯片作为 left accent |
| Discussion | Amber 系：`bg-amber-50`，`border-amber-300/40` |

状态：`running` 或 `input-available` 时整体 `animate-pulse`，Icon 替换为 `Loader2`。

#### SessionList（`components/chat/session-list.tsx`）

会话折叠面板：
- Header：左侧彩色圆点（紫色=lecture，蓝色=qa，琥珀色=discussion），右侧消息计数 + ChevronDown
- Active 状态：`border-purple-200`，背景 `bg-purple-50/30`，绿色脉冲点
- 展开动画：`height: 0 → 'auto'`，duration 0.2s，`easeInOut`
- 讨论/QA 结束后：显示红色 "结束讨论" / "结束问答" 按钮（pulse 红点）

#### LectureNotesView（`components/chat/lecture-notes-view.tsx`）

左侧 Lecture Notes 面板：
- 按 scene 分组，每组有 timeline dot（当前 scene 为紫色发光）
- 当前 scene：`bg-purple-50/80`，带 `ring-purple-200/60`，右上角 "当前" 标签
- 自动滚动到当前 scene（`scrollIntoView: smooth, block: center`）
- Spotlight/Laser/Discussion 动作以图标形式内联在文字行内

#### AgentBar（`components/agent/agent-bar.tsx`）

顶栏智能体选择：
- 每个 Agent 显示为 VoicePill（头像 + 声音名称 + 下拉箭头）
- 点击打开 Popover：按 Provider 分组，每组显示 voice 列表
- 选中 voice 高亮（`bg-primary/10`），右侧预览按钮（Speaker 图标）
- 预览播放：`fetch('/api/generate/tts')`，生成 base64 audio 播放

#### AgentConfigPanel（`components/agent/agent-config-panel.tsx`）

全屏智能体管理：
- 卡片列表：Avatar（带 color border） + name + role + priority badge
- 每个卡片展示：能力描述（line-clamp-2）、可用动作（前 3 个 + `+N`）
- 支持新建/编辑/删除操作

#### Whiteboard（`components/whiteboard/index.tsx`）

浮层白板，Spring 动画：
```typescript
// 弹出
{ type: 'spring', stiffness: 120, damping: 18, mass: 1.2 }
// 退出
{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }
```

Header 工具栏：ResetView（RotateCcw）、Clear（Eraser + 抖动动画）、History（快照计数 badge）、Minimize（Minimize2）。

Clear 动画：`base 380ms + 55ms * elementCount`，上限 1400ms（cascade 效果）。

背景：`radial-gradient` 点阵（24px 间隔）。

#### Roundtable（`components/roundtable/index.tsx`）

底部讨论区，承载实时语音交互：
- Agent 头像（圆形，带声音波形动画指示器）
- 输入框（支持麦克风录音 / 键盘输入）
- 播放控制：Play/Pause、Speed（0.75x/1x/1.25x/1.5x）、Stop
- 讨论触发卡片：ProactiveCard 弹出确认

### 11.4 视觉语言

**色彩系统（CSS Variables）**：
```css
/* Light mode */
--primary: #722ed1;           /* 紫主色 */
--background: oklch(1 0 0);
--foreground: oklch(0.145 0 0);

/* Dark mode */
--primary: #8b47ea;          /* 亮紫 */
--background: oklch(0.145 0 0);
--foreground: oklch(0.985 0 0);
```

**主题色用途**：
- Purple：主操作、活跃状态、教师消息、Whiteboard
- Indigo：Assistant 消息
- Amber：Discussion 讨论、Warning
- Red：Stop 按钮、Laser 效果
- Yellow：Spotlight 效果

**字体**：`--font-sans: var(--font-sans)`（Next.js Geist Sans）

**图标库**：Lucide React，stroke-width 统一（大部分用默认 2，ActionTag 用 2.5）

**组件库**：shadcn/ui + `tw-animate-css`

### 11.5 动效设计

| 元素 | 动画 | 参数 |
|------|------|------|
| Whiteboard 弹出 | spring | stiffness: 120, damping: 18, mass: 1.2 |
| Whiteboard 退出 | ease | duration: 0.5, ease: [0.4, 0, 0.2, 1] |
| Active 气泡 glow | box-shadow loop | duration: 2.5s, repeat: Infinity |
| 消息条出现 | fade + y | opacity 0→1, y: 4→0, duration: 0.3s |
| 会话展开/折叠 | height | 0→auto, duration: 0.2s, easeInOut |
| Loading 点 | pulse | 200ms stagger（3 个点） |
| Chat Tab amber 点 | ping + opacity | absolute, inline-flex |
| 停止讨论按钮 | ping | absolute, inline-flex, red |
| Clear 抖动 | rotate | [-15, 15, -10, 10, 0], duration: 0.5s |

**滚动策略**：
- 新消息到达：`scrollIntoView: { behavior: 'smooth', block: 'end' }`
- 文本增量：`requestAnimationFrame` 节流，检测 `isAtBottom` 决定是否跟随
- 用户上滑查看历史：取消 auto-scroll，`isAtBottomRef` 控制

### 11.6 SSE 事件 → UI 状态映射

| SSE 事件 | UI 状态 | 视觉表现 |
|----------|---------|----------|
| `thinking` | 思考中 | 消息区 3 个灰色脉冲点 |
| `agent_start` | 新气泡开始 | 气泡出现（fade+y），带 Agent 颜色 |
| `text_delta` | 流式输出 | 文字逐字追加，末尾 pulse 光标 |
| `action` | 动作徽章 | InlineActionTag 插入文字流末端 |
| `agent_end` | 气泡完成 | 光标消失，`metadata.interrupted` 时显示红方点 |
| `cue_user` | 等待输入 | Roundtable 激活输入框 |
| `done` | 会话结束 | 停止按钮消失，显示结束分割线 |
| `error` | 出错 | Toast 提示 + 状态重置 |

### 11.7 主题系统

**实现方式**：CSS Custom Properties + `.dark` class。

```css
/* Tailwind 主题配置 */
@custom-variant dark (&:is(.dark *));

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --primary: #8b47ea;
}
```

**Dark mode 切换**：`.dark` class 挂在 `<html>` 上，通过 `next-themes` 的 `ThemeProvider` 控制。

**透明/毛玻璃**：
- ChatArea：`bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl`
- Whiteboard：`bg-white/95 dark:bg-gray-800/95 backdrop-blur-2xl`
- 卡片：`bg-white/50 dark:bg-gray-800/50`

### 11.8 组件状态规范

| 组件 | 状态 |
|------|------|
| Button | default / hover（`hover:bg-gray-200/90`）/ active（`scale-90`）/ disabled / loading |
| VoicePill | default / hover / disabled（`opacity-30`，VolumeX 图标）|
| SessionCard | idle（灰边框）/ active（紫边框+pulse 点）/ expanded |
| MessageBubble | streaming（光标）/ interrupted（红方点）/ complete（无指示器）|
| Whiteboard | closed（不渲染）/ open（spring 动画）/ clearing（cascade 动画）|
| Input | default / focus（`ring-purple-500`）/ error（红边框）/ disabled |

### 11.9 复刻 UI 清单

| 优先级 | 文件 | 说明 |
|--------|------|------|
| P0 | `components/chat/chat-area.tsx` | 右侧面板 + Tabs + drag-resize |
| P0 | `components/chat/chat-session.tsx` | 气泡渲染 + 角色配色 + 流式光标 |
| P0 | `components/chat/inline-action-tag.tsx` | 动作徽章 + 5 套配色 |
| P0 | `components/chat/session-list.tsx` | 会话折叠 + 状态图标 |
| P0 | `components/chat/lecture-notes-view.tsx` | 课堂笔记 + 自动滚动 |
| P1 | `components/whiteboard/index.tsx` | 白板浮层 + spring 动画 |
| P1 | `components/roundtable/index.tsx` | 讨论区 + 播放控制 |
| P1 | `components/agent/agent-bar.tsx` | Agent 选择 + Voice Popover |
| P1 | `app/globals.css` | 主题变量 + dark mode |
| P2 | `components/agent/agent-config-panel.tsx` | Agent 管理面板 |

### 11.10 UI 关键陷阱

1. **StreamBuffer 控制显示时机**：Action Badge 不能在 StreamBuffer 到达前渲染，需要在 `onTextReveal` 回调中插入
2. **auto-scroll 防打扰**：用户上滑查看历史时设置 `isAtBottomRef = false`，新增消息不触发滚动
3. **sceneEpoch 丢弃过期回调**：场景切换时 bump epoch，任何基于旧 scene 的 SSE 回调必须被忽略
4. **manualStop 双 flash 防护**：通过 `manualStopRef` 标记防止 `onDiscussionEnd` 和 `doSessionCleanup` 重复触发结束动画
5. **Whiteboard 互斥**：Whiteboard 打开时 Slide Canvas 隐藏；Slide 效果需 `wb_close` 后才能使用
6. **dark mode 下 backdrop-blur**：部分 Android 浏览器 backdrop-blur 性能差，需降级处理
