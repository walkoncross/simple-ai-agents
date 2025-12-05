# Simple AI Agents - 设计文档

## 1. 项目概述

Simple AI Agents 是一个轻量级的 AI Agent 工厂框架，通过配置文件定义和管理多个 AI Agents，支持 LLM 和 VLM（Vision Language Model）。所有模型都通过兼容 OpenAI API 的接口进行调用。

### 1.1 核心特性

- 基于 system prompt 和 user prompt 构建简单 AI Agent
- 支持 LLM 和 VLM 两种模型类型
- 配置驱动的 Agent 管理
- 命令行界面（CLI）进行操作
- 结构化的 JSON 输出

## 2. 系统架构

### 2.1 目录结构

```
simple-ai-agents/
├── config.yaml                 # 主配置文件
├── config/
│   └── agents/                 # Agent 配置目录
│       ├── agent_name_1/
│       │   ├── config.json     # Agent 元数据配置
│       │   ├── system.txt      # System prompt
│       │   └── user.txt        # User prompt (可选)
│       └── agent_name_2/
│           ├── config.json
│           └── system.txt
├── src/
│   ├── main.py                 # CLI 入口
│   ├── core/
│   │   ├── agent.py            # Agent 基类
│   │   ├── factory.py          # Agent 工厂
│   │   └── model_client.py     # 模型客户端
│   ├── cli/
│   │   ├── commands.py         # CLI 命令实现
│   │   └── parser.py           # 参数解析
│   ├── formatters/
│   │   ├── base.py             # 格式化器基类
│   │   ├── json_formatter.py   # JSON 格式化器
│   │   ├── txt_formatter.py    # TXT 格式化器
│   │   └── yaml_formatter.py   # YAML 格式化器
│   └── utils/
│       ├── config_loader.py    # 配置加载器
│       ├── output_manager.py   # 输出管理
│       └── image_processor.py  # 图像处理器
├── output/                     # 执行结果输出目录
└── docs/                       # 文档目录
```

### 2.2 核心组件

#### 2.2.1 Agent

Agent 是系统的核心执行单元，包含：
- **类型**：llm 或 vlm
- **输入定义**：接受的输入参数列表
- **输出定义**：输出的字段列表
- **Prompts**：system prompt 和 user prompt（可选）

#### 2.2.2 Model Client

模型客户端负责：
- 与兼容 OpenAI API 的模型服务通信
- 处理 API 请求和响应
- 支持重试和错误处理

#### 2.2.3 Agent Factory

工厂模式管理 Agent：
- 根据配置文件创建 Agent 实例
- 管理 Agent 生命周期
- 提供 Agent 查询和统计功能

#### 2.2.4 输出格式化器

支持多种输出格式：
- **JSON Formatter**: 结构化 JSON 输出，适合程序处理
- **TXT Formatter**: 人类可读的文本格式，适合查看和调试
- **YAML Formatter**: YAML 格式，适合配置管理和人类阅读

格式化器接口：
```python
class BaseFormatter:
    def format(self, result: dict) -> str:
        """将结果格式化为字符串"""
        pass

    def get_extension(self) -> str:
        """返回文件扩展名"""
        pass
```

#### 2.2.5 图像处理器

处理 VLM 的图像输入：
- 验证图像文件和 URL
- 图像格式转换（支持 jpg, png, webp, gif）
- 图像压缩和尺寸调整
- Base64 编码
- 批量处理多图像输入
- 缓存已处理的图像（可选）

功能：
```python
class ImageProcessor:
    def process_image(self, image_path_or_url: str) -> str:
        """处理单个图像，返回 base64 或 URL"""
        pass

    def process_images(self, images: List[str]) -> List[dict]:
        """批量处理图像，返回 OpenAI 格式的图像列表"""
        pass

    def resize_image(self, image: Image, max_size: int) -> Image:
        """调整图像大小"""
        pass
```

## 3. 配置文件设计

### 3.1 主配置文件 (config.yaml)

