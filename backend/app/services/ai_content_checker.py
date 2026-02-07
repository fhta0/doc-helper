"""
AI Content Checker
独立的AI内容检测模块，专注于规则无法处理的检测任务：
- 错别字检测
- 交叉引用检查
- 术语一致性检查
"""
import json
import logging
import re
from typing import Dict, List, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIContentChecker:
    """
    AI内容检测器，专注于内容质量检查
    与规则引擎分离，作为独立的检测阶段
    """

    # 错别字检测的系统提示词
    SPELL_CHECK_SYSTEM_PROMPT = """你是一个专业的中文文档校对助手。你的任务是检测文档中的错别字。

请仔细检查以下内容的错别字，包括但不限于：
1. 同音字错误（如："必须" vs "必需"，"做出" vs "作出"）
2. 形近字错误（如："戊戌" vs "戌"）
3. 常见输入错误
4. 英文拼写错误

对于每个检测到的错别字，请返回：
- position: 错别字在原文中的位置索引（从0开始）
- original: 错误的文本
- correction: 正确的文本
- context: 错别字前后的上下文（帮助定位）
- reason: 修改理由

请只返回确实存在错误的项，不要误报。如果未检测到错别字，返回空数组。

返回格式必须是有效的JSON数组。"""

    # 交叉引用检查的系统提示词
    CROSS_REF_SYSTEM_PROMPT = """你是一个专业的文档格式检查助手。你的任务是检查文档中图表交叉引用的一致性。

请检查以下内容：
1. 文中提到的图表编号是否真实存在
2. 图表编号是否连续（无跳号）
3. 引用格式是否符合规范（如"图1-1"、"表2.1"等）

对于每个检测到的问题，请返回：
- type: 问题类型（missing_ref/invalid_format/discontinuous）
- reference: 文中的引用文本
- location: 引用位置的描述
- suggestion: 修改建议

返回格式必须是有效的JSON数组。"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120
    ):
        """
        初始化AI内容检测器

        Args:
            base_url: API基础URL
            api_key: API密钥
            model: 模型名称
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url if base_url is not None else settings.AI_BASE_URL
        self.api_key = api_key if api_key is not None else settings.AI_API_KEY
        self.model = model if model is not None else settings.AI_MODEL
        self.timeout = timeout

        if not self.api_key:
            logger.warning("AI_API_KEY未配置，AI内容检测将被禁用")

    def is_enabled(self) -> bool:
        """检查AI内容检测是否启用"""
        return bool(self.api_key)

    async def check_all(
        self,
        doc_data: Dict[str, Any],
        enabled_checks: List[str] = None
    ) -> Dict[str, Any]:
        """
        执行所有启用的AI检测

        Args:
            doc_data: 解析后的文档数据
            enabled_checks: 启用的检测类型列表，如 ["spell_check", "cross_ref_check"]

        Returns:
            检测结果字典，包含各种检测的结果
        """
        if not self.is_enabled():
            logger.warning("AI内容检测未启用")
            return {
                "spell_check": {"issues": [], "enabled": False},
                "cross_ref_check": {"issues": [], "enabled": False},
            }

        if enabled_checks is None:
            enabled_checks = ["spell_check", "cross_ref_check"]

        results = {
            "spell_check": {"issues": [], "enabled": "spell_check" in enabled_checks},
            "cross_ref_check": {"issues": [], "enabled": "cross_ref_check" in enabled_checks},
        }

        # 执行错别字检测
        if "spell_check" in enabled_checks:
            try:
                spell_issues = await self._check_spelling(doc_data)
                results["spell_check"]["issues"] = spell_issues
                logger.info(f"错别字检测完成，发现 {len(spell_issues)} 个问题")
            except Exception as e:
                logger.error(f"错别字检测失败: {e}")
                results["spell_check"]["error"] = str(e)

        # 执行交叉引用检测
        if "cross_ref_check" in enabled_checks:
            try:
                ref_issues = await self._check_cross_references(doc_data)
                results["cross_ref_check"]["issues"] = ref_issues
                logger.info(f"交叉引用检测完成，发现 {len(ref_issues)} 个问题")
            except Exception as e:
                logger.error(f"交叉引用检测失败: {e}")
                results["cross_ref_check"]["error"] = str(e)

        return results

    async def _check_spelling(self, doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行错别字检测

        Args:
            doc_data: 解析后的文档数据

        Returns:
            检测到的错别字列表
        """
        paragraphs = doc_data.get("paragraphs", [])

        # 为了提高效率，合并更多段落到每次请求
        # 限制：每次最多处理30个段落，约1500-2000字符
        all_issues = []
        batch_size = 30  # 增加批次大小，减少API调用次数

        for i in range(0, len(paragraphs), batch_size):
            batch = paragraphs[i:i + batch_size]
            batch_text = self._format_paragraphs_for_spell_check(batch, i)

            try:
                prompt = f"""请检查以下文本中的错别字：

{batch_text}

返回JSON格式的检测结果。只返回确实存在错误的项。"""

                response = await self._call_ai_api(
                    prompt,
                    self.SPELL_CHECK_SYSTEM_PROMPT,
                    temperature=0.1,  # 降低温度以获得更准确的结果
                    timeout=45  # 增加超时时间，因为批次变大了
                )

                if not response:
                    logger.warning(f"批次 {i}-{i+batch_size} AI返回空响应")
                    continue

                issues = self._parse_spell_check_response(response, batch, i)
                all_issues.extend(issues)

            except Exception as e:
                logger.error(f"批次 {i}-{i+batch_size} 错别字检测失败: {e}")

        return all_issues

    async def _check_cross_references(self, doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行交叉引用检查

        Args:
            doc_data: 解析后的文档数据

        Returns:
            检测到的引用问题列表
        """
        paragraphs = doc_data.get("paragraphs", [])
        headings = doc_data.get("headings", [])
        tables = doc_data.get("tables", [])
        figures = doc_data.get("figures", [])

        # 提取文中所有图表引用
        all_refs = []
        for para in paragraphs:
            refs = self._extract_references(para["text"])
            for ref in refs:
                all_refs.append({
                    "text": ref,
                    "paragraph_index": para["index"],
                    "location": f"第{para.get('page_number', '?')}页第{para.get('start_line', '?')}行"
                })

        if not all_refs:
            return []  # 没有引用，无需检查

        # 构建实际存在的图表列表
        existing_figures = [f"图{idx + 1}" for idx in range(len(figures))]
        existing_tables = [f"表{idx + 1}" for idx in range(len(tables))]

        # 使用AI进行检查
        try:
            prompt = f"""请检查以下文档中的图表交叉引用是否正确。

文中引用列表：
{json.dumps(all_refs, ensure_ascii=False, indent=2)}

实际存在的图表：
图片：{", ".join(existing_figures) if existing_figures else "无"}
表格：{", ".join(existing_tables) if existing_tables else "无"}

请检查：
1. 引用的图表是否真实存在
2. 图表编号是否连续
3. 引用格式是否规范

返回JSON格式的检测结果。"""

            response = await self._call_ai_api(
                prompt,
                self.CROSS_REF_SYSTEM_PROMPT,
                temperature=0.2
            )

            return self._parse_cross_ref_response(response, all_refs)

        except Exception as e:
            logger.error(f"交叉引用AI检测失败: {e}")
            # 降级到基于规则的检测
            return self._rule_based_cross_ref_check(all_refs, existing_figures, existing_tables)

    def _format_paragraphs_for_spell_check(
        self,
        paragraphs: List[Dict[str, Any]],
        offset: int
    ) -> str:
        """格式化段落用于错别字检测"""
        lines = []
        for para in paragraphs:
            idx = para["index"] - offset
            text = para["text"].strip()
            if text:  # 忽略空段落
                lines.append(f"[{idx}] {text}")
        return "\n\n".join(lines)

    def _extract_references(self, text: str) -> List[str]:
        """从文本中提取图表引用"""
        # 匹配 "图1"、"图1-1"、"表2"、"表2.1" 等格式
        patterns = [
            r'[图表]\d+(?:[-．.]\d+)*',  # 图1、图1-1、表2.1
            r'图\s*\d+(?:[-－．.]\d+)*',  # 图 1、图 1-1
            r'表\s*\d+(?:[-－．.]\d+)*',  # 表 1、表 2-1
            r'Figure\s*\d+(?:[-－．.]\d+)*',  # Figure 1
            r'Table\s*\d+(?:[-－．.]\d+)*',  # Table 1
        ]

        all_refs = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            all_refs.extend(matches)

        # 去重
        return list(set(all_refs))

    def _parse_spell_check_response(
        self,
        response: str,
        paragraphs: List[Dict[str, Any]],
        offset: int
    ) -> List[Dict[str, Any]]:
        """解析错别字检测的AI响应"""
        issues = []

        try:
            # 清理响应
            response = response.strip()

            # 尝试多种方式提取JSON
            json_data = self._extract_json(response)

            if not json_data:
                logger.warning("未能从AI响应中提取JSON数据")
                logger.debug(f"响应内容: {response[:500]}")
                return issues

            if not isinstance(json_data, list):
                logger.warning(f"AI响应不是列表格式: {type(json_data)}")
                return issues

            for item in json_data:
                # 确定位置
                position = item.get("position", 0)
                para_index = item.get("paragraph_index", position // 100 + offset)

                # 找到对应的段落
                target_para = None
                for para in paragraphs:
                    if para["index"] == para_index:
                        target_para = para
                        break

                if not target_para:
                    continue

                issues.append({
                    "rule_id": "AI_SPELL_CHECK",
                    "rule_name": "错别字检测",
                    "category": "content_quality",
                    "checker": "ai",
                    "error_message": f"检测到可能的错别字：{item.get('original', '')}",
                    "suggestion": f"建议修改为：{item.get('correction', '')}",
                    "reason": item.get("reason", ""),
                    "location": {
                        "type": "paragraph",
                        "index": para_index,
                        "page_number": target_para.get("page_number"),
                        "start_line": target_para.get("start_line"),
                        "description": f"第{target_para.get('page_number', '?')}页第{target_para.get('start_line', '?')}行"
                    },
                    "fix_action": "replace_text",
                    "fix_params": {
                        "original": item.get("original", ""),
                        "correction": item.get("correction", ""),
                        "paragraph_index": para_index,
                    }
                })

        except Exception as e:
            logger.error(f"解析错别字检测响应失败: {e}")
            logger.debug(f"响应内容: {response[:500]}")

        return issues

    def _extract_json(self, text: str) -> Any:
        """
        从文本中提取JSON数据，处理各种格式问题
        """
        if not text or not text.strip():
            logger.warning("AI返回空响应")
            return None

        # 尝试1: 直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试2: 移除markdown代码块标记
        text_stripped = text.strip()
        if text_stripped.startswith("```"):
            # 移除 ```json 或 ``` 标记
            text_cleaned = re.sub(r'^```json?\s*', '', text_stripped)
            text_cleaned = text_cleaned.rstrip('```').strip()
            try:
                return json.loads(text_cleaned)
            except json.JSONDecodeError:
                pass

        # 尝试3: 智能提取JSON（使用括号匹配）
        json_str = self._extract_json_array(text)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # 尝试4: 提取JSON对象
        json_str = self._extract_json_object(text)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        logger.warning(f"无法从响应中提取有效JSON: {text[:200]}")
        return None

    def _extract_json_array(self, text: str) -> str:
        """
        从文本中提取JSON数组，正确处理嵌套的括号
        """
        # 找到第一个 [
        start_idx = text.find('[')
        if start_idx == -1:
            return None

        # 从第一个 [ 开始，匹配对应的 ]
        bracket_count = 0
        in_string = False
        escape_next = False

        for i in range(start_idx, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    return text[start_idx:i+1]

        return None

    def _extract_json_object(self, text: str) -> str:
        """
        从文本中提取JSON对象，正确处理嵌套的括号
        """
        # 找到第一个 {
        start_idx = text.find('{')
        if start_idx == -1:
            return None

        # 从第一个 { 开始，匹配对应的 }
        brace_count = 0
        in_string = False
        escape_next = False

        for i in range(start_idx, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start_idx:i+1]

        return None

    def _parse_cross_ref_response(
        self,
        response: str,
        all_refs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """解析交叉引用检测的AI响应"""
        issues = []

        try:
            # 使用统一的JSON提取方法
            json_data = self._extract_json(response)

            if not json_data:
                logger.warning("未能从AI响应中提取JSON数据")
                logger.debug(f"响应内容: {response[:500]}")
                return issues

            if not isinstance(json_data, list):
                logger.warning(f"AI响应不是列表格式: {type(json_data)}")
                return issues

            for item in json_data:
                ref_text = item.get("reference", "")
                # 找到对应的引用位置
                ref_location = None
                for ref in all_refs:
                    if ref_text in ref["text"] or ref["text"] == ref_text:
                        ref_location = ref
                        break

                if not ref_location:
                    continue

                issues.append({
                    "rule_id": "AI_CROSS_REF_CHECK",
                    "rule_name": "交叉引用检查",
                    "category": "content_quality",
                    "checker": "ai",
                    "error_message": self._get_cross_ref_error_message(item),
                    "suggestion": item.get("suggestion", ""),
                    "location": {
                        "type": "paragraph",
                        "index": ref_location["paragraph_index"],
                        "description": ref_location["location"]
                    },
                    "fix_action": "replace_ref",
                    "fix_params": {
                        "original_ref": ref_text,
                        "suggested_ref": item.get("suggested_ref", ref_text),
                        "paragraph_index": ref_location["paragraph_index"],
                    }
                })

        except Exception as e:
            logger.error(f"解析交叉引用检测响应失败: {e}")
            logger.debug(f"响应内容: {response[:500]}")

        return issues

    def _rule_based_cross_ref_check(
        self,
        all_refs: List[Dict[str, Any]],
        existing_figures: List[str],
        existing_tables: List[str]
    ) -> List[Dict[str, Any]]:
        """基于规则的交叉引用检测（降级方案）"""
        issues = []

        existing_all = existing_figures + existing_tables

        for ref in all_refs:
            ref_text = ref["text"]

            # 检查是否存在于实际图表中
            normalized_ref = ref_text.replace("－", "-").replace("．", ".")

            if not any(normalized_ref in item or item in normalized_ref for item in existing_all):
                issues.append({
                    "rule_id": "AI_CROSS_REF_CHECK",
                    "rule_name": "交叉引用检查",
                    "category": "content_quality",
                    "checker": "ai",
                    "error_message": f"引用的图表不存在：{ref_text}",
                    "suggestion": "请检查图表编号是否正确",
                    "location": {
                        "type": "paragraph",
                        "index": ref["paragraph_index"],
                        "description": ref["location"]
                    },
                    "fix_action": None,  # 规则检测无法自动修复
                    "fix_params": {}
                })

        return issues

    def _get_cross_ref_error_message(self, item: Dict[str, Any]) -> str:
        """根据问题类型生成错误消息"""
        issue_type = item.get("type", "")

        messages = {
            "missing_ref": "引用的图表不存在",
            "invalid_format": "引用格式不符合规范",
            "discontinuous": "图表编号不连续"
        }

        return messages.get(issue_type, f"交叉引用问题：{item.get('reference', '')}")

    async def _call_ai_api(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.3,
        timeout: int = 30
    ) -> str:
        """
        调用AI API

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            timeout: 请求超时时间（秒），默认30秒

        Returns:
            AI响应文本，失败时返回空字符串
        """
        if not self.api_key or self.api_key == "your-api-key-here":
            logger.warning("AI API Key未配置，跳过AI调用")
            return ""

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": 3000,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"正在调用AI API: {self.model}, timeout={timeout}s")
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                result = data["choices"][0]["message"]["content"]
                logger.info(f"AI API调用成功，响应长度: {len(result)}")
                return result
        except httpx.TimeoutException:
            logger.error(f"AI API调用超时（{timeout}秒）")
            return ""
        except httpx.HTTPStatusError as e:
            logger.error(f"AI API返回错误: {e.response.status_code} - {e.response.text[:200]}")
            return ""
        except Exception as e:
            logger.error(f"AI API调用失败: {type(e).__name__}: {e}")
            return ""

    def convert_to_standard_issues(
        self,
        ai_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        将AI检测结果转换为标准issue格式

        Args:
            ai_results: AI检测结果字典

        Returns:
            标准issue列表
        """
        all_issues = []

        # 添加错别字检测问题
        spell_check = ai_results.get("spell_check", {})
        if spell_check.get("enabled") and spell_check.get("issues"):
            all_issues.extend(spell_check["issues"])

        # 添加交叉引用问题
        cross_ref = ai_results.get("cross_ref_check", {})
        if cross_ref.get("enabled") and cross_ref.get("issues"):
            all_issues.extend(cross_ref["issues"])

        return all_issues


# ============== 工厂函数 ==============

def create_ai_content_checker() -> AIContentChecker:
    """创建AI内容检测器实例"""
    return AIContentChecker()
