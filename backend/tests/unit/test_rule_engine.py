"""
Unit tests for Rule Engine.
"""
import pytest
from app.services.rule_engine import RuleEngine, config_to_rules


@pytest.mark.unit
@pytest.mark.service
class TestRuleEngine:
    """Test cases for RuleEngine."""

    def test_init(self, sample_rules):
        """Test rule engine initialization."""
        engine = RuleEngine(sample_rules)
        assert engine.rules == sample_rules
        assert engine.ai_checker is None
        assert engine.enable_ai is False

    def test_check_document_sync_no_issues(self, sample_doc_data, sample_rules):
        """Test document checking when no issues found."""
        # Modify doc data to match rule conditions
        sample_doc_data["runs"][1]["font"]["name"] = "SimSun"
        sample_doc_data["runs"][1]["font"]["size_pt"] = 14

        engine = RuleEngine(sample_rules)
        result = engine.check_document_sync(sample_doc_data)

        assert "total_issues" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)

    def test_check_document_sync_with_font_issues(self, sample_doc_data, sample_rules):
        """Test document checking with font issues."""
        # Set wrong font and use Chinese text to trigger font check
        sample_doc_data["runs"][1]["text"] = "这是正文内容"  # Add Chinese text
        sample_doc_data["runs"][1]["font"]["name"] = "Arial"
        sample_doc_data["runs"][1]["font"]["size_pt"] = 12

        engine = RuleEngine(sample_rules)
        result = engine.check_document_sync(sample_doc_data)

        assert result["total_issues"] > 0
        assert len(result["issues"]) > 0

        # Check issue structure
        issue = result["issues"][0]
        assert "rule_id" in issue
        assert "rule_name" in issue
        assert "category" in issue
        assert "error_message" in issue
        assert "suggestion" in issue
        assert "location" in issue

    def test_check_document_sync_with_margin_issues(self, sample_doc_data, sample_rules):
        """Test document checking with margin issues."""
        # Set wrong margins
        sample_doc_data["page_settings"]["margins"]["top_mm"] = 10.0
        sample_doc_data["page_settings"]["margins"]["left_mm"] = 20.0

        engine = RuleEngine(sample_rules)
        result = engine.check_document_sync(sample_doc_data)

        # Should find margin issue
        margin_issues = [i for i in result["issues"] if i["rule_id"] == "MARGIN_CHECK"]
        assert len(margin_issues) > 0

    def test_merge_issues_by_rule(self, sample_doc_data, sample_rules):
        """Test issue merging by rule ID."""
        # Create multiple issues with same rule ID
        issues = [
            {
                "rule_id": "FONT_CHECK",
                "rule_name": "字体检查",
                "category": "font",
                "error_message": "字体错误",
                "suggestion": "修改字体",
                "location": {"type": "paragraph", "index": 1, "description": "第1段"}
            },
            {
                "rule_id": "FONT_CHECK",
                "rule_name": "字体检查",
                "category": "font",
                "error_message": "字体错误",
                "suggestion": "修改字体",
                "location": {"type": "paragraph", "index": 2, "description": "第2段"}
            }
        ]

        engine = RuleEngine(sample_rules)
        merged = engine._merge_issues_by_rule(issues)

        assert len(merged) == 1
        assert merged[0]["rule_id"] == "FONT_CHECK"
        assert len(merged[0]["raw_locations"]) == 2

    def test_match_font_condition(self, sample_rules):
        """Test font condition matching."""
        engine = RuleEngine(sample_rules)

        # Test matching font
        target = {
            "text": "测试文本",
            "font": {"name": "SimSun", "size_pt": 14, "bold": False}
        }
        condition = {"chinese_font": "SimSun", "chinese_size_pt": 14}

        result = engine._match_font_condition(target, condition)
        assert result is True

        # Test non-matching font
        target["font"]["name"] = "Arial"
        result = engine._match_font_condition(target, condition)
        assert result is False

    def test_match_page_condition(self, sample_rules):
        """Test page condition matching."""
        engine = RuleEngine(sample_rules)

        target = {
            "page_settings": {
                "margins": {
                    "top_mm": 25.4,
                    "bottom_mm": 25.4,
                    "left_mm": 31.7,
                    "right_mm": 31.7
                }
            }
        }
        condition = {
            "top_mm": 25.4,
            "bottom_mm": 25.4,
            "left_mm": 31.7,
            "right_mm": 31.7,
            "tolerance_mm": 2
        }

        result = engine._match_page_condition(target, condition)
        assert result is True

        # Test outside tolerance
        target["page_settings"]["margins"]["top_mm"] = 20.0
        result = engine._match_page_condition(target, condition)
        assert result is False

    def test_config_to_rules(self):
        """Test converting config to rules."""
        config = {
            "page": {
                "margins": {
                    "top_cm": 2.5,
                    "bottom_cm": 2.5,
                    "left_cm": 3.0,
                    "right_cm": 2.5
                },
                "paper_name": "A4"
            },
            "body": {
                "font": "SimSun",
                "size_pt": 14,
                "line_spacing_pt": 28,
                "first_line_indent_chars": 2
            },
            "headings": [
                {
                    "level": 1,
                    "font": "SimHei",
                    "size_pt": 18,
                    "bold": True,
                    "alignment": "center"
                }
            ]
        }

        rules = config_to_rules(config)

        assert len(rules) > 0
        assert any(r["category"] == "page" for r in rules)
        assert any(r["category"] == "font" for r in rules)
        assert any(r["category"] == "heading" for r in rules)

    def test_get_check_targets_paragraph(self, sample_doc_data, sample_rules):
        """Test getting paragraph targets."""
        engine = RuleEngine(sample_rules)
        targets = engine._get_check_targets(sample_doc_data, "paragraph")

        assert len(targets) == len(sample_doc_data["paragraphs"])
        assert all(isinstance(t, dict) for t in targets)

    def test_get_check_targets_run(self, sample_doc_data, sample_rules):
        """Test getting run targets."""
        engine = RuleEngine(sample_rules)
        targets = engine._get_check_targets(sample_doc_data, "run")

        assert len(targets) > 0
        assert all("font" in t for t in targets)

    def test_build_location_paragraph(self, sample_rules):
        """Test building location for paragraph."""
        engine = RuleEngine(sample_rules)
        target = {
            "index": 5,
            "page_number": 2,
            "start_line": 10,
            "end_line": 12
        }

        location = engine._build_location(target, "paragraph")

        assert location["type"] == "paragraph"
        assert location["index"] == 5
        assert location["page_number"] == 2
        assert "description" in location

    def test_build_location_heading(self, sample_rules):
        """Test building location for heading."""
        engine = RuleEngine(sample_rules)
        target = {
            "level": 1,
            "text": "Test Heading",
            "paragraph_index": 0
        }

        location = engine._build_location(target, "heading")

        assert location["type"] == "heading"
        assert location["level"] == 1
        assert location["text"] == "Test Heading"
        assert "description" in location

    def test_merge_consecutive_runs(self, sample_rules):
        """Test merging consecutive run locations."""
        engine = RuleEngine(sample_rules)

        run_locs = [
            {"paragraph_index": 1, "description": "第2段"},
            {"paragraph_index": 2, "description": "第3段"},
            {"paragraph_index": 3, "description": "第4段"},
            {"paragraph_index": 5, "description": "第6段"}
        ]

        merged = engine._merge_consecutive_runs(run_locs)

        assert len(merged) == 2  # [1-3] and [5]
        assert "2~4段" in merged[0]  # paragraph_index 1-3 displays as 2-4段
        assert "第6段" in merged[1]  # paragraph_index 5 displays as 第6段

    def test_skip_ai_rules_in_sync_mode(self, sample_doc_data):
        """Test that AI rules are skipped in synchronous mode."""
        rules = [
            {
                "id": "AI_CHECK",
                "name": "AI检查",
                "category": "other",
                "checker": "ai",
                "prompt_template": "Check this document"
            },
            {
                "id": "DETERMINISTIC_CHECK",
                "name": "确定性检查",
                "category": "font",
                "checker": "deterministic",
                "match": "run",
                "condition": {"chinese_font": "SimSun"}
            }
        ]

        engine = RuleEngine(rules)
        result = engine.check_document_sync(sample_doc_data)

        # AI rules should be skipped, so only deterministic issues
        ai_issues = [i for i in result["issues"] if i["rule_id"] == "AI_CHECK"]
        assert len(ai_issues) == 0