```yaml
# 工作目录配置
output_dir: "./output"
temp_dir: "./temp"
cache_dir: "./cache"

# 模型配置
models:
  # LLM 示例
  qwen:
    type: "llm"
    api_base: "http://localhost:8001/v1"
    api_key: "your-api-key"
    model: "qwen-max"
    max_tokens: 4096
    temperature: 0.7

  # VLM 示例
  qwen_vl:
    type: "vlm"
    api_base: "http://localhost:8000/v1"
    api_key: "your-api-key"
    model: "qwen-vl-plus"
    max_tokens: 4096
    temperature: 0.1
    resize_image_for_api: true
    max_image_size: 2048

  # OpenAI GPT-4
  gpt4:
    type: "llm"
    api_base: "https://api.openai.com/v1"
    api_key: "sk-xxx"
    model: "gpt-4"
    max_tokens: 2048
    temperature: 0.7

# Agent 配置
agents:
  text_analyzer:
    model_provider: "qwen"          # 使用的模型名称
    config: "./config/agents/text_analyzer/config.json"
    enabled: true
    description: "文本分析 Agent"

  image_captioner:
    model_provider: "qwen_vl"
    config: "./config/agents/image_captioner/config.json"
    enabled: true
    description: "图像描述生成 Agent"

  summarizer:
    model_provider: "gpt4"
    config: "./config/agents/summarizer/config.json"
    enabled: false
    description: "内容摘要 Agent"

# API 配置
api:
  max_retries: 3
  retry_delay: 2.0
  timeout: 60

# 日志配置
logging:
  level: "INFO"
  file: "./logs/agent.log"
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
```

### 3.2 Agent 配置文件 (config/agents/*/config.json)

```json
{
  "type": "llm",
  "inputs": [
    "text",
    "context"
  ],
  "outputs": [
    "result",
    "confidence",
    "reasoning"
  ],
  "system_prompt": "./system.txt",
  "user_prompt": "./user.txt"
}
```

**字段说明**：
- `type`: Agent 类型，"llm" 或 "vlm"
- `inputs`: 输入参数列表（可选，用于参数验证）
- `outputs`: 期望的输出字段列表（可选，用于输出验证）
- `system_prompt`: system prompt 文件路径（相对于 config.json）
- `user_prompt`: user prompt 文件路径（可选）

**参数验证规则**：

如果指定了 `inputs` 字段：
1. **Prompt 模板验证**：系统会检查 system_prompt 和 user_prompt 中是否使用 `{{field_name}}` 引用了所有输入字段
2. **输入格式验证**：
   - 如果 `-i` 参数是文本或文本文件，内容必须是有效的 JSON 格式，可解析为字典
   - 如果是 JSON 文件，必须包含有效的 JSON 对象（字典）
3. **字段完整性检查**：
   - 解析输入数据后，检查是否包含所有必需的 inputs 字段
   - 如果缺少字段，发出警告并询问是否继续执行

如果指定了 `outputs` 字段：
1. **输出验证**：Agent 执行完成后，检查返回结果是否包含所有指定的 outputs 字段
2. **缺失字段处理**：如果输出缺少字段，记录警告但不中断执行

### 3.3 Prompt 文件

#### system.txt
```
你是一个专业的文本分析助手。请根据用户提供的文本进行深入分析。

分析时需要考虑：
1. 文本的主题和核心内容
2. 情感倾向
3. 关键信息提取

请严格按照以下 JSON 格式输出结果：
{
  "result": "分析结果",
  "confidence": 0.0-1.0,
  "reasoning": "分析推理过程"
}
```

#### user.txt
```
请分析以下文本：
{{text}}

上下文信息：
{{context}}

请提供详细的分析结果。
```

**注意**：
- 使用 `{{field_name}}` 语法引用输入字段
- 字段名必须与 config.json 中的 `inputs` 定义一致
- 系统会在运行时验证所有输入字段是否都被引用

## 4. CLI 命令设计

### 4.1 命令列表

#### 4.1.1 list/stat

列举和统计所有配置的 models 和 agents。

```bash
# 列出所有配置
python main.py list

# 统计信息
python main.py stat
```

