# Simple AI Agents

一个轻量级的 AI Agent 工厂框架，支持 LLM 和 VLM（Vision Language Model）。

## 特性

- 🤖 基于 system prompt 和 user prompt 构建简单 AI Agent
- 🔌 支持所有兼容 OpenAI API 的模型接口
- 📝 多格式输出：JSON, TXT, YAML
- 🖼️ VLM 多图像输入支持
- ✅ 三层参数验证机制
- 🛠️ 命令行界面（CLI）

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入实际的 API Key 等信息
```

## 配置

### 配置文件优先级

CLI 会按以下优先级查找配置文件：

1. `--config` 参数指定的文件
2. `config.local.yaml`（如果存在）
3. `config.yaml`（默认）

**推荐做法**：
- `config.yaml` - 提交到 Git，包含默认配置和环境变量占位符
- `config.local.yaml` - 不提交，本地开发时的实际配置

```bash
# 创建本地配置（不会被 Git 追踪）
cp config.yaml config.local.yaml
# 编辑 config.local.yaml，填入实际的 API Key 等信息
```

### 环境变量支持

配置文件支持环境变量替换，有两种语法：

1. `${ENV_VAR}`: 使用环境变量，如果不存在则报错
2. `${ENV_VAR:-default}`: 使用环境变量，如果不存在则使用默认值

示例：
```yaml
models:
  qwen:
    type: "llm"
    api_base: "${QWEN_API_BASE:-http://localhost:8001/v1}"
    api_key: "${QWEN_API_KEY}"  # 必须设置此环境变量
```

### 设置环境变量

方法 1：使用 .env 文件（推荐）
```bash
cp .env.example .env
# 编辑 .env 文件
export $(cat .env | xargs)  # 加载环境变量
```

方法 2：直接设置
```bash
export QWEN_API_KEY="your-api-key"
export QWEN_API_BASE="http://localhost:8001/v1"
```

方法 3：运行时设置
```bash
QWEN_API_KEY="your-key" python src/main.py run agent_name -i input.json
```

## 快速开始

1. 配置模型和 Agent（参见 `config.yaml`）
2. 创建 Agent 配置（参见 `config/agents/`）
3. 运行 Agent

```bash
# 列出所有 agents 和 models
python src/main.py list

# 查看 agent 信息
python src/main.py info agent_name

# 运行 agent
python src/main.py run agent_name -i input.json
```

## 文档

详细设计文档请查看 [docs/design.md](docs/design.md)

## 项目结构

```
simple-ai-agents/
├── config.yaml                 # 主配置文件
├── config/agents/              # Agent 配置目录
├── src/                        # 源代码
│   ├── main.py                # CLI 入口
│   ├── core/                  # 核心模块
│   ├── cli/                   # CLI 命令
│   ├── formatters/            # 输出格式化器
│   └── utils/                 # 工具函数
├── output/                    # 输出目录
└── logs/                      # 日志目录
```

## License

MIT
