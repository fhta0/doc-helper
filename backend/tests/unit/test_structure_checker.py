"""
Unit tests for Structure Checker.
"""
import pytest
from app.services.structure_checker import StructureChecker


@pytest.mark.unit
@pytest.mark.service
class TestStructureChecker:
    """Test cases for StructureChecker."""

    @pytest.fixture
    def doc_data_with_toc(self):
        """Document data with table of contents."""
        return {
            "table_of_contents": {
                "exists": True,
                "entries": [
                    {"title": "第一章 概述", "level": 1, "page_number": 1, "paragraph_index": 1},
                    {"title": "第二章 详细说明", "level": 1, "page_number": 5, "paragraph_index": 10}
                ],
                "paragraph_index": 0
            },
            "headings": [
                {"text": "第一章 概述", "level": 1, "paragraph_index": 5},
                {"text": "第二章 详细说明", "level": 1, "paragraph_index": 15}
            ],
            "paragraphs": [
                {"index": 5, "page_number": 1},
                {"index": 15, "page_number": 5}
            ],
            "heading_structure": {}
        }

    @pytest.fixture
    def doc_data_without_toc(self):
        """Document data without table of contents."""
        return {
            "table_of_contents": {
                "exists": False,
                "entries": [],
                "paragraph_index": None
            },
            "headings": [
                {"text": "Introduction", "level": 1, "paragraph_index": 0},
                {"text": "Methods", "level": 1, "paragraph_index": 5}
            ],
            "paragraphs": [
                {"index": 0, "page_number": 1},
                {"index": 5, "page_number": 2}
            ],
            "heading_structure": {}
        }

    def test_init(self, doc_data_with_toc):
        """Test structure checker initialization."""
        checker = StructureChecker(doc_data_with_toc)
        assert checker.doc_data == doc_data_with_toc
        assert checker.toc == doc_data_with_toc["table_of_contents"]
        assert checker.headings == doc_data_with_toc["headings"]

    def test_check_required_sections_all_present(self, doc_data_with_toc):
        """Test checking required sections when all are present."""
        checker = StructureChecker(doc_data_with_toc)
        required = ["概述", "详细说明"]

        issues = checker.check_required_sections(required)
        assert len(issues) == 0

    def test_check_required_sections_missing(self, doc_data_with_toc):
        """Test checking required sections when some are missing."""
        checker = StructureChecker(doc_data_with_toc)
        required = ["概述", "详细说明", "参考文献"]

        issues = checker.check_required_sections(required)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "REQUIRED_SECTION_MISSING"
        assert "参考文献" in issues[0]["error_message"]

    def test_check_toc_body_consistency_matching(self, doc_data_with_toc):
        """Test TOC-body consistency when they match."""
        checker = StructureChecker(doc_data_with_toc)
        issues = checker.check_toc_body_consistency()

        # Should have no issues if TOC and headings match
        toc_entry_issues = [i for i in issues if i["rule_id"] == "TOC_ENTRY_NOT_FOUND"]
        assert len(toc_entry_issues) == 0

    def test_check_toc_body_consistency_missing_toc(self, doc_data_without_toc):
        """Test TOC-body consistency when TOC is missing."""
        checker = StructureChecker(doc_data_without_toc)
        issues = checker.check_toc_body_consistency()

        assert len(issues) > 0
        assert issues[0]["rule_id"] == "TOC_MISSING"

    def test_check_toc_body_consistency_toc_entry_not_in_body(self):
        """Test when TOC entry is not found in body."""
        doc_data = {
            "table_of_contents": {
                "exists": True,
                "entries": [
                    {"title": "Chapter 1", "level": 1, "page_number": 1, "paragraph_index": 1},
                    {"title": "Chapter 2", "level": 1, "page_number": 5, "paragraph_index": 10}
                ],
                "paragraph_index": 0
            },
            "headings": [
                {"text": "Chapter 1", "level": 1, "paragraph_index": 5}
                # Chapter 2 missing from body
            ],
            "paragraphs": [
                {"index": 5, "page_number": 1}
            ],
            "heading_structure": {}
        }

        checker = StructureChecker(doc_data)
        issues = checker.check_toc_body_consistency()

        toc_not_found_issues = [i for i in issues if i["rule_id"] == "TOC_ENTRY_NOT_FOUND"]
        assert len(toc_not_found_issues) > 0

    def test_check_toc_body_consistency_heading_not_in_toc(self):
        """Test when body heading is not in TOC."""
        doc_data = {
            "table_of_contents": {
                "exists": True,
                "entries": [
                    {"title": "Chapter 1", "level": 1, "page_number": 1, "paragraph_index": 1}
                ],
                "paragraph_index": 0
            },
            "headings": [
                {"text": "Chapter 1", "level": 1, "paragraph_index": 5},
                {"text": "Chapter 2", "level": 1, "paragraph_index": 10}  # Not in TOC
            ],
            "paragraphs": [
                {"index": 5, "page_number": 1},
                {"index": 10, "page_number": 2}
            ],
            "heading_structure": {}
        }

        checker = StructureChecker(doc_data)
        issues = checker.check_toc_body_consistency()

        heading_not_in_toc_issues = [i for i in issues if i["rule_id"] == "HEADING_NOT_IN_TOC"]
        assert len(heading_not_in_toc_issues) > 0

    def test_check_heading_hierarchy_no_issues(self):
        """Test heading hierarchy when structure is correct."""
        doc_data = {
            "headings": [
                {"text": "Chapter 1", "level": 1, "paragraph_index": 0},
                {"text": "Section 1.1", "level": 2, "paragraph_index": 1},
                {"text": "Section 1.2", "level": 2, "paragraph_index": 2},
                {"text": "Chapter 2", "level": 1, "paragraph_index": 3}
            ],
            "paragraphs": [
                {"index": 0, "page_number": 1},
                {"index": 1, "page_number": 1},
                {"index": 2, "page_number": 1},
                {"index": 3, "page_number": 2}
            ],
            "table_of_contents": {"exists": False, "entries": []},
            "heading_structure": {}
        }

        checker = StructureChecker(doc_data)
        issues = checker.check_heading_hierarchy()

        assert len(issues) == 0

    def test_check_heading_hierarchy_level_jump(self):
        """Test heading hierarchy with level jumps."""
        doc_data = {
            "headings": [
                {"text": "Chapter 1", "level": 1, "paragraph_index": 0},
                {"text": "Subsection 1.1.1", "level": 3, "paragraph_index": 1},  # Jump from 1 to 3
                {"text": "Chapter 2", "level": 1, "paragraph_index": 2}
            ],
            "paragraphs": [
                {"index": 0, "page_number": 1},
                {"index": 1, "page_number": 1},
                {"index": 2, "page_number": 2}
            ],
            "table_of_contents": {"exists": False, "entries": []},
            "heading_structure": {}
        }

        checker = StructureChecker(doc_data)
        issues = checker.check_heading_hierarchy()

        assert len(issues) > 0
        assert issues[0]["rule_id"] == "HEADING_LEVEL_JUMP"

    def test_normalize_title(self):
        """Test title normalization."""
        doc_data = {
            "headings": [],
            "paragraphs": [],
            "table_of_contents": {"exists": False, "entries": []},
            "heading_structure": {}
        }
        checker = StructureChecker(doc_data)

        # Test removing numbering
        assert checker._normalize_title("一、概述") == "概述"
        assert checker._normalize_title("1. Introduction") == "Introduction"
        assert checker._normalize_title("（一）方法") == "方法"

        # Test removing whitespace and punctuation
        assert checker._normalize_title("第 一 章 概 述") == "第一章概述"

    def test_find_section(self):
        """Test section finding with fuzzy matching."""
        doc_data = {
            "headings": [],
            "paragraphs": [],
            "table_of_contents": {"exists": False, "entries": []},
            "heading_structure": {}
        }
        checker = StructureChecker(doc_data)

        found_sections = {"第一章 项目概述", "第二章 技术说明", "附录A"}

        # Exact match
        assert checker._find_section("项目概述", found_sections) is True

        # Fuzzy match
        assert checker._find_section("概述", found_sections) is True

        # Not found
        assert checker._find_section("参考文献", found_sections) is False

    def test_get_heading_page(self):
        """Test getting page number for heading."""
        # Need to create paragraphs with proper indexing (index = position in array)
        doc_data = {
            "headings": [],
            "paragraphs": [
                {"index": 0, "page_number": 1},
                {"index": 1, "page_number": 1},
                {"index": 2, "page_number": 1},
                {"index": 3, "page_number": 1},
                {"index": 4, "page_number": 1},
                {"index": 5, "page_number": 2},
                {"index": 6, "page_number": 2},
                {"index": 7, "page_number": 2},
                {"index": 8, "page_number": 2},
                {"index": 9, "page_number": 2},
                {"index": 10, "page_number": 3}
            ],
            "table_of_contents": {"exists": False, "entries": []},
            "heading_structure": {}
        }
        checker = StructureChecker(doc_data)

        assert checker._get_heading_page(0) == 1
        assert checker._get_heading_page(5) == 2
        assert checker._get_heading_page(10) == 3
        assert checker._get_heading_page(None) == 1
        assert checker._get_heading_page(100) == 1  # Out of range

    def test_check_toc_level_mismatch(self):
        """Test when TOC and body heading levels don't match."""
        doc_data = {
            "table_of_contents": {
                "exists": True,
                "entries": [
                    {"title": "Chapter 1", "level": 1, "page_number": 1, "paragraph_index": 1}
                ],
                "paragraph_index": 0
            },
            "headings": [
                {"text": "Chapter 1", "level": 2, "paragraph_index": 5}  # Level mismatch
            ],
            "paragraphs": [
                {"index": 5, "page_number": 1}
            ],
            "heading_structure": {}
        }

        checker = StructureChecker(doc_data)
        issues = checker.check_toc_body_consistency()

        level_mismatch_issues = [i for i in issues if i["rule_id"] == "TOC_LEVEL_MISMATCH"]
        assert len(level_mismatch_issues) > 0

    def test_empty_toc_entries(self):
        """Test handling of empty TOC entries."""
        doc_data = {
            "table_of_contents": {
                "exists": True,
                "entries": [],  # Empty TOC
                "paragraph_index": 0
            },
            "headings": [
                {"text": "Chapter 1", "level": 1, "paragraph_index": 5}
            ],
            "paragraphs": [
                {"index": 5, "page_number": 1}
            ],
            "heading_structure": {}
        }

        checker = StructureChecker(doc_data)
        issues = checker.check_toc_body_consistency()

        assert len(issues) > 0
        assert issues[0]["rule_id"] == "TOC_EMPTY"
