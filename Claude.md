# MCP Server Gateway 网关

**语言约定**：所有产出物（文档、代码注释、对话）使用简体中文。

本项目使用 Python 3.11 开发MCP Server Gateway 网关，提供一个代理层，连接Claude Code等智能体系统与外部的多MCP Server。

## 项目出发点

模型上下文协议（MCP）已成为连接LLM智能体与外部工具的通用接口。然而，在每一轮对话中无状态地传输完整的工具模式带来了一种隐藏的单轮开销——即MCP Tax或Tool Tax：
- 经济性： 无状态的重新注入使单次会话的支出增加了一个数量级
- 认知性： 一旦工具描述的上下文占用率超过约 70%，LLM 的推理质量就会崩塌，模型开始幻觉参数、混淆相似工具，并丢失情节性的任务记忆
- 安全性： 描述工具的模式文本同时也塑造了模型的注意力掩码，因此恶意的工具中毒攻击可以通过在看似无害的工具描述中注入对抗性指令来劫持控制流
根据开发者报告，在典型的多MCP Server部署中，这种开销大约在1万到6万个token之间。这种负载不仅对KV Cache造成了压力，还导致推理能力的下降（当工具描述的上下文占用率接近70%的断裂点时），并将token预算转化为一项持续的运营成本。

## 解决方案

构建一个单一的MCP Server Gateway网关，统一管理项目接入的MCP Servers，实现类似Skills的渐进式加载，而不是用Claude Code的.mcp.json或/mcp指令管理，Claude Code需要且仅需要添加这个MCP Server Gateway，网关会接管所有对外部MCP服务的调用

## 功能设计

采用单体项目，前后端不分离的设计。

### 前端

项目提供一个前端界面，展示所有接入的MCP Server和工具列表，并提供添加/删除MCP Server的功能，用户通过填写MCP Server的URL和认证信息来添加新的MCP Server：
1. 支持HTTP和stdio两种协议的MCP Server
2. 支持API Key/Bearer Token和OAuth两种认证方式
3. 当添加新的MCP Server时，网关自动调用该服务器的list_tools接口获取工具列表并存储在本地数据库中。

### MCP Server Gateway API

MCP Server Gateway提供两个元工具：
1. get_tool_schema(server_name, tool_name)：获取指定工具的完整调用参数schema
2. invoke_tool(server_name, tool_name, arguments)：调用指定工具并返回结果
<!-- MCP_MANAGER_TOOLS_START -->

# MCP Manager 可用工具

你可以通过mcp-manager Skill调用以下外部工具:

[aone-km]
  fetch-external-content-by-url: 通过钉钉或者语雀文档链接获取文档内容，如果获取不到内容，请检查知识库是否完成授权，如果知识库未完成授权，请访问链接进行授权检测
  search-code-wiki: 在 CodeWiki 中进行语义搜索，支持跨多个代码仓库搜索。返回按相关性排序的搜索结果。
  get-code-wiki-page-content: 获取 CodeWiki 指定页面的完整内容。返回页面标题、Markdown 内容和元数据信息。
  get-code-wiki-structure: 获取代码仓库的 CodeWiki 目录结构。默认仅返回当前层级，必要时可递归返回目录树。
  create-ding-doc-workspace-doc: 在钉钉知识库中新建文件夹或文档，支持在创建文档的同时写入 markdown 内容
  update-ding-doc-content: 向钉钉文档覆写内容（会替换文档的全部内容, 只提供 markdown 格式内容写入）
  search-doc-chunk: 通过自然语言召回符合问题答案的文档片段列表
  ask-dev-ops-knowledge: 通过自然语言提问关于阿里巴巴集团内中间件、研发运维平台相关问题，可以回答使用方法、功能介绍、接入方式、SDK代码片段、问题排查思路等
  search-dev-ops-knowledge: 通过自然语言提问关于阿里巴巴集团内中间件、研发运维平台相关问题，可以查询到使用方法、功能介绍、接入方式、SDK代码片段、问题排查思路等
  chat-with-knowledge-base: 基于知识库的智能问答，通过 ReAct 模式进行多轮推理和文档检索，返回带有文档引用的完整回答。适用于需要深度理解和多步推理的复杂问题。
  fetch-knowledge-directory-by-url: 通过钉钉或者语雀知识库链接获取知识库的目录列表，如果获取不到内容，请检查知识库是否完成授权，如果知识库未完成授权，请访问链接进行授权检测
  get-knowledge-group-structure: 根据知识组 ID 获取知识组的结构信息，包括基础信息（名称、描述等）、直属子知识组列表和知识库列表。用于了解一个知识组的整体组织结构。
  upload-doc-to-kb-repo: 上传 Markdown 文档到平台知识库，支持指定目录路径或父节点。若指定 pageId 则更新已有文档
  list-repo-directory: 根据知识库 ID 获取知识库的目录树结构，包括文件夹和文档节点。每个文档节点包含 pageId，可用于后续获取文档内容。
  hierarchical-search-personal-memory: 在个人记忆中做分层语义检索。
  smart-ingest-personal-memory: 写入个人记忆：默认自动路由到合适的 memory 节点。
  get-personal-memory-tree: 获取个人记忆目录树（含 folder / memory / `path`）。
  update-personal-memory: 根据记忆内容 ID 更新一条个人记忆内容。
  delete-personal-memory: 根据 记忆内容ID 删除一条个人记忆内容。
  get-repo-page-content: 获取知识库指定页面的完整内容。支持KB知识库及其关联的外部知识空间（CodeWiki/语雀/钉钉等）。
