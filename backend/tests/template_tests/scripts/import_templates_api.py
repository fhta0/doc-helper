#!/usr/bin/env python3
"""
通过调用现有API导入模板文件

测试现有的 parse_docx_to_rule 和 create_rule_template 功能
"""
import os
import sys
from pathlib import Path
import asyncio
import logging

# 添加项目根目录到路径（backend目录）
backend_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_root))

from app.core.database import SessionLocal
from app.models.rule_template import RuleTemplate, TemplateType
from app.models.user import User
from app.services.docx_parser import DocxParser
from app.api.rule_templates import _extract_config_from_doc_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def import_template_from_file(file_path: str, template_name: str, description: str, db):
    """
    使用现有功能导入模板

    模拟 parse_docx_to_rule 的逻辑：
    1. 使用 DocxParser 解析文档
    2. 调用 _extract_config_from_doc_data 提取配置
    3. 保存为系统模板
    """
    logger.info(f"=" * 60)
    logger.info(f"开始处理模板: {template_name}")
    logger.info(f"文件路径: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False

    try:
        # 步骤1: 使用现有的 DocxParser 解析文档
        logger.info("📄 步骤1: 解析文档...")
        parser = DocxParser(file_path)
        doc_data = parser.parse()
        logger.info(f"✅ 解析完成，段落数: {len(doc_data.get('paragraphs', []))}, "
                   f"标题数: {len(doc_data.get('headings', []))}")

        # 步骤2: 使用现有的 _extract_config_from_doc_data 提取配置
        logger.info("⚙️  步骤2: 提取格式配置...")
        config = _extract_config_from_doc_data(doc_data)

        # 打印配置摘要
        logger.info("📋 配置摘要:")
        if "page" in config:
            margins = config["page"].get("margins", {})
            logger.info(f"  页面: 上{margins.get('top_cm')}cm, "
                       f"下{margins.get('bottom_cm')}cm, "
                       f"左{margins.get('left_cm')}cm, "
                       f"右{margins.get('right_cm')}cm")

        if "headings" in config:
            logger.info(f"  标题: {len(config['headings'])} 级")
            for h in config['headings']:
                logger.info(f"    级别{h['level']}: {h['font']} {h['size_pt']}pt, "
                           f"{'加粗' if h.get('bold') else '不加粗'}, "
                           f"对齐: {h['alignment']}")

        if "body" in config:
            body = config["body"]
            logger.info(f"  正文: {body['font']} {body['size_pt']}pt, "
                       f"行距{body['line_spacing_pt']}磅, "
                       f"首行缩进{body['first_line_indent_chars']}字符")

        # 步骤3: 保存到数据库（模拟 create_rule_template 逻辑）
        logger.info("💾 步骤3: 保存到数据库...")

        # 检查是否已存在同名模板
        existing_template = db.query(RuleTemplate).filter(
            RuleTemplate.name == template_name,
            RuleTemplate.template_type == TemplateType.SYSTEM
        ).first()

        if existing_template:
            logger.info(f"更新现有模板 (ID: {existing_template.id})...")
            existing_template.description = description
            existing_template.config_json = config
            db.commit()
            db.refresh(existing_template)
            logger.info(f"✅ 成功更新模板: {template_name} (ID: {existing_template.id})")
        else:
            logger.info("创建新模板...")
            template = RuleTemplate(
                name=template_name,
                description=description,
                template_type=TemplateType.SYSTEM,
                config_json=config,
                is_default=False,
                use_count=0
            )
            db.add(template)
            db.commit()
            db.refresh(template)
            logger.info(f"✅ 成功创建模板: {template_name} (ID: {template.id})")

        return True

    except Exception as e:
        logger.error(f"❌ 处理失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("通过API功能导入模板文件")
    logger.info("测试 DocxParser + _extract_config_from_doc_data")
    logger.info("=" * 60)

    # 获取项目根目录
    project_root = Path(__file__).parent.parent

    # 模板文件配置
    templates = [
        {
            "file_path": str(project_root / "doc/方案模板/K3S-建设方案模板.docx"),
            "name": "K3S建设方案模板",
            "description": "K3S建设方案标准格式模板，包含完整的页面设置、标题样式和正文格式规范"
        },
        {
            "file_path": str(project_root / "doc/方案模板/K3S-设计方案模板.docx"),
            "name": "K3S设计方案模板",
            "description": "K3S设计方案标准格式模板，包含完整的页面设置、标题样式和正文格式规范"
        }
    ]

    # 获取数据库会话
    db = SessionLocal()

    try:
        success_count = 0
        fail_count = 0

        for template_config in templates:
            result = await import_template_from_file(
                file_path=template_config["file_path"],
                template_name=template_config["name"],
                description=template_config["description"],
                db=db
            )

            if result:
                success_count += 1
            else:
                fail_count += 1

        # 打印统计信息
        logger.info("")
        logger.info("=" * 60)
        logger.info("导入完成")
        logger.info(f"✅ 成功: {success_count} 个")
        logger.info(f"❌ 失败: {fail_count} 个")
        logger.info("=" * 60)

        # 查询并显示所有系统模板
        logger.info("")
        logger.info("📚 当前数据库中的系统模板:")
        system_templates = db.query(RuleTemplate).filter(
            RuleTemplate.template_type == TemplateType.SYSTEM
        ).order_by(RuleTemplate.id).all()

        for template in system_templates:
            logger.info(f"")
            logger.info(f"  ID: {template.id} - {template.name}")
            logger.info(f"  描述: {template.description}")
            logger.info(f"  使用次数: {template.use_count}")

            # 显示配置摘要
            config = template.config_json
            if config and "headings" in config:
                logger.info(f"  标题级数: {len(config['headings'])}")
            if config and "body" in config:
                body = config["body"]
                logger.info(f"  正文: {body.get('font')} {body.get('size_pt')}pt")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