**输出示例**：
```
Models:
  - qwen (llm) [enabled]
  - qwen_vl (vlm) [enabled]
  - gpt4 (llm) [enabled]

Agents:
  - text_analyzer -> qwen [enabled]
  - image_captioner -> qwen_vl [enabled]
  - summarizer -> gpt4 [disabled]

Summary:
  Total Models: 3 (3 enabled)
  Total Agents: 3 (2 enabled)
```

#### 4.1.2 info

打印指定 model 或 agent 的详细配置信息。

```bash
# 查看 model 信息
python main.py info qwen

# 查看 agent 信息
python main.py info text_analyzer
```

**输出示例**：
```
Model: qwen
  Type: llm
  API Base: http://localhost:8001/v1
  Model: qwen-max
  Max Tokens: 4096
  Temperature: 0.7

Agent: text_analyzer
  Model Provider: qwen
  Type: llm
  Enabled: true
  Description: 文本分析 Agent
  Inputs: [text, context]
  Outputs: [result, confidence, reasoning]
  System Prompt: ./config/agents/text_analyzer/system.txt
  User Prompt: ./config/agents/text_analyzer/user.txt
```

#### 4.1.3 run

执行指定的 agent。

**命令格式**：
```bash
python main.py run <agent_name> [options]
```

**参数说明**：
- `-i, --inputs`: 输入数据，可以是文本、文本文件路径、JSON 路径
- `--image`: 图像输入，支持 URL 或本地文件路径，可多次使用
- `-o, --output`: 输出文件路径（可选，默认自动生成）
- `--format`: 输出格式，可选 txt/json/yaml（默认：json）

**使用示例**：

```bash
# 基础文本输入
python main.py run text_analyzer -i "这是要分析的文本"

# 从文件读取输入
python main.py run text_analyzer -i input.txt

# 从 JSON 文件读取输入（支持多个输入参数）
python main.py run text_analyzer -i input.json

# 指定输出文件和格式
python main.py run text_analyzer -i input.json -o output.json --format json

# 单张图像输入（VLM）
python main.py run image_captioner --image ./images/photo.jpg

# 多张图像输入（VLM）
python main.py run image_captioner \
  --image ./images/photo1.jpg \
  --image ./images/photo2.jpg \
  --image https://example.com/photo3.jpg

# 图像 + 文本输入
python main.py run image_captioner \
  --image ./images/photo.jpg \
  -i "请详细描述这张图片"

# 使用不同输出格式
python main.py run text_analyzer -i input.txt --format txt
python main.py run text_analyzer -i input.txt --format yaml
python main.py run text_analyzer -i input.txt --format json

# 多图像 + JSON 输入 + YAML 输出
python main.py run visual_qa \
  --image ./img1.jpg \
  --image ./img2.jpg \
  -i questions.json \
  --format yaml \
  -o results.yaml
```

**输入 JSON 格式**：
```json
{
  "text": "这是要分析的文本内容",
  "context": "相关的上下文信息"
}
```

**输出格式详解**：

1. **JSON 格式** (默认)：
```json
{
  "agent": "text_analyzer",
  "timestamp": "2025-12-05T19:30:00",
  "inputs": {
    "text": "这是要分析的文本内容",
    "context": "相关的上下文信息",
    "images": [
      "./images/photo1.jpg",
      "https://example.com/photo2.jpg"
    ]
  },
  "outputs": {
    "result": "分析结果...",
    "confidence": 0.95,
    "reasoning": "分析推理过程..."
  },
  "execution_time": 2.34,
  "status": "success"
}
```

2. **TXT 格式**：
```
Agent: text_analyzer
Timestamp: 2025-12-05T19:30:00
Status: success
Execution Time: 2.34s

=== Inputs ===
text: 这是要分析的文本内容
context: 相关的上下文信息
images:
  - ./images/photo1.jpg
  - https://example.com/photo2.jpg

=== Outputs ===
result: 分析结果...
confidence: 0.95
reasoning: 分析推理过程...
```

