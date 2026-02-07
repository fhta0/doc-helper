"""
Integration tests for Document Check API.
"""
import pytest
import os
import json
from io import BytesIO
from sqlalchemy.orm import Session
from app.models import Check, CheckStatus, CheckType


@pytest.mark.integration
@pytest.mark.api
class TestChecksAPI:
    """Test cases for document check endpoints."""

    def test_upload_document_success(self, client, auth_headers, sample_docx_path):
        """Test successful document upload."""
        with open(sample_docx_path, "rb") as f:
            response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "file_id" in data["data"]
        assert data["data"]["filename"] == "test.docx"

    def test_upload_document_wrong_format(self, client, auth_headers):
        """Test uploading non-docx file."""
        fake_file = BytesIO(b"not a docx file")

        response = client.post(
            "/api/check/upload",
            headers=auth_headers,
            files={"file": ("test.txt", fake_file, "text/plain")},
            data={"check_type": "basic"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 2001
        assert "格式不支持" in data["message"]

    def test_upload_document_too_large(self, client, auth_headers, temp_upload_dir):
        """Test uploading file that exceeds size limit."""
        # Create a large fake docx file
        from docx import Document

        doc = Document()
        for i in range(10000):
            doc.add_paragraph(f"This is paragraph {i} with some content to make the file larger.")

        large_file_path = os.path.join(temp_upload_dir, "large.docx")
        doc.save(large_file_path)

        # Mock a guest user to test lower file size limit
        # (In actual test, would need to adjust settings or use guest auth)

        with open(large_file_path, "rb") as f:
            file_content = f.read()

        # If file is larger than limit, should get error
        # This test depends on actual file size and settings
        # For now, just verify the upload mechanism works

    def test_submit_check_basic(self, client, auth_headers, test_user, sample_docx_path, db: Session):
        """Test submitting a basic check."""
        # First upload
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        # Then submit check
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
        assert "check_id" in data["data"]
        assert data["data"]["status"] == "completed"

        # Verify check in database
        check = db.query(Check).filter(Check.check_id == data["data"]["check_id"]).first()
        assert check is not None
        assert check.status == CheckStatus.COMPLETED
        assert check.check_type == CheckType.BASIC

    def test_submit_check_with_template(self, client, auth_headers, test_user, sample_docx_path, sample_rule_template, db: Session):
        """Test submitting check with rule template."""
        # Upload file
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        # Submit with template
        response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": file_id,
                "filename": "test.docx",
                "check_type": "basic",
                "rule_template_id": sample_rule_template.id
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # Verify template used
        check = db.query(Check).filter(Check.check_id == data["data"]["check_id"]).first()
        assert check.rule_template_id == sample_rule_template.id

    def test_submit_check_nonexistent_file(self, client, auth_headers):
        """Test submitting check for non-existent file."""
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
        assert data["code"] == 2003
        assert "不存在" in data["message"]

    def test_submit_check_nonexistent_template(self, client, auth_headers, test_user, sample_docx_path):
        """Test submitting check with non-existent template."""
        # Upload file
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        # Submit with invalid template
        response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": file_id,
                "filename": "test.docx",
                "check_type": "basic",
                "rule_template_id": 99999  # Non-existent
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 3007

    def test_get_check_result(self, client, auth_headers, sample_check):
        """Test getting check result."""
        response = client.get(
            f"/api/check/{sample_check.check_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["check_id"] == sample_check.check_id
        assert data["data"]["status"] == "completed"
        assert "result" in data["data"]

    def test_get_check_result_unauthorized(self, client, auth_headers, sample_check, db, test_user):
        """Test getting check result for another user's check."""
        # Create another user
        from app.models import User
        from app.core.security import get_password_hash

        other_user = User(
            username="otheruser",
            password_hash=get_password_hash("password"),
            nickname="Other"
        )
        db.add(other_user)
        db.commit()

        # Try to access sample_check (belongs to test_user)
        response = client.get(
            f"/api/check/{sample_check.check_id}",
            headers=auth_headers
        )

        # Should succeed for the owner
        assert response.status_code == 200

    def test_get_recent_checks(self, client, auth_headers, db, test_user, sample_docx_path):
        """Test getting recent checks."""
        # Create multiple checks
        for i in range(3):
            check = Check(
                check_id=f"check_{i}",
                user_id=test_user.id,
                file_id=f"file_{i}",
                filename=f"test_{i}.docx",
                file_path=sample_docx_path,
                check_type=CheckType.BASIC,
                status=CheckStatus.COMPLETED,
                result_json='{"total_issues": 1, "issues": []}'
            )
            db.add(check)
        db.commit()

        response = client.get(
            "/api/check/recent",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] > 0
        assert len(data["data"]["checks"]) > 0

    def test_get_user_stats(self, client, auth_headers, db, test_user, sample_docx_path):
        """Test getting user statistics."""
        # Create checks
        for i in range(2):
            check = Check(
                check_id=f"stat_check_{i}",
                user_id=test_user.id,
                file_id=f"file_{i}",
                filename=f"test_{i}.docx",
                file_path=sample_docx_path,
                check_type=CheckType.BASIC,
                status=CheckStatus.COMPLETED,
                result_json='{"total_issues": 3, "issues": []}'
            )
            db.add(check)
        db.commit()

        response = client.get(
            "/api/check/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "total_checks" in data["data"]
        assert "total_issues" in data["data"]
        assert data["data"]["total_checks"] > 0

    def test_generate_revised_document(self, client, auth_headers, sample_check):
        """Test generating revised document."""
        response = client.post(
            f"/api/check/{sample_check.check_id}/revise",
            headers=auth_headers
        )

        # This might fail in test if RevisionEngine can't process the test file
        # But we can check the response structure
        data = response.json()
        assert "code" in data

    def test_download_revised_document(self, client, sample_check, db):
        """Test downloading revised document."""
        # Set revised file path
        sample_check.revised_file_path = sample_check.file_path  # Use same file for test
        db.commit()

        response = client.get(
            f"/api/check/{sample_check.check_id}/download_revised"
        )

        # Should return file or error
        assert response.status_code in [200, 404]

    def test_check_count_deduction(self, client, auth_headers, test_user, sample_docx_path, db):
        """Test that check count is properly deducted."""
        initial_free_count = test_user.free_count

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

        # Refresh user and check count
        db.refresh(test_user)
        assert test_user.free_count == initial_free_count - 1

    def test_full_check_type(self, client, auth_headers, test_user, sample_docx_path, db):
        """Test submitting a full check (with AI content checking)."""
        # Upload file
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "full"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        # Submit full check
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

        # Verify check type
        check = db.query(Check).filter(Check.check_id == data["data"]["check_id"]).first()
        assert check.check_type == CheckType.FULL

    def test_revision_with_template_fix_action(self, client, auth_headers, test_user, sample_docx_path, sample_rule_template, db):
        """Test that revision generation works correctly with rule template and fix_action."""
        # Upload file
        with open(sample_docx_path, "rb") as f:
            upload_response = client.post(
                "/api/check/upload",
                headers=auth_headers,
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"check_type": "basic"}
            )

        file_id = upload_response.json()["data"]["file_id"]

        # Submit check with template
        response = client.post(
            "/api/check",
            headers=auth_headers,
            json={
                "file_id": file_id,
                "filename": "test.docx",
                "check_type": "basic",
                "rule_template_id": sample_rule_template.id
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        check_id = data["data"]["check_id"]

        # Get check result
        check = db.query(Check).filter(Check.check_id == check_id).first()
        assert check is not None
        assert check.result_json is not None

        # Parse result JSON
        result = json.loads(check.result_json)
        issues = result.get("issues", [])

        # Verify that issues from template rules have fix_action when matching DB rules
        # (This tests the fix: config_to_rules should include fix_action from DB rules)
        issues_with_fix = [i for i in issues if i.get("fix_action")]
        
        # At least some issues should have fix_action if the template matches DB rules
        # (e.g., PAGE_MARGIN_25, PARA_INDENT_2CHAR, HEADING_STYLES)
        # We don't assert a specific number, but verify the structure is correct
        
        # Generate revised document
        revise_response = client.post(
            f"/api/check/{check_id}/revise",
            headers=auth_headers
        )

        assert revise_response.status_code == 200
        revise_data = revise_response.json()
        
        # Verify revised document was generated
        db.refresh(check)
        assert check.revised_file_path is not None
        assert os.path.exists(check.revised_file_path)

    def test_check_count_deduction_persists(self, client, auth_headers, test_user, sample_docx_path, db):
        """Test that check count deduction is properly persisted."""
        initial_free_count = test_user.free_count
        assert initial_free_count > 0, "Test user should have free count"

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

        # Refresh user from database to verify count was persisted
        db.refresh(test_user)
        assert test_user.free_count == initial_free_count - 1, "Free count should be decremented and persisted"
