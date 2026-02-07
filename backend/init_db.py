import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.models import User, Rule, Check, Product, RuleTemplate
from app.core.security import get_password_hash
import json
from datetime import date


def init_database():
    """Initialize database tables and seed data."""
    print(f"Connecting to database: {settings.DATABASE_URL}")

    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    # Drop all tables (use with caution!)
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)

    # Create all tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create test user
        print("Creating test user...")
        test_user = User(
            username="testuser",
            password_hash=get_password_hash("test123"),
            nickname="测试用户",
            free_count=3,
            last_reset_date=date.today()
        )
        db.add(test_user)

        # Initialize Products
        print("Initializing products...")
        products = [
            Product(
                key="basic_pack",
                name="基础检测包",
                price=10000,  # 100元
                count=10,
                count_type="basic",
                description="基础格式检测 10次",
                active=True
            ),
            Product(
                key="full_pack",
                name="完整检测包",
                price=20000,  # 200元
                count=10,
                count_type="full",
                description="基础+AI智能检测 10次",
                active=True
            ),
            Product(
                key="single_full",
                name="单次检测包",
                price=3000,  # 30元
                count=1,
                count_type="full",
                description="基础+AI智能检测 1次",
                active=True
            )
        ]
        for p in products:
            db.add(p)

        # Load rules from doc/sample_rules.json
        print("Loading rules from doc/sample_rules.json...")
        rules_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "doc", "sample_rules.json")
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
                for rule_data in rules_data:
                    rule = Rule(
                        id=rule_data["id"],
                        name=rule_data["name"],
                        category=rule_data["category"],
                        match=rule_data.get("match"),
                        condition_json=rule_data.get("condition", {}),
                        error_message=rule_data.get("error_message"),
                        suggestion=rule_data.get("suggestion"),
                        checker=rule_data.get("checker", "deterministic"),
                        prompt_template=rule_data.get("prompt_template"),
                        fix_action=rule_data.get("fix_action"),
                        fix_params=rule_data.get("fix_params")
                    )
                    db.add(rule)
        else:
            print(f"Warning: {rules_file} not found, skipping rules seeding")

        # Load structure rules from doc/structure_rules.json
        print("Loading structure rules from doc/structure_rules.json...")
        structure_rules_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "doc", "structure_rules.json")
        if os.path.exists(structure_rules_file):
            with open(structure_rules_file, 'r', encoding='utf-8') as f:
                structure_rules_data = json.load(f)
                for rule_data in structure_rules_data:
                    # Check if rule already exists
                    existing_rule = db.query(Rule).filter(Rule.id == rule_data["id"]).first()
                    if not existing_rule:
                        rule = Rule(
                            id=rule_data["id"],
                            name=rule_data["name"],
                            category=rule_data["category"],
                            match=rule_data.get("match", "document"),
                            condition_json=rule_data.get("condition", {}),
                            error_message=rule_data.get("error_message"),
                            suggestion=rule_data.get("suggestion"),
                            checker=rule_data.get("checker", "deterministic"),
                            prompt_template=rule_data.get("prompt_template"),
                            fix_action=rule_data.get("fix_action"),
                            fix_params=rule_data.get("fix_params")
                        )
                        db.add(rule)
                    else:
                        print(f"  Rule {rule_data['id']} already exists, skipping")
        else:
            print(f"Warning: {structure_rules_file} not found, skipping structure rules seeding")

        # Initialize system rule templates
        print("Initializing system rule templates...")
        system_templates = [
            {
                "name": "GB/T 7714-2015 学术论文",
                "description": "中国国家标准学术论文格式规范",
                "template_type": "system",
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
                }
            },
            {
                "name": "本科毕业论文标准",
                "description": "普通本科毕业论文格式要求",
                "template_type": "system",
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
                }
            },
            {
                "name": "硕士学位论文标准",
                "description": "硕士学位论文格式要求",
                "template_type": "system",
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
                }
            },
            {
                "name": "期刊投稿格式",
                "description": "一般期刊投稿论文格式要求",
                "template_type": "system",
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
                }
            }
        ]

        for template_data in system_templates:
            template = RuleTemplate(
                name=template_data["name"],
                description=template_data["description"],
                template_type=template_data["template_type"],
                user_id=None,  # 系统模板无所属用户
                config_json=template_data["config"],
                is_default=(template_data["name"] == "GB/T 7714-2015 学术论文")
            )
            db.add(template)

        db.commit()
        print("Database initialized successfully!")
        print("\nTest credentials:")
        print("  Username: testuser")
        print("  Password: test123")

    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
