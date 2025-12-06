# Simple AI Agents - 使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

**方法 1：使用 config.local.yaml（推荐）**

```bash
# 复制配置文件
cp config.yaml config.local.yaml

# 编辑 config.local.yaml，将环境变量替换为实际值
# 例如：
#   api_key: "${QWEN3_API_KEY}"  改为  api_key: "your-actual-api-key"

# config.local.yaml 会被自动使用且不会提交到 Git
```

**方法 2：使用环境变量**

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的 API Key
# 至少需要设置 QWEN3_API_KEY
```

### 3. 加载环境变量

```bash
# Linux/Mac
export $(cat .env | xargs)

# Windows (PowerShell)
Get-Content .env | ForEach-Object {
    $name, $value = $_.split('=')
    [Environment]::SetEnvironmentVariable($name, $value, 'Process')
}
```

## CLI 命令

### list - 列举所有配置

```bash
python src/main.py list
```

输出示例：
```
=== Models ===
  - qwen3_vl_plus (vlm) [enabled]
  - deepseek_r1 (llm) [enabled]

=== Agents ===
  - jira_req_bot -> deepseek_r1 [enabled]
      jira REQ 备注信息生成
```

**说明**：
- 只显示 `enabled: true` 的 models 和 agents
- 禁用的配置项在加载时被过滤，不会出现在列表中

### stat - 统计信息

```bash
python src/main.py stat
```

输出示例：
```
=== Statistics ===
Total Models: 2 (2 enabled)
Total Agents: 1 (1 enabled)
```

### info - 查看详细信息

```bash
# 查看 model 信息
python src/main.py info deepseek_r1

# 查看 agent 信息
python src/main.py info jira_req_bot
```

输出示例：
```
=== Model: deepseek_r1 ===
  Enabled: True
  Type: llm
  API Base: http://...
  Model: deepseek-r1
  Max Tokens: 4096
  Temperature: 0.1
```

### run - 运行 Agent

#### 基础使用

```bash
# 从文件读取输入（自动判断格式和输出格式）
python src/main.py run jira_req_bot -i input.yaml

# 直接输入 JSON
python src/main.py run text_analyzer -i '{"text": "今天天气真好，心情也很愉快！"}'

# 直接输入 YAML
python src/main.py run text_analyzer -i 'text: 今天天气真好，心情也很愉快！'

# 从 JSON 文件读取输入
echo '{"text": "这是一个测试文本"}' > input.json
python src/main.py run text_analyzer -i input.json

# 从 YAML 文件读取输入
cat > input.yaml << EOF
text: 这是一个测试文本
context: 测试上下文
EOF
python src/main.py run text_analyzer -i input.yaml

# 手动指定输出格式
python src/main.py run text_analyzer -i input.json --format yaml
python src/main.py run text_analyzer -i input.yaml --format txt

# 手动指定输出文件路径
python src/main.py run text_analyzer -i input.yaml -o custom-output.json
```

**执行结果示例**：
```
🤖 执行 Agent: jira_req_bot
==================================================
==================================================

💡 自动选择输出格式: md

⏱️  运行时间: 57.11 秒 (Agent执行: 57.11 秒)
📁 输出文件: /absolute/path/to/input-output.md
✅ 执行状态: success
```

#### 参数说明

| 参数 | 别名 | 必需 | 说明 |
|------|------|------|------|
| `-i, --input, --inputs` | - | ✅ | 输入数据（文本、文件路径、JSON 或 YAML） |
| `--image` | - | ❌ | 图像输入（可多次使用，用于 VLM） |
| `-o, --output` | - | ❌ | 输出文件路径（默认自动生成） |
| `--format` | - | ❌ | 输出格式（json/yaml/txt/md，默认自动判断） |

#### 输入格式支持

系统支持多种输入格式，自动识别：

1. **JSON 格式**
   ```bash
   # 字符串
   -i '{"text": "hello", "context": "world"}'

   # 文件 (*.json)
   -i input.json
   ```

2. **YAML 格式**（新功能✨）
   ```bash
   # 字符串
   -i 'text: hello\ncontext: world'

   # 文件 (*.yaml 或 *.yml)
   -i input.yaml
   ```

3. **纯文本**
   ```bash
   # 如果不是 JSON 或 YAML，会被包装为 {"input": "文本内容"}
   -i "这是纯文本"
   ```

**格式识别优先级**：
- 文件：根据扩展名 (.json / .yaml / .yml)
- 字符串：先尝试 JSON，再尝试 YAML，最后作为纯文本

#### 多格式输出示例

```bash
# 自动判断格式（默认）✨ 新增
python src/main.py run text_analyzer -i input.yaml
# 系统会根据输出内容自动选择最合适的格式

