from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletion
from app.core.config import settings
from typing import Optional
import tiktoken
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL
        )
        try:
            self.encoding = tiktoken.encoding_for_model(settings.LLM_MODEL)
        except KeyError:
            logger.warning(
                f"Model {settings.LLM_MODEL} not in tiktoken, using cl100k_base"
            )
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """计算 Token 数量，用于成本监控"""
        return len(self.encoding.encode(text))

    async def generate_code(self, messages: list[ChatCompletionMessageParam]) -> str:
        """
        调用LLM生成代码
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=0.1,  # 代码生成需要低温度，保证确定性
                max_tokens=settings.LLM_MAX_TOKENS,
            )

            content = response.choices[0].message.content
            usage = response.usage
            # 空值检查
            if usage:
                logger.info(
                    f"LLM Usage: Input={usage.prompt_tokens}, Output={usage.completion_tokens}"
                )
            else:
                logger.warning("LLM Usage info not available")

            content: Optional[str] = response.choices[0].message.content
            if content is None:
                raise ValueError("LLM returned empty content")

            # 安全提取代码块
            code = self._extract_python_code(content)
            return code

        except Exception as e:
            logger.error(f"LLM API Error: {e}")
            raise Exception(f"LLM 服务调用失败: {str(e)}")

    @staticmethod
    def _extract_python_code(content: str) -> str:
        """
        从LLM响应中提取Python代码块
        纯函数，便于单元测试
        """
        # 处理 ```python 标记
        if "```python" in content:
            parts = content.split("```python")
            if len(parts) >= 2:
                code = parts[1].split("```")[0].strip()
                return code

        # 处理通用 ``` 标记
        if "```" in content:
            parts = content.split("```")
            if len(parts) >= 2:
                code = parts[1].strip()
                return code

        # 没有标记，直接返回 (可能是纯代码)
        return content.strip()


# 单例
llm_service = LLMService()
