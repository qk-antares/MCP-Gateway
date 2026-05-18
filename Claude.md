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


<!-- MCP_GATEWAY_TOOLS_START -->

## MCP Gateway 可用工具

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

<!-- MCP_GATEWAY_TOOLS_END -->
