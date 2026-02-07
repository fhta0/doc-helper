"""
Structure Checker for Document Structure Validation
Checks document structure including TOC consistency and required sections.
"""
from typing import Dict, List, Any, Optional
import re


class StructureChecker:
    """Document structure integrity checker."""

    def __init__(self, doc_data: Dict[str, Any]):
        """
        Initialize the structure checker.

        Args:
            doc_data: Parsed document data from DocxParser
        """
        self.doc_data = doc_data
        self.toc = doc_data.get("table_of_contents", {})
        self.headings = doc_data.get("headings", [])
        self.heading_structure = doc_data.get("heading_structure", {})
        self.paragraphs = doc_data.get("paragraphs", [])

    def check_required_sections(self, required: List[str]) -> List[Dict[str, Any]]:
        """
        Check if required sections exist in the document.

        Args:
            required: List of required section names

        Returns:
            List of issues for missing sections
        """
        issues = []
        found_sections = set()

        # Extract section names from headings
        for heading in self.headings:
            text = heading.get("text", "").strip()
            if text:
                found_sections.add(text)

        # Check for missing sections
        for section in required:
            if not self._find_section(section, found_sections):
                issues.append({
                    "rule_id": "REQUIRED_SECTION_MISSING",
                    "rule_name": f"缺少必要章节：{section}",
                    "category": "structure",
                    "error_message": f"文档中未找到必要章节：{section}",
                    "suggestion": f"请在文档中添加章节：{section}",
                    "location": {
                        "type": "document",
                        "description": "文档结构",
                        "page_number": 1
                    }
                })

        return issues

    def _find_section(self, section_name: str, found_sections: set) -> bool:
        """
        Check if a section exists, with fuzzy matching.

        Args:
            section_name: Name of the section to find
            found_sections: Set of found section names

        Returns:
            True if section found, False otherwise
        """
        normalized_target = self._normalize_title(section_name)

        for found in found_sections:
            normalized_found = self._normalize_title(found)
            if normalized_target == normalized_found:
                return True
            # Check if target is a substring of found (e.g., "项目概述" matches "一、项目概述")
            if normalized_target in normalized_found or normalized_found in normalized_target:
                return True

        return False

    def check_toc_body_consistency(self) -> List[Dict[str, Any]]:
        """
        Check consistency between table of contents and body headings.

        Returns:
            List of issues for inconsistencies
        """
        issues = []

        # Check if TOC exists
        if not self.toc.get("exists"):
            issues.append({
                "rule_id": "TOC_MISSING",
                "rule_name": "缺少目录",
                "category": "structure",
                "error_message": "文档中未找到目录",
                "suggestion": "请添加目录",
                "location": {
                    "type": "document",
                    "description": "文档前部",
                    "page_number": 1
                }
            })
            return issues

        # Get TOC entries and body headings
        toc_entries = self.toc.get("entries", [])
        body_headings = self.headings.copy()

        if not toc_entries:
            issues.append({
                "rule_id": "TOC_EMPTY",
                "rule_name": "目录为空",
                "category": "structure",
                "error_message": "目录中没有条目",
                "suggestion": "请确保目录包含所有主要章节",
                "location": {
                    "type": "toc",
                    "description": "目录",
                    "page_number": 1
                }
            })
            return issues

        # Extract TOC titles and body titles
        toc_titles = {}
        for entry in toc_entries:
            title = entry.get("title", "").strip()
            if title:
                normalized = self._normalize_title(title)
                toc_titles[normalized] = {
                    "original": title,
                    "level": entry.get("level", 1),
                    "page_number": entry.get("page_number"),
                    "entry": entry
                }

        body_titles = {}
        for heading in body_headings:
            text = heading.get("text", "").strip()
            if text:
                normalized = self._normalize_title(text)
                body_titles[normalized] = {
                    "original": text,
                    "level": heading.get("level", 1),
                    "paragraph_index": heading.get("paragraph_index"),
                    "heading": heading
                }

        # Check 1: TOC entries should exist in body
        for normalized_toc, toc_data in toc_titles.items():
            found = False
            matching_body = None

            for normalized_body, body_data in body_titles.items():
                if normalized_toc == normalized_body:
                    found = True
                    matching_body = body_data
                    break

            if not found:
                # Try fuzzy matching
                for normalized_body, body_data in body_titles.items():
                    if normalized_toc in normalized_body or normalized_body in normalized_toc:
                        found = True
                        matching_body = body_data
                        break

            if not found:
                issues.append({
                    "rule_id": "TOC_ENTRY_NOT_FOUND",
                    "rule_name": "目录条目在正文中不存在",
                    "category": "structure",
                    "error_message": f"目录中的\"{toc_data['original']}\"在正文中未找到对应标题",
                    "suggestion": f"请检查目录，确保\"{toc_data['original']}\"在正文中存在对应的标题",
                    "location": {
                        "type": "toc",
                        "description": f"目录条目：{toc_data['original']}",
                        "page_number": 1
                    }
                })
            elif matching_body:
                # Check level consistency
                toc_level = toc_data.get("level", 1)
                body_level = matching_body.get("level", 1)
                if toc_level != body_level:
                    issues.append({
                        "rule_id": "TOC_LEVEL_MISMATCH",
                        "rule_name": "目录层级与正文不一致",
                        "category": "structure",
                        "error_message": f"目录中的\"{toc_data['original']}\"层级({toc_level}级)与正文中的层级({body_level}级)不一致",
                        "suggestion": f"请检查目录和正文中\"{toc_data['original']}\"的层级设置，确保一致",
                        "location": {
                            "type": "heading",
                            "text": toc_data['original'],
                            "paragraph_index": matching_body.get("paragraph_index"),
                            "page_number": self._get_heading_page(matching_body.get("paragraph_index"))
                        }
                    })

        # Check 2: Main headings (level 1) in body should be in TOC
        level_1_headings = [h for h in body_headings if h.get("level") == 1]
        for heading in level_1_headings:
            title = heading.get("text", "").strip()
            if not title:
                continue

            normalized_title = self._normalize_title(title)
            found_in_toc = False

            for normalized_toc in toc_titles.keys():
                if normalized_title == normalized_toc:
                    found_in_toc = True
                    break
                # Try fuzzy matching
                if normalized_title in normalized_toc or normalized_toc in normalized_title:
                    found_in_toc = True
                    break

            if not found_in_toc:
                issues.append({
                    "rule_id": "HEADING_NOT_IN_TOC",
                    "rule_name": "正文标题未出现在目录中",
                    "category": "structure",
                    "error_message": f"正文中的一级标题\"{title}\"未出现在目录中",
                    "suggestion": f"请在目录中添加\"{title}\"",
                    "location": {
                        "type": "heading",
                        "text": title,
                        "paragraph_index": heading.get("paragraph_index"),
                        "page_number": self._get_heading_page(heading.get("paragraph_index"))
                    }
                })

        return issues

    def check_heading_hierarchy(self) -> List[Dict[str, Any]]:
        """
        Check heading hierarchy consistency.

        Returns:
            List of issues for hierarchy problems
        """
        issues = []
        headings = self.headings.copy()

        if len(headings) < 2:
            return issues

        # Check for level jumps (e.g., Heading 1 -> Heading 3, skipping Heading 2)
        for i in range(1, len(headings)):
            prev_level = headings[i - 1].get("level", 1)
            curr_level = headings[i].get("level", 1)

            # Skip if current level is 1 (new top-level section)
            if curr_level == 1:
                continue

            # Check if level jumps too much
            if curr_level > prev_level + 1:
                issues.append({
                    "rule_id": "HEADING_LEVEL_JUMP",
                    "rule_name": "标题层级跳跃",
                    "category": "structure",
                    "error_message": f"标题层级从{prev_level}级跳转到{curr_level}级，中间缺少{prev_level + 1}级标题",
                    "suggestion": f"请在\"{headings[i-1].get('text')}\"和\"{headings[i].get('text')}\"之间添加{prev_level + 1}级标题",
                    "location": {
                        "type": "heading",
                        "text": headings[i].get("text"),
                        "paragraph_index": headings[i].get("paragraph_index"),
                        "page_number": self._get_heading_page(headings[i].get("paragraph_index"))
                    }
                })

        return issues

    def _normalize_title(self, title: str) -> str:
        """
        Normalize title text for comparison.

        Args:
            title: Title text to normalize

        Returns:
            Normalized title string
        """
        # Remove all whitespace, punctuation, and common prefixes
        # Remove common numbering patterns: "一、", "1.", "（一）" etc.
        normalized = title.strip()

        # Remove common numbering prefixes
        normalized = re.sub(r'^[一二三四五六七八九十]+[、.]', '', normalized)
        normalized = re.sub(r'^\d+[、.]', '', normalized)
        normalized = re.sub(r'^[（(]\s*[一二三四五六七八九十]+[）)]', '', normalized)
        normalized = re.sub(r'^[（(]\s*\d+[）)]', '', normalized)

        # Remove all whitespace and punctuation
        normalized = re.sub(r'[\s　]+', '', normalized)
        normalized = re.sub(r'[，。、；：！？]', '', normalized)

        return normalized

    def _get_heading_page(self, paragraph_index: Optional[int]) -> int:
        """
        Get page number for a heading by paragraph index.

        Args:
            paragraph_index: Index of the paragraph containing the heading

        Returns:
            Page number (default 1 if not found)
        """
        if paragraph_index is None:
            return 1

        if paragraph_index < len(self.paragraphs):
            return self.paragraphs[paragraph_index].get("page_number", 1)

        return 1
