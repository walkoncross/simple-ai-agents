"""
CLI 命令实现

实现 list/stat、info、run 命令
"""
import sys
import json
import yaml
from pathlib import Path
from typing import Optional, List
from loguru import logger

from ..utils.config_loader import ConfigLoader
from ..core.factory import AgentFactory
from ..formatters.factory import FormatterFactory


class Commands:
    """CLI 命令处理器"""

    def __init__(self, config_loader: ConfigLoader):
        """
        Args:
            config_loader: 配置加载器
        """
        self.config_loader = config_loader
        self.config = config_loader.config
        self.factory = AgentFactory(self.config)

    def list_command(self):
        """列举所有 models 和 agents"""
        print("\n=== Models ===")
        for name, model_config in self.config.models.items():
            status = "enabled" if model_config.enabled else "disabled"
            print(f"  - {name} ({model_config.type}) [{status}]")

        print("\n=== Agents ===")
        agents_info = self.factory.list_agents()
        for name, info in agents_info.items():
            status = "enabled" if info['enabled'] else "disabled"
            print(f"  - {name} -> {info['model_provider']} [{status}]")
            if info['description']:
                print(f"      {info['description']}")

        print()

    def stat_command(self):
        """统计 models 和 agents"""
        models = self.config.models
        agents = self.config.agents

        enabled_models = len([m for m in models.values() if m.enabled])
        enabled_agents = len([a for a in agents.values() if a.enabled])

        print("\n=== Statistics ===")
        print(f"Total Models: {len(models)} ({enabled_models} enabled)")
        print(f"Total Agents: {len(agents)} ({enabled_agents} enabled)")
        print()

    def info_command(self, target_name: str):
        """
        打印 model 或 agent 的详细信息

        Args:
            target_name: model 或 agent 名称
        """
        # 先检查是否是 model
        if target_name in self.config.models:
            self._print_model_info(target_name)
            return

        # 再检查是否是 agent
        if target_name in self.config.agents:
            self._print_agent_info(target_name)
            return

        # 都不是
        print(f"❌ 错误: '{target_name}' 不是有效的 model 或 agent 名称")
        print(f"\n可用的 Models: {', '.join(self.config.models.keys())}")
        print(f"可用的 Agents: {', '.join(self.config.agents.keys())}")

    def _print_model_info(self, model_name: str):
        """打印 model 信息"""
        model = self.config.models[model_name]

        print(f"\n=== Model: {model_name} ===")
        print(f"  Enabled: {model.enabled}")
        print(f"  Type: {model.type}")
        print(f"  API Base: {model.api_base}")
        print(f"  Model: {model.model}")
        print(f"  Max Tokens: {model.max_tokens}")
        print(f"  Temperature: {model.temperature}")

        if model.type == 'vlm':
            print(f"  Resize Image: {model.resize_image_for_api}")
            print(f"  Max Image Size: {model.max_image_size}")
            print(f"  Image Quality: {model.image_quality}")

        print()

    def _print_agent_info(self, agent_name: str):
        """打印 agent 信息"""
        reg = self.config.agents[agent_name]

        print(f"\n=== Agent: {agent_name} ===")
        print(f"  Enabled: {reg.enabled}")
        print(f"  Model Provider: {reg.model_provider}")
        print(f"  Description: {reg.description}")
        print(f"  Config: {reg.config}")

        # 加载详细配置（所有已加载的 agent 都是启用的）
        try:
            agent_config, _ = self.config_loader.load_agent_config(agent_name)
            print(f"  Type: {agent_config.type}")
            print(f"  Inputs: {agent_config.inputs}")
            print(f"  Outputs: {agent_config.outputs}")
            print(f"  System Prompt: {agent_config.system_prompt}")
            print(f"  User Prompt: {agent_config.user_prompt or 'N/A'}")
        except Exception as e:
            logger.warning(f"无法加载 Agent 详细配置: {e}")

        print()

    def run_command(
        self,
        agent_name: str,
        inputs: Optional[str] = None,
        images: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        format_type: Optional[str] = None
    ):
        """
        运行 Agent

        Args:
            agent_name: Agent 名称
            inputs: 输入数据（文本、文件路径或 JSON 字符串）
            images: 图像列表
            output_file: 输出文件路径
            format_type: 输出格式（None 表示自动判断）
        """
        try:
            # 创建 Agent
            logger.info(f"创建 Agent: {agent_name}")
            agent = self.factory.create_agent(agent_name, self.config_loader)

            # 准备输入数据
            input_data, input_basename = self._prepare_inputs(inputs)

            # 执行 Agent - 记录开始时间
            import time
            start_time = time.time()

            logger.info(f"执行 Agent: {agent_name}")
            print(f"\n🤖 执行 Agent: {agent_name}")
            print("=" * 50)

            result = agent.run(input_data, images=images)

            # 计算总执行时间（包括 agent 内部时间 + 其他处理时间）
            total_time = time.time() - start_time

            print("=" * 50)

            # 如果未指定格式，自动判断
            if format_type is None:
                format_type = self._infer_format(result)
                logger.info(f"自动判断输出格式: {format_type}")
                print(f"\n💡 自动选择输出格式: {format_type}")

            # 格式化输出
            formatter = FormatterFactory.create(format_type)
            formatted_output = formatter.format(result)

            # 确定输出文件路径
            if output_file is None:
                # 生成默认输出路径
                ext = formatter.get_extension()
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                if input_basename:
                    # 有输入文件：<agent_name>-<timestamp>-<input-basename>.<ext>
                    output_filename = f"{agent_name}-{timestamp}-{input_basename}.{ext}"
                else:
                    # 无输入文件：<agent_name>-<timestamp>.<ext>
                    output_filename = f"{agent_name}-{timestamp}.{ext}"

                # 默认保存到 output_dir
                output_dir = Path(self.config.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / output_filename
            else:
                output_file = Path(output_file)

            # 输出到文件
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_output)

            # 获取 agent 执行时间
            agent_exec_time = result.get('execution_time', total_time)

            # 打印运行信息
            print(f"\n⏱️  运行时间: {total_time:.2f} 秒 (Agent执行: {agent_exec_time:.2f} 秒)")
            print(f"📁 输出文件: {output_path.absolute()}")
            print(f"✅ 执行状态: {result.get('status', 'unknown')}")

            # 记录到日志
            logger.info(f"Agent 执行完成 - 总耗时: {total_time:.2f}秒, Agent耗时: {agent_exec_time:.2f}秒")
            logger.info(f"输出文件保存到: {output_path.absolute()}")

            # 返回状态码
            if result['status'] == 'success':
                return 0
            elif result['status'] == 'partial_success':
                return 1
            else:
                return 2

        except Exception as e:
            logger.error(f"执行失败: {e}")
            print(f"\n❌ 错误: {e}")
            return 3

    def _infer_format(self, result: dict) -> str:
        """
        从 agent 输出结果推断最合适的格式

        Args:
            result: agent 执行结果

        Returns:
            推断的格式类型 (json/yaml/md/txt)
        """
        # 获取输出数据
        outputs = result.get('outputs', {})

        if not outputs:
            return 'txt'

        # 如果是 raw_response（未解析的原始响应）
        if 'raw_response' in outputs and len(outputs) == 1:
            raw = outputs['raw_response']
            # 检查是否有 markdown 特征（#标题、**加粗**、- 列表等）
            if isinstance(raw, str):
                if any(marker in raw for marker in ['##', '**', '- **', '```']):
                    return 'md'
            return 'txt'

        # 统计输出字段数量和类型
        field_count = len(outputs)
        has_long_text = False
        has_structured_data = False

        for value in outputs.values():
            if isinstance(value, str):
                # 检查是否有长文本（多行或超过 200 字符）
                if '\n' in value or len(value) > 200:
                    has_long_text = True
            elif isinstance(value, (list, dict)):
                has_structured_data = True

        # 判断逻辑：
        # 1. 如果有结构化数据（列表、字典），优先使用 json（保持数据结构完整性）
        if has_structured_data:
            return 'json'

        # 2. 如果有长文本且字段较多（>= 3），适合 markdown
        if has_long_text and field_count >= 3:
            return 'md'

        # 3. 如果字段较多（>= 4），适合结构化格式
        if field_count >= 4:
            return 'yaml'

        # 4. 默认使用 txt（简单输出）
        return 'txt'

    def _prepare_inputs(self, inputs: Optional[str]) -> tuple[dict, Optional[str]]:
        """
        准备输入数据

        Args:
            inputs: 输入（文本、文件路径、JSON 字符串或 YAML 字符串）

        Returns:
            (输入数据字典, 输入文件basename)
        """
        if inputs is None:
            return {}, None

        # 检查是否是文件路径
        input_path = Path(inputs)
        if input_path.exists() and input_path.is_file():
            # 获取文件basename（不含扩展名）
            input_basename = input_path.stem

            # 读取文件
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 根据文件扩展名判断格式
            suffix = input_path.suffix.lower()

            # 尝试解析为 YAML
            if suffix in ['.yaml', '.yml']:
                try:
                    data = yaml.safe_load(content)
                    if isinstance(data, dict):
                        return data, input_basename
                    else:
                        return {"input": data}, input_basename
                except yaml.YAMLError:
                    pass

            # 尝试解析为 JSON
            if suffix == '.json':
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        return data, input_basename
                    else:
                        return {"input": data}, input_basename
                except json.JSONDecodeError:
                    pass

            # 如果没有明确扩展名，先尝试 JSON，再尝试 YAML
            if suffix not in ['.json', '.yaml', '.yml']:
                # 先尝试 JSON
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        return data, input_basename
                    else:
                        return {"input": data}, input_basename
                except json.JSONDecodeError:
                    pass

                # 再尝试 YAML
                try:
                    data = yaml.safe_load(content)
                    if isinstance(data, dict):
                        return data, input_basename
                    else:
                        return {"input": data}, input_basename
                except yaml.YAMLError:
                    pass

            # 都失败了，返回文本
            return {"input": content}, input_basename

        # 不是文件，尝试解析字符串
        # 先尝试 JSON
        try:
            data = json.loads(inputs)
            if isinstance(data, dict):
                return data, None
            else:
                return {"input": data}, None
        except json.JSONDecodeError:
            pass

        # 再尝试 YAML
        try:
            data = yaml.safe_load(inputs)
            if isinstance(data, dict):
                return data, None
            else:
                return {"input": data}, None
        except yaml.YAMLError:
            pass

        # 都不是，返回纯文本
        return {"input": inputs}, None
