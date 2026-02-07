"""
Unit tests for AI Content Checker.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.ai_content_checker import AIContentChecker


@pytest.mark.unit
@pytest.mark.service
class TestAIContentChecker:
    """Test cases for AIContentChecker."""

    def test_init_with_defaults(self):
        """Test initialization with default settings."""
        with patch("app.services.ai_content_checker.settings") as mock_settings:
            mock_settings.AI_BASE_URL = "https://api.example.com"
            mock_settings.AI_API_KEY = "test_key"
            mock_settings.AI_MODEL = "gpt-3.5-turbo"

            checker = AIContentChecker()

            assert checker.base_url == "https://api.example.com"
            assert checker.api_key == "test_key"
            assert checker.model == "gpt-3.5-turbo"

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        checker = AIContentChecker(
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
        checker = AIContentChecker(api_key="test_key")
        assert checker.is_enabled() is True

    def test_is_enabled_without_api_key(self):
        """Test that checker is disabled when API key is missing."""
        # Use empty string to simulate missing API key
        checker = AIContentChecker(api_key="")
        assert checker.is_enabled() is False

    @pytest.mark.asyncio
    async def test_check_all_disabled(self):
        """Test check_all when checker is disabled."""
        checker = AIContentChecker(api_key="")
        doc_data = {"paragraphs": []}

        result = await checker.check_all(doc_data)

        assert result["spell_check"]["enabled"] is False
        assert result["cross_ref_check"]["enabled"] is False
        assert len(result["spell_check"]["issues"]) == 0
        assert len(result["cross_ref_check"]["issues"]) == 0

    @pytest.mark.asyncio
    async def test_check_all_with_enabled_checks(self):
        """Test check_all with specific enabled checks."""
        checker = AIContentChecker(api_key="test_key")
        doc_data = {
            "paragraphs": [
                {"index": 0, "text": "测试文本", "page_number": 1, "start_line": 1}
            ],
            "headings": [],
            "tables": [],
            "figures": []
        }

        with patch.object(checker, "_check_spelling") as mock_spell:
            with patch.object(checker, "_check_cross_references") as mock_cross:
                mock_spell.return_value = []
                mock_cross.return_value = []

                result = await checker.check_all(doc_data, enabled_checks=["spell_check"])

                assert result["spell_check"]["enabled"] is True
                assert result["cross_ref_check"]["enabled"] is False
                mock_spell.assert_called_once()
                mock_cross.assert_not_called()

    def test_extract_references_with_figure_patterns(self):
        """Test extracting figure references from text."""
        checker = AIContentChecker(api_key="test_key")

        text = "如图1所示，详见图1-1和图2.1，还有表1和表2-1。"
        refs = checker._extract_references(text)

        assert len(refs) > 0
        assert any("图" in ref or "表" in ref for ref in refs)

    def test_extract_references_with_english_patterns(self):
        """Test extracting English figure references."""
        checker = AIContentChecker(api_key="test_key")

        text = "See Figure 1 and Table 2 for details."
        refs = checker._extract_references(text)

        assert len(refs) > 0
        assert any("Figure" in ref or "Table" in ref for ref in refs)

    def test_format_paragraphs_for_spell_check(self):
        """Test formatting paragraphs for spell check."""
        checker = AIContentChecker(api_key="test_key")

        paragraphs = [
            {"index": 0, "text": "第一段内容"},
            {"index": 1, "text": "第二段内容"},
            {"index": 2, "text": ""}  # Empty paragraph
        ]

        formatted = checker._format_paragraphs_for_spell_check(paragraphs, 0)

        assert "[0] 第一段内容" in formatted
        assert "[1] 第二段内容" in formatted
        assert "[2]" not in formatted  # Empty paragraph should be skipped

    def test_extract_json_from_plain_json_array(self):
        """Test extracting JSON from plain JSON array."""
        checker = AIContentChecker(api_key="test_key")

        json_text = '[{"key": "value"}, {"key2": "value2"}]'
        result = checker._extract_json(json_text)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["key"] == "value"

    def test_extract_json_from_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        checker = AIContentChecker(api_key="test_key")

        json_text = '''```json
        [{"error": "test"}]
        ```'''
        result = checker._extract_json(json_text)

        assert isinstance(result, list)
        assert len(result) == 1

    def test_extract_json_from_mixed_content(self):
        """Test extracting JSON from text with extra content."""
        checker = AIContentChecker(api_key="test_key")

        json_text = 'Here are the issues: [{"issue": "test"}] and more text.'
        result = checker._extract_json(json_text)

        assert isinstance(result, list)
        assert result[0]["issue"] == "test"

    def test_extract_json_with_nested_objects(self):
        """Test extracting nested JSON structures."""
        checker = AIContentChecker(api_key="test_key")

        json_text = '[{"outer": {"inner": "value"}}]'
        result = checker._extract_json(json_text)

        assert isinstance(result, list)
        assert result[0]["outer"]["inner"] == "value"

    def test_extract_json_returns_none_for_invalid(self):
        """Test that invalid JSON returns None."""
        checker = AIContentChecker(api_key="test_key")

        invalid_texts = [
            "",
            "not json at all",
            "{incomplete",
            "[{broken: json}]"
        ]

        for text in invalid_texts:
            result = checker._extract_json(text)
            assert result is None

    def test_extract_json_array_with_brackets(self):
        """Test _extract_json_array method."""
        checker = AIContentChecker(api_key="test_key")

        text = 'Some text [{"a": 1}] more text'
        result = checker._extract_json_array(text)

        assert result == '[{"a": 1}]'

    def test_extract_json_array_with_nested_brackets(self):
        """Test _extract_json_array with nested brackets."""
        checker = AIContentChecker(api_key="test_key")

        text = '[{"array": [1, 2, 3]}, {"b": 2}]'
        result = checker._extract_json_array(text)

        assert result == '[{"array": [1, 2, 3]}, {"b": 2}]'

    def test_extract_json_object(self):
        """Test _extract_json_object method."""
        checker = AIContentChecker(api_key="test_key")

        text = 'Text before {"key": "value"} text after'
        result = checker._extract_json_object(text)

        assert result == '{"key": "value"}'

    def test_parse_spell_check_response_valid(self):
        """Test parsing valid spell check response."""
        checker = AIContentChecker(api_key="test_key")

        response = '''[
            {
                "position": 0,
                "original": "错误字",
                "correction": "正确字",
                "reason": "这是错别字",
                "paragraph_index": 0
            }
        ]'''

        paragraphs = [
            {"index": 0, "text": "包含错误字的文本", "page_number": 1, "start_line": 1}
        ]

        issues = checker._parse_spell_check_response(response, paragraphs, 0)

        assert len(issues) == 1
        assert issues[0]["rule_id"] == "AI_SPELL_CHECK"
        assert issues[0]["rule_name"] == "错别字检测"
        assert "错误字" in issues[0]["error_message"]
        assert "正确字" in issues[0]["suggestion"]
        assert issues[0]["fix_action"] == "replace_text"
        assert issues[0]["fix_params"]["original"] == "错误字"
        assert issues[0]["fix_params"]["correction"] == "正确字"

    def test_parse_spell_check_response_empty(self):
        """Test parsing empty spell check response."""
        checker = AIContentChecker(api_key="test_key")

        response = '[]'
        paragraphs = []

        issues = checker._parse_spell_check_response(response, paragraphs, 0)

        assert len(issues) == 0

    def test_parse_spell_check_response_invalid_json(self):
        """Test parsing invalid spell check response."""
        checker = AIContentChecker(api_key="test_key")

        response = 'not valid json'
        paragraphs = []

        issues = checker._parse_spell_check_response(response, paragraphs, 0)

        # Should handle gracefully
        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_get_cross_ref_error_message(self):
        """Test generating cross reference error messages."""
        checker = AIContentChecker(api_key="test_key")

        assert "不存在" in checker._get_cross_ref_error_message({"type": "missing_ref"})
        assert "格式" in checker._get_cross_ref_error_message({"type": "invalid_format"})
        assert "不连续" in checker._get_cross_ref_error_message({"type": "discontinuous"})

    def test_rule_based_cross_ref_check_missing_ref(self):
        """Test rule-based cross reference check for missing references."""
        checker = AIContentChecker(api_key="test_key")

        all_refs = [
            {"text": "图1", "paragraph_index": 0, "location": "第1页第1行"},
            {"text": "图5", "paragraph_index": 1, "location": "第1页第2行"}  # Does not exist
        ]
        existing_figures = ["图1", "图2", "图3"]
        existing_tables = []

        issues = checker._rule_based_cross_ref_check(all_refs, existing_figures, existing_tables)

        # Should find issue with 图5
        assert len(issues) > 0
        missing_issues = [i for i in issues if "图5" in i["error_message"]]
        assert len(missing_issues) > 0

    def test_parse_cross_ref_response_valid(self):
        """Test parsing valid cross reference response."""
        checker = AIContentChecker(api_key="test_key")

        response = '''[
            {
                "type": "missing_ref",
                "reference": "图99",
                "suggestion": "删除或修改为正确的图表编号"
            }
        ]'''

        all_refs = [
            {"text": "图99", "paragraph_index": 5, "location": "第2页第10行"}
        ]

        issues = checker._parse_cross_ref_response(response, all_refs)

        assert len(issues) == 1
        assert issues[0]["rule_id"] == "AI_CROSS_REF_CHECK"
        assert "不存在" in issues[0]["error_message"]

    def test_convert_to_standard_issues(self):
        """Test converting AI results to standard issues."""
        checker = AIContentChecker(api_key="test_key")

        ai_results = {
            "spell_check": {
                "enabled": True,
                "issues": [
                    {"rule_id": "AI_SPELL_CHECK", "error_message": "Test"}
                ]
            },
            "cross_ref_check": {
                "enabled": True,
                "issues": [
                    {"rule_id": "AI_CROSS_REF_CHECK", "error_message": "Test2"}
                ]
            }
        }

        issues = checker.convert_to_standard_issues(ai_results)

        assert len(issues) == 2
        assert issues[0]["rule_id"] == "AI_SPELL_CHECK"
        assert issues[1]["rule_id"] == "AI_CROSS_REF_CHECK"

    def test_convert_to_standard_issues_disabled_checks(self):
        """Test converting with disabled checks."""
        checker = AIContentChecker(api_key="test_key")

        ai_results = {
            "spell_check": {
                "enabled": False,
                "issues": [{"rule_id": "AI_SPELL_CHECK"}]
            },
            "cross_ref_check": {
                "enabled": True,
                "issues": [{"rule_id": "AI_CROSS_REF_CHECK"}]
            }
        }

        issues = checker.convert_to_standard_issues(ai_results)

        # Only cross_ref_check should be included
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "AI_CROSS_REF_CHECK"

    @pytest.mark.asyncio
    async def test_call_ai_api_success(self):
        """Test successful AI API call."""
        checker = AIContentChecker(
            base_url="https://api.example.com",
            api_key="test_key",
            model="gpt-3.5-turbo"
        )

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "[]"
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

            result = await checker._call_ai_api("Test prompt", "Test system", temperature=0.5)

            assert result == "[]"
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_ai_api_timeout(self):
        """Test AI API call timeout handling."""
        checker = AIContentChecker(api_key="test_key")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            import httpx
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await checker._call_ai_api("Test", "Test", timeout=1)

            assert result == ""

    @pytest.mark.asyncio
    async def test_call_ai_api_http_error(self):
        """Test AI API HTTP error handling."""
        checker = AIContentChecker(api_key="test_key")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            import httpx
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Server error"
            error = httpx.HTTPStatusError("Error", request=Mock(), response=mock_response)
            mock_client.post.side_effect = error
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await checker._call_ai_api("Test", "Test")

            assert result == ""

    @pytest.mark.asyncio
    async def test_call_ai_api_without_key(self):
        """Test that API call is skipped without key."""
        checker = AIContentChecker(api_key="")

        result = await checker._call_ai_api("Test", "Test")

        assert result == ""

    @pytest.mark.asyncio
    async def test_check_spelling_with_batching(self):
        """Test spell checking with paragraph batching."""
        checker = AIContentChecker(api_key="test_key")

        # Create more than 30 paragraphs to test batching
        paragraphs = [
            {"index": i, "text": f"段落{i}内容", "page_number": 1, "start_line": i}
            for i in range(35)
        ]

        doc_data = {"paragraphs": paragraphs}

        with patch.object(checker, "_call_ai_api") as mock_api:
            mock_api.return_value = "[]"

            issues = await checker._check_spelling(doc_data)

            # Should make 2 API calls (30 + 5 paragraphs)
            assert mock_api.call_count == 2

    @pytest.mark.asyncio
    async def test_check_cross_references_no_refs(self):
        """Test cross reference check when no references exist."""
        checker = AIContentChecker(api_key="test_key")

        doc_data = {
            "paragraphs": [{"index": 0, "text": "没有任何引用的文本"}],
            "headings": [],
            "tables": [],
            "figures": []
        }

        issues = await checker._check_cross_references(doc_data)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_check_cross_references_with_refs(self):
        """Test cross reference check with references."""
        checker = AIContentChecker(api_key="test_key")

        doc_data = {
            "paragraphs": [
                {"index": 0, "text": "如图1所示", "page_number": 1, "start_line": 1}
            ],
            "headings": [],
            "tables": [],
            "figures": [{"index": 0}]
        }

        with patch.object(checker, "_call_ai_api") as mock_api:
            mock_api.return_value = "[]"

            issues = await checker._check_cross_references(doc_data)

            mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_cross_references_api_error_fallback(self):
        """Test cross reference check falls back to rule-based on API error."""
        checker = AIContentChecker(api_key="test_key")

        doc_data = {
            "paragraphs": [
                {"index": 0, "text": "如图99所示", "page_number": 1, "start_line": 1}
            ],
            "headings": [],
            "tables": [],
            "figures": [{"index": 0}]
        }

        with patch.object(checker, "_call_ai_api") as mock_api:
            mock_api.side_effect = Exception("API Error")

            issues = await checker._check_cross_references(doc_data)

            # Should use rule-based fallback and find the missing reference
            assert len(issues) > 0

    def test_factory_function(self):
        """Test create_ai_content_checker factory function."""
        from app.services.ai_content_checker import create_ai_content_checker

        with patch("app.services.ai_content_checker.settings") as mock_settings:
            mock_settings.AI_BASE_URL = "https://api.test.com"
            mock_settings.AI_API_KEY = "key"
            mock_settings.AI_MODEL = "model"

            checker = create_ai_content_checker()

            assert isinstance(checker, AIContentChecker)
            assert checker.base_url == "https://api.test.com"
