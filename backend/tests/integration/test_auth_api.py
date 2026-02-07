"""
Integration tests for Authentication API.
"""
import pytest
from sqlalchemy.orm import Session
from app.models import User


@pytest.mark.integration
@pytest.mark.api
class TestAuthAPI:
    """Test cases for authentication endpoints."""

    def test_register_success(self, client, db: Session):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "password": "password123",
                "nickname": "New User"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert "user" in data["data"]
        assert data["data"]["user"]["username"] == "newuser"

        # Verify user created in database
        user = db.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.nickname == "New User"
        assert user.free_count == 3

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with existing username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",  # Already exists
                "password": "password123",
                "nickname": "Duplicate"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
        assert "已存在" in data["message"]

    def test_register_with_guest_migration(self, client, db: Session, guest_user):
        """Test registration with guest data migration."""
        # Create a check for guest user
        from app.models import Check, CheckType, CheckStatus, CostType

        guest_check = Check(
            check_id="guest_check_123",
            user_id=guest_user.id,
            file_id="file_123",
            filename="guest_file.docx",
            file_path="/tmp/guest_file.docx",
            check_type=CheckType.BASIC,
            status=CheckStatus.COMPLETED,
            cost_type=CostType.FREE
        )
        db.add(guest_check)
        db.commit()

        response = client.post(
            "/api/auth/register",
            json={
                "username": "registered_user",
                "password": "password123",
                "nickname": "Registered User",
                "guest_username": "guest_test123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # Verify guest data migrated
        new_user = db.query(User).filter(User.username == "registered_user").first()
        migrated_checks = db.query(Check).filter(Check.user_id == new_user.id).all()
        assert len(migrated_checks) > 0

        # Verify guest user deleted
        guest = db.query(User).filter(User.username == "guest_test123").first()
        assert guest is None

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert "user" in data["data"]

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1001
        assert "密码错误" in data["message"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1001

    def test_get_profile_authenticated(self, client, auth_headers, test_user):
        """Test getting user profile when authenticated."""
        response = client.get(
            "/api/auth/user/profile",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == "testuser"
        assert data["data"]["nickname"] == "Test User"
        assert "free_count" in data["data"]
        assert "basic_count" in data["data"]
        assert "full_count" in data["data"]

    def test_get_profile_unauthenticated(self, client):
        """Test getting profile without authentication."""
        response = client.get("/api/auth/user/profile")

        # Should return 401 or 403
        assert response.status_code in [401, 403]

    def test_get_profile_with_last_template(self, client, auth_headers, test_user, sample_rule_template, db):
        """Test getting profile with last used template."""
        # Set last template
        test_user.last_template_id = sample_rule_template.id
        db.commit()

        response = client.get(
            "/api/auth/user/profile",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["last_template"] is not None
        assert data["data"]["last_template"]["id"] == sample_rule_template.id
        assert data["data"]["last_template"]["name"] == "测试模板"

    def test_get_user_orders_empty(self, client, auth_headers):
        """Test getting user orders when none exist."""
        response = client.get(
            "/api/auth/user/orders",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] == 0
        assert len(data["data"]["orders"]) == 0

    def test_get_user_orders_with_pagination(self, client, auth_headers, test_user, db):
        """Test getting user orders with pagination."""
        from app.models import Order, OrderStatus

        # Create some orders
        for i in range(15):
            order = Order(
                user_id=test_user.id,
                order_no=f"ORDER_{i:03d}",
                product_name="Test Product",
                product_count=10,
                amount=1000,
                status=OrderStatus.PAID
            )
            db.add(order)
        db.commit()

        # Get first page
        response = client.get(
            "/api/auth/user/orders?page=1&page_size=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 15
        assert len(data["data"]["orders"]) == 10

        # Get second page
        response = client.get(
            "/api/auth/user/orders?page=2&page_size=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["orders"]) == 5

    def test_login_with_guest_migration(self, client, db, test_user, guest_user):
        """Test login with guest data migration."""
        from app.models import Check, CheckType, CheckStatus, CostType

        # Create guest check
        guest_check = Check(
            check_id="guest_check_456",
            user_id=guest_user.id,
            file_id="file_456",
            filename="guest_file2.docx",
            file_path="/tmp/guest_file2.docx",
            check_type=CheckType.BASIC,
            status=CheckStatus.COMPLETED,
            cost_type=CostType.FREE
        )
        db.add(guest_check)
        db.commit()

        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123",
                "guest_username": "guest_test123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # Verify migration
        checks = db.query(Check).filter(Check.user_id == test_user.id).all()
        assert len(checks) > 0

        guest = db.query(User).filter(User.username == "guest_test123").first()
        assert guest is None

    def test_profile_quota_calculation(self, client, auth_headers, test_user, db):
        """Test that profile correctly calculates quota usage."""
        from app.models import Order, Product, OrderStatus

        # Create a paid order
        product = Product(
            name="Basic Package",
            key="basic_package",  # key is required
            count_type="basic",
            count=10,
            price=1000
        )
        db.add(product)
        db.commit()

        order = Order(
            user_id=test_user.id,
            order_no="ORDER_TEST",
            product_id=product.id,
            product_name=product.name,
            product_count=10,
            amount=1000,
            status=OrderStatus.PAID
        )
        db.add(order)
        db.commit()

        response = client.get(
            "/api/auth/user/profile",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        quota = data["data"]["quota"]
        assert "basic" in quota
        assert quota["basic"]["total"] == 10
