# BetterGI AI

[English](README.md)

BetterGI AI 是一个面向 BetterGI 和 AutoBGI 的单一 Agent Skill 包，以及一组本地辅助脚本。

它不替代 BetterGI，不重新实现游戏自动化，也不另起一套 runner。BetterGI 仍然是上游桌面自动化应用；AutoBGI 是推荐的执行层，通过 MCP SSE 服务对外提供受约束的调用能力。

## 项目定位

BetterGI AI 目前只做三件事：

- 帮助 agent 配置和理解 BetterGI、AutoBGI、AutoBGI MCP 的关系。
- 安全编辑 BetterGI 本地 JSON 配置，包括一条龙、配置组、脚本仓库订阅等。
- 通过 AutoBGI MCP 查询状态，并在用户明确授权后启动一条龙或配置组。

明确不做：

- 不直接控制原神窗口、键鼠输入或任意 shell 命令。
- 不绕过 BetterGI/AutoBGI 自身能力重新实现执行器。
- 不自动修改账号、凭据、cookie、API key 或无关设置。

## Skill 安装

只需要安装或复制这个目录：

```text
skills/bettergi-ai
```

例如可以同步到：

```text
C:\Users\10020\.agents\skills\bettergi-ai
```

这个包里包含：

- `SKILL.md`：唯一的 skill 入口。
- `references/`：按任务拆分的说明，包括安装配置、状态读取、生命周期、一条龙、配置组、AutoBGI 安全控制。
- `scripts/`：用于 JSON 编辑、库存扫描、MCP 探测和离线策略测试的 Python 脚本。

## 内部结构

`bettergi-ai` 是唯一的外层 skill。它根据任务类型加载对应参考文档：

```text
skills/bettergi-ai/SKILL.md
  -> references/setup.md
  -> references/status.md
  -> references/lifecycle.md
  -> references/config-editor.md
  -> references/one-dragon.md
  -> references/autobgi-safe-control.md
  -> scripts/*.py
```

agent 不应该一次性读取所有参考文档，而是按用户请求加载必要部分。

## 本地配置

机器相关配置不进入 Git。辅助脚本会读取 `.bettergi-ai/local.settings.json`：

```json
{
  "bettergi": {
    "installPath": "C:\\Program Files\\BetterGI"
  },
  "autobgi": {
    "installPath": "C:\\Tools\\autobgi",
    "mcp": {
      "url": "http://127.0.0.1:10086/mcp/sse",
      "apiKey": "..."
    }
  }
}
```

不要提交真实 API key、cookie、账号数据、日志、截图或 BetterGI 用户数据。

## 常用命令

运行 BetterGI 配置辅助脚本的 smoke test：

```bash
python skills/bettergi-ai/scripts/run_bettergi_config_smoke_tests.py
```

默认会创建临时 BetterGI fixture，因此即使没有真实 BetterGI 安装，也可以在 macOS、Linux 或 Windows 上验证辅助逻辑。需要针对真实 BetterGI 安装验证时：

```bash
python skills/bettergi-ai/scripts/run_bettergi_config_smoke_tests.py --install-path "C:\Program Files\BetterGI"
```

探测 AutoBGI MCP 工具：

```bash
python skills/bettergi-ai/scripts/probe_autobgi_mcp.py --output .bettergi-ai/status/autobgi-tools.json
```

离线验证 AutoBGI MCP 安全策略：

```bash
python skills/bettergi-ai/scripts/run_autobgi_policy_smoke_tests.py
```

读取 AutoBGI 进度并汇总可用能力：

```bash
python skills/bettergi-ai/scripts/probe_autobgi_mcp.py --call-tool findBgiIndex --output .bettergi-ai/status/findBgiIndex.json
python skills/bettergi-ai/scripts/summarize_bettergi_capabilities.py --status-json .bettergi-ai/status/findBgiIndex.json
```

## 安全策略

默认允许的 AutoBGI MCP 工具：

- `findBgiIndex`
- `queryBackpack`
- `captureDesktopScreenshot`，仅在用户明确要求视觉确认时使用
- `queryCharacterBuild`，仅查询用户指定的单个角色
- `RunCronTask`，仅允许立即执行用户确认过的 `启动一条龙` 或 `启动配置组`

默认禁用：

- `continueOneDragon`
- `startObsRecording`
- `stopObsRecording`
- `collectMaterialRoutes`
- `collectCookingRoutes`
- 关闭、备份、签到、更新、原始输入、远程控制或任意命令执行

## 执行顺序

通过 AutoBGI MCP 执行任务时，不要提前打开 BetterGI。

原因是：BetterGI 已经打开时，AutoBGI 的 BetterGI 命令行启动可能失败。正确流程是：

```text
检查或启动 AutoBGI
  -> 调用 findBgiIndex 读取状态
  -> 确认目标一条龙或配置组名称
  -> 调用 RunCronTask
  -> 再次调用 findBgiIndex 验证状态
```

执行后必须报告 MCP 调用结果或错误。没有工具结果时，不应声称任务已经启动。
