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

所有工具的摘要通过 `/refresh-mcp` skill 手动刷新写入本文件末尾，供 Claude 感知 Gateway 托管的工具。

<!-- MCP_GATEWAY_TOOLS_START -->

## MCP Gateway 可用工具

[aone-km]
  askDevOpsKnowledge: 通过自然语言提问关于阿里巴巴集团内中间件、研发运维平台相关问题，可以回答使用方法、功能介绍、接入方式、SDK代码片段、问题排查思路等
  chatWithKnowledgeBase: 基于知识库的智能问答，通过 ReAct 模式进行多轮推理和文档检索，返回带有文档引用的完整回答。适用于需要深度理解和多步推理的复杂问题。
  createDingDocWorkspaceDoc: 在钉钉知识库中新建文件夹或文档，支持在创建文档的同时写入 markdown 内容
  deletePersonalMemory: 根据 记忆内容ID 删除一条个人记忆内容。
  fetchExternalContentByUrl: 通过钉钉或者语雀文档链接获取文档内容，如果获取不到内容，请检查知识库是否完成授权，如果知识库未完成授权，请访问链接进行授权检测
  fetchKnowledgeDirectoryByUrl: 通过钉钉或者语雀知识库链接获取知识库的目录列表，如果获取不到内容，请检查知识库是否完成授权，如果知识库未完成授权，请访问链接进行授权检测
  getCodeWikiPageContent: 获取 CodeWiki 指定页面的完整内容。返回页面标题、Markdown 内容和元数据信息。
  getCodeWikiStructure: 获取代码仓库的 CodeWiki 目录结构。默认仅返回当前层级，必要时可递归返回目录树。
  getKnowledgeGroupStructure: 根据知识组 ID 获取知识组的结构信息，包括基础信息（名称、描述等）、直属子知识组列表和知识库列表。用于了解一个知识组的整体组织结构。
  getPersonalMemoryTree: 获取个人记忆目录树（含 folder / memory / `path`）。 可用于选择 `targetPath` 或构造 `scopePaths`；目录...
  getRepoPageContent: 获取知识库指定页面的完整内容。支持KB知识库及其关联的外部知识空间（CodeWiki/语雀/钉钉等）。
  hierarchicalSearchPersonalMemory: 在个人记忆中做分层语义检索。 可用 `scopePaths` 限定目录；返回项中的 `id` 可用于更新和删除。
  listRepoDirectory: 根据知识库 ID 获取知识库的目录树结构，包括文件夹和文档节点。每个文档节点包含 pageId，可用于后续获取文档内容。
  searchCodeWiki: 在 CodeWiki 中进行语义搜索，支持跨多个代码仓库搜索。返回按相关性排序的搜索结果。
  searchDevOpsKnowledge: 通过自然语言提问关于阿里巴巴集团内中间件、研发运维平台相关问题，可以查询到使用方法、功能介绍、接入方式、SDK代码片段、问题排查思路等
  searchDocChunk: 通过自然语言召回符合问题答案的文档片段列表
  smartIngestPersonalMemory: 写入个人记忆：默认自动路由到合适的 memory 节点。 传 `targetPath` 时按路径定向写入
  updateDingDocContent: 向钉钉文档覆写内容（会替换文档的全部内容, 只提供 markdown 格式内容写入）
  updatePersonalMemory: 根据记忆内容 ID 更新一条个人记忆内容。
  uploadDocToKbRepo: 上传 Markdown 文档到平台知识库，支持指定目录路径或父节点。若指定 pageId 则更新已有文档
