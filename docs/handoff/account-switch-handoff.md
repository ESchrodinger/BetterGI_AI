# BetterGI_AI 账号切换交接文档

更新时间：2026-07-22

## 当前状态

- 仓库：`https://github.com/ESchrodinger/BetterGI_AI`
- 本地路径：`C:\Users\10020\project\BetterGI_AI`
- 当前分支：`codex/agent-control-plane`
- 最新提交：`02e8503 Improve BetterGI AI skill robustness`
- 远端状态：该提交已推送到 `origin/codex/agent-control-plane`
- 交接文档状态：本文件用于账号切换后的恢复和继续开发；提交后应与远端分支一起保存。
- 工作区状态：提交本文件后应保持干净。若未来看到无关未跟踪目录，先确认来源，不要顺手删除。

## 项目方向

BetterGI_AI 现在不是重新实现 runner，也不是替代 BetterGI/AutoBGI。

当前定位是：

- BetterGI：上游桌面自动化应用，真正执行游戏自动化。
- AutoBGI：上游执行层/Web 层/MCP 层，负责启动 BetterGI、提供 MCP SSE 工具、读取状态。
- BetterGI_AI：单一 Agent Skill 包，负责让 agent 安全、稳定地配置 BetterGI/AutoBGI，并通过受约束的 AutoBGI MCP 执行用户确认过的任务。

重点目标：

- 开箱即用地帮助 agent 配置 BetterGI + AutoBGI。
- 安全编辑 BetterGI 本地 JSON，包括一条龙、配置组、脚本仓库订阅。
- 通过 AutoBGI MCP 读取状态和启动一条龙/配置组。
- 不瞎编 BetterGI 脚本，不绕过 BetterGI/AutoBGI 自己造执行器。

## Skill 安装形态

仓库中的主 skill：

```text
skills/bettergi-ai
```

用户目录中的已同步 skill：

```text
C:\Users\10020\.agents\skills\bettergi-ai
```

只有 `bettergi-ai` 这一个总括 skill 应该交给其他 agents 使用，不要把内部 reference 当成多个独立 skill 安装。

如果仓库 skill 更新后，需要同步到用户目录：

```powershell
$src = Resolve-Path -LiteralPath "C:\Users\10020\project\BetterGI_AI\skills\bettergi-ai"
$dst = "C:\Users\10020\.agents\skills\bettergi-ai"
robocopy $src.Path $dst /MIR /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -le 7) { exit 0 } else { exit $LASTEXITCODE }
```

## 入口文件

先读：

```text
skills/bettergi-ai/SKILL.md
```

再按任务读取对应 reference：

- `references/setup.md`：安装路径、MCP URL、apiKey、AutoBGI 配置。
- `references/status.md`：读取状态、进度、版本检查。
- `references/lifecycle.md`：启动/重启 AutoBGI、BetterGI/AutoBGI/原神关系。
- `references/config-editor.md`：配置组、脚本库存、脚本仓库、订阅。
- `references/one-dragon.md`：一条龙 JSON 配置。
- `references/intent-resolution.md`：模糊游戏说法联网解析。
- `references/autobgi-safe-control.md`：AutoBGI MCP 安全调用策略。
- `references/upstream-docs.md`：上游项目文档和版本更新信息。
- `references/windows-encoding.md`：Windows PowerShell 中文编码处理。

## MCP 连接关键点

默认 MCP 配置形态：

```json
{
  "mcpServers": {
    "AutoBGI": {
      "type": "sse",
      "url": "http://127.0.0.1:10086/mcp/sse",
      "headers": {
        "apiKey": "abgi"
      }
    }
  }
}
```

不要死记默认值，实际值要从 AutoBGI 配置读取：

- MCP URL = AutoBGI Web 服务地址 + `/mcp/sse`
- 端口来自 AutoBGI `main.json` 的 `post`
- `post` 为空或 `":"` 时，AutoBGI 源码 fallback 是 `:8082`
- `apiKey` 来自 AutoBGI `abgiUser.yaml` 的 `auth.api_key`
- 请求头名字必须是 `apiKey`
- Web 登录和 MCP 是两回事；Web 未登录不代表 MCP 不能用
- MCP 必须要求 AutoBGI 正在运行，并且 `main.json` 里 `Control.IsMcp=true`

探测：

```bash
python skills/bettergi-ai/scripts/probe_autobgi_mcp.py --output .bettergi-ai/status/autobgi-tools.json
```

