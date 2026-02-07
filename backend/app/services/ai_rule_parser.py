"""
AI Rule Parser Service
Uses LLM to parse natural language format requirements into structured rule configuration.
"""
import logging
import re
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIRuleParser:
    """使用AI解析自然语言格式要求为结构化规则配置"""

    # System Prompt for AI parsing
    SYSTEM_PROMPT = """你是一个专业的文档格式规范解析专家。你的任务是将用户输入的论文格式要求描述解析为标准的JSON格式。

请严格按照以下JSON结构返回结果，不要添加任何其他文字说明：

{
  "page": {
    "margins": {
      "top_cm": 2.5,
      "bottom_cm": 2.5,
      "left_cm": 3.0,
      "right_cm": 2.5
    },
    "paper_name": "A4",
    "gutter_cm": 0,
    "header_cm": 1.5,
    "footer_cm": 2.0
  },
  "headings": [
    {
      "level": 1,
      "font": "SimHei",
      "size_pt": 16,
      "bold": true,
      "alignment": "center"
    },
    {
      "level": 2,
      "font": "SimHei",
      "size_pt": 14,
      "bold": true,
      "alignment": "left"
    },
    {
      "level": 3,
      "font": "SimHei",
      "size_pt": 13,
      "bold": true,
      "alignment": "left"
    },
    {
      "level": 4,
      "font": "SimHei",
      "size_pt": 12,
      "bold": true,
      "alignment": "left"
    }
  ],
  "body": {
    "font": "SimSun",
    "size_pt": 12,
    "line_spacing_pt": 25,
    "first_line_indent_chars": 2,
    "align_to_grid": true
  },
  "page_number": {
    "font": "Times New Roman",
    "size_pt": 10.5,
    "alignment": "center",
    "number_format": "arabic",
    "toc_number_format": "roman"
  },
  "table": {
    "border_width_pt": 2.25,
    "header_font": "SimHei",
    "header_size_pt": 12,
    "body_font": "FangSong",
    "body_size_pt": 12,
    "line_spacing_pt": 23
  },
  "figure_caption": {
    "format": "{level}-{index}",
    "position": "below"
  },
  "table_caption": {
    "format": "{level}-{index}",
    "position": "above"
  }
}

【字段说明与转换规则】

**页面设置 (page):**
- margins.top_cm/bottom_cm/left_cm/right_cm: 页边距，单位cm
- paper_name: 纸张类型，如"A4"
- gutter_cm: 装订线距离，单位cm
- header_cm: 页眉距离，单位cm
- footer_cm: 页脚距离，单位cm

**标题样式 (headings):**
- level: 标题级别，1-4级
- font: 字体名称（见下方映射表）
- size_pt: 字号，单位pt
- bold: 是否加粗，true/false
- alignment: 对齐方式，可选值：center/left/right/justify

**正文格式 (body):**
- font: 正文字体名称
- size_pt: 正文字号
- line_spacing_pt: 行距，单位pt（固定值）
- first_line_indent_chars: 首行缩进字符数
- align_to_grid: 是否对齐网格，true/false

**页码设置 (page_number):**
- font: 页码字体
- size_pt: 页码字号
- alignment: 页码位置，left/center/right
- number_format: 正文页码格式，"arabic"(阿拉伯数字1,2,3)或"roman"(罗马数字Ⅰ,Ⅱ,Ⅲ)
- toc_number_format: 目录页码格式，"arabic"或"roman"

**表格样式 (table):**
- border_width_pt: 外框线宽度，单位pt（1 1/2磅 = 2.25pt）
- header_font: 表头字体
- header_size_pt: 表头字号
- body_font: 表内正文字体
- body_size_pt: 表内正文字号
- line_spacing_pt: 表内行距

**图表标题 (figure_caption/table_caption):**
- format: 编号格式模板，"{level}-{index}"表示"二级标题-序号"
- position: 位置，above(上方)/below(下方)

【字体名称映射】
- 宋体 → SimSun
- 仿宋 或 仿宋_GB2312 → FangSong
- 楷体 或 楷体_GB2312 → KaiTi
- 黑体 → SimHei
- Times New Roman → Times New Roman

【字号转换表】
- 初号=42pt, 小初=36pt
- 一号=26pt, 小一=24pt
- 二号=22pt, 小二=18pt
- 三号=16pt, 小三=15pt
- 四号=14pt, 小四=12pt
- 五号=10.5pt, 小五=9pt

【行距转换】
- 单倍行距 ≈ 17pt
- 1.5倍行距 ≈ 25pt
- 20磅 = 20pt
- 25磅 = 25pt
- 30磅 = 30pt

【页边距默认值】
- 通常上下2.5cm，左右3cm（或2.5cm）
- 装订线默认0cm
- 页眉默认1.5cm，页脚默认2.0cm

【重要提醒】
1. 如果用户未提及某项设置，请使用合理的默认值
2. 仔细识别用户的格式要求，不要遗漏任何明确说明的参数
3. 特别注意：三级标题、四级标题、页码格式、表格样式等细节要求
4. 字体名称中的下划线后缀（如_GB2312）可以忽略
5. 表格边框"1 1/2磅"应转换为2.25pt
6. 确保JSON格式正确，所有字符串用双引号包裹
"""

    def __init__(self):
        """初始化AI解析器"""
        self.client = None
        if settings.AI_API_KEY:
            self.client = AsyncOpenAI(
                api_key=settings.AI_API_KEY,
                base_url=settings.AI_BASE_URL
            )

    async def parse_text(self, text: str) -> Dict[str, Any]:
        """
        解析自然文本为规则配置

        Args:
            text: 用户输入的格式要求文字

        Returns:
            解析后的规则配置字典
        """
        # 如果没有配置AI，使用规则解析
        if not self.client:
            logger.warning("AI not configured, using rule-based parsing")
            return self._rule_based_parse(text)

        try:
            # 调用LLM解析
            response = await self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"请将以下格式要求解析为JSON：\n\n{text}"}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content.strip()

            # 尝试提取JSON（处理可能的多余文字）
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result_text = json_match.group()

            config = json.loads(result_text)

            # 验证并修正配置
            config = self._validate_and_fix_config(config)

            logger.info(f"AI parsed rule config: {config}")
            return config

        except Exception as e:
            logger.error(f"AI parsing failed: {e}, falling back to rule-based parsing")
            return self._rule_based_parse(text)

    def _rule_based_parse(self, text: str) -> Dict[str, Any]:
        """
        基于规则的解析（后备方案）

        使用正则表达式提取常见的格式要求
        """
        config = self._get_default_config()

        try:
            # 提取页边距
            top_match = re.search(r"上(?:页边距|边距)?[：:]\s*(\d+\.?\d*)\s*cm", text)
            bottom_match = re.search(r"下(?:页边距|边距)?[：:]\s*(\d+\.?\d*)\s*cm", text)
            left_match = re.search(r"左(?:页边距|边距)?[：:]\s*(\d+\.?\d*)\s*cm", text)
            right_match = re.search(r"右(?:页边距|边距)?[：:]\s*(\d+\.?\d*)\s*cm", text)

            if top_match:
                config["page"]["margins"]["top_cm"] = float(top_match.group(1))
            if bottom_match:
                config["page"]["margins"]["bottom_cm"] = float(bottom_match.group(1))
            if left_match:
                config["page"]["margins"]["left_cm"] = float(left_match.group(1))
            if right_match:
                config["page"]["margins"]["right_cm"] = float(right_match.group(1))

            # 提取装订线
            gutter_match = re.search(r"装订线[：:]\s*(\d+\.?\d*)\s*cm", text)
            if gutter_match:
                config["page"]["gutter_cm"] = float(gutter_match.group(1))

            # 提取页眉
            header_match = re.search(r"页眉[：:]\s*(\d+\.?\d*)\s*cm", text)
            if header_match:
                config["page"]["header_cm"] = float(header_match.group(1))

            # 提取页脚
            footer_match = re.search(r"页脚[：:]\s*(\d+\.?\d*)\s*cm", text)
            if footer_match:
                config["page"]["footer_cm"] = float(footer_match.group(1))

            # 提取正文字体
            body_font_match = re.search(r"正文[：:]\s*([^\s，。；,]+?)\s*(\d+\.?\d*)\s*([号pt磅]|[四三二一小初]+)", text)
            if body_font_match:
                font_name = body_font_match.group(1)
                size_value = body_font_match.group(2)
                size_unit = body_font_match.group(3)

                # 字体名称映射
                font_map = {
                    "宋体": "SimSun", "仿宋": "FangSong", "楷体": "KaiTi", "黑体": "SimHei"
                }
                for cn_name, en_name in font_map.items():
                    if cn_name in font_name:
                        config["body"]["font"] = en_name
                        break

                # 字号转换
                config["body"]["size_pt"] = self._convert_size_to_pt(size_value, size_unit)

            # 提取行距
            spacing_match = re.search(r"行距[：:]\s*(\d+\.?\d*)\s*(磅|pt|倍)", text)
            if spacing_match:
                spacing_value = float(spacing_match.group(1))
                spacing_unit = spacing_match.group(2)

                if spacing_unit in ["磅", "pt"]:
                    config["body"]["line_spacing_pt"] = int(spacing_value)
                elif spacing_unit == "倍":
                    config["body"]["line_spacing_pt"] = int(spacing_value * 16.67)

            # 提取首行缩进
            indent_match = re.search(r"首行缩进[：:]\s*(\d+)\s*字符?", text)
            if indent_match:
                config["body"]["first_line_indent_chars"] = int(indent_match.group(1))

            # 提取对齐网格
            if re.search(r"对齐网格", text):
                config["body"]["align_to_grid"] = True

            # 提取标题样式（支持1-4级）
            heading_patterns = [
                (1, r"一?级标题[：:]\s*([^\s，。；,]+?)\s*(\d+\.?\d*)\s*([号pt磅]|[四三二一小初]+)"),
                (2, r"二?级标题[：:]\s*([^\s，。；,]+?)\s*(\d+\.?\d*)\s*([号pt磅]|[四三二一小初]+)"),
                (3, r"三?级标题[：:]\s*([^\s，。；,]+?)\s*(\d+\.?\d*)\s*([号pt磅]|[四三二一小初]+)"),
                (4, r"四?级标题[：:]\s*([^\s，。；,]+?)\s*(\d+\.?\d*)\s*([号pt磅]|[四三二一小初]+)")
            ]

            for level, pattern in heading_patterns:
                match = re.search(pattern, text)
                if match:
                    font_name = match.group(1)
                    size_value = match.group(2)
                    size_unit = match.group(3)

                    # 查找或添加标题配置
                    heading_config = next((h for h in config["headings"] if h["level"] == level), None)
                    if not heading_config:
                        heading_config = {
                            "level": level,
                            "font": "SimHei",
                            "size_pt": 14,
                            "bold": True,
                            "alignment": "left" if level > 1 else "center"
                        }
                        config["headings"].append(heading_config)

                    # 字体名称映射
                    font_map = {
                        "宋体": "SimSun", "仿宋": "FangSong", "楷体": "KaiTi", "黑体": "SimHei"
                    }
                    for cn_name, en_name in font_map.items():
                        if cn_name in font_name:
                            heading_config["font"] = en_name
                            break

                    # 字号转换
                    heading_config["size_pt"] = self._convert_size_to_pt(size_value, size_unit)

            # 提取页码设置
            page_number_match = re.search(r"页码[：:]\s*([^。，；;\n]+)", text)
            if page_number_match:
                page_number_text = page_number_match.group(1)

                # 检测居中
                if "居中" in page_number_text:
                    config["page_number"]["alignment"] = "center"
                elif "左" in page_number_text:
                    config["page_number"]["alignment"] = "left"
                elif "右" in page_number_text:
                    config["page_number"]["alignment"] = "right"

                # 检测字体
                if "Times" in page_number_text or "times" in page_number_text:
                    config["page_number"]["font"] = "Times New Roman"

                # 检测字号
                page_number_size_match = re.search(r"(\d+\.?\d*)\s*([号pt磅]|[五小]+)", page_number_text)
                if page_number_size_match:
                    size_value = page_number_size_match.group(1)
                    size_unit = page_number_size_match.group(2)
                    config["page_number"]["size_pt"] = self._convert_size_to_pt(size_value, size_unit)

            # 检测页码格式（罗马数字 vs 阿拉伯数字）
            if "罗马" in text and ("Ⅰ" in text or "ⅠⅡ" in text or "ⅰⅱ" in text.lower()):
                config["page_number"]["toc_number_format"] = "roman"
            if re.search(r"目录[^\n]*罗马|ⅠⅡ|ⅰⅱ", text):
                config["page_number"]["toc_number_format"] = "roman"

            # 提取图表编号格式
            caption_match = re.search(r"图、?表?[编号格式]*[：:]\s*([^。，；;\n]+)", text)
            if caption_match:
                caption_text = caption_match.group(1)
                # 检测"二级标题-序号"格式
                if re.search(r"二级标题[：:－-]?序号|(\d+[-—]\d+)", caption_text):
                    config["figure_caption"] = {"format": "{level}-{index}", "position": "below"}
                    config["table_caption"] = {"format": "{level}-{index}", "position": "above"}

            # 提取表格样式
            table_border_match = re.search(r"表格[：:][^。\n]*外框[宽度]*[：:]\s*(\d+\s*\d*/?\d*)\s*磅", text)
            if table_border_match:
                border_text = table_border_match.group(1)
                # 转换"1 1/2"为2.25
                if "1/2" in border_text:
                    config["table"]["border_width_pt"] = 2.25
                else:
                    config["table"]["border_width_pt"] = float(border_text)

            # 提取表头样式
            table_header_match = re.search(r"表头[：:]\s*([^\s，。；]+?)\s*(小?四|三|五|\d+\.?\d*)[号pt磅]?", text)
            if table_header_match:
                font_name = table_header_match.group(1)
                size_text = table_header_match.group(2)

                # 字体映射
                font_map = {"黑体": "SimHei", "宋体": "SimSun", "仿宋": "FangSong", "楷体": "KaiTi"}
                for cn_name, en_name in font_map.items():
                    if cn_name in font_name:
                        config["table"]["header_font"] = en_name
                        break

                # 字号转换
                config["table"]["header_size_pt"] = self._convert_size_to_pt("12" if "小四" in size_text or "四" in size_text else size_text.replace("小", ""), "号" if "号" in size_text or "小" in size_text else "pt")

            # 提取表内样式
            table_body_match = re.search(r"其他[：:]\s*([^\s，。；]+?)\s*(小?四|三|五|\d+\.?\d*)[号pt磅]?[,，]?表内行距[：:]\s*(\d+)\s*磅", text)
            if table_body_match:
                font_name = table_body_match.group(1)
                size_text = table_body_match.group(2)
                line_spacing = table_body_match.group(3)

                # 字体映射
                font_map = {"黑体": "SimHei", "宋体": "SimSun", "仿宋": "FangSong", "楷体": "KaiTi"}
                for cn_name, en_name in font_map.items():
                    if cn_name in font_name:
                        config["table"]["body_font"] = en_name
                        break

                # 字号和行距
                config["table"]["body_size_pt"] = self._convert_size_to_pt("12" if "小四" in size_text or "四" in size_text else size_text.replace("小", ""), "号" if "号" in size_text or "小" in size_text else "pt")
                config["table"]["line_spacing_pt"] = int(line_spacing)

            logger.info(f"Rule-based parsed config: {config}")
            return config

        except Exception as e:
            logger.error(f"Rule-based parsing failed: {e}")
            return self._get_default_config()

    def _convert_size_to_pt(self, value: str, unit: str) -> int:
        """将字号转换为pt"""
        size_map = {
            "初号": 42, "小初": 36,
            "一号": 26, "小一": 24,
            "二号": 22, "小二": 18,
            "三号": 16, "小三": 15,
            "四号": 14, "小四": 12,
            "五号": 10.5, "小五": 9
        }

        if unit in size_map:
            return size_map[unit]
        elif unit in ["号", "pt", "磅"]:
            return int(float(value))
        else:
            return 12  # 默认12pt

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "page": {
                "margins": {
                    "top_cm": 2.5,
                    "bottom_cm": 2.5,
                    "left_cm": 3.0,
                    "right_cm": 2.5
                },
                "paper_name": "A4",
                "gutter_cm": 0,
                "header_cm": 1.5,
                "footer_cm": 2.0
            },
            "headings": [
                {
                    "level": 1,
                    "font": "SimHei",
                    "size_pt": 16,
                    "bold": True,
                    "alignment": "center"
                },
                {
                    "level": 2,
                    "font": "SimHei",
                    "size_pt": 14,
                    "bold": True,
                    "alignment": "left"
                },
                {
                    "level": 3,
                    "font": "SimHei",
                    "size_pt": 13,
                    "bold": True,
                    "alignment": "left"
                },
                {
                    "level": 4,
                    "font": "SimHei",
                    "size_pt": 12,
                    "bold": True,
                    "alignment": "left"
                }
            ],
            "body": {
                "font": "SimSun",
                "size_pt": 12,
                "line_spacing_pt": 25,
                "first_line_indent_chars": 2,
                "align_to_grid": False
            },
            "page_number": {
                "font": "Times New Roman",
                "size_pt": 10.5,
                "alignment": "center",
                "number_format": "arabic",
                "toc_number_format": "arabic"
            },
            "table": {
                "border_width_pt": 0.5,
                "header_font": "SimHei",
                "header_size_pt": 12,
                "body_font": "FangSong",
                "body_size_pt": 12,
                "line_spacing_pt": 20
            }
        }

    def _validate_and_fix_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证并修正配置"""
        default = self._get_default_config()

        # 确保所有必需字段都存在
        if "page" not in config:
            config["page"] = default["page"]
        else:
            if "margins" not in config["page"]:
                config["page"]["margins"] = default["page"]["margins"]
            else:
                for key in ["top_cm", "bottom_cm", "left_cm", "right_cm"]:
                    if key not in config["page"]["margins"]:
                        config["page"]["margins"][key] = default["page"]["margins"][key]
            # 确保可选的页面字段存在
            for key in ["gutter_cm", "header_cm", "footer_cm"]:
                if key not in config["page"]:
                    config["page"][key] = default["page"].get(key, 0 if key == "gutter_cm" else 1.5 if key == "header_cm" else 2.0)

        if "headings" not in config:
            config["headings"] = default["headings"]

        if "body" not in config:
            config["body"] = default["body"]
        else:
            for key in ["font", "size_pt", "line_spacing_pt", "first_line_indent_chars"]:
                if key not in config["body"]:
                    config["body"][key] = default["body"][key]
            # align_to_grid 是可选的
            if "align_to_grid" not in config["body"]:
                config["body"]["align_to_grid"] = default["body"].get("align_to_grid", False)

        # page_number 是可选的
        if "page_number" not in config:
            config["page_number"] = default["page_number"]
        else:
            for key in ["font", "size_pt", "alignment", "number_format", "toc_number_format"]:
                if key not in config["page_number"]:
                    config["page_number"][key] = default["page_number"].get(key)

        # table 是可选的
        if "table" not in config:
            config["table"] = default.get("table", {
                "border_width_pt": 0.5,
                "header_font": "SimHei",
                "header_size_pt": 12,
                "body_font": "FangSong",
                "body_size_pt": 12,
                "line_spacing_pt": 20
            })

        return config