# 手动指定 JSON 格式
python src/main.py run text_analyzer -i '{"text": "测试文本"}' --format json

# YAML 格式
python src/main.py run text_analyzer -i '{"text": "测试文本"}' --format yaml

# TXT 格式（人类可读）
python src/main.py run text_analyzer -i '{"text": "测试文本"}' --format txt

# Markdown 格式（文档报告）
python src/main.py run text_analyzer -i '{"text": "测试文本"}' --format markdown
python src/main.py run text_analyzer -i input.yaml --format md -o report.md
```

#### 输出格式说明

系统支持 4 种输出格式：

| 格式 | 别名 | 扩展名 | 适用场景 |
|------|------|--------|----------|
| JSON | json | .json | 程序处理、API 对接 |
| YAML | yaml | .yaml | 配置文件、人类可读 |
| TXT | txt | .txt | 快速查看、调试 |
| Markdown | md, markdown | .md | 文档、报告、展示 |

**格式自动判断** ✨ 智能特性：
- 未指定 `--format` 时，系统自动根据输出内容选择最合适的格式
- **判断规则**（按优先级）：
  1. **结构化数据优先**：包含列表或字典 → **json** 🔥 *（保持数据结构完整性）*
  2. **Markdown 检测**：如果 raw_response 包含 markdown 特征（`##`、`**`、`- **`、` ``` `）→ **markdown**
  3. **长文本 + 多字段**：包含长文本且字段多（≥3）→ **markdown**
  4. **多字段**：字段较多（≥4）→ **yaml**
  5. **默认**：其他情况 → **txt**

**Markdown 格式特点**：
- ✅ 清晰的层级结构
- ✅ 支持代码高亮
- ✅ 适合生成文档和报告
- ✅ 可直接在 GitHub/GitLab 等平台预览
- ✅ 多行文本自动格式化

**JSON 格式优势**：
- ✅ 保持数据结构完整性（数组、对象）
- ✅ 便于程序解析和处理
- ✅ 标准的 API 数据交换格式
- ✅ 支持嵌套结构

**格式选择建议**：
- **包含 list/dict** → 自动选择 JSON（推荐让系统自动判断）
- **纯文本叙事** → Markdown 格式
- **配置数据** → YAML 格式
- **快速调试** → TXT 格式

**输出文件名规则** ✨ 智能命名：
- 有输入文件：`<agent_name>-<YYYY-MM-DD_HH-MM-SS>-<input-basename>.<ext>`
  - 例如：`output/text_analyzer-2025-12-06_14-40-29-myinput.json`
- 无输入文件：`<agent_name>-<YYYY-MM-DD_HH-MM-SS>.<ext>`
  - 例如：`output/text_analyzer-2025-12-06_14-29-30.json`
- 文件默认保存在 `./output/` 目录（由 `config.yaml` 的 `output_dir` 配置）
- 显示完整绝对路径

**命名优势**：
- ✅ **时间戳前置**：按文件名排序 = 按时间排序，最新结果在底部
- ✅ **Agent 名称前缀**：知道是哪个 agent 处理的
- ✅ **包含输入文件名**：可追溯数据源
- ✅ **方便批量操作**：`text_analyzer-2025-12-06*` 选择某天的所有结果

## 创建自定义 Agent

### 1. 创建 Agent 目录

```bash
mkdir -p config/agents/my_agent
```

### 2. 创建配置文件

`config/agents/my_agent/config.json`:
```json
{
  "type": "llm",
  "inputs": ["text", "context"],
  "outputs": ["result", "confidence"],
  "system_prompt": "./system.txt",
  "user_prompt": "./user.txt"
}
```

### 3. 编写 Prompts

`config/agents/my_agent/system.txt`:
```
你是一个助手...

输出格式：
{
  "result": "...",
  "confidence": 0.95
}
```

`config/agents/my_agent/user.txt`:
```
文本：{{text}}
上下文：{{context}}
```

### 4. 注册 Agent

在 `config.yaml` 中添加：
```yaml
agents:
  my_agent:
    model_provider: "qwen3"
    config: "./config/agents/my_agent/config.json"
    enabled: true
    description: "我的自定义 Agent"
```

### 5. 测试 Agent

```bash
python src/main.py info my_agent
python src/main.py run my_agent -i '{"text": "...", "context": "..."}'
```

## VLM (Vision Language Model) 使用

### 便捷脚本使用 ✨ 推荐