3. **YAML 格式**：
```yaml
agent: text_analyzer
timestamp: '2025-12-05T19:30:00'
status: success
execution_time: 2.34
inputs:
  text: 这是要分析的文本内容
  context: 相关的上下文信息
  images:
    - ./images/photo1.jpg
    - https://example.com/photo2.jpg
outputs:
  result: 分析结果...
  confidence: 0.95
  reasoning: 分析推理过程...
```

**注意**：
- YAML 格式层次清晰，适合配置管理和人类阅读
- 对于多图像输入，图像路径以列表形式展示
- TXT 格式适合快速查看，JSON 格式适合程序处理，YAML 格式适合配置和文档

### 4.2 CLI 参数详细规格

#### 4.2.1 --image 参数

**用途**: 为 VLM 提供图像输入

**格式**:
```bash
--image <path_or_url>
```

**特性**:
- 可多次使用，支持多图像输入
- 支持本地文件路径（相对路径和绝对路径）
- 支持 HTTP/HTTPS URL
- 自动检测图像格式
- 按参数顺序处理图像

**示例**:
```bash
# 单个图像
--image photo.jpg

# 多个图像（顺序处理）
--image img1.jpg --image img2.jpg --image img3.jpg

# 混合本地和远程
--image ./local.jpg --image https://example.com/remote.jpg

# 绝对路径
--image /Users/admin/images/photo.png
```

**错误处理**:
- 文件不存在时报错并退出
- 不支持的图像格式时警告
- URL 无效时报错
- 网络问题时支持重试

#### 4.2.2 --format 参数

**用途**: 指定输出格式

**格式**:
```bash
--format <format_type>
```

**可选值**:
- `json` (默认): JSON 格式
- `txt`: 文本格式
- `yaml`: YAML 格式

**行为**:
- 默认值为 `json`
- 自动添加对应的文件扩展名（如果指定了 `-o`）
- 影响终端输出和文件输出

**示例**:
```bash
# 默认 JSON
python main.py run agent_name -i input.txt

# 明确指定 JSON
python main.py run agent_name -i input.txt --format json

# TXT 格式
python main.py run agent_name -i input.txt --format txt -o output.txt

# YAML 格式
python main.py run agent_name -i input.txt --format yaml -o output.yaml
```

**与 -o 参数的交互**:
```bash
# 自动推断扩展名
python main.py run agent -i input.txt --format yaml
# 输出: ./output/agent_<timestamp>.yaml

# 手动指定文件名
python main.py run agent -i input.txt --format yaml -o report.yaml
# 输出: report.yaml

# 扩展名不匹配时警告但继续执行
python main.py run agent -i input.txt --format json -o output.txt
# 警告: Format is 'json' but output file has '.txt' extension
```

#### 4.2.3 参数组合规则

1. **--image 与 -i 结合**:
   ```bash
   # 图像 + 文本输入
   python main.py run agent --image photo.jpg -i "分析这张图片"

   # 图像 + JSON 输入
   python main.py run agent --image photo.jpg -i config.json
   ```

2. **多个 --image**:
   ```bash
   # 所有图像都会传递给 Agent
   python main.py run agent \
     --image img1.jpg \
     --image img2.jpg \
     --image img3.jpg
   ```

3. **完整组合**:
   ```bash
   python main.py run agent \
     --image img1.jpg \
     --image img2.jpg \
     -i input.json \
     --format yaml \
     -o results.yaml
   ```

## 5. 数据流程

### 5.1 Agent 执行流程

