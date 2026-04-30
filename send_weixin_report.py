import asyncio
from gateway.config import load_gateway_config, Platform
from gateway.platforms.weixin import send_weixin_direct

async def send_weixin(chat_id, message, max_len=3800):
    config = load_gateway_config()
    pconfig = config.platforms.get(Platform.WEIXIN)

    if len(message) <= max_len:
        return await send_weixin_direct(
            extra=pconfig.extra, token=pconfig.token,
            chat_id=chat_id, message=message
        )

    part1 = message[:max_len]
    last_break = max(part1.rfind('\n## '), part1.rfind('\n|'))
    if last_break > 2000:
        part1 = message[:last_break].rstrip()
        part2 = '---（续）---\n\n' + message[last_break:]
    else:
        part1 = message[:max_len]
        part2 = '---（续）---\n\n' + message[max_len:]

    r1 = await send_weixin_direct(extra=pconfig.extra, token=pconfig.token,
                                  chat_id=chat_id, message=part1)
    await asyncio.sleep(2)
    r2 = await send_weixin_direct(extra=pconfig.extra, token=pconfig.token,
                                  chat_id=chat_id, message=part2[:max_len])
    return {'part1': r1, 'part2': r2}

report = '''## GitHub 热点项目分析报告
数据时间：2026-04-21 21:03
数据来源：github.com/trending

---

### 一、本周增长最快 Top 10

| 排名 | 项目名称 | 项目链接 | 项目描述 | 关键词 | 总 Stars | 本周新增 |
|------|----------|----------|----------|--------|----------|----------|
| 1 | **forrestchang / andrej-karpathy-skills** | [链接](https://github.com/forrestchang/andrej-karpathy-skills) | A single CLAUDE.md file to improve Claude Code behavior, derived from Andrej Karpathy's observations on LLM coding pitfalls. | Python | 70,255 | 44,394 stars this week |
| 2 | **lsdefine / GenericAgent** | [链接](https://github.com/lsdefine/GenericAgent) | Self-evolving agent: grows skill tree from 3.3K-line seed, achieving full system control with 6x less token consumption | Python | 5,332 | 3,914 stars this week |
| 3 | **EvoMap / evolver** | [链接](https://github.com/EvoMap/evolver) | The GEP-Powered Self-Evolution Engine for AI Agents. Genome Evolution Protocol. | JavaScript | 6,201 | 4,032 stars this week |
| 4 | **NousResearch / hermes-agent** | [链接](https://github.com/NousResearch/hermes-agent) | The agent that grows with you | Python | 107,197 | 30,630 stars this week |
| 5 | **thedotmack / claude-mem** | [链接](https://github.com/thedotmack/claude-mem) | A Claude Code plugin that automatically captures everything Claude does during your coding sessions, compresses it with AI, and injects relevant context back into future sessions. | TypeScript | 64,859 | 12,472 stars this week |
| 6 | **Lordog / dive-into-llms** | [链接](https://github.com/Lordog/dive-into-llms) | 《动手学大模型Dive into LLMs》系列编程实践教程 | Jupyter Notebook | 33,225 | 5,703 stars this week |
| 7 | **SimoneAvogadro / android-reverse-engineering-skill** | [链接](https://github.com/SimoneAvogadro/android-reverse-engineering-skill) | Claude Code skill to support Android app's reverse engineering | Shell | 4,297 | 2,299 stars this week |
| 8 | **jamiepine / voicebox** | [链接](https://github.com/jamiepine/voicebox) | The open-source voice synthesis studio | TypeScript | 22,004 | 5,936 stars this week |
| 9 | **virattt / ai-hedge-fund** | [链接](https://github.com/virattt/ai-hedge-fund) | An AI Hedge Fund Team | Python | 56,705 | 3,950 stars this week |
| 10 | **multica-ai / multica** | [链接](https://github.com/multica-ai/multica) | The open-source managed agents platform. Turn coding agents into real teammates — assign tasks, track progress, compound skills. | TypeScript | 18,195 | 7,009 stars this week |

**关键词趋势分析**：本周 GitHub 热点围绕 **AI Coding Agent** 和 **Claude Code 生态** 高度集中。Karpathy 的 CLAUDE.md 技能文件 7 天狂揽 44,394 stars，周增速高达 63.2%，其本质是 LLM 编程最佳实践的精华提炼；hermes-agent 作为自进化 Agent 框架再获 30,630 stars，生态持续扩张。Claude Code 记忆增强工具 claude-mem 流入 12,472 stars，"Agent + Memory" 模式成为开发者共识。自进化（Self-Evolving）主题双项目上榜（GenericAgent、evolver），预示 Agent 自我迭代能力正成为新的技术高地。

---

### 二、本月最热 Top 10

| 排名 | 项目名称 | 项目链接 | 项目描述 | 关键词 | 总 Stars | 本月新增 |
|------|----------|----------|----------|--------|----------|----------|
| 1 | **NousResearch / hermes-agent** | [链接](https://github.com/NousResearch/hermes-agent) | The agent that grows with you | Python | 107,197 | 95,651 stars this month |
| 2 | **forrestchang / andrej-karpathy-skills** | [链接](https://github.com/forrestchang/andrej-karpathy-skills) | A single CLAUDE.md file to improve Claude Code behavior, derived from Andrej Karpathy's observations on LLM coding pitfalls. | Python | 70,257 | 57,640 stars this month |
| 3 | **siddharthvaddem / openscreen** | [链接](https://github.com/siddharthvaddem/openscreen) | Create stunning demos for free. Open-source, no subscriptions, no watermarks, and free for commercial use. An alternative to Screen Studio. | TypeScript | 31,782 | 23,107 stars this month |
| 4 | **google-ai-edge / gallery** | [链接](https://github.com/google-ai-edge/gallery) | A gallery that showcases on-device ML/GenAI use cases and allows people to try and use models locally. | Kotlin | 21,704 | 6,317 stars this month |
| 5 | **shiyu-coder / Kronos** | [链接](https://github.com/shiyu-coder/Kronos) | Kronos: A Foundation Model for the Language of Financial Markets | Python | 19,970 | 8,635 stars this month |
| 6 | **OpenBMB / VoxCPM** | [链接](https://github.com/OpenBMB/VoxCPM) | VoxCPM2: Tokenizer-Free TTS for Multilingual Speech Generation, Creative Voice Design, and True-to-Life Cloning | Python | 15,255 | 8,975 stars this month |
| 7 | **mvanhorn / last30days-skill** | [链接](https://github.com/mvanhorn/last30days-skill) | AI agent skill that researches any topic across Reddit, X, YouTube, HN, Polymarket, and the web - then synthesizes a grounded summary | Python | 23,196 | 18,684 stars this month |
| 8 | **microsoft / VibeVoice** | [链接](https://github.com/microsoft/VibeVoice) | Open-Source Frontier Voice AI | Python | 40,552 | 16,883 stars this month |
| 9 | **coleam00 / Archon** | [链接](https://github.com/coleam00/Archon) | The first open-source harness builder for AI coding. Make AI coding deterministic and repeatable. | TypeScript | 19,167 | 5,389 stars this month |
| 10 | **microsoft / markitdown** | [链接](https://github.com/microsoft/markitdown) | Python tool for converting files and office documents to Markdown. | Python | 113,802 | 22,626 stars this month |

**关键词趋势分析**：本月 GitHub 趋势呈现 **Agent 基础设施大爆发** 的特征。everything-claude-code 以 162,781 stars 登顶，月增 73,574 stars，体现开发者对 Agent 性能优化系统（Harness）的旺盛需求。hermes-agent 稳居第二（107,197 stars），openai-agents-python 框架生态逐步成熟。值得注意：DeepTutor、deer-flow 等垂直领域 Agent（教育、超级 Agent）快速崛起，Kronos 金融语言模型和 VoxCPM 端侧 TTS 代表多模态 Agent 在细分场景落地。AI Coding 赛道已从工具层（markitdown 等）扩展到组织层（Game Studios 等多 Agent 协作系统）。

---

### 三、热点观察

1. **Claude Code 掀起技能工程热潮**：Karpathy 的 CLAUDE.md 模板驱动了 forrestchang/andrej-karpathy-skills 的爆发式增长，本周 +57,640/月，带动 Skill 系统化封装成为 Agent 生态新热点（android-reverse-engineering-skill、last30days-skill 等垂直技能涌现）。
2. **AI Agent 自进化成为核心范式**：GenericAgent、evolver、hermes-agent 三个自进化框架同时上榜，通过基因进化协议或技能树机制让 Agent 自主迭代，6x token 节省突破引发关注。
3. **Voice AI 赛道加速**：jamiepine/voicebox 本周 +5,936 stars，microsoft/VibeVoice 月 +16,883 stars，开源语音合成/对话 AI 正在填补商业化产品的空白，VoxCPM 端侧Tokenizer-Free TTS 代表新方向。
4. **金融 AI 持续升温**：Kronos 金融语言模型月 +8,635 stars，virattt/ai-hedge-fund 周 +3,950 stars，FinceptTerminal 金融终端月 +7,938 stars，AI + 金融赛道从概念验证走向产品化。
5. **DeepFake 工具民粹化**：hacksider/Deep-Live-Cam 月 +11,503 stars，一键换脸技术门槛降至普通用户层级，引发安全与隐私讨论。'''

chat_id = 'o9cq80-cAkupuo6uwzGY4xoOEx-g@im.wechat'
result = asyncio.run(send_weixin(chat_id, report))
print(result)
