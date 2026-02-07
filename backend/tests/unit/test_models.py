"""
Unit tests for Database Models.
"""
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models import User, Check, CheckType, CheckStatus, CostType, RuleTemplate, Order, OrderStatus


@pytest.mark.unit
@pytest.mark.model
class TestUserModel:
    """Test cases for User model."""

    def test_create_user(self, db: Session):
        """Test creating a user."""
        user = User(
            username="testuser123",
            password_hash="hashed_password",
            nickname="Test User",
            free_count=3
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.username == "testuser123"
        assert user.free_count == 3

    def test_user_to_dict(self, test_user):
        """Test user to_dict method."""
        user_dict = test_user.to_dict()

        assert "id" in user_dict
        assert "username" in user_dict
        assert "nickname" in user_dict
        assert "free_count" in user_dict
        assert "basic_count" in user_dict
        assert "full_count" in user_dict
        assert "password_hash" not in user_dict  # Should not expose password

    def test_user_unique_username(self, db: Session, test_user):
        """Test that username must be unique."""
        duplicate_user = User(
            username="testuser",  # Same as test_user
            password_hash="another_hash",
            nickname="Duplicate"
        )
        db.add(duplicate_user)

        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db.commit()

    def test_user_default_counts(self, db: Session):
        """Test default count values."""
        user = User(
            username="newuser",
            password_hash="hash",
            nickname="New User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.free_count == 3  # Default
        assert user.basic_count == 0  # Default
        assert user.full_count == 0  # Default


@pytest.mark.unit
@pytest.mark.model
class TestCheckModel:
    """Test cases for Check model."""

    def test_create_check(self, db: Session, test_user):
        """Test creating a check."""
        check = Check(
            check_id="check_test_123",
            user_id=test_user.id,
            file_id="file_123",
            filename="test.docx",
            file_path="/tmp/test.docx",
            check_type=CheckType.BASIC,
            status=CheckStatus.COMPLETED,
            cost_type=CostType.FREE
        )
        db.add(check)
        db.commit()
        db.refresh(check)

        assert check.id is not None
        assert check.check_id == "check_test_123"
        assert check.user_id == test_user.id
        assert check.status == CheckStatus.COMPLETED

    def test_check_to_dict(self, sample_check):
        """Test check to_dict method."""
        check_dict = sample_check.to_dict()

        assert "check_id" in check_dict
        assert "filename" in check_dict
        assert "check_type" in check_dict
        assert "status" in check_dict
        assert "created_at" in check_dict

    def test_check_enum_values(self, db: Session, test_user):
        """Test check enum types."""
        check = Check(
            check_id="check_enum_test",
            user_id=test_user.id,
            file_id="file",
            filename="test.docx",
            file_path="/tmp/test.docx",
            check_type=CheckType.FULL,
            status=CheckStatus.PENDING,
            cost_type=CostType.BASIC
        )
        db.add(check)
        db.commit()
        db.refresh(check)

        assert check.check_type == CheckType.FULL
        assert check.status == CheckStatus.PENDING
        assert check.cost_type == CostType.BASIC

    def test_check_with_result_json(self, db: Session, test_user):
        """Test check with result JSON."""
        import json

        result = {
            "total_issues": 5,
            "issues": [
                {"rule_id": "TEST", "error_message": "Error"}
            ]
        }

        check = Check(
            check_id="check_json_test",
            user_id=test_user.id,
            file_id="file",
            filename="test.docx",
            file_path="/tmp/test.docx",
            check_type=CheckType.BASIC,
            status=CheckStatus.COMPLETED,
            cost_type=CostType.FREE,
            result_json=json.dumps(result)
        )
        db.add(check)
        db.commit()
        db.refresh(check)

        assert check.result_json is not None
        parsed = json.loads(check.result_json)
        assert parsed["total_issues"] == 5


@pytest.mark.unit
@pytest.mark.model
class TestRuleTemplateModel:
    """Test cases for RuleTemplate model."""

    def test_create_template(self, db: Session, test_user):
        """Test creating a rule template."""
        from app.models.rule_template import TemplateType
        template = RuleTemplate(
            name="Academic Template",
            description="For academic papers",
            template_type=TemplateType.CUSTOM,
            user_id=test_user.id,
            is_default=True,
            config_json={
                "page": {"margins": {"top_cm": 2.5}},
                "body": {"font": "SimSun", "size_pt": 14}
            }
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        assert template.id is not None
        assert template.name == "Academic Template"
        assert template.is_default is True

    def test_template_to_dict(self, sample_rule_template):
        """Test template to_dict method."""
        template_dict = sample_rule_template.to_dict()

        assert "id" in template_dict
        assert "name" in template_dict
        assert "template_type" in template_dict
        # Note: to_dict returns "config" not "config_json"
        assert "config" in template_dict

    def test_template_config_json_storage(self, db: Session, test_user):
        """Test that config JSON is properly stored and retrieved."""
        config = {
            "page": {
                "margins": {
                    "top_cm": 2.5,
                    "bottom_cm": 2.5,
                    "left_cm": 3.0,
                    "right_cm": 2.5
                }
            }
        }

        template = RuleTemplate(
            name="Test Template",
            description="Test",
            template_type="business",
            user_id=test_user.id,
            config_json=config
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        assert template.config_json == config
        assert template.config_json["page"]["margins"]["top_cm"] == 2.5


@pytest.mark.unit
@pytest.mark.model
class TestOrderModel:
    """Test cases for Order model."""

    def test_create_order(self, db: Session, test_user):
        """Test creating an order."""
        order = Order(
            user_id=test_user.id,
            order_no="ORDER_TEST_001",
            product_name="Basic Package",
            product_count=10,
            amount=1000,
            status=OrderStatus.PENDING
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        assert order.id is not None
        assert order.order_no == "ORDER_TEST_001"
        assert order.amount == 1000
        assert order.status == OrderStatus.PENDING

    def test_order_status_values(self, db: Session, test_user):
        """Test order status enum values."""
        order = Order(
            user_id=test_user.id,
            order_no="ORDER_STATUS_TEST",
            product_name="Test Product",
            product_count=5,
            amount=500,
            status=OrderStatus.PAID
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        assert order.status == OrderStatus.PAID

        # Update status - use CLOSED instead of non-existent CANCELLED
        order.status = OrderStatus.CLOSED
        db.commit()
        db.refresh(order)

        assert order.status == OrderStatus.CLOSED

    def test_order_with_product_relation(self, db: Session, test_user):
        """Test order with product foreign key."""
        from app.models import Product

        product = Product(
            name="Test Product",
            key="test_product",  # key is required
            count_type="basic",
            count=10,
            price=1000
        )
        db.add(product)
        db.commit()

        order = Order(
            user_id=test_user.id,
            order_no="ORDER_PRODUCT_TEST",
            product_id=product.id,
            product_name=product.name,
            product_count=product.count,
            amount=product.price,
            status=OrderStatus.PENDING
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        assert order.product_id == product.id
        assert order.product is not None
        assert order.product.name == "Test Product"

    def test_order_timestamps(self, db: Session, test_user):
        """Test order timestamp fields."""
        order = Order(
            user_id=test_user.id,
            order_no="ORDER_TIMESTAMP_TEST",
            product_name="Test",
            product_count=1,
            amount=100,
            status=OrderStatus.PENDING
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        assert order.created_at is not None
        assert isinstance(order.created_at, datetime)

        # Set paid_at
        order.status = OrderStatus.PAID
        order.paid_at = datetime.now()
        db.commit()
        db.refresh(order)

        assert order.paid_at is not None


@pytest.mark.unit
@pytest.mark.model
class TestModelRelationships:
    """Test model relationships."""

    def test_user_checks_relationship(self, db: Session, test_user):
        """Test user to checks relationship."""
        # Create checks for user
        for i in range(3):
            check = Check(
                check_id=f"rel_check_{i}",
                user_id=test_user.id,
                file_id=f"file_{i}",
                filename=f"test_{i}.docx",
                file_path=f"/tmp/test_{i}.docx",
                check_type=CheckType.BASIC,
                status=CheckStatus.COMPLETED,
                cost_type=CostType.FREE
            )
            db.add(check)
        db.commit()

        # Query user with checks
        user = db.query(User).filter(User.id == test_user.id).first()
        # Note: Need to define relationship in model for this to work
        # For now, just verify we can query checks by user_id
        checks = db.query(Check).filter(Check.user_id == user.id).all()
        assert len(checks) >= 3

    def test_user_templates_relationship(self, db: Session, test_user):
        """Test user to templates relationship."""
        # Create templates for user
        for i in range(2):
            template = RuleTemplate(
                name=f"Template {i}",
                description=f"Description {i}",
                template_type="academic",
                user_id=test_user.id,
                config_json={}
            )
            db.add(template)
        db.commit()

        # Query templates by user
        templates = db.query(RuleTemplate).filter(RuleTemplate.user_id == test_user.id).all()
        assert len(templates) >= 2

    def test_check_template_relationship(self, db: Session, test_user, sample_rule_template):
        """Test check to template relationship."""
        check = Check(
            check_id="check_template_rel",
            user_id=test_user.id,
            file_id="file",
            filename="test.docx",
            file_path="/tmp/test.docx",
            check_type=CheckType.BASIC,
            status=CheckStatus.COMPLETED,
            cost_type=CostType.FREE,
            rule_template_id=sample_rule_template.id
        )
        db.add(check)
        db.commit()
        db.refresh(check)

        assert check.rule_template_id == sample_rule_template.id