```
1. 解析 CLI 参数
   ↓
2. 加载配置文件
   ↓
3. 验证 Agent 是否启用
   ↓
4. 加载 Agent 配置和 Prompts
   ↓
5. **【验证阶段】Prompt 模板验证**
   - 如果 config.json 定义了 inputs 字段：
     * 检查 system_prompt 中是否使用 {{field}} 引用了所有输入字段
     * 检查 user_prompt 中是否使用 {{field}} 引用了所有输入字段
     * 未引用的字段发出警告
   ↓
6. 准备输入数据
   - 文本直接使用（需要是 JSON 格式）
   - 文本文件读取内容（需要是 JSON 格式）
   - JSON 文件解析为字典
   - 图像处理（--image 参数）
     * 本地文件：读取并编码为 base64
     * URL：验证并传递 URL
     * 支持多图像输入
   ↓
7. **【验证阶段】输入数据验证**
   - 如果 config.json 定义了 inputs 字段：
     * 验证输入是否为有效 JSON（如果是文本或文本文件）
     * 检查解析后的数据是否包含所有必需的 inputs 字段
     * 如果缺少字段：
       - 显示缺失的字段列表
       - 询问用户是否继续（y/n）
       - 用户选择 n 则退出
   ↓
8. 渲染 Prompts（替换模板变量）
   - 使用 {{field}} 语法替换为实际值
   - 处理多图像占位符
   ↓
9. 调用模型 API
   ↓
10. 解析响应
   ↓
11. **【验证阶段】输出数据验证**
   - 如果 config.json 定义了 outputs 字段：
     * 解析 Agent 返回的 JSON 结果
     * 检查是否包含所有指定的 outputs 字段
     * 如果缺少字段：
       - 记录警告日志
       - 在输出中标记缺失字段
       - 继续执行（不中断）
   ↓
12. 根据 --format 参数格式化输出
   - json: 结构化 JSON 输出
   - txt: 人类可读的文本格式
   - yaml: YAML 配置格式
   ↓
13. 保存结果到文件（如果指定 -o）
   ↓
14. 输出执行结果到终端
```

### 5.2 VLM 图像处理流程

对于 VLM（Vision Language Model），通过 `--image` 参数支持多图像输入：

#### 5.2.1 图像输入方式

1. **本地文件路径**
   ```bash
   --image ./images/photo.jpg
   --image /absolute/path/to/image.png
   ```
   - 验证文件是否存在
   - 检查文件格式（jpg, png, webp, gif）
   - 读取图像文件
   - 根据配置调整大小（`resize_image_for_api`）
   - 编码为 base64

2. **URL**
   ```bash
   --image https://example.com/photo.jpg
   --image http://cdn.example.com/image.png
   ```
   - 验证 URL 格式
   - 可选：下载并验证图像
   - 直接传递 URL 或转换为 base64

3. **多图像输入**
   ```bash
   --image img1.jpg --image img2.jpg --image https://example.com/img3.jpg
   ```
   - 按顺序处理每个图像
   - 构建图像列表传递给 API
   - 在 prompt 中可以通过 `{images}` 或 `{image_0}`, `{image_1}` 引用

#### 5.2.2 图像处理配置

在模型配置中：
```yaml
models:
  qwen_vl:
    type: "vlm"
    resize_image_for_api: true      # 是否压缩图片
    max_image_size: 2048             # 最大尺寸（像素）
    image_quality: 85                # JPEG 压缩质量
    supported_formats: ["jpg", "png", "webp", "gif"]
```

#### 5.2.3 OpenAI API 格式

多图像会按照 OpenAI Vision API 格式构建：
```python
messages = [
    {
        "role": "system",
        "content": system_prompt
    },
    {
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img1}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img2}"}},
            {"type": "image_url", "image_url": {"url": "https://example.com/img3.jpg"}}
        ]
    }
]
```

## 6. 参数验证机制

### 6.1 验证概述

为确保 Agent 正确执行，系统提供三层验证机制：
1. **Prompt 模板验证**：确保 prompts 正确引用所有输入字段
2. **输入数据验证**：确保输入数据包含所有必需字段
3. **输出数据验证**：确保输出数据包含所有期望字段

### 6.2 Prompt 模板验证

**验证时机**：加载 Agent 配置后，执行前

