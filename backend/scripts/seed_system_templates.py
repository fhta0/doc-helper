"""
Seed system rule templates to the database.

Run this script to populate the rule_templates table with default system templates.
Usage: python seed_system_templates.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.rule_template import RuleTemplate, TemplateType


def seed_system_templates():
    """Seed system rule templates to the database."""
    print(f"Connecting to database: {settings.DATABASE_URL}")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if system templates already exist
        existing_count = db.query(RuleTemplate).filter(
            RuleTemplate.template_type == TemplateType.SYSTEM
        ).count()

        if existing_count > 0:
            print(f"Found {existing_count} existing system templates.")
            choice = input("Do you want to delete and reseed them? (y/N): ")
            if choice.lower() != 'y':
                print("Aborted.")
                return

            # Delete existing system templates
            db.query(RuleTemplate).filter(
                RuleTemplate.template_type == TemplateType.SYSTEM
            ).delete()
            db.commit()
            print("Deleted existing system templates.")

        # System templates data
        system_templates = [
            {
                "name": "GB/T 7714-2015 学术论文",
                "description": "中国国家标准学术论文格式规范",
                "template_type": TemplateType.SYSTEM,
                "config": {
                    "page": {
                        "margins": {"top_cm": 2.5, "bottom_cm": 2.5, "left_cm": 3.0, "right_cm": 2.5},
                        "paper_name": "A4"
                    },
                    "headings": [
                        {"level": 1, "font": "SimHei", "size_pt": 16, "bold": True, "alignment": "center"},
                        {"level": 2, "font": "SimHei", "size_pt": 14, "bold": True, "alignment": "left"},
                        {"level": 3, "font": "SimHei", "size_pt": 13, "bold": True, "alignment": "left"}
                    ],
                    "body": {
                        "font": "SimSun",
                        "size_pt": 12,
                        "line_spacing_pt": 25,
                        "first_line_indent_chars": 2
                    }
                },
                "is_default": True
            },
            {
                "name": "本科毕业论文标准",
                "description": "普通本科毕业论文格式要求",
                "template_type": TemplateType.SYSTEM,
                "config": {
                    "page": {
                        "margins": {"top_cm": 2.5, "bottom_cm": 2.5, "left_cm": 3.0, "right_cm": 2.5},
                        "paper_name": "A4"
                    },
                    "headings": [
                        {"level": 1, "font": "SimHei", "size_pt": 18, "bold": True, "alignment": "center"},
                        {"level": 2, "font": "SimHei", "size_pt": 16, "bold": True, "alignment": "left"}
                    ],
                    "body": {
                        "font": "SimSun",
                        "size_pt": 12,
                        "line_spacing_pt": 22,
                        "first_line_indent_chars": 2
                    }
                },
                "is_default": False
            },
            {
                "name": "硕士学位论文标准",
                "description": "硕士学位论文格式要求",
                "template_type": TemplateType.SYSTEM,
                "config": {
                    "page": {
                        "margins": {"top_cm": 2.5, "bottom_cm": 2.5, "left_cm": 3.0, "right_cm": 2.5},
                        "paper_name": "A4"
                    },
                    "headings": [
                        {"level": 1, "font": "SimHei", "size_pt": 18, "bold": True, "alignment": "center"},
                        {"level": 2, "font": "SimHei", "size_pt": 16, "bold": True, "alignment": "left"},
                        {"level": 3, "font": "SimHei", "size_pt": 14, "bold": True, "alignment": "left"}
                    ],
                    "body": {
                        "font": "SimSun",
                        "size_pt": 12,
                        "line_spacing_pt": 25,
                        "first_line_indent_chars": 2
                    }
                },
                "is_default": False
            },
            {
                "name": "期刊投稿格式",
                "description": "一般期刊投稿论文格式要求",
                "template_type": TemplateType.SYSTEM,
                "config": {
                    "page": {
                        "margins": {"top_cm": 2.5, "bottom_cm": 2.5, "left_cm": 2.5, "right_cm": 2.5},
                        "paper_name": "A4"
                    },
                    "headings": [
                        {"level": 1, "font": "SimHei", "size_pt": 15, "bold": True, "alignment": "left"},
                        {"level": 2, "font": "SimHei", "size_pt": 13, "bold": True, "alignment": "left"}
                    ],
                    "body": {
                        "font": "SimSun",
                        "size_pt": 10.5,
                        "line_spacing_pt": 20,
                        "first_line_indent_chars": 2
                    }
                },
                "is_default": False
            }
        ]

        # Add templates
        print("Adding system rule templates...")
        for template_data in system_templates:
            template = RuleTemplate(
                name=template_data["name"],
                description=template_data["description"],
                template_type=template_data["template_type"],
                user_id=None,  # 系统模板无所属用户
                config_json=template_data["config"],
                is_default=template_data["is_default"]
            )
            db.add(template)
            print(f"  + {template_data['name']}")

        db.commit()
        print(f"\n✅ Successfully seeded {len(system_templates)} system templates!")

    except Exception as e:
        print(f"❌ Error seeding templates: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_system_templates()