[code]
  accept_merge_request: 通过代码评审（MR）
  apply_repo_access: 申请代码仓库权限。分两步使用： 第一步：仅传入仓库路径，获取审批人列表（包含花名和工号）； 第二步：传入审批人（花名或工号）、权限类型和申请理由，发起权限...
  cherry_pick: 将指定的提交（commit）通过 cherry-pick 方式应用到目标分支上。支持单个提交或提交范围的 cherry-pick。此操作会直接修改仓库分支...
  comment_merge_request: 在代码评审（MR）上发表全局评论，也可以通过指定父评论ID来回复已有的顶层评论。注意：只能回复顶层评论，不支持在子评论（回复）上添加嵌套回复
  comment_merge_request_changed_file: 在代码评审（MR）变更的文件上发表行评论
  comment_merge_request_code_suggestion: 在代码评审（MR）变更的文件上发表代码建议评论
  create_branch: 新建分支
  create_issue: 创建新的 Issue
  create_issue_comment: 为 Issue 添加评论
  create_merge_request: 根据用户提供的仓库ID，关联分支，标题和描述创建代码评审
  create_repository: 创建代码仓库
  create_tag: 创建代码仓库标签
  delete_branch: 删除分支，此操作属于危险操作，执行前请先让用户确认，用户同意后再执行
  delete_merge_request_comment: 删除代码评审（MR）评论
  edit_repo_files: 批量编辑文件，支持代码仓库文件的创建、更新、删除和移动位置。注意：此操作会直接修改仓库文件，属于危险操作，执行前请先向用户展示将要执行的变更内容并请求用户...
  get_changed_file_diff: 查询代码仓库变更文件diff
  get_file_blame: 查询代码仓库文件的blame信息，显示每行代码的提交历史和作者信息，用于追踪文件中每一行的变更历史
  get_file_block: 获取代码仓库文件指定行区间内的文件内容
  get_issue: 获取 Issue 详情和评论列表
  get_me: 获取当前登录用户基本信息，比如用户名，花名，邮箱，工号等
  get_merge_request_changed_file_diff: 查询代码仓库变更文件diff
  get_merge_request_detail: 查询代码评审（MR）详情
  get_repo_by_path: 根据仓库路径获取仓库基本信息，比如仓库ID，比如仓库：git@gitlab.alibaba-inc.com:foo/bar.git 的仓库路径是foo/bar
  get_repo_security_level: 批量获取仓库代码安全等级。安全等级分为：C1（公开代码）可对外开源，无敏感信息或知识产权风险；C2（内部代码）对外闭源，不涉及核心敏感业务逻辑；C3（核心...
  get_single_file: 查询代码仓库单个文件指定版本的内容
  list_changed_files: 查询代码仓库分支变更文件列表
  list_commits: 获取分支或者分支+文件的提交历史，支持时间范围和分页查询
  list_groups: 查询用户有权限的分组列表，支持搜索和分页功能
  list_issues: 查询 Issue 列表，支持简单搜索和分页
  list_merge_request_ai_comments: 获取代码评审（MR）的AI评审评论列表，包含AI自动生成的代码审查意见，如果AI评论没有被采纳（adopted=1），是不会展示在最终的代码评审评论列表中的
  list_merge_request_changed_files: 查询代码评审（MR）上变更的文件列表
  list_merge_request_ci_tasks: 获取代码评审关联CI任务详情列表
  list_merge_request_comments: 获取代码评审（MR）评论列表
  list_merge_request_commits: 查询代码评审（MR）的提交列表
  list_merge_requests_created_by_me: 全局查询我创建的代码评审MR列表，可以根据搜索词，代码评审状态等查询代码评审列表
  list_merge_requests_reviewed_by_me: 全局查询我评审的代码评审MR列表，可以根据搜索词，代码评审状态等查询代码评审列表
  list_my_branches: 查询我的分支列表
  list_repo_branches: 查询代码仓库分支列表，支持查询所有分支、活跃分支（90天内有提交）或停滞分支（90天内无提交）
  list_repo_files: 查询代码仓库文件列表
  list_repo_merge_requests: 查询代码仓库代码评审MR列表，可以根据仓库ID，搜索词，代码评审状态等查询代码评审列表
  list_repo_merge_requests_created_by_me: 查询我创建的代码仓库代码评审MR列表，可以根据仓库ID，搜索词，代码评审状态等查询代码评审列表
  list_repo_merge_requests_reviewed_by_me: 查询我评审的代码仓库代码评审MR列表，可以根据仓库ID，搜索词，代码评审状态等查询代码评审列表
  manage_group_members: 代码分组成员管理，通过 action 参数选择操作： - list：列出分组成员，支持搜索和分页 - get：查询单个成员详情（user 必填） - ad...
  manage_issue_label: 管理 Issue 的标签关联，支持添加或删除标签。添加时通过标签名操作，如果标签不存在会自动创建；删除时通过标签 ID 操作，可通过 manage_lab...
  manage_issue_tracer: 管理 Issue 的关注人（抄送人），支持添加或删除。关注人会收到 Issue 变更通知
  manage_label: 管理仓库的 Issue 标签（仓库级别），支持查询、创建和删除标签。注意：这是管理仓库的标签定义，不是管理 Issue 与标签的关联关系（关联关系请使用 ...
  manage_repo_members: 代码仓库成员管理，通过 action 参数选择操作： - list：列出仓库成员，支持搜索和分页 - get：查询单个成员详情（user 必填） - ad...
  merge_branch: 合并分支到目标分支
  merge_merge_request: 合并代码评审（MR）
  operate_ai_comment: 操作AI评审评论，支持采纳、忽略和拒绝AI自动生成的代码审查意见。在获取AI评论列表后，可使用此工具对具体的AI评论进行处理
  remind_merge_request_assignees: 提醒代码评审评审人评审代码评审
  repo_vector_search: 在代码仓库中根据语义搜索主干分支代码
  search_authorized_repositories: 搜索我有权限访问的代码仓库，支持模糊搜索仓库名称
  search_classes: 搜索参与的仓库或指定仓库内的类
  search_code: 搜索仓库内的代码片段和代码文件元数据，支持搜索所有仓库或指定仓库
  search_file_path: 根据文件名或文件路径关键词搜索代码仓库中的文件路径
  search_methods: 搜索参与的仓库或指定仓库内的方法
  update_issue_status: 更新 Issue 状态。必填参数：repo, issueId, status；status 可选值（不区分大小写，支持中英文同义词）：new/待处理、as...
  update_merge_request: 更新代码评审（MR）的标题、描述、评审人或关联工作项
  update_merge_request_comment_status: 更新代码评审（MR）评论状态