**验证逻辑**：
```python
def validate_prompt_templates(agent_config, system_prompt, user_prompt):
    """验证 prompt 模板是否引用了所有输入字段"""
    if "inputs" not in agent_config:
        return True  # 没有定义 inputs，跳过验证

    required_fields = set(agent_config["inputs"])

    # 从 prompts 中提取所有 {{field}} 引用
    referenced_fields = set()
    for prompt in [system_prompt, user_prompt]:
        if prompt:
            matches = re.findall(r'\{\{(\w+)\}\}', prompt)
            referenced_fields.update(matches)

    # 检查是否所有输入字段都被引用
    missing_refs = required_fields - referenced_fields

    if missing_refs:
        logger.warning(f"Prompt 模板未引用以下输入字段: {missing_refs}")
        return False

    return True
```

**示例**：
```json
// config.json
{
  "inputs": ["text", "context", "language"]
}
```

```
// user.txt - ❌ 错误：未引用 language
请分析以下文本：
{{text}}

上下文：{{context}}
```

**警告输出**：
```
⚠️  Warning: Prompt 模板未引用以下输入字段: ['language']
建议在 system.txt 或 user.txt 中添加 {{language}} 引用
```

### 6.3 输入数据验证

**验证时机**：准备输入数据后，渲染 prompts 前

**验证逻辑**：
```python
def validate_input_data(agent_config, input_data):
    """验证输入数据是否包含所有必需字段"""
    if "inputs" not in agent_config:
        return True  # 没有定义 inputs，跳过验证

    required_fields = set(agent_config["inputs"])
    provided_fields = set(input_data.keys())

    missing_fields = required_fields - provided_fields

    if missing_fields:
        print(f"❌ 错误: 输入数据缺少以下必需字段: {list(missing_fields)}")
        print(f"必需字段: {list(required_fields)}")
        print(f"已提供字段: {list(provided_fields)}")

        # 询问用户是否继续
        response = input("\n是否继续执行? (y/n): ")
        if response.lower() != 'y':
            return False

    return True
```

**场景 1：文本输入**
```bash
# config.json 定义 inputs: ["text", "context"]
python main.py run text_analyzer -i "这是一段文本"
```

**错误输出**：
```
❌ 错误: 输入格式不正确
期望 JSON 格式的输入，例如: {"text": "...", "context": "..."}
实际收到: "这是一段文本"

请使用以下格式之一：
1. JSON 字符串: -i '{"text": "...", "context": "..."}'
2. JSON 文件: -i input.json
```

**场景 2：缺少字段**
```bash
# input.json 内容: {"text": "这是一段文本"}
python main.py run text_analyzer -i input.json
```

**交互式输出**：
```
❌ 错误: 输入数据缺少以下必需字段: ['context']
必需字段: ['text', 'context']
已提供字段: ['text']

是否继续执行? (y/n): _
```

**场景 3：正确输入**
```bash
# input.json 内容: {"text": "这是一段文本", "context": "用户评论"}
python main.py run text_analyzer -i input.json
```

**成功输出**：
```
✅ 输入验证通过
执行 Agent: text_analyzer
```

### 6.4 输出数据验证

**验证时机**：解析 API 响应后，格式化输出前

**验证逻辑**：
```python
def validate_output_data(agent_config, output_data):
    """验证输出数据是否包含所有期望字段"""
    if "outputs" not in agent_config:
        return True, []  # 没有定义 outputs，跳过验证

    required_fields = set(agent_config["outputs"])

    # 尝试解析 JSON 输出
    try:
        if isinstance(output_data, str):
            parsed_output = json.loads(output_data)
        else:
            parsed_output = output_data
    except json.JSONDecodeError:
        logger.warning("Agent 输出不是有效的 JSON 格式")
        return False, list(required_fields)

    provided_fields = set(parsed_output.keys())
    missing_fields = required_fields - provided_fields

    if missing_fields:
        logger.warning(f"Agent 输出缺少以下字段: {list(missing_fields)}")
        # 不中断执行，继续处理

    return True, list(missing_fields)
```

**场景 1：输出完整**
```json
// config.json
{
  "outputs": ["result", "confidence", "reasoning"]
}

// Agent 返回
{
  "result": "正面情感",
  "confidence": 0.95,
  "reasoning": "文本包含积极词汇"
}
```

**成功输出**：
```
✅ 输出验证通过
```