[aone-mix]
  query-cf-rules: 该工具用于根据应用名称或应用ID查询对应的CF封网规则信息。当用户询问某个应用在封网期间的规则、是否被封网影响、封网时间安排等信息时，使用此...
  close-change-request: 关闭Aone变更
  get-current-package-deploy-mix-flow-inst-of-cr: 获取指定变更的运行中的包类部署流水线实例
  bind-workitem-to-changerequest: 针对已有的变更，绑定工作项(需求/缺陷)
  reenter-mix-flow-inst: 重新部署应用或包的某条流水线，入参有两种传参选择：
  create-change-request: 创建Aone变更,返回变更ID,变更详情链接,分支名
  list-dev-object-pipelines: 获取应用或包绑定的流水线
  add-pipeline-to-dev-object: 向应用或包绑定流水线
  quit-cr-from-mix-flow-inst: 从应用或包的流水线实例中退出指定的变更，需要传入应用或包名称、流水线ID和要退出的变更ID列表
  search-pipelines: 基于用户输入的自然语言检索Aone流水线市场中的符合条件的流水线
  get-change-request-detail: 获取Aone变更详情
  submit-code-review: 为变更提交代码评审,用于触发代码审核流程
  get-pipeline-change-requests: 获取应用流水线集成中的变更列表，入参有两种传参选择：
  create-mix-flow-inst: 提交应用或包的变更到应用或包绑定的某条流水线上启动流水线,返回流水线实例id以及流水线详情页url.
  submit-cr-to-pre-intg: 将Aone变更置为待发布[PREINTG]状态,此方法不能用于关闭变更
  get-change-request-by-branch: 通过分支URL获取变更信息，返回变更ID、变更名称和变更详情URL
  list-change-requests: 查询Aone变更列表，支持按变更ID、状态、类型、描述、应用、开发人员、时间范围等条件过滤，返回分页后的变更列表及总条数。
  create-pypi-deploy-pipeline: 将PYPI变更提交到部署流水线，如果有进行中的流水线会直接重新部署
  get-mix-flow-inst-detail: 获取应用或包的某条流水线下活跃实例详情，入参有两种传参选择：
  create-publish-plan-simple: 提供一个简化的接口来创建发布计划，用户只需输入发布计划名称即可完成创建操作。默认情况下，当前用户将被设置为发布计划的负责人，并自动设置计划发...
  save-plan-rel-ref-objs: 将变更加入到发布计划
  get-publish-plan: 根据发布计划id获取发布计划详情
  list-publish-plan: 根据条件查询发布计划列表