框架提供了便捷的 bash 脚本来快速运行 Agent：

#### image_captioner - 图像描述生成

```bash
# 无参数运行 - 使用默认示例图片
./scripts/image_captioner.sh

# 使用本地图片
./scripts/image_captioner.sh photo.jpg

# 使用网络图片 URL
./scripts/image_captioner.sh https://example.com/photo.jpg

# 自定义问题
./scripts/image_captioner.sh photo.jpg "图片中有哪些物体？"
./scripts/image_captioner.sh https://example.com/photo.jpg "What animals are in this image?"
```

**脚本特性**：
- ✅ 自动识别本地文件和网络 URL
- ✅ 支持默认示例（无需参数即可测试）
- ✅ 友好的提示信息
- ✅ 自动判断输出格式为 JSON（保持结构化数据完整性）

**输出示例**：
```json
{
  "outputs": {
    "caption": "一位年轻女子和她的金毛犬在沙滩上互动...",
    "details": "这是一幅充满温馨与欢乐氛围的户外场景...",
    "objects": ["年轻女子", "金毛犬", "沙滩", "海洋", "夕阳"],
    "scene": "室外，海滩，日落时分，温暖宁静的自然环境"
  }
}
```

#### text_analyzer - 文本分析

```bash
# 无参数运行 - 使用默认示例文本
./scripts/text_analyzer.sh

# 直接输入文本
./scripts/text_analyzer.sh "今天天气真好，心情也很愉快！"

# 从文件读取文本
./scripts/text_analyzer.sh text_file.txt
```

**注意**：text_analyzer 需要在 config.yaml 中启用并配置相应的 LLM 模型。

### 配置 VLM Agent

`config/agents/image_analyzer/config.json`:
```json
{
  "type": "vlm",
  "inputs": ["question"],
  "outputs": ["answer"],
  "system_prompt": "./system.txt",
  "user_prompt": "./user.txt"
}
```

### 使用图像输入（CLI 方式）

```bash
# 单张图像
python src/main.py run image_captioner \
  --image photo.jpg \
  -i '{"question": "图片中有什么？"}'

# 多张图像
python src/main.py run image_captioner \
  --image photo1.jpg \
  --image photo2.jpg \
  --image https://example.com/photo3.jpg \
  -i '{"question": "请比较这些图片"}'

# 支持本地文件和网络 URL
python src/main.py run image_captioner \
  --image https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg \
  -i '{"question": "请详细描述这张图片的内容"}'
```

## 参数验证

系统提供三层验证：

### 1. Prompt 模板验证

自动检查 system.txt 和 user.txt 中是否使用 `{{field}}` 引用了所有 inputs 字段。

### 2. 输入数据验证

运行时检查输入数据是否包含所有必需字段，缺少字段时会询问是否继续。

### 3. 输出数据验证

检查 Agent 输出是否包含所有 outputs 字段，缺少字段会警告但继续执行。

## 环境变量

配置文件支持两种环境变量语法：

```yaml
# 必需的环境变量（不存在则报错）
api_key: "${QWEN3_API_KEY}"

# 带默认值的环境变量
api_base: "${QWEN3_API_BASE:-http://localhost:8001/v1}"
model: "${QWEN3_MODEL:-qwen3-max}"
```

**懒加载机制** ✨ 性能优化：
- 配置加载时**不验证**环境变量，即使未设置也不会报错
- 只在**实际使用模型**时才验证环境变量
- 允许配置文件包含多个模型，但只需设置正在使用的模型的环境变量

**Agent 按需加载** ✨ 高效加载：
- `python src/main.py` 启动时只读取 agent 的元数据（名称、描述）
- `python src/main.py run <agent_name>` 执行时才加载指定 agent 的详细配置
- 已加载的 agent 会缓存，重复使用时更快
- 其他未使用的 agent 配置不会被加载，节省内存和时间

## 启用/禁用配置

### enabled 字段

Models 和 Agents 都支持 `enabled` 字段来控制是否启用：

```yaml
models:
  qwen3:
    type: "llm"
    api_key: "${QWEN3_API_KEY}"
    # ...其他配置
    enabled: true  # 启用此模型

  gpt4:
    type: "llm"
    api_key: "${OPENAI_API_KEY}"
    # ...其他配置
    enabled: false  # 禁用此模型（不加载）

agents:
  text_analyzer:
    model_provider: "qwen3"
    config: "./config/agents/text_analyzer/config.json"
    enabled: true  # 启用此 Agent
    description: "文本分析 Agent"

  old_agent:
    model_provider: "old_model"
    config: "./config/agents/old_agent/config.json"
    enabled: false  # 禁用此 Agent（不加载）
    description: "已废弃的 Agent"
```