**场景 2：输出不完整**
```json
// Agent 返回
{
  "result": "正面情感",
  "confidence": 0.95
  // 缺少 "reasoning" 字段
}
```

**警告输出**：
```
⚠️  Warning: Agent 输出缺少以下字段: ['reasoning']
期望字段: ['result', 'confidence', 'reasoning']
实际字段: ['result', 'confidence']

继续执行并保存部分结果...
```

**JSON 输出（标记缺失字段）**：
```json
{
  "agent": "text_analyzer",
  "timestamp": "2025-12-05T19:30:00",
  "status": "partial_success",
  "validation": {
    "missing_output_fields": ["reasoning"]
  },
  "outputs": {
    "result": "正面情感",
    "confidence": 0.95,
    "reasoning": null
  }
}
```

### 6.5 验证配置

可以在 config.yaml 中配置验证行为：

```yaml
# 验证配置
validation:
  # Prompt 模板验证
  prompt_template_validation: true
  prompt_template_strict: false  # true: 验证失败则退出

  # 输入数据验证
  input_validation: true
  input_strict: false  # false: 缺少字段时询问用户

  # 输出数据验证
  output_validation: true
  output_strict: false  # false: 缺少字段时警告但继续
  output_fill_missing: true  # true: 缺失字段填充 null
```

### 6.6 CLI 验证选项

```bash
# 跳过所有验证（不推荐）
python main.py run agent_name -i input.json --no-validation

# 严格模式：任何验证失败都退出
python main.py run agent_name -i input.json --strict

# 仅跳过输入验证
python main.py run agent_name -i input.json --skip-input-validation
```

## 7. 错误处理

### 7.1 配置错误
- 配置文件缺失或格式错误
- Agent 配置不完整
- 模型配置缺失
- Prompt 文件缺失

### 7.2 验证错误
- Prompt 模板未引用必需字段
- 输入数据格式错误（非 JSON）
- 输入数据缺少必需字段
- 输出数据缺少期望字段

### 7.3 运行时错误
- API 调用失败（支持重试）
- 网络超时
- 输入数据格式错误
- Agent 未启用

### 6.3 错误输出格式

```json
{
  "agent": "text_analyzer",
  "timestamp": "2025-12-05T19:30:00",
  "status": "error",
  "error": {
    "type": "APIError",
    "message": "Connection timeout",
    "details": "..."
  }
}
```

## 7. 扩展性设计

### 7.1 添加新 Agent

1. 在 `config/agents/` 下创建新目录
2. 编写 `config.json`、`system.txt`、`user.txt`
3. 在 `config.yaml` 中注册 Agent
4. 执行 `python main.py list` 验证

### 7.2 添加新模型

1. 在 `config.yaml` 的 `models` 部分添加配置
2. 确保 API 兼容 OpenAI 格式
3. 指定模型类型（llm/vlm）

### 7.3 自定义输入处理

支持扩展输入处理器：
- 文本处理器
- 文件处理器
- JSON 处理器
- 图像处理器（VLM）

## 8. 技术栈

### 8.1 核心依赖

- **Python**: 3.8+
- **openai**: OpenAI Python SDK（支持兼容接口）
- **pydantic**: 数据验证和配置管理
- **click**: CLI 框架
- **PyYAML**: YAML 配置解析
- **Pillow**: 图像处理（VLM）
- **loguru**: 日志管理

### 8.2 可选依赖

- **requests**: HTTP 客户端
- **tenacity**: 重试机制

## 9. 开发计划

### Phase 1: 核心功能
- [ ] 配置文件加载和验证
- [ ] Agent 基类和工厂
- [ ] 模型客户端（LLM）
- [ ] CLI 基础命令（list, info）
- [ ] JSON 输出格式化器

### Phase 2: 执行引擎
- [ ] Agent 执行流程
- [ ] Prompt 渲染引擎
- [ ] 输入处理器（文本、文件、JSON）
- [ ] 输出管理器
- [ ] CLI run 命令基础功能

