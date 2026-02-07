"""
Database migration script for upgrading to the latest version.

This script:
1. Creates rule_templates table if not exists
2. Adds rule_template_id and rule_config_json columns to checks table if not exists
3. Adds last_template_id column to users table if not exists
4. Seeds system rule templates

Usage: python migrate_database.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError
from app.core.config import settings
from app.models.rule_template import RuleTemplate, TemplateType


def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table."""
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT COUNT(*) as count
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '{table_name}'
            AND COLUMN_NAME = '{column_name}'
        """))
        row = result.fetchone()
        return row[0] > 0


def check_table_exists(engine, table_name):
    """Check if a table exists."""
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT COUNT(*) as count
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '{table_name}'
        """))
        row = result.fetchone()
        return row[0] > 0


def migrate_checks_table(engine):
    """Add new columns to checks table if they don't exist."""
    print("\n=== Migrating checks table ===")

    # Check if columns exist
    has_rule_template_id = check_column_exists(engine, 'checks', 'rule_template_id')
    has_rule_config_json = check_column_exists(engine, 'checks', 'rule_config_json')

    if has_rule_template_id and has_rule_config_json:
        print("✓ checks table already has required columns")
        return

    print("Adding new columns to checks table...")

    with engine.connect() as conn:
        # Add rule_template_id column
        if not has_rule_template_id:
            print("  - Adding rule_template_id column...")
            conn.execute(text("""
                ALTER TABLE checks
                ADD COLUMN rule_template_id INT NULL
                COMMENT '使用的规则模板ID'
            """))
            # Add foreign key constraint
            conn.execute(text("""
                ALTER TABLE checks
                ADD FOREIGN KEY (rule_template_id)
                REFERENCES rule_templates(id)
                ON DELETE SET NULL
            """))
            conn.commit()
            print("    ✓ rule_template_id column added")

        # Add rule_config_json column
        if not has_rule_config_json:
            print("  - Adding rule_config_json column...")
            conn.execute(text("""
                ALTER TABLE checks
                ADD COLUMN rule_config_json JSON NULL
                COMMENT '规则配置快照（JSON格式）'
            """))
            conn.commit()
            print("    ✓ rule_config_json column added")

    print("✓ checks table migration completed")


def migrate_users_table(engine):
    """Add last_template_id column to users table if it doesn't exist."""
    print("\n=== Migrating users table ===")

    # Check if column exists
    has_last_template_id = check_column_exists(engine, 'users', 'last_template_id')

    if has_last_template_id:
        print("✓ users table already has last_template_id column")
        return

    print("Adding last_template_id column to users table...")

    with engine.connect() as conn:
        # Add last_template_id column
        print("  - Adding last_template_id column...")
        conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN last_template_id INT NULL
            COMMENT '上次使用的规则模板ID'
        """))
        # Add foreign key constraint
        conn.execute(text("""
            ALTER TABLE users
            ADD FOREIGN KEY (last_template_id)
            REFERENCES rule_templates(id)
            ON DELETE SET NULL
        """))
        conn.commit()
        print("    ✓ last_template_id column added")

    print("✓ users table migration completed")


def create_rule_templates_table(engine):
    """Create rule_templates table if it doesn't exist."""
    print("\n=== Creating rule_templates table ===")

    if check_table_exists(engine, 'rule_templates'):
        print("✓ rule_templates table already exists")
        return

    print("Creating rule_templates table...")

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE rule_templates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL COMMENT '模板名称',
                description TEXT COMMENT '模板描述',
                template_type VARCHAR(20) NOT NULL DEFAULT 'custom' COMMENT '模板类型',
                user_id INT NULL COMMENT '所属用户ID',
                config_json JSON NOT NULL COMMENT '规则配置',
                is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
                is_default TINYINT(1) DEFAULT 0 COMMENT '是否为默认模板',
                use_count INT DEFAULT 0 COMMENT '使用次数',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_template_type (template_type),
                INDEX idx_user_id (user_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='规则模板表'
        """))
        conn.commit()

    print("✓ rule_templates table created")


def seed_system_templates():
    """Seed system rule templates."""
    print("\n=== Seeding system templates ===")

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
            choice = input("Do you want to reseed them? (y/N): ")
            if choice.lower() != 'y':
                print("Skipping template seeding.")
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
                        "paper_name": "A4",
                        "gutter_cm": 0,
                        "header_cm": 1.5,
                        "footer_cm": 2.0
                    },
                    "headings": [
                        {"level": 1, "font": "SimHei", "size_pt": 16, "bold": True, "alignment": "center"},
                        {"level": 2, "font": "SimHei", "size_pt": 14, "bold": True, "alignment": "left"},
                        {"level": 3, "font": "SimHei", "size_pt": 13, "bold": True, "alignment": "left"},
                        {"level": 4, "font": "SimHei", "size_pt": 12, "bold": True, "alignment": "left"}
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
                        "paper_name": "A4",
                        "gutter_cm": 0,
                        "header_cm": 1.5,
                        "footer_cm": 2.0
                    },
                    "headings": [
                        {"level": 1, "font": "SimHei", "size_pt": 18, "bold": True, "alignment": "center"},
                        {"level": 2, "font": "SimHei", "size_pt": 16, "bold": True, "alignment": "left"}
                    ],
                    "body": {
                        "font": "SimSun",
                        "size_pt": 12,
                        "line_spacing_pt": 22,
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
                        "paper_name": "A4",
                        "gutter_cm": 0,
                        "header_cm": 1.5,
                        "footer_cm": 2.0
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
                        "paper_name": "A4",
                        "gutter_cm": 0,
                        "header_cm": 1.5,
                        "footer_cm": 2.0
                    },
                    "headings": [
                        {"level": 1, "font": "SimHei", "size_pt": 15, "bold": True, "alignment": "left"},
                        {"level": 2, "font": "SimHei", "size_pt": 13, "bold": True, "alignment": "left"}
                    ],
                    "body": {
                        "font": "SimSun",
                        "size_pt": 10.5,
                        "line_spacing_pt": 20,
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
                user_id=None,  # System templates have no owner
                config_json=template_data["config"],
                is_default=template_data["is_default"]
            )
            db.add(template)
            print(f"  + {template_data['name']}")

        db.commit()
        print(f"\n✓ Successfully seeded {len(system_templates)} system templates!")

    except Exception as e:
        print(f"❌ Error seeding templates: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main migration function."""
    print("=" * 60)
    print("DocAI Database Migration Script")
    print("=" * 60)
    print(f"\nDatabase: {settings.DATABASE_URL}")

    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")

        # Step 1: Create rule_templates table
        create_rule_templates_table(engine)

        # Step 2: Migrate checks table
        migrate_checks_table(engine)

        # Step 3: Migrate users table
        migrate_users_table(engine)

        # Step 4: Seed system templates
        seed_system_templates()

        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)

    except OperationalError as e:
        print(f"\n❌ Database connection error: {e}")
        print("Please check your database configuration in .env file")
        sys.exit(1)
    except ProgrammingError as e:
        print(f"\n❌ SQL error: {e}")
        print("Please check the SQL statements in the migration script")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
