"""
Rule Template API Routes
Handles rule template CRUD, AI parsing, and docx reverse engineering.
"""
from fastapi import APIRouter, Depends, Query, UploadFile, File, Body
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import json
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.models.rule_template import RuleTemplate, TemplateType
from app.models.user import User
from app.api.schemas import ApiResponse
from app.api.deps import get_current_user, get_current_user_optional
from app.services.docx_parser import DocxParser
from app.services.ai_rule_parser import AIRuleParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rule-templates", tags=["Rule Templates"])


# Request models
class RuleTemplateCreateRequest(BaseModel):
    name: str
    description: str = ""
    config: dict


class RuleTemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None


# ==================== Rule Template CRUD ====================

@router.get("", response_model=ApiResponse)
def get_rule_templates(
    template_type: Optional[str] = Query(None, description="模板类型：system/custom"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取规则模板列表

    系统模板对所有用户可见
    用户自定义模板只对创建者可见
    """
    query = db.query(RuleTemplate)

    # 筛选模板类型
    if template_type == "system":
        query = query.filter(RuleTemplate.template_type == TemplateType.SYSTEM)
    elif template_type == "custom":
        # 用户只能看到自己的自定义模板
        if current_user:
            query = query.filter(
                RuleTemplate.template_type == TemplateType.CUSTOM,
                RuleTemplate.user_id == current_user.id
            )
        else:
            # 未登录用户没有自定义模板
            query = query.filter(RuleTemplate.id == -1)
    else:
        # 返回所有系统模板 + 当前用户的自定义模板
        if current_user:
            query = query.filter(
                (RuleTemplate.template_type == TemplateType.SYSTEM) |
                ((RuleTemplate.template_type == TemplateType.CUSTOM) & (RuleTemplate.user_id == current_user.id))
            )
        else:
            query = query.filter(RuleTemplate.template_type == TemplateType.SYSTEM)

    templates = query.order_by(RuleTemplate.is_default.desc(), RuleTemplate.created_at.desc()).all()

    templates_data = []
    for template in templates:
        templates_data.append({
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "template_type": template.template_type,
            "is_default": template.is_default,
            "use_count": template.use_count,
            "config": template.config_json
        })

    return ApiResponse(
        code=200,
        message="成功",
        data={"templates": templates_data}
    )


@router.get("/{template_id}", response_model=ApiResponse)
def get_rule_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """获取单个规则模板详情"""
    template = db.query(RuleTemplate).filter(RuleTemplate.id == template_id).first()

    if not template:
        return ApiResponse(code=1004, message="模板不存在", data=None)

    return ApiResponse(
        code=200,
        message="成功",
        data=template.to_dict()
    )


@router.post("", response_model=ApiResponse)
def create_rule_template(
    request: RuleTemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建自定义规则模板

    Body JSON格式:
    {
        "name": "模板名称",
        "description": "模板描述",
        "config": {
            "page": {...},
            "headings": [...],
            "body": {...}
        }
    }
    """
    template = RuleTemplate(
        name=request.name,
        description=request.description,
        template_type=TemplateType.CUSTOM,
        user_id=current_user.id,
        config_json=request.config
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    logger.info(f"User {current_user.id} created rule template: {template.id}")

    return ApiResponse(
        code=200,
        message="创建成功",
        data=template.to_dict()
    )


@router.put("/{template_id}", response_model=ApiResponse)
def update_rule_template(
    template_id: int,
    request: RuleTemplateUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新规则模板（只能更新自己的自定义模板）"""
    template = db.query(RuleTemplate).filter(RuleTemplate.id == template_id).first()

    if not template:
        return ApiResponse(code=1004, message="模板不存在", data=None)

    # 只能更新自定义模板
    if template.template_type != TemplateType.CUSTOM:
        return ApiResponse(code=1003, message="系统模板不能修改", data=None)

    # 只能更新自己的模板
    if template.user_id != current_user.id:
        return ApiResponse(code=1003, message="无权修改此模板", data=None)

    if request.name:
        template.name = request.name
    if request.description is not None:
        template.description = request.description
    if request.config:
        template.config_json = request.config

    db.commit()
    db.refresh(template)

    logger.info(f"User {current_user.id} updated rule template: {template.id}")

    return ApiResponse(
        code=200,
        message="更新成功",
        data=template.to_dict()
    )


@router.delete("/{template_id}", response_model=ApiResponse)
def delete_rule_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除规则模板（只能删除自己的自定义模板）"""
    template = db.query(RuleTemplate).filter(RuleTemplate.id == template_id).first()

    if not template:
        return ApiResponse(code=1004, message="模板不存在", data=None)

    # 只能删除自定义模板
    if template.template_type != TemplateType.CUSTOM:
        return ApiResponse(code=1003, message="系统模板不能删除", data=None)

    # 只能删除自己的模板
    if template.user_id != current_user.id:
        return ApiResponse(code=1003, message="无权删除此模板", data=None)

    db.delete(template)
    db.commit()

    logger.info(f"User {current_user.id} deleted rule template: {template_id}")

    return ApiResponse(code=200, message="删除成功", data=None)


# ==================== AI Parsing ====================

@router.post("/parse/text", response_model=ApiResponse)
async def parse_text_to_rule(
    text: str = Query(..., description="格式要求文本"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    A通道：自然语言解析

    用户粘贴格式要求文字，AI解析为结构化规则配置
    """
    try:
        # 调用AI解析服务
        ai_parser = AIRuleParser()
        config = await ai_parser.parse_text(text)

        # 可以选择直接保存为模板，或者只返回配置供用户确认
        return ApiResponse(
            code=200,
            message="解析成功",
            data={"config": config}
        )

    except Exception as e:
        logger.error(f"Error parsing text to rule: {e}")
        return ApiResponse(code=1001, message=f"解析失败: {str(e)}", data=None)


# ==================== Docx Reverse Engineering ====================

@router.post("/parse/docx", response_model=ApiResponse)
async def parse_docx_to_rule(
    file: UploadFile = File(..., description="上传的docx范文文件"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    B通道：范文逆向克隆

    上传格式完美的docx范文，逆向解析出规则配置
    """
    try:
        # 保存上传文件
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # 使用DocxParser解析文档
            parser = DocxParser(tmp_file_path)
            doc_data = parser.parse()

            # 提取格式规则
            config = _extract_config_from_doc_data(doc_data)

            # 添加目录和标题结构信息（用于前端展示）
            result_data = {
                "config": config,
                "structure": {
                    "table_of_contents": doc_data.get("table_of_contents", {}),
                    "heading_structure": doc_data.get("heading_structure", {})
                }
            }

            return ApiResponse(
                code=200,
                message="解析成功",
                data=result_data
            )

        finally:
            # 删除临时文件
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    except Exception as e:
        logger.error(f"Error parsing docx to rule: {e}")
        return ApiResponse(code=1001, message=f"解析失败: {str(e)}", data=None)


# ==================== Helper Functions ====================

def _extract_config_from_doc_data(doc_data: dict) -> dict:
    """
    从DocxParser解析的数据中提取格式配置

    算法逻辑：
    1. 页面设置：直接提取
    2. 正文样式：统计出现频率最高的段落属性
    3. 标题样式：根据outline_level提取各级标题的样式
    """
    config = {}

    # 1. 提取页面设置
    page_settings = doc_data.get("page_settings", {})
    config["page"] = {
        "margins": {
            "top_cm": page_settings.get("margins", {}).get("top_mm", 25) / 10,
            "bottom_cm": page_settings.get("margins", {}).get("bottom_mm", 25) / 10,
            "left_cm": page_settings.get("margins", {}).get("left_mm", 30) / 10,
            "right_cm": page_settings.get("margins", {}).get("right_mm", 25) / 10,
        },
        "paper_name": "A4"  # 默认A4
    }

    # 2. 提取标题样式
    headings = doc_data.get("headings", [])
    heading_levels = {}

    for heading in headings:
        level = heading.get("level", 1)
        if level not in heading_levels:
            heading_levels[level] = []

        heading_levels[level].append({
            "font": heading.get("font", {}),
            "alignment": heading.get("alignment"),
            "size_pt": heading.get("font", {}).get("size_pt", 12)
        })

    # 统计每级标题的常用样式（使用最常用的样式，而不是第一个）
    config["headings"] = []
    for level in sorted(heading_levels.keys()):
        level_headings = heading_levels[level]
        if level_headings:
            # Filter out headings with incomplete font info
            # Be more lenient with size requirements for real-world documents
            valid_headings = []
            for h in level_headings:
                font_name = h["font"].get("name")
                size_pt = h.get("size_pt")
                # Accept headings with font info (even if font_name is None, we have font dict)
                # or with valid size_pt
                if font_name or (size_pt and size_pt > 0):
                    valid_headings.append(h)

            # If no valid headings, skip this level
            if not valid_headings:
                continue

            # Count font names to find the most common one
            font_name_map = {
                "宋体": "SimSun",
                "SimSun": "SimSun",
                "黑体": "SimHei",
                "SimHei": "SimHei",
                "微软雅黑": "Microsoft YaHei",
                "Microsoft YaHei": "Microsoft YaHei",
                "楷体": "KaiTi",
                "KaiTi": "KaiTi",
                "仿宋": "FangSong",
                "FangSong": "FangSong",
                "方正小标宋简体": "方正小标宋简体",
            }

            font_counts = {}
            size_counts = {}
            bold_counts = {}
            align_counts = {}

            for h in valid_headings:
                font_name = h["font"].get("name", "SimHei")
                if font_name:
                    raw_name = font_name.split(',')[0].strip()
                    font_name = font_name_map.get(raw_name, raw_name)

                font_counts[font_name] = font_counts.get(font_name, 0) + 1
                size_counts[h.get("size_pt")] = size_counts.get(h.get("size_pt"), 0) + 1
                bold_counts[h["font"].get("bold", True)] = bold_counts.get(h["font"].get("bold", True), 0) + 1
                align_counts[h.get("alignment", "left")] = align_counts.get(h.get("alignment", "left"), 0) + 1

            # Use the most common values
            common_font = max(font_counts.items(), key=lambda x: x[1])[0]
            common_size = max(size_counts.items(), key=lambda x: x[1])[0]
            common_bold = max(bold_counts.items(), key=lambda x: x[1])[0]
            common_align = max(align_counts.items(), key=lambda x: x[1])[0]

            config["headings"].append({
                "level": level,
                "font": common_font,
                "size_pt": common_size,
                "bold": common_bold,
                "alignment": common_align
            })

    # 3. 提取正文样式（统计非标题段落的样式）
    paragraphs = doc_data.get("paragraphs", [])
    body_paragraphs = []

    # 收集所有非标题段落
    heading_para_indices = {h.get("paragraph_index") for h in headings}
    for para in paragraphs:
        if para.get("index") not in heading_para_indices:
            body_paragraphs.append(para)

    if body_paragraphs:
        # 统计最常用的字体、字号
        font_counts = {}
        size_counts = {}

        # Font name mapping (Chinese to English)
        font_name_map = {
            "宋体": "SimSun",
            "SimSun": "SimSun",
            "黑体": "SimHei",
            "SimHei": "SimHei",
            "微软雅黑": "Microsoft YaHei",
            "Microsoft YaHei": "Microsoft YaHei",
            "楷体": "KaiTi",
            "KaiTi": "KaiTi",
            "仿宋": "FangSong",
            "FangSong": "FangSong",
            "方正小标宋简体": "方正小标宋简体",  # Keep as is
        }
        
        for para in body_paragraphs:
            # Normalize font name (extract first font from comma-separated list and map)
            font_name = para.get("font", {}).get("name", "SimSun")
            if font_name:
                raw_name = font_name.split(',')[0].strip()
                font_name = font_name_map.get(raw_name, raw_name)
            font = font_name or "SimSun"
            size = para.get("font", {}).get("size_pt") or 12  # 确保不为None

            font_counts[font] = font_counts.get(font, 0) + 1
            size_counts[size] = size_counts.get(size, 0) + 1

        # 取众数
        common_font = max(font_counts.items(), key=lambda x: x[1])[0] if font_counts else "SimSun"
        common_size = max(size_counts.items(), key=lambda x: x[1])[0] if size_counts else 12

        # 统计常用行距（优先使用line_spacing_pt，否则计算）
        spacing_counts = {}
        for para in body_paragraphs:
            formatting = para.get("formatting", {})
            # 优先使用line_spacing_pt（如果已计算）
            if "line_spacing_pt" in formatting:
                spacing_pt = formatting["line_spacing_pt"]
                spacing_counts[spacing_pt] = spacing_counts.get(spacing_pt, 0) + 1
            else:
                # 否则使用line_spacing并转换
                spacing = formatting.get("line_spacing", 1.5)
                rule = formatting.get("line_spacing_rule", "MULTIPLE")
                font_size = para.get("font", {}).get("size_pt") or 12  # 确保不为None
                if rule == "EXACT" or isinstance(spacing, (int, float)) and spacing > 10:
                    # 固定磅数
                    spacing_pt = spacing
                else:
                    # 倍数行距，转换为磅数
                    spacing_pt = spacing * font_size
                spacing_pt = round(spacing_pt)
                spacing_counts[spacing_pt] = spacing_counts.get(spacing_pt, 0) + 1

        common_spacing_pt = max(spacing_counts.items(), key=lambda x: x[1])[0] if spacing_counts else 25
        line_spacing_pt = int(common_spacing_pt)

        # 统计首行缩进
        indent_counts = {}
        for para in body_paragraphs:
            indent = para.get("formatting", {}).get("first_line_indent_chars", 2)
            indent_counts[indent] = indent_counts.get(indent, 0) + 1

        common_indent = max(indent_counts.items(), key=lambda x: x[1])[0] if indent_counts else 2

        config["body"] = {
            "font": common_font,
            "size_pt": common_size,
            "line_spacing_pt": line_spacing_pt,
            "first_line_indent_chars": common_indent
        }
    else:
        # 默认正文样式
        config["body"] = {
            "font": "SimSun",
            "size_pt": 12,
            "line_spacing_pt": 25,
            "first_line_indent_chars": 2
        }

    return config