**行为说明**：
- `enabled: false` 的配置在加载时就被**过滤掉**
- 禁用的 model/agent 不会出现在 `list` 和 `stat` 命令中
- 尝试使用禁用的 model/agent 会提示"不存在或未启用"
- 默认值为 `true`（向后兼容）

**使用场景**：
- 临时禁用某些不常用的 models/agents
- 开发环境中只启用需要测试的配置
- 避免加载需要特殊环境变量的配置（如 OpenAI API Key）

## 常见问题

### Q: 为什么不能使用 `list` 作为自定义函数名？

A: `list` 是 Python 的内置函数。在早期版本中，使用 `list` 作为函数名会导致 Click CLI 参数解析失败。框架已修复此问题，使用 `@cli.command(name='list')` 配合 `def list_cmd()` 的方式避免冲突。

如果你在创建自定义命令时遇到类似问题，避免使用这些 Python 内置名称：
- `list`, `dict`, `set`, `tuple`
- `str`, `int`, `float`, `bool`
- `input`, `print`, `open`, `file`

### Q: 运行 agent 时是只加载指定的 agent 吗？

A: 是的，框架采用**按需加载**机制：

**启动阶段** (`python src/main.py`)：
- ✅ 读取所有 `enabled: true` 的 models 和 agents 的元数据
- ✅ 供 `list`、`stat`、`info` 命令使用
- ❌ 不加载 agent 详细配置（config.json、prompts）
- ❌ 不验证环境变量

**执行阶段** (`python src/main.py run <agent_name>`)：
- ✅ 只加载指定 agent 的详细配置
- ✅ 只获取该 agent 使用的模型配置
- ✅ 只验证该模型的环境变量
- ✅ 已加载的 agent 会缓存，重复使用更快

**优势**：
- 快速启动，不需要加载所有配置
- 环境变量按需验证，未使用的模型可以缺少 API Key
- 内存占用小，只加载需要的内容

### Q: 如何调试 Agent？

A: 查看日志文件 `logs/agent.log`，或设置日志级别为 DEBUG：

```yaml
logging:
  level: "DEBUG"
```

### Q: 如何处理大图像？

A: 在模型配置中调整图像处理参数：

```yaml
models:
  qwen3_vl:
    resize_image_for_api: true
    max_image_size: 1024  # 减小尺寸
    image_quality: 75     # 降低质量
```

### Q: 如何启用图像缓存以提升性能？

A: 图像缓存可以避免重复处理相同的图像，提升性能：

**启用缓存**：
```yaml
models:
  qwen3_vl:
    type: "vlm"
    # ... 其他配置
    # 图像缓存配置
    image_cache_enabled: true       # 启用图像缓存
    image_cache_ttl: 86400          # 缓存过期时间（秒），默认 24 小时
```

**缓存机制说明**：
- **缓存键生成**：基于图像源路径 + 配置参数（max_size、quality、resize）+ 文件修改时间的 SHA256 hash
- **自动过期**：默认 24 小时后过期，可通过 `image_cache_ttl` 调整
- **智能失效**：本地图像修改后会自动使用新的缓存键
- **存储格式**：Base64 编码的图像数据 + 元数据，存储在 `cache/images/` 目录
- **URL 缓存**：仅在下载图像时缓存（`download=True`），直接传递 URL 不缓存

**缓存文件示例**：
```json
{
  "data": "data:image/jpeg;base64,/9j/4AAQ...",
  "timestamp": 1764999879.347573,
  "metadata": {
    "original_size": [800, 600],
    "processed_size": [800, 600],
    "format": "JPEG",
    "mime_type": "image/jpeg"
  }
}
```

**使用场景**：
- ✅ 批量处理相同图像
- ✅ 开发调试时重复测试
- ✅ API 成本优化（减少重复处理）
- ⚠️ 注意磁盘空间占用

**性能提升**：
- 跳过图像读取、解码、resize、编码等步骤
- 首次运行正常处理，后续运行直接从缓存加载
- 日志会显示 "从缓存加载图像: xxx"

**默认禁用**：为避免意外的磁盘占用，缓存默认是禁用的，需要显式启用

### Q: 如何跳过验证？

A: 在配置文件中禁用验证：

```yaml
validation:
  prompt_template_validation: false
  input_validation: false
  output_validation: false
```

## 更多示例

查看 `docs/design.md` 了解完整的设计文档和更多使用示例。
