---
title: 模型只是 CPU，插件运行时才是 Agent 的操作系统：从 DeepSeek Harness 到 Zongsoft
date: 2026-08-15 23:00:00
comments: true
categories:
- zongsoft
tags:
- DeepSeek Harness
- Cordis
- Zongsoft.Plugins
- AI Agent
- 插件架构
---

![由可插拔模块组成的 Agent 运行时](/blog/images/agent-os-hero.png)

> **导读**：DeepSeek Harness（DSH）开源后，“一切皆插件”成了 AI Agent 圈最热的口号。但口号人人会说，机制决定生死。本文不写“DSH 很厉害”的观后感，而是翻开它的真实组合清单与源码，把“一切皆插件”拆成插件运行时必须回答的**五个底层问题**——能力坐标、依赖激活、效果撤回、组合形态、自省演化。
>
> 有意思的是：这五个问题，[Zongsoft.Plugins](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Plugins) 从 **2010 年 4 月**创立那天起，就在用另一套机制回答。十六年后，两条独立演化的技术路线在 Agent 时代会合。它们给出的答案不同，但问的是同一个问题。本文要论证的，正是标题里的那句判断：**模型只是 CPU，插件运行时才是 Agent 的操作系统。**

## 引言：模型只是 CPU，插件运行时才是 Agent 的操作系统

当所有人都在追逐更大的模型时，DeepSeek 却把一个看起来不那么性感的东西推到了聚光灯下：**Harness（驾驭框架）**。如果借用计算机体系结构的比喻，模型更像 CPU——它决定推理能力的上限，却不会自动长出文件系统、工具、权限、会话、持久化、沙箱、界面和协作协议。真正把这些能力组织成产品的，是模型外面的 Harness。Claude Code 与 ChatGPT(Codex) CLI 的走红，不单单是模型之胜，与之配套的 Harness 才是帮助它们走向决战之巅的战车：**模型之外的那一层，正在成为产品差异的主战场。**

当然，“操作系统”不是给插件框架换一个时髦名字。它提出的是一条更严格的判断标准：

> **当一个运行时可以安装、组合、替换、撤销和治理 Agent 的各种能力时，它才开始具备 Agent OS 的形状。**