### Phase 3: VLM 和图像支持
- [ ] 图像处理器（ImageProcessor）
- [ ] 支持本地图像文件
- [ ] 支持图像 URL
- [ ] 多图像输入支持
- [ ] 图像压缩和 Base64 编码
- [ ] VLM 客户端适配

### Phase 4: 多格式输出
- [ ] TXT 格式化器
- [ ] YAML 格式化器
- [ ] 格式化器工厂和注册机制
- [ ] --format 参数实现
- [ ] 自动文件扩展名处理

### Phase 5: 增强功能
- [ ] 错误处理和重试机制
- [ ] 日志系统
- [ ] 图像缓存（可选）
- [ ] 性能优化
- [ ] 单元测试和集成测试

### Phase 6: 文档和示例
- [ ] API 文档
- [ ] 使用示例和教程
- [ ] 最佳实践指南
- [ ] 示例 Agent 配置

## 10. 使用示例

### 10.1 文本分析

```bash
# 直接输入文本 - JSON 格式输出
python main.py run text_analyzer -i "请分析这段文本的情感"

# 从文件输入 - TXT 格式输出
echo "请分析这段文本的情感" > input.txt
python main.py run text_analyzer -i input.txt --format txt

# JSON 输入 - YAML 格式输出
cat > input.json << EOF
{
  "text": "今天天气真好，心情也很愉快！",
  "context": "用户评论"
}
EOF
python main.py run text_analyzer -i input.json --format yaml -o result.yaml
```

### 10.2 图像分析（VLM）

```bash
# 单张图像分析
python main.py run image_captioner --image ./images/sample.jpg

# 多张图像分析
python main.py run image_captioner \
  --image ./images/photo1.jpg \
  --image ./images/photo2.jpg \
  --image ./images/photo3.jpg \
  --format txt

# 图像 + 文本输入（使用 JSON）
cat > input.json << EOF
{
  "question": "请比较这些图片中的差异",
  "detail_level": "high"
}
EOF
python main.py run image_captioner \
  --image img1.jpg \
  --image img2.jpg \
  -i input.json \
  -o comparison.json

# 混合 URL 和本地文件
python main.py run visual_qa \
  --image https://example.com/remote.jpg \
  --image ./local.jpg \
  -i "这两张图片有什么共同点？" \
  --format txt
```

### 10.3 批量处理

```bash
# 批量处理文本文件（YAML 输出便于分析）
for file in ./inputs/*.txt; do
  python main.py run text_analyzer \
    -i "$file" \
    --format yaml \
    -o "./output/$(basename $file .txt).yaml"
done

# 批量处理图像（JSON 输出）
for img in ./images/*.jpg; do
  python main.py run image_captioner \
    --image "$img" \
    --format json \
    -o "./output/$(basename $img .jpg).json"
done

# 批量转换格式（JSON 转 YAML）
for json_file in output/*.json; do
  python main.py run reformatter \
    -i "$json_file" \
    --format yaml \
    -o "${json_file%.json}.yaml"
done
```

### 10.4 高级用例

```bash
# 多模态分析：图像 + 结构化输入
cat > analysis_task.json << EOF
{
  "task": "产品质量检测",
  "criteria": ["完整性", "清晰度", "合规性"],
  "threshold": 0.8
}
EOF
python main.py run quality_checker \
  --image product1.jpg \
  --image product2.jpg \
  --image product3.jpg \
  -i analysis_task.json \
  --format yaml \
  -o quality_report.yaml

# 生成不同格式的报告
python main.py run content_analyzer -i content.json --format json -o report.json
python main.py run content_analyzer -i content.json --format txt -o report.txt
python main.py run content_analyzer -i content.json --format yaml -o report.yaml
```

## 11. 安全性考虑

- API Key 通过环境变量或安全配置文件管理
- 输入验证防止注入攻击
- 敏感信息不记录到日志
- 文件路径验证防止路径遍历

## 12. 性能优化

- 配置文件缓存
- Prompt 模板预编译
- 异步 API 调用（可选）
- 批量处理支持

---

**文档版本**: v1.0
**最后更新**: 2025-12-05
**维护者**: Simple AI Agents Team
