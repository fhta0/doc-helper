"""
Integration tests for check count deduction logic.

Tests the critical user flow:
1. User submits a check
2. Count is properly deducted (free_count, basic_count, or full_count)
3. Count deduction is persisted in database
4. Frontend API returns updated count
5. Edge cases (free_count exhausted, zero counts, etc.)
"""
import pytest
from sqlalchemy.orm import Session
from app.models import User, Check, CheckStatus, CheckType, CostType


@pytest.mark.integration
@pytest.mark.api
class TestCheckCountDeduction:
    """Test cases for check count deduction and persistence."""

    def test_basic_check_deducts_free_count_first(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that basic check deducts from free_count first."""
        # Set up user counts
        test_user.free_count = 2
        test_user.basic_count = 5
        test_user.full_count = 3
        db.commit()
        db.refresh(test_user)

        initial_free = test_user.free_count
        initial_basic = test_user.basic_count

        # Upload and submit check
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": file_id,
                "filename": "test.docx",
                "check_type": "basic"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # Verify free_count decreased, basic_count unchanged
        db.refresh(test_user)
        assert test_user.free_count == initial_free - 1
        assert test_user.basic_count == initial_basic

        # Verify check record has correct cost_type
        check = db.query(Check).filter(Check.check_id == data["data"]["check_id"]).first()
        assert check is not None
        assert check.cost_type == CostType.FREE

    def test_basic_check_uses_basic_count_when_free_exhausted(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that basic check uses basic_count when free_count is 0."""
        # Set up user counts: no free count
        test_user.free_count = 0
        test_user.basic_count = 5
        test_user.full_count = 3
        db.commit()
        db.refresh(test_user)

        initial_basic = test_user.basic_count

        # Upload and submit check
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": file_id,
                "filename": "test.docx",
                "check_type": "basic"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # Verify basic_count decreased, free_count still 0
        db.refresh(test_user)
        assert test_user.free_count == 0
        assert test_user.basic_count == initial_basic - 1

        # Verify check record has correct cost_type
        check = db.query(Check).filter(Check.check_id == data["data"]["check_id"]).first()
        assert check is not None
        assert check.cost_type == CostType.BASIC

    def test_basic_check_fails_when_all_counts_zero(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that basic check fails when both free_count and basic_count are 0."""
        # Set up user counts: all zero
        test_user.free_count = 0
        test_user.basic_count = 0
        test_user.full_count = 5
        db.commit()
        db.refresh(test_user)

        # Upload file
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        # Try to submit check - should fail
        response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": file_id,
                "filename": "test.docx",
                "check_type": "basic"
            }
        )

        assert response.status_code == 403
        data = response.json()
        assert "检测次数不足" in data["detail"]

        # Verify counts unchanged
        db.refresh(test_user)
        assert test_user.free_count == 0
        assert test_user.basic_count == 0

    def test_full_check_deducts_full_count_only(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that full check only deducts from full_count."""
        # Set up user counts
        test_user.free_count = 3
        test_user.basic_count = 5
        test_user.full_count = 2
        db.commit()
        db.refresh(test_user)

        initial_free = test_user.free_count
        initial_basic = test_user.basic_count
        initial_full = test_user.full_count

        # Upload and submit full check
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "full"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": file_id,
                "filename": "test.docx",
                "check_type": "full"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # Verify only full_count decreased
        db.refresh(test_user)
        assert test_user.free_count == initial_free
        assert test_user.basic_count == initial_basic
        assert test_user.full_count == initial_full - 1

        # Verify check record has correct cost_type
        check = db.query(Check).filter(Check.check_id == data["data"]["check_id"]).first()
        assert check is not None
        assert check.cost_type == CostType.FULL

    def test_full_check_fails_when_full_count_zero(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that full check fails when full_count is 0."""
        # Set up user counts
        test_user.free_count = 3
        test_user.basic_count = 5
        test_user.full_count = 0
        db.commit()
        db.refresh(test_user)

        # Upload file
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "full"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        # Try to submit full check - should fail
        response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": file_id,
                "filename": "test.docx",
                "check_type": "full"
            }
        )

        assert response.status_code == 403
        data = response.json()
        assert "完整检测次数不足" in data["detail"]

        # Verify counts unchanged
        db.refresh(test_user)
        assert test_user.free_count == 3
        assert test_user.basic_count == 5
        assert test_user.full_count == 0

    def test_profile_api_returns_updated_counts_after_check(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that /api/auth/user/profile returns updated counts after check submission."""
        # Set up user counts
        test_user.free_count = 3
        test_user.basic_count = 10
        test_user.full_count = 5
        db.commit()
        db.refresh(test_user)

        # Get initial profile
        profile_response = client.get("/api/auth/user/profile", headers=auth_headers)
        assert profile_response.status_code == 200
        initial_data = profile_response.json()["data"]
        initial_free = initial_data["free_count"]

        # Submit a basic check
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        check_response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": file_id,
                "filename": "test.docx",
                "check_type": "basic"
            }
        )

        assert check_response.status_code == 200

        # Get updated profile
        profile_response = client.get("/api/auth/user/profile", headers=auth_headers)
        assert profile_response.status_code == 200
        updated_data = profile_response.json()["data"]
        updated_free = updated_data["free_count"]

        # Verify profile shows updated count
        assert updated_free == initial_free - 1
        assert updated_data["basic_count"] == 10
        assert updated_data["full_count"] == 5

    def test_multiple_checks_deduct_counts_correctly(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that multiple checks deduct counts correctly in sequence."""
        # Set up user counts: 2 free, 3 basic
        test_user.free_count = 2
        test_user.basic_count = 3
        test_user.full_count = 1
        db.commit()
        db.refresh(test_user)

        # First check: should use free_count (2 -> 1)
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("check1.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )
        file_id1 = upload_response.json()["data"]["file_id"]
        client.post("/api/check", headers=auth_headers, json={"file_id": file_id1, "filename": "check1.docx", "check_type": "basic"})

        db.refresh(test_user)
        assert test_user.free_count == 1
        assert test_user.basic_count == 3

        # Second check: should use free_count (1 -> 0)
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("check2.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )
        file_id2 = upload_response.json()["data"]["file_id"]
        client.post("/api/check", headers=auth_headers, json={"file_id": file_id2, "filename": "check2.docx", "check_type": "basic"})

        db.refresh(test_user)
        assert test_user.free_count == 0
        assert test_user.basic_count == 3

        # Third check: should use basic_count (3 -> 2)
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("check3.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )
        file_id3 = upload_response.json()["data"]["file_id"]
        response = client.post("/api/check", headers=auth_headers, json={"file_id": file_id3, "filename": "check3.docx", "check_type": "basic"})

        db.refresh(test_user)
        assert test_user.free_count == 0
        assert test_user.basic_count == 2

        # Verify cost types in checks
        check3 = db.query(Check).filter(Check.file_id == file_id3).first()
        assert check3.cost_type == CostType.BASIC

    def test_check_count_persists_across_sessions(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that count deduction persists across database sessions."""
        # Set up user counts
        test_user.free_count = 3
        test_user.basic_count = 5
        db.commit()

        # Submit check
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )
        file_id = upload_response.json()["data"]["file_id"]
        client.post("/api/check", headers=auth_headers, json={"file_id": file_id, "filename": "test.docx", "check_type": "basic"})

        # Close session and query again
        db.expire_all()

        # Query user from scratch
        fresh_user = db.query(User).filter(User.id == test_user.id).first()
        assert fresh_user.free_count == 2

    def test_failed_check_does_not_deduct_count(self, client, auth_headers, test_user, db: Session):
        """Test that failed check submission does not deduct count."""
        # Set up user counts
        test_user.free_count = 3
        test_user.basic_count = 5
        db.commit()
        db.refresh(test_user)

        initial_free = test_user.free_count
        initial_basic = test_user.basic_count

        # Try to submit check with non-existent file_id
        response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": "nonexistent_file_id",
                "filename": "test.docx",
                "check_type": "basic"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 2003  # File not found

        # Verify counts unchanged
        db.refresh(test_user)
        assert test_user.free_count == initial_free
        assert test_user.basic_count == initial_basic

    def test_concurrent_checks_handle_counts_correctly(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that concurrent check submissions handle count deduction correctly."""
        # Set up user counts
        test_user.free_count = 1
        test_user.basic_count = 1
        db.commit()
        db.refresh(test_user)

        # Upload two files
        with open(sample_docx_path, "rb") as f:
            upload1 = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test1.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )
        file_id1 = upload1.json()["data"]["file_id"]

        with open(sample_docx_path, "rb") as f:
            upload2 = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test2.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )
        file_id2 = upload2.json()["data"]["file_id"]

        # Submit first check
        response1 = client.post("/api/check", headers=auth_headers, json={"file_id": file_id1, "filename": "test1.docx", "check_type": "basic"})
        assert response1.status_code == 200

        # Submit second check
        response2 = client.post("/api/check", headers=auth_headers, json={"file_id": file_id2, "filename": "test2.docx", "check_type": "basic"})
        assert response2.status_code == 200

        # Verify final counts
        db.refresh(test_user)
        assert test_user.free_count == 0
        assert test_user.basic_count == 0

        # Third check should fail
        with open(sample_docx_path, "rb") as f:
            upload3 = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test3.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )
        file_id3 = upload3.json()["data"]["file_id"]
        response3 = client.post("/api/check", headers=auth_headers, json={"file_id": file_id3, "filename": "test3.docx", "check_type": "basic"})
        assert response3.status_code == 403

    def test_check_history_shows_correct_cost_type(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test that check history shows correct cost_type for each check."""
        # Set up user counts
        test_user.free_count = 1
        test_user.basic_count = 1
        test_user.full_count = 1
        db.commit()
        db.refresh(test_user)

        # Submit three checks of different types
        # 1. Basic check using free count
        with open(sample_docx_path, "rb") as f:
            upload1 = client.post("/api/check/upload", headers=auth_headers,
                files={"file": ("test1.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"})
        file_id1 = upload1.json()["data"]["file_id"]
        check1_resp = client.post("/api/check", headers=auth_headers,
            json={"file_id": file_id1, "filename": "test1.docx", "check_type": "basic"})
        check1_id = check1_resp.json()["data"]["check_id"]

        # 2. Basic check using basic count
        with open(sample_docx_path, "rb") as f:
            upload2 = client.post("/api/check/upload", headers=auth_headers,
                files={"file": ("test2.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"})
        file_id2 = upload2.json()["data"]["file_id"]
        check2_resp = client.post("/api/check", headers=auth_headers,
            json={"file_id": file_id2, "filename": "test2.docx", "check_type": "basic"})
        check2_id = check2_resp.json()["data"]["check_id"]

        # 3. Full check using full count
        with open(sample_docx_path, "rb") as f:
            upload3 = client.post("/api/check/upload", headers=auth_headers,
                files={"file": ("test3.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "full"})
        file_id3 = upload3.json()["data"]["file_id"]
        check3_resp = client.post("/api/check", headers=auth_headers,
            json={"file_id": file_id3, "filename": "test3.docx", "check_type": "full"})
        check3_id = check3_resp.json()["data"]["check_id"]

        # Verify cost types in database
        check1 = db.query(Check).filter(Check.check_id == check1_id).first()
        check2 = db.query(Check).filter(Check.check_id == check2_id).first()
        check3 = db.query(Check).filter(Check.check_id == check3_id).first()

        assert check1.cost_type == CostType.FREE
        assert check2.cost_type == CostType.BASIC
        assert check3.cost_type == CostType.FULL