2026 年 8 月，DeepSeek 开源了 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（DSH）开发者预览版，底层以 vendor 方式引入 [Cordis](https://github.com/cordiverse/cordis) 插件框架，并配套了论文 [A Programming Paradigm for Spatiotemporal Composability](https://github.com/cordiverse/paper)。它最显眼的宣言只有一句话：

> **Everything is a Plugin —— 模型适配器、工具、会话、沙箱、存储、Agent 循环、乃至整个 Web 界面，都是插件。**

这句话很有流量，但也容易产生误导。很多人把“插件化”理解成“把功能拆成很多 npm 包”——这只是物理拆分，还没有解决组合问题。真正的插件化，必须回答一组更底层的问题：

- 插件把能力放在哪里，别人怎么找到它？
- 插件什么时候可以开始工作，依赖没了怎么办？
- 插件改变了世界，卸载时怎么把世界还回去？
- “产品是什么”由谁决定，能不能晚于编译再决定？
- 运行中的系统能被观察、被修改吗，谁有资格改？

这五个问题，我称之为**插件运行时的五项机制**。DSH 用 Cordis 的“上下文 + 效果 + 反应式依赖”回答它们；而 [Zongsoft.Plugins](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Plugins) 从 **2010 年 4 月**创立那天起，就用“插件树 + 清单 + 构建器/解析器”回答它们。十六年后，两条独立演化的路线在 Agent 时代会合，并且抵达了同一个结论：

> **插件不是“给完成的应用加功能”的扩展点，而是“组成这个应用本身”的组织单位。**

## 一、先看 DSH：一行一个插件

要理解 DSH，最好的入口不是架构图，而是它的**组合清单**。DSH 把每个 profile（产品形态）定义为一棵从“空根”上长出来的插件树，每个插件在 `cordis.patch.yml` 里占**一行**。下面是从 `dsh-base` 组合包的真实 `cordis.patch.yml` 中节选的片段（该包是每个 profile 的第一层）：

```yaml
# dsh-base/cordis.patch.yml（节选）
- insert:
    - id: timer
      name: '@deepseek-ai/cordis-plugin-timer'
    - id: llm
      name: '@deepseek-ai/dsh-llm'
    - id: session
      name: '@deepseek-ai/dsh-session'
    - id: agent
      name: '@deepseek-ai/dsh-agent'
    - id: agent-default-model
      name: '@deepseek-ai/dsh-agent-default-model'
      config:
        provider: deepseek-official
        model: deepseek-v4-flash
    - id: tools
      name: '@deepseek-ai/dsh-tools'
    - id: agent-loop
      name: '@deepseek-ai/dsh-agent-loop'
      config:
        agents: []
    - id: sandbox
      name: '@deepseek-ai/dsh-sandbox-local'
    - id: approval
      name: '@deepseek-ai/dsh-user-approval'
    - id: session-persistence-jsonl
      name: '@deepseek-ai/dsh-session-persistence-jsonl'
    - id: web
      name: '@deepseek-ai/dsh-web'
      config:
        searchProvider: deepseek-official
```

每一行的语义是：“把名为 X 的插件，以这份 config 挂进运行时”。行与行之间**没有加载顺序的含义**——清单里的注释写得很直白：“Row order carries no load semantics (activation is service-availability driven)”，即**激活由服务可用性驱动，而不是行序**。一个插件声明自己依赖哪些服务（`inject`），依赖齐了它才启动；依赖消失，它先失活，等依赖回来再重新激活。这是“插件”与“一堆 import”最本质的区别。

![Agent Runtime 的完整分层](/blog/images/agent-os-runtime-stack.png)

### 连“内核”都是插件

DSH 最激进的地方在于：**它没有一个需要被“扩展”的特权内核**。我们通常认为的 Agent 内核——循环、会话、工具系统——在 DSH 里全部是插件行。看 `dsh-agent-loop` 包的 README，这句话值得反复读：

> “这是 harness 中唯一包含具体循环逻辑的包。其他所有内容要么是抽象服务，要么是针对扩展点的插件：新行为应放入插件，而不是这里。”

也就是说，整个 DSH 只有一个“具体实现”：那个调用模型、运行工具、然后重复的 React Loop。其余一切——压缩、持久化、遥测、审批、沙箱、UI——都是监听事件分类体系（`agent/*`、`tools/*`、`session/event`）的插件。工具执行也不是硬编码的“调一下函数”，而是一条可以被任何插件拦截的流水线：

```text
tools/pre-execute（允许/拒绝/询问）
  → guard（单调策略）
    → tools/execute（超时/重试包装）
      → tools/post-execute（检查/替换结果、附加上下文）
        → finalizeContent（最终内容）
          → tools/result（只读观测）
```

权限沙箱挂在 `pre-execute`，计划模式挂在 `pre-execute` + 提示词，上下文压缩监听 `agent/pre-step` 与 `agent/request-error`，崩溃恢复监听 `agent/request-error` 做退避重试……每个“能力”都是事件流上的一个听众，而不是循环里的一个 `if` 分支。

不过要划清一条边界：“没有特权产品内核”不等于“没有运行时基座”。DSH 仍然依赖 Cordis 提供上下文、依赖解析、事件与生命周期语义。准确的说法是：**Cordis 是组合规则，DSH 是由这些规则组装出来的产品。**

### 连 UI 都是插件

再往外一层：DSH 的 Web 界面也不是“给 Agent 写的一个前端”，而是一批 `dsh.client` 插件行。`dsh-web-app/cordis.patch.yml` 的真实内容里，浏览器里每一个可见的部件都有对应的一行：

```yaml
# dsh-web-app/cordis.patch.yml（节选）
- insert:
    - id: connection
      name: '@deepseek-ai/dsh-client-connection'
    - id: ui-conversation
      name: '@deepseek-ai/dsh-client-ui-conversation'
    - id: ui-tool
      name: '@deepseek-ai/dsh-client-ui-tool'
    - id: ui-settings
      name: '@deepseek-ai/dsh-client-ui-settings'
    - id: ui-cordis
      name: '@deepseek-ai/dsh-client-ui-cordis'
    - id: ui-plan
      name: '@deepseek-ai/dsh-client-ui-plan'
    - id: ui-goal
      name: '@deepseek-ai/dsh-client-ui-goal'
```

“模块节点把这张插件名录扫描进 `window.__DSH_BOOT__`”——浏览器插件在 Cordis 存在之前就被引导，然后作为插件条目被运行时收养。删除一行，某个 UI 部件就从界面上消失；加上一行，新部件就长出来。**界面是组合结果，不是仓库里的一个目录。**

### 会话是事实流，不是聊天数组

DSH 的会话子系统把交互历史做成**仅追加的事件日志**（`SessionEvent`）：`user/message`、`assistant/chunk`、`assistant/message`、`tool/call`、`tool/result`、`turn/start`、`turn/end`……模型看到的消息，由这条日志**投影**出来；原始流式分片被保留，供 UI 还原；恢复、分叉、转录、遥测、持久化都从同一事件流派生。压缩不是“删掉旧对话”，而是追加一条 `replace` 语义的摘要事件，把被遮蔽的旧条目从未来的模型输入中移除——日志本身永远只增不改。

这让系统获得了很强的可观察性：一次 Turn 可以包含零个或多个 Step，一个 Step 就是一次模型请求及其工具调用；即使输入被拒绝、首步为空或请求失败，运行轨迹仍可以有明确的开始与结束。

> 会话事件可回放，回答的是“发生过什么”；插件效果可撤销，回答的是“卸载后留下什么”。二者互相配合，但不是一回事。

### Agent 能修改运行时自己

DSH 还内置了一套自引用工具：`cordis_inspect`（查看当前进程的插件、服务、事件）、`cordis_define` / `cordis_run` / `cordis_stop` / `cordis_undefine`（定义、运行、停止、撤回一个动态包）。这意味着 **Agent 不仅能调用工具，还能检查运行时结构、组装新能力、再把实验撤掉**。

官方文档对此有非常清醒的边界声明：动态包只存在于进程内存，不会写入配置、不会跨重启存续、也不会自动晋升为正式插件；其 `node:vm` 隔离 globals，但**不是安全边界**，应当像授予 bash 权限一样谨慎。一个能修改自身的 Agent，如果没有权限、审计、作用域与进程级沙箱，得到的不是进化能力，而是更大的爆炸半径。

## 二、插件运行时的五项机制

看完了 DSH 的“表象”，现在把镜头拉远。无论是 DSH/Cordis 的高动态运行时，还是 Zongsoft 的企业级插件框架，要兑现“一切皆插件”，都必须回答下面五个问题。这不是我的发明——是两套代码各自独立长出来的共同结构。

### 机制一：能力坐标 —— 插件把能力放在哪里？

**没有坐标的插件化，等于换了一种目录结构的耦合。**

- **DSH / Cordis**：能力放在 `ctx.<key>`。每个服务占据一个稳定的上下文键（`ctx.llm`、`ctx.tools`、`ctx.sessions`），其他插件通过**键**查找能力，而不是 import 具体实现。事件则通过 TypeScript 声明合并注册名字，再以 `emit` / `waterfall` / `parallel` / `serial` 四种模式分发。插件条目本身也有稳定 id（`llm`、`session`、`agent-loop`），patch 按 id 定位——id 就是坐标。
- **Zongsoft**：能力放在**插件树路径**上。对象、服务、模块、事件处理器、命令、启动项被挂载到稳定路径，例如 `/Workbench/Modules`、`/Workspace/Environment/Services`、`/Workbench/Events`。路径既是位置，也是契约：提供者把能力放到约定节点，消费者通过路径或 `expose` 关系取得它。

```xml
<!-- Automao.Trading-daemon.plugin（真实插件，节选） -->
<plugin name="Automao.Trading.Daemon"
        title="Automao.Trading.Daemon Plugin">
	<manifest>
		<dependencies>
			<dependency name="Automao.Trading" />
			<dependency name="Automao.Paying" />
		</dependencies>
	</manifest>

	<!-- 挂载支付事件处理程序：支付完成的通知由后台服务(daemon)处理 -->
	<extension path="/Workbench/Modules/Paying/Events/Payment/Paid">
		<object type="Automao.Trading.Features.PaymentHandler, Automao.Trading" />
	</extension>

	<!-- 挂载定时统计任务 -->
	<extension path="/Workbench/Scheduler/Handlers">
		<object name="OrderStatisticHandler" type="Automao.Trading.Services.OrderStatisticHandler, Automao.Trading" />
	</extension>
</plugin>
```

这个例子最能体现插件化的装配灵活性：**支付完成的通知由 daemon（后台服务）程序处理**。支付网关的回调是异步的、与用户请求链路不同步，天然适合放进后台常驻服务去消费——所以交易模块把支付处理器挂到 `/Workbench/Modules/Paying/Events/Payment/Paid` 事件路径，把 `OrderStatisticHandler` 挂到调度器，二者都只存在于 `Automao.Trading.Daemon` 这个后台插件里；而交易模块的 Web 插件（`Automao.Trading.Web`）只声明程序集与依赖，不挂任何事件处理器。**同一个事件路径，谁消费、在哪个宿主里消费，完全由“装进哪个宿主的哪个插件”决定。**服务键与树路径，一个靠“名字 + 作用域”，一个靠“层级路径”，解决的是同一个问题：**让能力拥有独立于具体对象实例的稳定坐标。**

坐标之上还有作用域：Cordis 的 `isolate` 让同一个服务键在不同上下文绑定到不同实现，`intercept` 则允许权限、审计等横切策略附着在服务访问上，而不改变 Provider 本身——这就是“名字 + 作用域”的具体语义。

### 机制二：依赖激活 —— 插件何时可以开始工作？

这是“插件化”与“模块化”最根本的分水岭。

- **DSH / Cordis**：插件用 `inject` 声明“我需要哪些服务”。运行时把依赖当作**反应式 coeffect**——服务从不满足变为满足，插件激活（`PENDING → LOADING → ACTIVE`）；Provider 消失或换成另一个实现，消费者**先失活、再针对新的依赖视图重新激活**。加载顺序不是人肉排的，而是依赖解析出来的。

```ts
// Cordis 官方的 Quick Start（节选）
const greeter = Object.assign((ctx: Context) => {
  ctx.on('app/ready', (message) => {
    ctx.logger.info('%s #%d', message, ctx.counter.next())
  })
}, {
  inject: ['counter'],   // 声明依赖：counter 就绪后才启动
})

const root = new Context()
await root.plugin(Counter)
await root.plugin(greeter)
```

- **Zongsoft**：插件里也有 `<dependencies>`，但源码注释把边界划得非常清楚：**“依赖项只表明插件的加载顺序，并无类型依赖的暗喻”**。加载器递归预加载插件，用栈做依赖拓扑，主插件先加载、从插件后加载；运行时定位则交给插件树路径。也就是说，Zongsoft 的依赖是**排序语义**，Cordis 的依赖是**状态语义**——前者表达“先装谁”，后者表达“依赖齐了没”。

顺带厘清一组概念：**物理依赖**指代码层面的程序集/类型引用，编译期就固定；**逻辑依赖**指运行时的行为契约（事件路径、服务约定），只在运行中成立。Zongsoft 插件文件里的 `<dependencies>` 两者都不是——它只表达加载顺序：类型引用交给 .NET 的程序集解析，运行时协作交给插件树路径。所以“插件里没有依赖”不等于“两者毫无关系”：核心模块之间完全可以靠逻辑依赖（事件路径）协作，而插件依赖只负责决定谁先装。

为什么会有这个差异？因为场景不同。Agent 运行时的拓扑在**运行中**高频变化（HMR、动态包、会话级插件），依赖必须能响应变化；企业系统的插件集合在**部署时**确定，加载顺序足够，稳定性更重要。这不是谁优谁劣，而是动力学与静力学的分工。

这也解释了为什么“用了依赖注入容器”不等于“拥有插件运行时”：DI 容器擅长把接口解析成对象，但对象图通常在应用启动后保持稳定；消息总线擅长解耦发送者与接收者，却未必知道一个监听器属于哪个组件；包管理器能下载代码，却不负责代码运行后留下的效果。插件运行时必须把三件事连起来——**能力怎样被定位，依赖怎样随运行状态重新解析，效果怎样归属并随组件撤回**。少任何一项，动态组合都会在别处以约定和人工纪律的形式重新出现。

### 机制三：效果撤回 —— 插件改变世界后，怎么把世界还回去？

“能加载”只完成了一半。插件加载时会注册服务、监听事件、创建子组件、申请资源——**卸载时这些效果必须能归属、能撤销**。

- **Cordis**：把效果抽象为“上下文变换 + 逆操作”。`ctx.effect(callback)` 执行的每次修改都返回自己的清理函数，运行时按发生顺序累积、卸载时**逆序执行**；子效果的撤销组合进父上下文，父组件离开会级联撤销子组件。销毁是幂等的，异步清理会被等待。

```ts
// Cordis 的效果模型（示意）
ctx.effect(() => {
  const id = setInterval(tick, 1000)   // 效果：改变世界
  return () => clearInterval(id)       // 逆操作：把世界还回去
})
```

- **Zongsoft**：`IBuilder` 同时定义 `Build` 与 `Destroy`；插件卸载走一条递归协议——先卸载子插件，再卸载依赖它的从插件，然后把构件（Builtin）逐个从插件树卸下（这一步会调用对应构建器的 `Destroy`），最后清理构建器、解析器等固定元素。可释放的集合成员也会被处理。

两套机制表达了**同样的对称意识**：创建效果与清理效果要成对出现、由运行时负责触发时机。区别在于保证强度：Cordis 要求**每一次**上下文变换都可组合地逆操作，并给出形式化证明；Zongsoft 则以构建/销毁协议与递归卸载落实“能装就能卸”，但它没有要求每个变换都携带逆操作，而是依赖框架的约定与纪律。

> 相似的是问题意识，差异的是保证强度和主要场景。

### 机制四：组合与形态 —— 产品是什么？

插件化最容易翻车的地方，是“插件很多，但没有产品”。一个真正的插件运行时，必须让**产品形态成为组合的结果**。

- **DSH**：产品 = profile = 一摞有序的 patch 层。官方 README 的描述是：“The tree composes over an empty root”——先在空根上叠加基础组合包（`dsh-base`），再叠加形态组合包（`dsh-web-app` 或 `dsh-headless`），然后是 profile 自己的 `cordis.patch.yml`、机器级的 `$DSH_HOME/cordis.patch.yml`，最后是命令行 `--patch` 叠加。patch 按 id 定位，**整行替换 config，最后写入者胜**；`--dump-config` 可以随时把组合结果导出查看。想确认某个插件的真实配置？看组合结果，而不是猜代码。
- **Zongsoft**：产品 = 空宿主 + 插件集合 + 配置分层。宿主（Terminal / Daemon / Web）本身**没有任何业务代码**，部署 = 把插件及其附属文件放进 `plugins/` 目录。配置同样分层：`X.option` 是环境无关的缺省值，`X.{env}.option`（`test` / `production` / `development`）按环境覆盖，`X.{env}-debug.option` 再覆盖一层调试参数——同一份插件，在不同环境长出不同配置。

```text
DSH：dsh-base → dsh-web-app / dsh-headless → profile patch → home patch → --patch
```

```text
Zongsoft：空宿主 → 插件程序集 + *.plugin → X.option → X.{env}.option → X.{env}-debug.option
```

这套“组合优先”的设计，战略价值不在于少写几个 `if`，而在于：**产品边界可以晚于编译被决定**。同一个 base，加上 Web 组合包就是聊天界面，加上 Headless 组合包就是一次性任务执行器；同一个空宿主，放进不同的插件集合，可以是终端、后台服务，也可以是 SaaS 的管理端、商家端、客户端站点。产品不再是“某个主程序类”，而是“宿主、插件清单与配置的组合”。

组合之所以能成立，还因为**能力被拆成了定义、提供者与消费者三层**。例如文件系统不是某个工具内部的一段实现：服务定义描述契约，Provider 决定能力落在本机还是远端沙箱，面向模型的工具只是消费者。替换 Provider，Bash、PTY、LSP 等共享同一执行世界的能力就能整体迁移，而无需分别 fork。

### 机制五：自省与演化 —— 运行时能被观察、被修改吗？

前四项机制回答“系统如何被组装”，最后一项回答“系统如何被认知和改变”。

- **DSH**：把自省做成了 Agent 可用的工具。`cordis_inspect` 报告当前进程里“谁在跑、每个服务能做什么”；`cordis_define` / `cordis_run` / `cordis_stop` / `cordis_undefine` 让 Agent 在**进程内存**里定义、运行、停止、撤回一个动态插件包。它还能检查自己的 API 目录——这个目录与官方文档由同一份 AST 遍历生成，因此“模型读到的数据”与“渲染出来的文档”不可能彼此偏离。这是把“一切皆插件”延伸到**自我描述协议**的一步：运行时结构不再只是人眼可读，而是模型可读、可操作。
- **Zongsoft**：插件树自带 `find` / `list` / `tree` 命令，可以把运行中的系统结构以树状打印出来；`Mount` / `Unmount` 支持运行时挂载与卸载对象。它的演化走的是另一条更重的路：编译后的插件程序集 + 声明式插件文件 + 部署工具链（`deploy` / `*.deploy` 部署文件）+ 环境化配置，强调版本、审核、回滚与责任边界。

两者的分野在这里变得非常清楚：

| 维度 | DSH / Cordis | Zongsoft |
|---|---|---|
| 能力坐标 | 上下文服务键 `ctx.<key>`、事件名、loader 条目 id | 插件树稳定路径（`/Workbench/...`）与 expose |
| 依赖语义 | `inject` 反应式 coeffect，依赖驱动激活/失活 | 插件依赖 `<dependencies>` 只表达加载顺序 |
| 效果撤回 | `ctx.effect` 累积逆操作，逆序执行，级联撤销 | `Build/Destroy`、内置节点清理、递归卸载 |
| 组合形态 | profile = bundle patch 分层，整行替换，HMR | 空宿主 + 插件文件 + 环境 option 分层 |
| 自省演化 | `cordis_inspect/define/run/stop/undefine`，进程内自修改 | 插件树命令、`Mount/Unmount`、部署工具链 |
| 主要场景 | 高动态 Agent 运行时、自修改、细粒度恢复 | 企业软件、跨宿主复用、版本化治理 |

> 一个面向运行时的动力学，一个面向企业的静力学。它们不是竞争关系，而是插件化平台的一体两面。

## 三、Zongsoft 的十六年：把“一切皆插件”落在企业软件里

如果只讲 DSH，这篇就只是一篇技术解读。把 Zongsoft 放进来，是想展示另一条同样成立、但很少被 AI 圈看到的路径：**没有 Agent、没有热更新、没有自修改，插件化能不能撑起真实的产品？**

### 空宿主：多类应用，同一套装配

[Zongsoft Hosting](https://github.com/Zongsoft/hosting) 提供终端（Terminal）、后台服务（Daemon）和网站（Web）等多种宿主，分别应对不同种类的应用形态。它们的入口代码都薄得惊人——区别只是参数里的一行：`host=` 指定宿主类型，`site=` 指定站点。

> 需要说明的是，这些宿主参数**并不是必需的**——它们的唯一作用是**标注宿主程序的类型**：一方面，自动升级插件（Upgrader）可以据此进行包管理与定位，知道当前该为哪个宿主、哪个站点拉取和安装升级包；另一方面，宿主类型会进入应用程序上下文与配置，其他业务插件可以随时获取自己运行在哪种宿主、哪个站点上。

#### 终端应用（Terminal）

```csharp
// Zongsoft.Hosting.Terminal/Program.cs（完整）
internal class Program
{
    static void Main(string[] args)
    {
        Zongsoft.Plugins.Hosting.Application
            .Terminal("zongsoft.terminal", [.. args, "host=terminal", "site=daemon"])
            .Run();
    }
}
```

#### 后台服务（Daemon）

```csharp
// Zongsoft.Hosting.Daemon/Program.cs（完整）
internal class Program
{
    static void Main(string[] args)
    {
        #if WINDOWS
        Zongsoft.Plugins.Hosting.Application
            .Daemon("zongsoft.daemon", [.. args, "host=daemon", "site=daemon"], builder =>
            {
                builder.Services.AddWindowsService(options => options.ServiceName = builder.Environment.ApplicationName);
            }).Run();
        #elif LINUX
        Zongsoft.Plugins.Hosting.Application
            .Daemon("zongsoft.daemon", [.. args, "host=daemon", "site=daemon"], builder =>
            {
                builder.Services.AddSystemd();
            }).Run();
        #else
        Zongsoft.Plugins.Hosting.Application
            .Daemon("zongsoft.daemon", [.. args, "host=daemon", "site=daemon"])
            .Run();
        #endif
    }
}
```

> 后台宿主的差异只在“以何种身份常驻”：Windows 上注册为系统服务（`AddWindowsService`），Linux 上交给 systemd 托管（`AddSystemd`）——插件装配的逻辑一字未改。

#### 网站应用（Web）

```csharp
// Zongsoft.Hosting.Web/default/Program.cs（完整）
internal class Program
{
    static void Main(string[] args)
    {
        var app = Zongsoft.Web.Application.Web([.. args, "host=web", "site=default", "daemon=zongsoft.web"]);

        // 如需启用私有部署模式，打开下行注释
        // app.Configuration["Deployment"] = "private";

        app.Run();
    }
}
```

三种入口背后是同一个插件运行时：宿主只负责初始化环境，自身不含任何具体功能。功能从哪来？部署——运行部署脚本把需要的插件及其配置、证书放进 `plugins/` 目录，这个动作本身就是“组合”。宿主因为插件集合不同而成为不同产品（终端、后台服务、管理端网站、商家端网站……）；同一个业务插件，可以进入不同宿主、不同站点。这也正是 Automao 中 258 个插件能被反复组合出大量产品形态的底层原因。

### 部署即组合：插件自带的“出厂清单”

空宿主把功能全部留给部署——那“部署”本身由什么描述？Zongsoft 的做法是：**每个插件库自带一份 `*.deploy` 自描述清单**，自我表达“我该被放到哪里、依赖哪些包、需要哪些原生库、默认携带哪些配置文件”。[`Zongsoft.Data`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data)、[`Zongsoft.Data/drivers/*`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data/drivers)、[`messaging/*`](https://github.com/Zongsoft/framework/tree/main/messaging)、[`externals/*`](https://github.com/Zongsoft/framework/tree/main/externals) 的每个插件库都有自己的 `.deploy` 文件：

```ini
# Zongsoft.Data/src/Zongsoft.Data.deploy
artifacts/Zongsoft.Data.plugin
lib/$(Framework)/Zongsoft.Data.*
lib/$(Framework)/*/Zongsoft.Data.resources.*
```

```ini
# Zongsoft.Data/drivers/mysql/src/Zongsoft.Data.MySql.deploy
artifacts/Zongsoft.Data.MySql.plugin
lib/$(Framework)/Zongsoft.Data.MySql.*
nuget:MySqlConnector@2.4.0
```

```ini
# messaging/kafka/src/Zongsoft.Messaging.Kafka.deploy
artifacts/Zongsoft.Messaging.Kafka.plugin
artifacts/Zongsoft.Messaging.Kafka.option
lib/$(Framework)/Zongsoft.Messaging.Kafka.*
nuget:Confluent.Kafka@2.15.0
%NUGET_PACKAGES%/librdkafka.redist/2.15.0/runtimes/win-$(architecture)/native/*  <platform:win,windows>
%NUGET_PACKAGES%/librdkafka.redist/2.15.0/runtimes/linux-$(architecture)/native/* <platform:linux>
```

> `artifacts/` 是插件文件，`lib/$(Framework)/` 按目标框架展开程序集，`nuget:` 声明第三方依赖，`%NUGET_PACKAGES%/...` 配合 `<platform:...>` 按平台挑原生库——`$(Framework)`、`$(architecture)` 是部署时的展开变量。一份清单，把“这个插件需要什么环境”说得明明白白。

宿主侧则声明“我要哪些插件”。[`hosting/web/web.deploy`](https://github.com/Zongsoft/hosting/tree/main/web/web.deploy) 以 `#@import ../packages` 引入共享包清单 [`hosting/packages`](https://github.com/Zongsoft/hosting/tree/main/packages)，再按 `[plugins 分类 名称]` 分组声明要部署的 NuGet 包（如 [`Zongsoft.Security.Web`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Security/api)、[`Zongsoft.Externals.Wechat.Web`](https://github.com/Zongsoft/framework/tree/main/externals/wechat/api)）；[`terminal/.deploy`](https://github.com/Zongsoft/hosting/tree/main/terminal/.deploy)、[`daemon/.deploy`](https://github.com/Zongsoft/hosting/tree/main/daemon/.deploy) 各自声明自己的集合，并且把配置文件的来源也写成带变量的映射，例如：

```ini
# daemon/.deploy（节选）
../.deploy/$(scheme)/options/app.$(environment).option       = Zongsoft.Hosting.Daemon.option   <!debug:on>
../.deploy/$(scheme)/options/app.$(environment)-debug.option = Zongsoft.Hosting.Daemon.option    <debug:on>

#@import ../packages
[plugins]
nuget:Zongsoft.Plugins/plugins/Main.plugin
```

部署脚本 [`web/default/deploy.cmd`](https://github.com/Zongsoft/hosting/tree/main/web/default/deploy.cmd) 交互式询问 scheme / environment / debug / platform / architecture / framework，随后 `dotnet cake` 编译、清空 `plugins/` 目录，再执行 `dotnet deploy --host:web --site:default --scheme:... --environment:...`——底层由 [`Zongsoft.Tools.Deployer`](https://github.com/Zongsoft/tools/tree/main/deployer) 部署工具提供能力，最终把各层清单组合成实际的 `plugins/` 目录。部署专属的产物则放在 [`hosting/.deploy/`](https://github.com/Zongsoft/hosting/tree/main/.deploy)：按环境拆分的配置（`app.development.option`、`app.test.option`、`app.production.option` 及 `-debug` 变体）、nginx 配置、systemd 服务单元（[`zongsoft.daemon.service`](https://github.com/Zongsoft/hosting/tree/main/.deploy/default/systemd/zongsoft.daemon.service)、[`zongsoft.web.service`](https://github.com/Zongsoft/hosting/tree/main/.deploy/default/systemd/zongsoft.web.service)）。

> 这正好与 DSH 形成呼应：DSH 用 `--dump-config` 把“运行时组合”导出为可读清单，Zongsoft 用 `*.deploy` 把“部署组合”写成自描述清单——前者组合发生在运行时配置，后者组合发生在部署清单。落点不同，思想一致：**组合的结果必须可声明、可审计、可复现。**

### 插件树：路径即契约

[PluginTree](https://github.com/Zongsoft/framework/blob/main/Zongsoft.Plugins/src/PluginTree.cs) 是 Zongsoft 的核心数据结构。它的根节点下挂着 `/Workbench/Modules`、`/Workbench/Services`、`/Workbench/Events`、`/Workspace/Environment/Services` 等稳定路径；插件文件通过 `<extension path="...">` 把构件挂到这些节点上。构件（Builtin）是“延迟构造的对象描述”：被引用时才通过构建器构建，卸载时通过构建器销毁。

更彻底的是：**框架连“如何解释和构建插件”本身也做成了插件**。`object`、`expose`、`lazy` 等构建器，`path`、`service`、`option`、`type` 等解析器，都由主插件清单注册；它们随后又被用来装配模块、服务、文件系统、事件交换器和命令。换言之，Zongsoft 没有只把“业务功能”做成插件——它把“插件的语法”也开放为可组合能力。这是“一切皆插件”最容易被忽略、也最彻底的一层。

### Automao：250+ 个插件的真实 SaaS

插件化最常受到的质疑是：Demo 很漂亮，业务一复杂就退化为依赖地狱。Automao 是这个问题最好的反例——一个基于 Zongsoft 开发框架构建的插件化 SaaS 系统。仅源码目录就存在 **258 个 `.plugin` 文件**：基础技术、通用业务模块、行业产品（房产、车辆、资产、票务……）、管理端/商家端/客户端/网关/IoT 站点，全部通过插件组合。

当插件数量达到这个量级，考验早已不是“能否加载一个 DLL”，而是**命名、依赖、边界与交付方式能否长期保持可理解**。Automao 的意义正在于此：它把插件化从一个框架特性，变成了团队组织复杂业务的共同语言——业务能力与交付形态正交（交易是一个领域能力，Web/后台任务/不同站点是承载方式），扩展位置成为架构语言（退款处理器挂载到明确事件路径，而不是隐式调用约定）。

这也呼应了 [EluxJS](https://github.com/hiisea/elux) 作者在“微模块”探索中反复强调的取舍：真正按业务领域划分的模块，需要共享运行时与明确的协作协议，才能既保持自治，又避免微前端式隔离带来的重量。Zongsoft 和 Automao 把这个命题推到了后端与完整 SaaS 系统中。

### 依赖解耦：核心模块与技术方案的边界

多重依赖是插件化最容易失控的地方：会员（Membership）与支付（Paying）都是核心业务模块，微信（WeChat）是具体技术方案——如果不加约束，就会出现“会员 → 支付 → 微信”的链式耦合，换一个支付渠道就要动三个模块。Automao 的答案是：**把技术方案从核心模块里拆出去，让依赖方向反转**。

看真实插件。会员模块与支付模块的核心插件，`manifest` 依赖都只有 `Automao.Common`——两个核心模块之间、以及它们与任何支付技术之间，既没有物理依赖（程序集/类型引用），也没有插件声明的加载依赖；它们的协作只发生在逻辑依赖（事件路径契约）上。支付模块通过插件树**发布事件契约**：

```xml
<!-- Automao.Paying.plugin（事件契约，节选） -->
<extension path="/Workbench/Modules/Paying/Events">
	<expose name="Payment" value="{path:../@Payment}">
		<expose name="Paid" value="{path:../@Paid}" />
	</expose>
	<expose name="Refundment" value="{path:../@Refundment}">
		<expose name="Refunded" value="{path:../@Refunded}" />
	</expose>
</extension>
```

会员模块把 `ChargeHandler` / `RefundHandler` 挂到这两个事件路径上（甚至没有在插件里声明对支付模块的依赖）——模块之间通过路径通信（逻辑依赖），而不是通过类型引用（物理依赖）。而具体支付技术方案，作为**独立的 provider 插件**存在：`modules/paying/providers/` 下同时有 alipay / card / cash / wechat 四个提供程序，`modules/membership/providers/wechat/` 则提供微信会员卡提供程序。每个 provider 的依赖方向都是“核心模块 + 对应外部 SDK”：

```xml
<!-- Automao.Paying.Providers.Wechat.plugin -->
<manifest>
	<dependencies>
		<dependency name="Automao.Paying" />
		<dependency name="Automao.Externals.Wechat" />
	</dependencies>
</manifest>
```

```xml
<!-- Automao.Paying.Providers.Alipay.plugin -->
<manifest>
	<dependencies>
		<dependency name="Automao.Paying" />
		<dependency name="Automao.Externals.Alipay" />
	</dependencies>
</manifest>
```

核心模块不知道微信、支付宝的存在；provider 反向依赖核心模块与外部 SDK。换支付方案 = 换部署的 provider 插件，业务模块一行不改；同一时刻也可以并存多个 provider（现金、会员卡、微信、支付宝……）。这正是“依赖倒置”在插件层的落地——**谁依赖谁，由部署时装入哪个插件决定，而不是由代码结构决定。**

### 数据引擎与安全：“核心部件”也只是插件

在企业系统里，数据引擎（数据框架）与安全控制通常被视为不折不扣的“核心部件”——而 Zongsoft 的插件化主张，恰恰在这里接受最严峻的考验：**它们也必须以普通插件的身份存在。**

看框架源码的目录结构就知道这不是口号。数据框架 [Zongsoft.Data](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data) 本身是一个插件，而它的数据库驱动——[`Zongsoft.Data/drivers`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data/drivers) 下的 [`mysql`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data/drivers/mysql)、[`postgres`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data/drivers/postgres)、[`duckdb`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data/drivers/duckdb)、[`sqlite`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data/drivers/sqlite)、[`clickhouse`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data/drivers/clickhouse)、[`tdengine`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data/drivers/tdengine)、[`mssql`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Data/drivers/mssql)……每一个都是独立的驱动插件：`MySqlDriver`、`DuckDBDriver` 等都实现统一的数据驱动抽象 `IDataDriver`，各自带有自己的 `*.deploy` 自描述部署清单（前文部署小节展示的 [`Zongsoft.Data.MySql.deploy`](https://github.com/Zongsoft/framework/blob/main/Zongsoft.Data/drivers/mysql/src/Zongsoft.Data.MySql.deploy) 就是其中之一）。安全控制同理：[`Zongsoft.Security`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Security) 是插件，验证码（[`Zongsoft.Security.Captcha`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Security/captcha)）、Web 变体（[`Zongsoft.Security.Web`](https://github.com/Zongsoft/framework/tree/main/Zongsoft.Security/api)）也都是独立插件。

这意味着什么？**切换数据库 = 替换或新增一个数据引擎驱动插件，业务模块零改动**——业务代码只面向统一的数据访问抽象，驱动以插件身份被选择与装配；安全能力的更换同理。连性命攸关的数据引擎与安全控制都不享有“天生特权”，这正是**插件平等、一切皆插件**的设计初衷：在一个真正插件化的系统里，“核心”不是一个受保护的类，而是一个与其它能力平等的节点——它只是恰好被每个部署都装上而已。

### 企业级的插件化，慢一点，但更稳

Zongsoft 的路线没有 DSH 那么“炫”，却天然贴近企业关心的问题：版本可控、可审计、可部署、可复用、责任边界清晰。它的卸载协议由构建器与框架纪律保证，而不是要求每一次变换都可逆；它的依赖是排序语义，而不是响应式状态。**它的目标不是让系统在运行中不断自变，而是让系统在长期演进中保持可组合。**

## 四、殊途同归：插件成为系统的组织单位

把两套体系放在一起，最有价值的不是强行寻找一一对应，而是看它们怎样用不同机制回答同一组问题——这正是上文那张对照表的含义。

Cordis 论文给这套共同问题提供了理论坐标：**时间可组合性**（效果能否完全撤回）与**空间可组合性**（依赖能否随环境变化）。它把经典的效果（effect）与余效果（coeffect）这对对偶概念提升为运行时机制：效果 _(effect)_ 回答“计算对世界做了什么”（副作用、变更），余效果 _(coeffect)_ 回答“计算需要从世界得到什么”（上下文依赖、前置要求）。可逆效果让每次上下文变换都携带逆操作，反应式 coeffect 让上下文变化主动通知组件——并给出组件演算的元理论。DSH 把这套理论带进了会话、工具、模型、沙箱乃至 Agent 自修改；Zongsoft 则用插件树、声明式挂载、空宿主和生命周期管理，把同样的两个维度落实在企业软件里。

> 注：余效果（coeffect）的“余”字取数学中 co- 前缀的传统译法（如余弦、余切之于正弦、正切），意为与 effect 互补、对偶。

论文也直面了一个“粒度不匹配”的问题：操作系统可以在进程退出时回收内存和句柄，容器编排器可以在服务层处理依赖与重启，但为了换掉一个 Agent 工具而重启整个进程，会丢失连接、缓存和进行中的任务；把每个细小能力都拆成独立服务，又会引入网络、序列化和运维成本。Cordis 想建立的，是一种介于函数局部作用域与进程边界之间的**组件级恢复域**：既保留同进程调用的效率，又让一个组件能够独立退出。而且论文给出的性质非常克制：它并不声称现实世界的所有副作用都能倒放——发送出去的邮件、已经被外部系统读取的文件、完成的支付，通常不可逆，只能补偿；恶意插件若能直接接触宿主运行时，也不能靠语言级 Context 变成可信代码。**可组合性减少的是结构性失控，不是抹除现实世界的不可逆性。**

![时空可组合性的两条坐标轴](/blog/images/agent-os-spatiotemporal-composability.png)

这里必须诚实：**没有证据表明两条路线存在直接影响关系**。Zongsoft 的插件树与 Cordis 的上下文，各自独立演化。恰恰因为如此，这次会合才更值得重视：

![DSH/Cordis 与 Zongsoft/Automao 的插件化路径](/blog/images/agent-os-dsh-zongsoft-plugin-architecture.png)

> 当两条相隔多年、面向不同场景的技术路线，都把“插件”从扩展点提升为系统组织单位时，我们看到的可能不是一阵热点，而是一种正在成为基础设施的架构范式。

## 五、对 Agent 时代的启示：插件运行时应该长什么样

回到开头的问题：DSH 的火热，表面来自 DeepSeek 的品牌与 Agent 浪潮；更深层的原因，是开发者终于集体撞上了一个经典的软件工程问题——**当能力越来越多、变化越来越快，系统靠什么保持可组合？**

从 DSH 与 Zongsoft 的经验里，可以提炼出一份插件运行时的“验收清单”——四条，每条都能对着真实代码打钩：

**① 能力有坐标：查得到、找得着。** 服务键、事件名、树路径，三者至少要有其一。没有命名空间的插件化，最终会退化成换了目录结构的耦合。

**② 组合即产品：形态是分层配置的结果。** 产品能力由 bundle/patch 或宿主/清单组合而来，能 dump、能审计、能对比——而不是埋在万能入口的 if 分支里。

**③ 卸载即还原：效果归属创建者，并按序撤销。** 事件、工具、服务、子组件、资源必须能随组件一起被清退；不能安全卸载的插件，本质上仍是一次不可逆的全局修改。

**④ 自改须受控：自省要可见，修改要过沙箱与审批。** 越接近“系统可以改写自己”，治理就越不是附加功能——动态实验与持久插件之间，必须有一道明确的晋升边界。

由此还可以得到一个对 Agent 平台的具体判断：**动态与治理不应二选一，而应各归其位。** Cordis 式的运行时自适应（HMR、动态包、会话级插件）适合放在受限的会话里做实验；Zongsoft 式的工程化治理（版本、审核、部署、责任边界）适合把验证过的能力沉淀为正式插件。自进化发生在沙箱里，可治理性沉淀在仓库里——这可能是未来 Agent 平台的标准分工。

## 结语：模型决定 Agent 能走多远，运行时决定它能走多久

DeepSeek Harness 告诉我们：模型适配器可以是一行配置，Agent 循环可以是插件行，整个 UI 可以是一张插件名录。Zongsoft 则用十六年告诉我们：这条路不只属于高动态的 Agent，它也属于版本化、可审计、跨站点复用的企业软件——连数据引擎与安全控制这样的“核心部件”，也只是插件树里的普通节点。

Cordis 用“可逆效果 + 反应式 coeffect”把动态组合推向形式化；DSH 把它带进了会话、工具、模型、沙箱乃至 Agent 自修改；Zongsoft.Plugins 则从 2010 年起，通过插件树、声明式挂载、空宿主和生命周期管理，把“一切皆插件”落实在企业软件中；Automao 进一步证明，这套思想可以承载真实 SaaS 的模块、产品和站点组合。它们不是同一个实现，也没有证据表明存在直接影响关系——恰恰因为如此，这次思想共振才更值得重视。

两条路线，一套信念：

> 没有特权的产品内核，只有可组合的运行时规则；能力被命名、被获得、被生效、被撤回、被组合、被观察——插件，从“扩展点”升格为“系统的组织单位”。

模型还会继续迭代，今天最强的名字迟早会被替换。真正能够穿越模型周期的，是那套让能力被装上、换下、组合、观察并安全演进的运行时。**模型决定 Agent 能走多远；插件运行时决定它能否在不断变化中，仍然作为一个系统向前走。**

---

## 延伸阅读

- [DeepSeek Harness 官方仓库](https://github.com/deepseek-ai/deepseek-harness)
- [DeepSeek Harness 架构文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)
- [Cordis 入门（官方文档）](https://deepseek-harness.github.io/deepseek-harness/reference/cordis-primer)
- [A Programming Paradigm for Spatiotemporal Composability（Cordis 论文）](https://github.com/cordiverse/paper)
- [Zongsoft 开发框架（含 Zongsoft.Plugins）](https://github.com/Zongsoft/framework)
- [Zongsoft Hosting（空宿主）](https://github.com/Zongsoft/hosting)