读取进度：

```bash
python skills/bettergi-ai/scripts/probe_autobgi_mcp.py --call-tool findBgiIndex --output .bettergi-ai/status/findBgiIndex.json
```

手动连接检查：

```bash
curl.exe -i -N --max-time 5 -H "apiKey: abgi" http://127.0.0.1:10086/mcp/sse
```

成功信号：

- `Content-Type: text/event-stream`
- SSE 中出现 `event: endpoint`

常见失败：

- `connection_refused`：AutoBGI 没运行、端口错、旧进程没重启。
- `http_401` / `http_403`：apiKey 错。
- `http_404`：路径错，应为 `/mcp/sse`。
- 返回 HTML 或非 SSE：AutoBGI Web 在，但 MCP 没注册；检查 `Control.IsMcp=true` 并重启 AutoBGI。

## AutoBGI 重启

推荐命令：

```bash
python skills/bettergi-ai/scripts/manage_bettergi_lifecycle.py --action restart-autobgi
```

重启后必须验证：

- PID 或进程启动时间发生变化。
- AutoBGI 从自己的安装目录启动。
- Web 端口与 `main.json.post` 一致。
- `/mcp/sse` 带正确 `apiKey` 后返回 SSE。

不要通过“提前打开 BetterGI”解决 AutoBGI MCP 连接问题。执行任务时应让 AutoBGI 启动 BetterGI，再由 BetterGI 启动/控制原神。

## 安全 MCP 子集

默认允许：

- `findBgiIndex`
- `queryBackpack`
- `captureDesktopScreenshot`，仅用户明确要求视觉确认时使用
- `queryCharacterBuild`，仅查询一个用户指定角色
- `RunCronTask`，仅允许立即执行 `启动一条龙` 或 `启动配置组`，且 `delayInSeconds=0`

默认禁用：

- `continueOneDragon`
- `startObsRecording`
- `stopObsRecording`
- `collectMaterialRoutes`
- `collectCookingRoutes`
- 关闭、备份、签到、更新、原始输入、远程控制或任意命令执行

执行前必须：

1. 调 `findBgiIndex`。
2. 确认没有冲突任务。
3. 本地验证目标一条龙/配置组名称存在。
4. 用户已明确批准 exact target。
5. 调 `RunCronTask`。
6. 再调 `findBgiIndex` 验证状态。

没有 MCP 工具结果时，不要声称任务已经启动。

## 配置组规则

配置组文件在：

```text
User\ScriptGroup\<name>.json
```

重要规则：

- 创建配置组不等于执行。
- 配置组不会自动加入一条龙。
- 如果用户要作为一条龙运行，必须编辑目标 `User\OneDragon\<name>.json`，把配置组加入并启用。
- 如果用户要单独运行配置组，使用 AutoBGI MCP `RunCronTask`，`taskName="启动配置组"`，`params` 为精确配置组名。
- 配置组项目必须来自 BetterGI 本地库存或仓库搜索结果。
- 不允许瞎编 JS 文件、路线文件、键鼠脚本或 Shell 项。

创建/编辑配置组脚本：

```bash
python skills/bettergi-ai/scripts/edit_bettergi_script_group.py --group-name "采集示例" --create --add-project "Pathing|史莱姆速刷.json|敌人与魔物\史莱姆" --dry-run
```

该脚本默认会拒绝不存在的项目引用，避免 agent 瞎编脚本。

## 一条龙规则

一条龙文件在：

```text
User\OneDragon\<name>.json
```

BetterGI 现有结构粒度：

- 自动秘境
- 合成树脂
- 自动地脉花
- 领取邮件 / 领取每日奖励
- 领取尘歌壶奖励
- 自动首领讨伐 / 自动幽境危战
- 用户自建 ScriptGroup 项

重要规则：

- 新建一条龙不能是空配置，必须显式启用至少一个任务或一个已存在配置组。
- 如果用户要窄任务，优先用 `--only-task` 清掉无关任务。
- 创建/编辑一条龙不等于执行。
- 执行一条龙必须切到 AutoBGI MCP 安全流程，调用 `RunCronTask`，`taskName="启动一条龙"`，`params` 为精确一条龙配置名。

列出本机 BetterGI 动态选项：

```bash
python skills/bettergi-ai/scripts/edit_bettergi_one_dragon.py --list-options
```

示例：

