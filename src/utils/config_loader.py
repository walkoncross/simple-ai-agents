"""
配置加载器

加载和验证 config.yaml 和 agent 配置文件
支持环境变量替换：${ENV_VAR} 或 ${ENV_VAR:-default_value}
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field, validator
from loguru import logger


def expand_env_vars(value: Any, strict: bool = True) -> Any:
    """
    递归替换配置中的环境变量

    支持的格式：
    - ${ENV_VAR}: 使用环境变量，如果不存在则报错（strict=True）或保留原样（strict=False）
    - ${ENV_VAR:-default}: 使用环境变量，如果不存在则使用默认值

    Args:
        value: 要处理的值
        strict: 严格模式。True=缺少环境变量时报错，False=保留原样等待后续验证

    Examples:
        api_key: ${OPENAI_API_KEY}
        api_base: ${API_BASE:-http://localhost:8000}
    """
    if isinstance(value, str):
        # 匹配 ${VAR} 或 ${VAR:-default}
        pattern = r'\$\{([^}:]+)(?::(-)?([^}]*))?\}'

        def replace_env(match):
            var_name = match.group(1)
            has_default = match.group(2) is not None
            default_value = match.group(3) if has_default else None

            env_value = os.environ.get(var_name)

            if env_value is not None:
                return env_value
            elif has_default:
                return default_value or ""
            else:
                if strict:
                    raise ValueError(
                        f"环境变量 '{var_name}' 未设置且没有提供默认值。"
                        f"请设置环境变量或使用 ${{VAR:-default}} 语法提供默认值。"
                    )
                else:
                    # 非严格模式，保留原样
                    return match.group(0)

        return re.sub(pattern, replace_env, value)

    elif isinstance(value, dict):
        return {k: expand_env_vars(v, strict) for k, v in value.items()}

    elif isinstance(value, list):
        return [expand_env_vars(item, strict) for item in value]

    else:
        return value


class ModelConfig(BaseModel):
    """模型配置"""
    type: str = Field(..., description="模型类型: llm 或 vlm")
    api_base: str = Field(..., description="API 基础 URL")
    api_key: str = Field(..., description="API Key")
    model: str = Field(..., description="模型名称")
    max_tokens: int = Field(default=4096, description="最大token数")
    temperature: float = Field(default=0.7, description="温度参数")
    enabled: bool = Field(default=True, description="是否启用")

    # VLM 特有配置
    resize_image_for_api: bool = Field(default=False, description="是否压缩图片")
    max_image_size: int = Field(default=2048, description="最大图片尺寸")
    image_quality: int = Field(default=85, description="JPEG 压缩质量")

    @validator('type')
    def validate_type(cls, v):
        if v not in ['llm', 'vlm']:
            raise ValueError(f"模型类型必须是 'llm' 或 'vlm', 但得到: {v}")
        return v


class AgentRegistration(BaseModel):
    """Agent 注册信息"""
    model_provider: str = Field(..., description="使用的模型名称")
    config: str = Field(..., description="Agent 配置文件路径")
    enabled: bool = Field(default=True, description="是否启用")
    description: str = Field(default="", description="Agent 描述")


class AgentConfig(BaseModel):
    """Agent 配置（来自 config/agents/*/config.json）"""
    type: str = Field(..., description="Agent 类型: llm 或 vlm")
    inputs: list[str] = Field(default_factory=list, description="输入参数列表")
    outputs: list[str] = Field(default_factory=list, description="输出字段列表")
    system_prompt: str = Field(..., description="system prompt 文件路径")
    user_prompt: Optional[str] = Field(None, description="user prompt 文件路径")

    @validator('type')
    def validate_type(cls, v):
        if v not in ['llm', 'vlm']:
            raise ValueError(f"Agent 类型必须是 'llm' 或 'vlm', 但得到: {v}")
        return v


class ValidationConfig(BaseModel):
    """验证配置"""
    prompt_template_validation: bool = True
    prompt_template_strict: bool = False
    input_validation: bool = True
    input_strict: bool = False
    output_validation: bool = True
    output_strict: bool = False
    output_fill_missing: bool = True


class APIConfig(BaseModel):
    """API 配置"""
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout: int = 60


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    file: str = "./logs/agent.log"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"


class Config(BaseModel):
    """主配置"""
    output_dir: str = "./output"
    temp_dir: str = "./temp"
    cache_dir: str = "./cache"

    models: Dict[str, ModelConfig]
    agents: Dict[str, AgentRegistration]

    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config: Optional[Config] = None
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.agent_prompts: Dict[str, Dict[str, str]] = {}

    def load(self) -> Config:
        """加载主配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)

            # 扩展环境变量（非严格模式，保留未设置的环境变量）
            config_dict = expand_env_vars(config_dict, strict=False)

            # 过滤掉 enabled=false 的 models
            original_model_count = len(config_dict.get('models', {}))
            if 'models' in config_dict:
                config_dict['models'] = {
                    name: model_config
                    for name, model_config in config_dict['models'].items()
                    if model_config.get('enabled', True)  # 默认为 True
                }
                disabled_models = original_model_count - len(config_dict['models'])
                if disabled_models > 0:
                    logger.debug(f"跳过 {disabled_models} 个禁用的模型")

            # 过滤掉 enabled=false 的 agents
            original_agent_count = len(config_dict.get('agents', {}))
            if 'agents' in config_dict:
                config_dict['agents'] = {
                    name: agent_config
                    for name, agent_config in config_dict['agents'].items()
                    if agent_config.get('enabled', True)  # 默认为 True
                }
                disabled_agents = original_agent_count - len(config_dict['agents'])
                if disabled_agents > 0:
                    logger.debug(f"跳过 {disabled_agents} 个禁用的 Agent")

            self.config = Config(**config_dict)
            logger.info(f"成功加载配置文件: {self.config_path}")
            logger.debug(f"已加载 {len(self.config.models)} 个模型，{len(self.config.agents)} 个 Agent")

            # 创建必要的目录
            self._create_directories()

            return self.config

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise

    def _create_directories(self):
        """创建必要的目录"""
        if self.config:
            for dir_path in [self.config.output_dir, self.config.temp_dir,
                           self.config.cache_dir, Path(self.config.logging.file).parent]:
                Path(dir_path).mkdir(parents=True, exist_ok=True)

    def load_agent_config(self, agent_name: str) -> tuple[AgentConfig, Dict[str, str]]:
        """
        加载指定 agent 的配置和 prompts

        Returns:
            (AgentConfig, prompts_dict)
        """
        if not self.config:
            raise RuntimeError("请先调用 load() 加载主配置")

        if agent_name not in self.config.agents:
            raise ValueError(f"Agent '{agent_name}' 不存在或未启用")

        agent_reg = self.config.agents[agent_name]

        # 加载 agent 配置文件
        config_path = Path(agent_reg.config)
        if not config_path.exists():
            raise FileNotFoundError(f"Agent 配置文件不存在: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                agent_config_dict = json.load(f)

            agent_config = AgentConfig(**agent_config_dict)

            # 加载 prompts
            agent_dir = config_path.parent
            prompts = {}

            # 加载 system prompt
            system_prompt_path = agent_dir / agent_config.system_prompt
            if not system_prompt_path.exists():
                raise FileNotFoundError(f"System prompt 文件不存在: {system_prompt_path}")

            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                prompts['system'] = f.read()

            # 加载 user prompt (可选)
            if agent_config.user_prompt:
                user_prompt_path = agent_dir / agent_config.user_prompt
                if user_prompt_path.exists():
                    with open(user_prompt_path, 'r', encoding='utf-8') as f:
                        prompts['user'] = f.read()
                else:
                    logger.warning(f"User prompt 文件不存在: {user_prompt_path}")
                    prompts['user'] = ""
            else:
                prompts['user'] = ""

            # 缓存
            self.agent_configs[agent_name] = agent_config
            self.agent_prompts[agent_name] = prompts

            logger.info(f"成功加载 Agent '{agent_name}' 的配置")

            return agent_config, prompts

        except Exception as e:
            logger.error(f"加载 Agent '{agent_name}' 配置失败: {e}")
            raise

    def get_model_config(self, model_name: str) -> ModelConfig:
        """获取模型配置"""
        if not self.config:
            raise RuntimeError("请先调用 load() 加载主配置")

        if model_name not in self.config.models:
            raise ValueError(f"模型 '{model_name}' 不存在或未启用")

        # 获取模型配置（已过滤掉未启用的模型）
        model_config = self.config.models[model_name]
        model_dict = model_config.dict()

        # 严格验证环境变量，确保所有必需的环境变量都已设置
        model_dict = expand_env_vars(model_dict, strict=True)

        return ModelConfig(**model_dict)

    def list_models(self) -> Dict[str, ModelConfig]:
        """列出所有模型"""
        if not self.config:
            raise RuntimeError("请先调用 load() 加载主配置")

        return self.config.models

    def list_agents(self) -> Dict[str, AgentRegistration]:
        """列出所有 agents"""
        if not self.config:
            raise RuntimeError("请先调用 load() 加载主配置")

        return self.config.agents
