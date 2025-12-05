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
#   api_key: "${QWEN_API_KEY}"  改为  api_key: "your-actual-api-key"

# config.local.yaml 会被自动使用且不会提交到 Git
```

**方法 2：使用环境变量**

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的 API Key
# 至少需要设置 QWEN_API_KEY
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
- **判断规则**：
  1. **Markdown 检测**：如果 raw_response 包含 markdown 特征（`##`、`**`、`- **`、` ``` `）→ **markdown**
  2. **长文本 + 多字段**：包含长文本且字段多（≥3）→ **markdown**
  3. **结构化数据**：包含列表或字典 → **json**
  4. **多字段**：字段较多（≥4）→ **yaml**
  5. **默认**：其他情况 → **txt**

**Markdown 格式特点**：
- ✅ 清晰的层级结构
- ✅ 支持代码高亮
- ✅ 适合生成文档和报告
- ✅ 可直接在 GitHub/GitLab 等平台预览
- ✅ 多行文本自动格式化

**输出文件名规则** ✨ 智能命名：
- 有输入文件：`<input-basename>-output.<ext>`
  - 例如：`input.yaml` → `input-output.md`
- 无输入文件：`inputs-<YYYYMMDD_HHMMSS>-output.<ext>`
  - 例如：`inputs-20251205_214250-output.json`
- 文件保存在当前目录，显示完整绝对路径

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
    model_provider: "qwen"
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

### 使用图像输入

```bash
# 单张图像
python src/main.py run image_analyzer \
  --image photo.jpg \
  -i '{"question": "图片中有什么？"}'

# 多张图像
python src/main.py run image_analyzer \
  --image photo1.jpg \
  --image photo2.jpg \
  --image https://example.com/photo3.jpg \
  -i '{"question": "请比较这些图片"}'
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
api_key: "${QWEN_API_KEY}"

# 带默认值的环境变量
api_base: "${QWEN_API_BASE:-http://localhost:8001/v1}"
model: "${QWEN_MODEL:-qwen-max}"
```

**懒加载机制** ✨ 性能优化：
- 配置加载时**不验证**环境变量，即使未设置也不会报错
- 只在**实际使用模型**时才验证环境变量
- 允许配置文件包含多个模型，但只需设置正在使用的模型的环境变量

## 启用/禁用配置

### enabled 字段

Models 和 Agents 都支持 `enabled` 字段来控制是否启用：

```yaml
models:
  qwen:
    type: "llm"
    api_key: "${QWEN_API_KEY}"
    # ...其他配置
    enabled: true  # 启用此模型

  gpt4:
    type: "llm"
    api_key: "${OPENAI_API_KEY}"
    # ...其他配置
    enabled: false  # 禁用此模型（不加载）

agents:
  text_analyzer:
    model_provider: "qwen"
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
  qwen_vl:
    resize_image_for_api: true
    max_image_size: 1024  # 减小尺寸
    image_quality: 75     # 降低质量
```

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