[coop]
  add_comment: 增加评论。
  add_module: 新建模块。
  add_project_members: 添加项目成员。
  add_workitem_tags: 给工作项添加标签。
  add_workitem_tracker: 增加工作项抄送人。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的报错信息
  batch_update_workitem_field: 批量更新工作项字段信息,一次支持更新多个字段的值 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返...
  change_workitem_assign_to: 修改工作项指派人。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的报错信息
  change_workitem_priority: 修改工作项优先级。 优先级可选值：94-紧急, 95-高, 96-中, 97-低 结果为 JSON 字符串，包含字段 "success"，值为 true ...
  change_workitem_project: 修改工作项归属的项目。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的...
  change_workitem_sprint: 修改工作项所属迭代。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的报错信息
  change_workitem_status: 修改工作项状态。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的报错信息
  create_project: 创建项目。
  create_relation: 工作项之间创建关联关系
  create_sprint: 创建迭代。
  create_sub_workitem: 创建子需求 / 子任务，需要提供标题、指派者、归属项目、父工作项 Id，描述内容按需要提供 如果没有提供工作项类型，也就是需求、任务、缺陷，则默认创建缺陷...
  create_version: 新建版本, 要求 projectId 以及 name 必填，description 可填。
  create_workitem: 创建工作项，需要提供标题、指派者、归属项目，描述内容按需要提供。 如果没有提供工作项类型，也就是需求、任务、缺陷，则默认创建缺陷。 默认工作项类型是缺陷，...
  delete_workitem_tags: 删除工作项的标签。
  export_workitem: 导出工作项
  get_export_workitem: 通过导出任务的 task 获取导出工作项的结果
  get_project_info_by_project_id: 根据项目 ID 获取项目信息
  get_project_members: 根据项目 id 获取项目内的成员，当且仅当需要查询特定项目内的成员时可以使用该接口。
  get_show_field_list: 获取工作项能导出的字段
  get_sprint_by_id: 通过迭代id获取迭代信息
  get_sprints_by_project_id: 获取项目id关联的迭代列表
  get_sub_pluginTask: 查询工作项下关联的变更
  get_sub_workitem: 查询子工作项
  get_user_info_by_staff_id: 通过工号获取用户信息
  get_workitem_attachments: 获取工作项的附件列表
  get_workitem_comments: 查询工作项评论。
  get_workitem_related_code_review: 获取工作项关联的代码评审信息
  list_module: 通过项目id 获取模块列表。
  list_version: 列出项目的版本，可以通过 keyword 参数对项目中版本进行模糊搜索。
  lock_sprint: 锁定迭代
  query_recent_workitem_list: 展示我最近的工作项，缺陷、需求和任务都是工作项，可以按类型展示。 默认展示工作项是缺陷，即 stamp=Bug, 也可以展示需求，即 stamp=Req,...
  query_user_recent_visit_projects: 获取用户最近访问的项目。
  query_workitem_detail: 获取工作项详情。
  remove_module: 删除模块。
  remove_project_members: 删除项目成员。
  search_project_by_project_name: 根据项目名称搜索
  search_user_related_workitem_by_sprint: 根据迭代查找与当前用户相关的工作项。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 mess...
  search_workitem_assigned_to_user: 搜索指派给我的工作项。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的...
  search_workitem_by_project: 根据项目查找工作项。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的报错信息
  search_workitem_by_sprint: 根据迭代查找工作项。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的报错信息
  search_workitem_title: 搜索工作项。 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的报错信息
  update_module: 更新模块。
  update_project: 通过项目 id 更新项目属性信息。
  update_sprint: 更新迭代。
  update_version: 更新版本。
  update_workitem_description: 更新工作项描述信息 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返回 messages 中的报错信息
  update_workitem_field: 更新工作项字段信息, 一次只支持更新一个字段的值 结果为 JSON 字符串，包含字段 "success"，值为 true 或 false，如果失败了，就返...
  update_workitem_module: 更新工作项模块信息。
  update_workitem_sprint: 更新工作项迭代信息。
  update_workitem_versions: 更新工作项版本信息。

<!-- MCP_GATEWAY_TOOLS_END -->