```bash
python skills/bettergi-ai/scripts/edit_bettergi_one_dragon.py --config-name "ai_domain_only" --create --only-task "自动秘境" --domain-name "霜凝的机枢" --dry-run
```

## 模糊指令处理

用户经常会说：

- “博士的周本”
- “木偶的周本天赋材料”
- “新出的圣遗物本”
- “刷某个角色材料”

规则：

1. 不靠模型记忆猜。
2. 先联网搜索，确认当前版本里的标准角色、材料、周本、秘境名称。
3. 再回到 BetterGI 本地数据匹配：
   - `edit_bettergi_one_dragon.py --list-options`
   - `list_bettergi_inventory.py --search "..."`
   - `search_bettergi_repo.py --search "..."`
4. 本地没有时，搜索仓库索引/订阅路径，并提醒用户通过 BetterGI 更新订阅。
5. 仍有歧义时问用户，不要直接写 JSON 或启动任务。

## 脚本仓库和订阅

相关路径：

```text
User\Subscriptions\*.json
Repos\<repo-folder>\repo.json
Repos\<repo-folder>\repo_updated.json
```

搜索仓库索引：

```bash
python skills/bettergi-ai/scripts/search_bettergi_repo.py --search "子探测单元" --include-directories --limit 20
```

编辑订阅：

```bash
python skills/bettergi-ai/scripts/edit_bettergi_subscriptions.py --add-path "pathing/地方特产/枫丹/子探测单元" --dry-run
```

编辑订阅不等于下载文件。真正同步需要 BetterGI UI 里的“一键更新订阅”或上游支持的更新流程。

## Windows / PowerShell 编码

本项目包含大量中文 JSON/Markdown。PowerShell 默认编码经常把中文显示成乱码，但这不代表文件损坏。

在 PowerShell 里读写中文文件前先执行：

```powershell
. .\skills\bettergi-ai\scripts\Use-Utf8PowerShell.ps1
```

然后用：

```powershell
Read-Utf8Text -LiteralPath .\README.zh-CN.md
```

或至少：

```powershell
Get-Content -Encoding UTF8 -LiteralPath .\README.zh-CN.md
```

JSON 修改优先用 Python helper，不要用 PowerShell 重定向 `>` / `>>` 写中文 JSON。

编码验证：

```bash
python skills/bettergi-ai/scripts/run_encoding_smoke_tests.py
```

## 版本检查

通过 AutoBGI 只读 Web API 检查 BetterGI/AutoBGI 版本：

```bash
python skills/bettergi-ai/scripts/check_upstream_versions.py --output .bettergi-ai/status/versions.json
```

只读检查可以直接做；任何更新动作都必须用户明确批准。

## 验证命令

提交前建议跑：

```bash
python skills/bettergi-ai/scripts/run_encoding_smoke_tests.py
python skills/bettergi-ai/scripts/run_autobgi_policy_smoke_tests.py
python skills/bettergi-ai/scripts/run_bettergi_config_smoke_tests.py
git diff --check
```

当前最后一次上传前结果：

- 编码烟测：7 项通过。
- AutoBGI MCP 策略烟测：14 项通过。
- BetterGI 配置烟测：18 项通过。
- `git diff --check`：通过，仅有 Windows 行尾提示。

## 新账号接手建议

1. 先读本文件。
2. 再读 `skills/bettergi-ai/SKILL.md`。
3. 如果要真实操作本机 BetterGI/AutoBGI，先确认本机路径、AutoBGI 是否运行、MCP 是否可达。
4. 不要直接启动 BetterGI 来绕过 AutoBGI MCP。
5. 不要把本机真实安装路径、apiKey、账号信息写入仓库文档。
6. 如果需要修改 skill，改仓库内 `skills/bettergi-ai`，验证通过后同步到 `C:\Users\10020\.agents\skills\bettergi-ai`。
7. 修改完成后再提交和推送。

## 已知下一步

- 继续扩充更多真实 BetterGI 一条龙设置样例，并尽量让每个样例都有 dry-run 和真实 UI 验证路径。
- 探索 AutoBGI MCP 剩余工具，但默认保持禁用，只有设计出安全 workflow 后再开放。
- 对模糊意图解析做更多案例测试，例如角色外号、周本材料、圣遗物本、天赋书日程。
- 继续避免硬编码用户安装路径，让新用户通过询问或本地 settings 提供路径。
