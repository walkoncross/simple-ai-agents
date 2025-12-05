"""
Agent 工厂

创建和管理 Agent 实例
"""
from typing import Dict, Optional
from loguru import logger

from ..utils.config_loader import ConfigLoader, Config
from .agent import Agent


class AgentFactory:
    """Agent 工厂"""

    def __init__(self, config: Config):
        """
        Args:
            config: 主配置对象
        """
        self.config = config
        self._agent_cache: Dict[str, Agent] = {}

    def create_agent(self, agent_name: str, config_loader: ConfigLoader) -> Agent:
        """
        创建 Agent 实例

        Args:
            agent_name: Agent 名称
            config_loader: 配置加载器

        Returns:
            Agent 实例

        Raises:
            ValueError: Agent 不存在或未启用
        """
        # 检查缓存
        if agent_name in self._agent_cache:
            logger.debug(f"从缓存获取 Agent: {agent_name}")
            return self._agent_cache[agent_name]

        # 检查 Agent 是否存在
        if agent_name not in self.config.agents:
            available = ', '.join(self.config.agents.keys())
            raise ValueError(
                f"Agent '{agent_name}' 不存在。"
                f"可用的 Agent: {available}"
            )

        agent_reg = self.config.agents[agent_name]

        # 检查是否启用
        if not agent_reg.enabled:
            raise ValueError(f"Agent '{agent_name}' 未启用")

        # 加载 Agent 配置和 prompts
        logger.info(f"创建 Agent: {agent_name}")
        agent_config, prompts = config_loader.load_agent_config(agent_name)

        # 获取模型配置
        model_name = agent_reg.model_provider
        if model_name not in self.config.models:
            raise ValueError(f"模型 '{model_name}' 不存在")

        model_config = self.config.models[model_name]

        # 创建 Agent 实例
        agent = Agent(
            name=agent_name,
            agent_config=agent_config,
            prompts=prompts,
            model_config=model_config,
            validation_config=self.config.validation,
            api_config=self.config.api
        )

        # 缓存
        self._agent_cache[agent_name] = agent

        return agent

    def list_agents(self) -> Dict[str, dict]:
        """
        列出所有 Agent

        Returns:
            Agent 信息字典
        """
        agents_info = {}

        for name, reg in self.config.agents.items():
            agents_info[name] = {
                'enabled': reg.enabled,
                'model_provider': reg.model_provider,
                'description': reg.description,
                'config': reg.config
            }

        return agents_info

    def get_agent_info(self, agent_name: str) -> Optional[dict]:
        """
        获取指定 Agent 的详细信息

        Args:
            agent_name: Agent 名称

        Returns:
            Agent 信息字典，如果不存在则返回 None
        """
        if agent_name not in self.config.agents:
            return None

        reg = self.config.agents[agent_name]

        info = {
            'name': agent_name,
            'enabled': reg.enabled,
            'model_provider': reg.model_provider,
            'description': reg.description,
            'config': reg.config,
        }

        # 如果 Agent 已加载，添加详细配置
        if agent_name in self._agent_cache:
            agent = self._agent_cache[agent_name]
            info['type'] = agent.agent_config.type
            info['inputs'] = agent.agent_config.inputs
            info['outputs'] = agent.agent_config.outputs

        return info

    def clear_cache(self):
        """清除 Agent 缓存"""
        self._agent_cache.clear()
        logger.info("已清除 Agent 缓存")