[code]
  search-authorized-repositories: 搜索我有权限访问的代码仓库，支持模糊搜索仓库名称
  list-repo-files: 查询代码仓库文件列表
  search-code: 搜索仓库内的代码片段和代码文件元数据，支持搜索所有仓库或指定仓库
  create-tag: 创建代码仓库标签
  create-issue: 创建新的 Issue
  create-issue-comment: 为 Issue 添加评论
  manage-label: 管理仓库的 Issue 标签（仓库级别），支持查询、创建和删除标签。注意：这是管理仓库的标签定义，不是管理 Issue...
  manage-issue-label: 管理 Issue 的标签关联，支持添加或删除标签。添加时通过标签名操作，如果标签不存在会自动创建；删除时通过标签 ID 操作，可通过...
  manage-issue-tracer: 管理 Issue 的关注人（抄送人），支持添加或删除。关注人会收到 Issue 变更通知
  update-issue-status: 更新 Issue 状态。必填参数：repo, issueId, status；status...
  list-issues: 查询 Issue 列表，支持简单搜索和分页
  get-issue: 获取 Issue 详情和评论列表
  repo-vector-search: 在代码仓库中根据语义搜索主干分支代码
  search-classes: 搜索参与的仓库或指定仓库内的类
  search-methods: 搜索参与的仓库或指定仓库内的方法
  list-merge-request-commits: 查询代码评审（MR）的提交列表
  create-merge-request: 根据用户提供的仓库ID，关联分支，标题和描述创建代码评审
  operate-ai-comment: 操作AI评审评论，支持采纳、忽略和拒绝AI自动生成的代码审查意见。在获取AI评论列表后，可使用此工具对具体的AI评论进行处理
  remind-merge-request-assignees: 提醒代码评审评审人评审代码评审
  list-merge-request-ci-tasks: 获取代码评审关联CI任务详情列表
  merge-merge-request: 合并代码评审（MR）
  list-merge-requests-created-by-me: 全局查询我创建的代码评审MR列表，可以根据搜索词，代码评审状态等查询代码评审列表
  get-merge-request-changed-file-diff: 查询代码仓库变更文件diff
  list-merge-request-changed-files: 查询代码评审（MR）上变更的文件列表
  comment-merge-request-code-suggestion: 在代码评审（MR）变更的文件上发表代码建议评论
  list-repo-merge-requests-created-by-me: 查询我创建的代码仓库代码评审MR列表，可以根据仓库ID，搜索词，代码评审状态等查询代码评审列表
  list-repo-merge-requests-reviewed-by-me: 查询我评审的代码仓库代码评审MR列表，可以根据仓库ID，搜索词，代码评审状态等查询代码评审列表
  list-merge-requests-reviewed-by-me: 全局查询我评审的代码评审MR列表，可以根据搜索词，代码评审状态等查询代码评审列表
  update-merge-request-comment-status: 更新代码评审（MR）评论状态
  comment-merge-request-changed-file: 在代码评审（MR）变更的文件上发表行评论
  get-merge-request-detail: 查询代码评审（MR）详情
  list-merge-request-comments: 获取代码评审（MR）评论列表
  delete-merge-request-comment: 删除代码评审（MR）评论
  list-repo-merge-requests: 查询代码仓库代码评审MR列表，可以根据仓库ID，搜索词，代码评审状态等查询代码评审列表
  accept-merge-request: 通过代码评审（MR）
  update-merge-request: 更新代码评审（MR）的标题、描述、评审人或关联工作项
  list-merge-request-ai-comments: 获取代码评审（MR）的AI评审评论列表，包含AI自动生成的代码审查意见，如果AI评论没有被采纳（adopted=1），是不会展示在最终的代码...
  comment-merge-request: 在代码评审（MR）上发表全局评论，也可以通过指定父评论ID来回复已有的顶层评论。注意：只能回复顶层评论，不支持在子评论（回复）上添加嵌套回复
  search-file-path: 根据文件名或文件路径关键词搜索代码仓库中的文件路径
  list-commits: 获取分支或者分支+文件的提交历史，支持时间范围和分页查询
  get-file-block: 获取代码仓库文件指定行区间内的文件内容
  get-changed-file-diff: 查询代码仓库变更文件diff
  get-me: 获取当前登录用户基本信息，比如用户名，花名，邮箱，工号等
  get-single-file: 查询代码仓库单个文件指定版本的内容
  merge-branch: 合并分支到目标分支
  list-changed-files: 查询代码仓库分支变更文件列表
  edit-repo-files: 批量编辑文件，支持代码仓库文件的创建、更新、删除和移动位置。注意：此操作会直接修改仓库文件，属于危险操作，执行前请先向用户展示将要执行的变更...
  delete-branch: 删除分支，此操作属于危险操作，执行前请先让用户确认，用户同意后再执行
  create-branch: 新建分支
  list-repo-branches: 查询代码仓库分支列表，支持查询所有分支、活跃分支（90天内有提交）或停滞分支（90天内无提交）
  create-repository: 创建代码仓库
  get-file-blame: 查询代码仓库文件的blame信息，显示每行代码的提交历史和作者信息，用于追踪文件中每一行的变更历史
  get-repo-by-path: 根据仓库路径获取仓库基本信息，比如仓库ID，比如仓库：git@gitlab.alibaba-inc.com:foo/bar.git...
  get-repo-security-level: 批量获取仓库代码安全等级。安全等级分为：C1（公开代码）可对外开源，无敏感信息或知识产权风险；C2（内部代码）对外闭源，不涉及核心敏感业务逻...
  apply-repo-access: 申请代码仓库权限。分两步使用：
  manage-repo-members: 代码仓库成员管理，通过 action 参数选择操作：
  manage-group-members: 代码分组成员管理，通过 action 参数选择操作：
  list-my-branches: 查询我的分支列表
  list-groups: 查询用户有权限的分组列表，支持搜索和分页功能
  cherry-pick: 将指定的提交（commit）通过 cherry-pick 方式应用到目标分支上。支持单个提交或提交范围的...

<!-- MCP_MANAGER_TOOLS_END -->
