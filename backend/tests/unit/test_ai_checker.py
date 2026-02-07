"""
Unit tests for AI Checker.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.ai_checker import AIChecker


@pytest.mark.unit
@pytest.mark.service
class TestAIChecker:
    """Test cases for AIChecker."""

    def test_init_with_defaults(self):
        """Test initialization with default settings."""
        with patch("app.services.ai_checker.settings") as mock_settings:
            mock_settings.AI_BASE_URL = "https://api.example.com"
            mock_settings.AI_API_KEY = "test_key"
            mock_settings.AI_MODEL = "gpt-3.5-turbo"

            checker = AIChecker()

            assert checker.base_url == "https://api.example.com"
            assert checker.api_key == "test_key"
            assert checker.model == "gpt-3.5-turbo"

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        checker = AIChecker(
            base_url="https://custom.api.com",
            api_key="custom_key",
            model="custom-model",
            timeout=120
        )

        assert checker.base_url == "https://custom.api.com"
        assert checker.api_key == "custom_key"
        assert checker.model == "custom-model"
        assert checker.timeout == 120

    def test_is_enabled_with_api_key(self):
        """Test that checker is enabled when API key is present."""
        checker = AIChecker(api_key="test_key")
        assert checker.is_enabled() is True

    def test_is_enabled_without_api_key(self):
        """Test that checker is disabled when API key is missing."""
        # Use empty string to simulate missing API key
        # (None would use settings default, which is not what we want to test)
        checker = AIChecker(api_key="")
        assert checker.is_enabled() is False

    def test_build_prompt(self):
        """Test prompt building from template."""
        checker = AIChecker(api_key="test_key")
        doc_data = {
            "info": {"filename": "test.docx"},
            "paragraphs": [
                {"text": "First paragraph"},
                {"text": "Second paragraph"}
            ],
            "headings": [
                {"level": 1, "text": "Chapter 1"}
            ]
        }

        template = "Check this document: {doc_info}\nParagraphs: {paragraphs}"
        prompt = checker._build_prompt(doc_data, template)

        assert "test.docx" in prompt
        assert "First paragraph" in prompt

    def test_extract_document_context(self):
        """Test extracting context from document data."""
        checker = AIChecker(api_key="test_key")
        doc_data = {
            "info": {"filename": "test.docx"},
            "paragraphs": [
                {"text": "First paragraph"},
                {"text": "Second paragraph"}
            ],
            "headings": [
                {"level": 1, "text": "Chapter 1"}
            ]
        }

        context = checker._extract_document_context(doc_data)

        assert "doc_info" in context
        assert "paragraphs" in context
        assert "headings" in context
        assert "paragraphs_count" in context
        assert context["paragraphs_count"] == 2
        assert context["headings_count"] == 1

    @pytest.mark.asyncio
    async def test_call_ai_api_success(self):
        """Test successful AI API call."""
        checker = AIChecker(
            base_url="https://api.example.com",
            api_key="test_key",
            model="gpt-3.5-turbo"
        )

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"issues": []}'
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.json.return_value = mock_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await checker._call_ai_api("Test prompt")

            assert result == '{"issues": []}'
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_ai_api_with_proper_headers(self):
        """Test that API call includes proper headers."""
        checker = AIChecker(
            base_url="https://api.example.com",
            api_key="test_key"
        )

        mock_response = {
            "choices": [{"message": {"content": "test"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.json.return_value = mock_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await checker._call_ai_api("Test")

            call_args = mock_client.post.call_args
            headers = call_args[1]["headers"]

            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer test_key"
            assert headers["Content-Type"] == "application/json"

    def test_parse_ai_response_json_array(self):
        """Test parsing AI response as JSON array."""
        checker = AIChecker(api_key="test_key")
        rule = {
            "id": "TEST_RULE",
            "name": "Test Rule",
            "category": "test"
        }

        response_text = '''[
            {
                "error_message": "Issue 1",
                "suggestion": "Fix 1",
                "location": {"type": "paragraph", "description": "Para 1"}
            }
        ]'''

        issues = checker._parse_ai_response(response_text, rule)

        assert len(issues) == 1
        assert issues[0]["rule_id"] == "TEST_RULE"
        assert issues[0]["error_message"] == "Issue 1"

    def test_parse_ai_response_json_with_code_block(self):
        """Test parsing AI response with markdown code block."""
        checker = AIChecker(api_key="test_key")
        rule = {"id": "TEST", "name": "Test", "category": "test"}

        response_text = '''```json
        [
            {"error_message": "Issue", "suggestion": "Fix"}
        ]
        ```'''

        issues = checker._parse_ai_response(response_text, rule)

        assert len(issues) == 1

    def test_parse_ai_response_json_object_with_issues_key(self):
        """Test parsing AI response as object with issues key."""
        checker = AIChecker(api_key="test_key")
        rule = {"id": "TEST", "name": "Test", "category": "test"}

        response_text = '''{
            "issues": [
                {"error_message": "Issue 1"},
                {"error_message": "Issue 2"}
            ]
        }'''

        issues = checker._parse_ai_response(response_text, rule)

        assert len(issues) == 2

    def test_parse_ai_response_invalid_json(self):
        """Test handling of invalid JSON response."""
        checker = AIChecker(api_key="test_key")
        rule = {"id": "TEST", "name": "Test", "category": "test"}

        response_text = "This is not JSON"

        issues = checker._parse_ai_response(response_text, rule)

        # Should handle gracefully, not crash
        assert isinstance(issues, list)

    def test_parse_ai_response_fallback_with_chinese(self):
        """Test fallback parsing when JSON fails but response contains Chinese."""
        checker = AIChecker(api_key="test_key")
        rule = {"id": "TEST", "name": "Test", "category": "test"}

        response_text = "发现问题：格式不正确"

        issues = checker._parse_ai_response(response_text, rule)

        assert len(issues) == 1
        assert "问题" in issues[0]["error_message"] or "问题" in issues[0]["suggestion"]

    def test_create_issue_from_ai_item(self):
        """Test creating issue from AI response item."""
        checker = AIChecker(api_key="test_key")
        rule = {
            "id": "TEST_RULE",
            "name": "Test Rule",
            "category": "test",
            "error_message": "Default error",
            "suggestion": "Default suggestion"
        }

        item = {
            "error_message": "Custom error",
            "suggestion": "Custom suggestion",
            "location": {"type": "paragraph", "description": "Para 1"}
        }

        issue = checker._create_issue_from_ai_item(item, rule)

        assert issue["rule_id"] == "TEST_RULE"
        assert issue["error_message"] == "Custom error"
        assert issue["suggestion"] == "Custom suggestion"
        assert issue["location"]["type"] == "paragraph"

    def test_create_issue_from_ai_item_with_defaults(self):
        """Test creating issue with default values."""
        checker = AIChecker(api_key="test_key")
        rule = {
            "id": "TEST_RULE",
            "name": "Test Rule",
            "category": "test",
            "error_message": "Default error",
            "suggestion": "Default suggestion"
        }

        item = {}  # Empty item

        issue = checker._create_issue_from_ai_item(item, rule)

        assert issue["error_message"] == "Default error"
        assert issue["suggestion"] == "Default suggestion"
        assert issue["location"]["type"] == "document"

    @pytest.mark.asyncio
    async def test_check_rule_disabled_checker(self):
        """Test that check_rule returns empty list when checker is disabled."""
        checker = AIChecker(api_key="")  # Disabled
        doc_data = {"paragraphs": []}
        rule = {"id": "TEST", "prompt_template": "Check this"}

        issues = await checker.check_rule(doc_data, rule)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_check_rule_missing_prompt_template(self):
        """Test handling of missing prompt template."""
        checker = AIChecker(api_key="test_key")
        doc_data = {"paragraphs": []}
        rule = {"id": "TEST"}  # No prompt_template

        issues = await checker.check_rule(doc_data, rule)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_check_rule_api_error_handling(self):
        """Test that API errors don't crash the check."""
        checker = AIChecker(api_key="test_key")
        doc_data = {"paragraphs": [], "headings": [], "info": {}}
        rule = {"id": "TEST", "prompt_template": "Check: {doc_info}"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("API Error")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            issues = await checker.check_rule(doc_data, rule)

            # Should return empty list on error, not crash
            assert isinstance(issues, list)
            assert len(issues) == 0

    def test_factory_function(self):
        """Test create_ai_checker factory function."""
        from app.services.ai_checker import create_ai_checker

        with patch("app.services.ai_checker.settings") as mock_settings:
            mock_settings.AI_BASE_URL = "https://api.test.com"
            mock_settings.AI_API_KEY = "key"
            mock_settings.AI_MODEL = "model"

            checker = create_ai_checker()

            assert isinstance(checker, AIChecker)
            assert checker.base_url == "https://api.test.com"
