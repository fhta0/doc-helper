"""
Rule Engine for Document Format Checking
Executes rules against parsed document data to find format issues.
"""
from typing import Dict, List, Any, Optional
import re
from app.services.docx_parser import contains_chinese, contains_english


class RuleEngine:
    """Engine for executing format checking rules."""

    def __init__(self, rules: List[Dict[str, Any]], ai_checker: Optional[Any] = None, enable_ai: bool = False):
        """
        Initialize the rule engine.

        Args:
            rules: List of rule dictionaries
            ai_checker: Optional AI checker instance for AI rules
            enable_ai: Whether to enable AI rule checking
        """
        self.rules = rules
        self.ai_checker = ai_checker
        self.enable_ai = enable_ai

    async def check_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check a document against all rules.

        Args:
            doc_data: Parsed document data from DocxParser

        Returns:
            Dictionary with total_issues and list of issues
        """
        issues = []
        ai_issues = []

        for rule in self.rules:
            checker_type = rule.get("checker", "deterministic")

            # Handle deterministic rules
            if checker_type == "deterministic":
                rule_issues = self._check_rule(rule, doc_data)
                issues.extend(rule_issues)

            # Handle AI rules (only if enabled and ai_checker is available)
            elif checker_type == "ai":
                if self.enable_ai and self.ai_checker and self.ai_checker.is_enabled():
                    rule_issues = await self.ai_checker.check_rule(doc_data, rule)
                    ai_issues.extend(rule_issues)
                # If AI not enabled, skip AI rules silently

            # Handle hybrid rules (deterministic + AI)
            elif checker_type == "hybrid":
                # Run deterministic check first
                rule_issues = self._check_rule(rule, doc_data)
                issues.extend(rule_issues)

                # Then run AI check if enabled
                if self.enable_ai and self.ai_checker and self.ai_checker.is_enabled():
                    ai_rule_issues = await self.ai_checker.check_rule(doc_data, rule)
                    ai_issues.extend(ai_rule_issues)

        # Combine all issues
        all_issues = issues + ai_issues

        # Group issues by rule_id and merge locations
        merged_issues = self._merge_issues_by_rule(all_issues)

        return {
            "total_issues": len(merged_issues),
            "issues": merged_issues
        }

    def check_document_sync(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check a document against all rules (synchronous, no AI).

        Args:
            doc_data: Parsed document data from DocxParser

        Returns:
            Dictionary with total_issues and list of issues
        """
        import logging
        logger = logging.getLogger(__name__)
        
        issues = []

        for rule in self.rules:
            # Skip AI-only rules in sync mode
            if rule.get("checker") == "ai":
                continue

            rule_issues = self._check_rule(rule, doc_data)
            
            # Debug: Log rule fix_action
            if rule_issues:
                logger.debug(f"Rule {rule.get('id')} found {len(rule_issues)} issues, fix_action={rule.get('fix_action')}")
                for issue in rule_issues[:2]:  # Log first 2 issues
                    logger.debug(f"  Issue fix_action: {issue.get('fix_action')}")
            
            issues.extend(rule_issues)

        # Group issues by rule_id and merge locations
        merged_issues = self._merge_issues_by_rule(issues)
        
        # Debug: Log merged issues
        for merged in merged_issues:
            logger.debug(f"Merged issue {merged.get('rule_id')}: fix_action={merged.get('fix_action')}")

        return {
            "total_issues": len(merged_issues),
            "issues": merged_issues
        }

    def _merge_issues_by_rule(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge issues with the same rule_id, combining all locations.

        Args:
            issues: List of issue dictionaries

        Returns:
            List of merged issue dictionaries
        """
        # Group by rule_id
        grouped = {}
        for issue in issues:
            rule_id = issue["rule_id"]
            if rule_id not in grouped:
                grouped[rule_id] = {
                    "rule_id": issue["rule_id"],
                    "rule_name": issue["rule_name"],
                    "category": issue["category"],
                    "error_message": issue["error_message"],
                    "suggestion": issue["suggestion"],
                    "fix_action": issue.get("fix_action"),
                    "fix_params": issue.get("fix_params"),
                    "locations": []
                }
            grouped[rule_id]["locations"].append(issue["location"])

        # Build merged issues
        merged = []
        for rule_id, issue_data in grouped.items():
            merged_issue = {
                "rule_id": issue_data["rule_id"],
                "rule_name": issue_data["rule_name"],
                "category": issue_data["category"],
                "error_message": issue_data["error_message"],
                "suggestion": issue_data["suggestion"],
                "fix_action": issue_data.get("fix_action"),
                "fix_params": issue_data.get("fix_params"),
                "location": self._merge_locations(issue_data["locations"]),
                "locations_list": self._build_locations_list(issue_data["locations"]),
                "raw_locations": issue_data["locations"]
            }
            merged.append(merged_issue)

        return merged

    def _merge_locations(self, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple locations into a single description (for summary).

        Args:
            locations: List of location dictionaries

        Returns:
            Merged location dictionary with summary description
        """
        if not locations:
            return {"type": "unknown", "description": "未知位置"}

        count = len(locations)
        return {
            "type": "merged",
            "description": f"共{count}处位置",
            "count": count
        }

    def _build_locations_list(self, locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build a list of locations grouped by page for frontend display.
        Consecutive locations are merged for better readability.

        Args:
            locations: List of location dictionaries

        Returns:
            List of grouped location dictionaries with merged consecutive locations
        """
        if not locations:
            return []

        # Group locations by page number
        pages = {}
        for loc in locations:
            page = loc.get("page_number", 1)
            if page not in pages:
                pages[page] = []
            pages[page].append(loc)

        # Build list grouped by page
        result = []
        for page in sorted(pages.keys()):
            page_locs = pages[page]

            # Separate by type
            run_locs = [loc for loc in page_locs if loc.get("type") == "run"]
            para_locs = [loc for loc in page_locs if loc.get("type") == "paragraph"]
            figure_locs = [loc for loc in page_locs if loc.get("type") == "figure"]
            other_locs = [loc for loc in page_locs if loc.get("type") not in ("run", "paragraph", "figure")]

            all_items = []

            # Process run type - merge consecutive paragraphs
            if run_locs:
                run_locs_sorted = sorted(run_locs, key=lambda x: x.get("paragraph_index", 0))
                merged_run = self._merge_consecutive_runs(run_locs_sorted)
                all_items.extend(merged_run)

            # Process paragraph type - merge consecutive paragraphs
            if para_locs:
                para_locs_sorted = sorted(para_locs, key=lambda x: x.get("index", 0))
                merged_para = self._merge_consecutive_paragraphs(para_locs_sorted)
                all_items.extend(merged_para)

            # Process figure type - merge consecutive figures
            if figure_locs:
                figure_locs_sorted = sorted(figure_locs, key=lambda x: x.get("index", 0))
                merged_figures = self._merge_consecutive_figures(figure_locs_sorted)
                all_items.extend(merged_figures)

            # Process other types - no merging
            for loc in other_locs:
                all_items.append(loc.get("description", ""))

            # Limit display items
            display_items = all_items[:20]
            has_more = len(all_items) > 20

            result.append({
                "page": page,
                "items": display_items,
                "all_items": all_items,
                "total": len(page_locs),
                "has_more": has_more
            })

        return result

    def _merge_consecutive_runs(self, run_locs: List[Dict[str, Any]]) -> List[str]:
        """
        Merge consecutive run locations by paragraph index.

        Args:
            run_locs: List of run location dictionaries sorted by paragraph_index

        Returns:
            List of merged location strings
        """
        if not run_locs:
            return []

        # Sort and deduplicate by paragraph_index
        sorted_locs = sorted(run_locs, key=lambda x: x.get("paragraph_index", 0))
        seen_indices = set()
        unique_locs = []
        for loc in sorted_locs:
            idx = loc.get("paragraph_index", 0)
            if idx not in seen_indices:
                seen_indices.add(idx)
                unique_locs.append(loc)

        merged = []
        i = 0

        while i < len(unique_locs):
            start_idx = unique_locs[i].get("paragraph_index", 0)
            j = i + 1

            # Find consecutive paragraph indices
            while j < len(unique_locs):
                next_idx = unique_locs[j].get("paragraph_index", 0)
                if next_idx == start_idx + (j - i):
                    j += 1
                else:
                    break

            # Generate merged string
            if j - i >= 3:
                # Merge 3 or more consecutive
                end_idx = unique_locs[j - 1].get("paragraph_index", 0)
                merged.append(f"第{start_idx + 1}~{end_idx + 1}段")
            else:
                # Show individually
                for k in range(i, j):
                    idx = unique_locs[k].get("paragraph_index", 0)
                    merged.append(f"第{idx + 1}段")

            i = j

        return merged

    def _merge_consecutive_paragraphs(self, para_locs: List[Dict[str, Any]]) -> List[str]:
        """
        Merge consecutive paragraph locations by index and line numbers.

        Args:
            para_locs: List of paragraph location dictionaries sorted by index

        Returns:
            List of merged location strings
        """
        if not para_locs:
            return []

        # Deduplicate by index (keep first occurrence)
        seen_indices = set()
        unique_locs = []
        for loc in para_locs:
            idx = loc.get("index", 0)
            if idx not in seen_indices:
                seen_indices.add(idx)
                unique_locs.append(loc)

        merged = []
        i = 0

        while i < len(unique_locs):
            start_idx = unique_locs[i].get("index", 0)
            start_line = unique_locs[i].get("start_line", 1)
            end_line = unique_locs[i].get("end_line", start_line)
            j = i + 1

            # Find consecutive indices with consecutive line numbers
            while j < len(unique_locs):
                next_idx = unique_locs[j].get("index", 0)
                next_start = unique_locs[j].get("start_line", 1)
                next_end = unique_locs[j].get("end_line", next_start)

                # Check if paragraphs are consecutive and line numbers are also consecutive
                if next_idx == start_idx + (j - i) and next_start == end_line + 1:
                    end_line = next_end
                    j += 1
                else:
                    break

            # Generate merged string
            if j - i >= 3:
                # Merge 3 or more consecutive
                if start_line == end_line:
                    merged.append(f"第{start_idx + 1}~{unique_locs[j - 1].get('index', 0) + 1}段(第{start_line}行)")
                else:
                    merged.append(f"第{start_idx + 1}~{unique_locs[j - 1].get('index', 0) + 1}段(第{start_line}~{end_line}行)")
            else:
                # Show individually
                for k in range(i, j):
                    idx = unique_locs[k].get("index", 0)
                    s = unique_locs[k].get("start_line", 1)
                    e = unique_locs[k].get("end_line", s)
                    if s == e:
                        merged.append(f"第{idx + 1}段(第{s}行)")
                    else:
                        merged.append(f"第{idx + 1}段({s}~{e}行)")

            i = j

        return merged

    def _merge_consecutive_figures(self, figure_locs: List[Dict[str, Any]]) -> List[str]:
        """
        Merge consecutive figure/table locations by index.

        Args:
            figure_locs: List of figure location dictionaries sorted by index

        Returns:
            List of merged location strings
        """
        if not figure_locs:
            return []

        # Sort and deduplicate by index
        sorted_locs = sorted(figure_locs, key=lambda x: x.get("index", 0))
        seen_indices = set()
        unique_locs = []
        for loc in sorted_locs:
            idx = loc.get("index", 0)
            if idx not in seen_indices:
                seen_indices.add(idx)
                unique_locs.append(loc)

        merged = []
        i = 0

        while i < len(unique_locs):
            start_idx = unique_locs[i].get("index", 0)
            j = i + 1

            # Find consecutive indices
            while j < len(unique_locs):
                next_idx = unique_locs[j].get("index", 0)
                if next_idx == start_idx + (j - i):
                    j += 1
                else:
                    break

            # Generate merged string
            if j - i >= 3:
                # Merge 3 or more consecutive
                end_idx = unique_locs[j - 1].get("index", 0)
                merged.append(f"第{start_idx + 1}~{end_idx + 1}个图表")
            else:
                # Show individually
                for k in range(i, j):
                    idx = unique_locs[k].get("index", 0)
                    merged.append(f"第{idx + 1}个图表")

            i = j

        return merged

    def _check_rule(self, rule: Dict[str, Any], doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check a single rule against the document.

        Args:
            rule: Rule dictionary
            doc_data: Parsed document data

        Returns:
            List of issues found by this rule
        """
        # Handle structure checking rules
        category = rule.get("category")
        if category == "structure":
            return self._check_structure_rule(rule, doc_data)

        issues = []
        match_type = rule.get("match", "document")
        condition = rule.get("condition", {})

        # Get target data based on match type (pass category for filtering)
        targets = self._get_check_targets(doc_data, match_type, category)

        # Check each target
        for target in targets:
            if not self._match_condition(target, condition, category, match_type):
                issue = self._create_issue(rule, target, match_type)
                issues.append(issue)

        # For run type rules, aggregate issues by paragraph to reduce duplicates
        if match_type == "run" and issues:
            issues = self._aggregate_run_issues_by_paragraph(issues, doc_data)

        return issues

    def _check_structure_rule(self, rule: Dict[str, Any], doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check structure-related rules.

        Args:
            rule: Rule dictionary
            doc_data: Parsed document data

        Returns:
            List of issues found by this rule
        """
        from app.services.structure_checker import StructureChecker

        checker = StructureChecker(doc_data)
        rule_id = rule.get("id")
        condition = rule.get("condition", {})

        issues = []

        if rule_id == "REQUIRED_SECTIONS_CHECK":
            required = condition.get("required_sections", [])
            if required:
                issues = checker.check_required_sections(required)

        elif rule_id == "TOC_BODY_CONSISTENCY":
            issues = checker.check_toc_body_consistency()

        elif rule_id == "HEADING_HIERARCHY_CHECK":
            issues = checker.check_heading_hierarchy()

        # Ensure all issues have required rule fields
        for issue in issues:
            issue.setdefault("rule_id", rule.get("id"))
            issue.setdefault("rule_name", rule.get("name", ""))
            issue.setdefault("category", rule.get("category", "structure"))
            issue.setdefault("error_message", rule.get("error_message", ""))
            issue.setdefault("suggestion", rule.get("suggestion", ""))
            # Include fix_action and fix_params from rule if available
            if "fix_action" not in issue:
                issue["fix_action"] = rule.get("fix_action")
            if "fix_params" not in issue:
                issue["fix_params"] = rule.get("fix_params")

        return issues

    def _aggregate_run_issues_by_paragraph(
        self,
        run_issues: List[Dict[str, Any]],
        doc_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate run-level issues to paragraph level.

        This reduces duplicate issues when multiple runs in the same paragraph
        all have the same formatting issue (e.g., wrong font).

        Args:
            run_issues: List of issues from run-level checking
            doc_data: Full document data

        Returns:
            List of aggregated issues at paragraph level
        """
        if not run_issues:
            return []

        # Group issues by paragraph_index
        para_issues = {}
        for issue in run_issues:
            para_idx = issue["location"].get("paragraph_index", 0)
            if para_idx not in para_issues:
                # Store first issue for this paragraph
                para_issues[para_idx] = {
                    "rule_id": issue["rule_id"],
                    "rule_name": issue["rule_name"],
                    "category": issue["category"],
                    "error_message": issue["error_message"],
                    "suggestion": issue["suggestion"],
                    "fix_action": issue.get("fix_action"),
                    "fix_params": issue.get("fix_params"),
                    "paragraph_index": para_idx,
                    "run_count": 0
                }
            para_issues[para_idx]["run_count"] += 1

        # Build aggregated issues with paragraph-level location
        aggregated = []
        paragraphs = doc_data.get("paragraphs", [])

        for para_idx, issue_data in para_issues.items():
            # Get paragraph data if available
            if para_idx < len(paragraphs):
                para = paragraphs[para_idx]
                location = {
                    "type": "paragraph",
                    "index": para_idx,
                    "page_number": para.get("page_number", 1),
                    "start_line": para.get("start_line", 1),
                    "end_line": para.get("end_line", 1),
                    "description": f"第{para_idx + 1}段"
                }
            else:
                # Fallback if paragraph data not available
                location = {
                    "type": "paragraph",
                    "index": para_idx,
                    "page_number": 1,
                    "start_line": 1,
                    "end_line": 1,
                    "description": f"第{para_idx + 1}段"
                }

            aggregated.append({
                "rule_id": issue_data["rule_id"],
                "rule_name": issue_data["rule_name"],
                "category": issue_data["category"],
                "error_message": issue_data["error_message"],
                "suggestion": issue_data["suggestion"],
                "fix_action": issue_data.get("fix_action"),
                "fix_params": issue_data.get("fix_params"),
                "location": location
            })

        return aggregated

    def _get_check_targets(self, doc_data: Dict[str, Any], match_type: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Get target data based on match type.

        Args:
            doc_data: Full document data
            match_type: Type of target to extract
            category: Rule category (e.g., "font" for body text filtering)

        Returns:
            List of target data dictionaries
        """
        if match_type == "document":
            return [doc_data]
        elif match_type == "paragraph":
            paragraphs = doc_data.get("paragraphs", [])
            # For body text checks, filter out heading paragraphs
            if category == "paragraph":
                headings = doc_data.get("headings", [])
                heading_para_indices = {h.get("paragraph_index") for h in headings}
                return [p for p in paragraphs if p.get("index") not in heading_para_indices]
            return paragraphs
        elif match_type == "run":
            runs = doc_data.get("runs", [])
            # For body text font checks, filter out runs from heading paragraphs
            if category == "font":
                headings = doc_data.get("headings", [])
                heading_para_indices = {h.get("paragraph_index") for h in headings}
                return [r for r in runs if r.get("paragraph_index") not in heading_para_indices]
            return runs
        elif match_type == "heading":
            return doc_data.get("headings", [])
        elif match_type == "table":
            return doc_data.get("tables", [])
        elif match_type == "figure":
            return doc_data.get("figures", [])
        elif match_type == "section":
            return self._extract_sections(doc_data)
        elif match_type == "style":
            return self._extract_styles(doc_data)
        else:
            return []

    def _extract_sections(self, doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sections from headings."""
        headings = doc_data.get("headings", [])
        sections = []
        for heading in headings:
            sections.append({
                "type": "section",
                "level": heading.get("level"),
                "text": heading.get("text"),
                "paragraph_index": heading.get("paragraph_index"),
            })
        return sections

    def _extract_styles(self, doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract unique styles from document."""
        headings = doc_data.get("headings", [])
        styles = []

        # Group headings by level
        for level in range(1, 4):
            level_headings = [h for h in headings if h.get("level") == level]
            if level_headings:
                # Use the first heading of this level as reference
                h = level_headings[0]
                styles.append({
                    "type": f"heading_level_{level}",
                    "level": level,
                    "font": h.get("font", {}),
                    "alignment": h.get("alignment"),
                })

        return styles

    def _match_condition(
        self,
        target: Dict[str, Any],
        condition: Dict[str, Any],
        category: str,
        match_type: str
    ) -> bool:
        """
        Check if a target matches the condition.

        Args:
            target: Target data to check
            condition: Rule condition
            category: Rule category
            match_type: Match type

        Returns:
            True if matches (no issue), False if doesn't match (issue found)
        """
        if category == "page":
            return self._match_page_condition(target, condition)
        elif category == "font":
            return self._match_font_condition(target, condition)
        elif category == "paragraph":
            return self._match_paragraph_condition(target, condition)
        elif category == "heading":
            return self._match_heading_condition(target, condition, match_type)
        elif category == "figure":
            return self._match_figure_condition(target, condition)
        elif category == "other":
            return self._match_other_condition(target, condition)
        else:
            return self._match_generic_condition(target, condition)

    def _match_page_condition(self, target: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Match page settings condition."""
        page_settings = target.get("page_settings", {})

        # Check margins
        margins = page_settings.get("margins", {})
        tolerance = condition.get("tolerance_mm", 0.5)

        for key in ["top_mm", "bottom_mm", "left_mm", "right_mm"]:
            if key in condition:
                expected = condition[key]
                actual = margins.get(key, 0)
                if abs(actual - expected) > tolerance:
                    return False

        # Check paper size
        if "paper_name" in condition:
            paper_size = page_settings.get("paper_size", {})
            if condition["paper_name"] == "A4":
                width = paper_size.get("width_mm", 0)
                height = paper_size.get("height_mm", 0)
                # Allow 1mm tolerance
                if not (abs(width - 210) < 1 and abs(height - 297) < 1):
                    return False
            elif "width_mm" in condition and "height_mm" in condition:
                width = paper_size.get("width_mm", 0)
                height = paper_size.get("height_mm", 0)
                if abs(width - condition["width_mm"]) > 1:
                    return False
                if abs(height - condition["height_mm"]) > 1:
                    return False

        return True

    def _match_font_condition(self, target: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Match font condition."""
        font = target.get("font", {})
        text = target.get("text", "")

        # If font info is incomplete (e.g., inherited from style), skip this run
        # This prevents false positives when font info cannot be directly extracted
        if font.get("name") is None or font.get("size_pt") is None:
            return True  # Skip check (pass) for runs with incomplete font info

        # Normalize font name for comparison (extract first font from comma-separated list)
        # and map Chinese font names to English equivalents
        def normalize_font_name(name):
            if not name:
                return None
            # Split by comma and take the first one, strip whitespace
            raw_name = name.split(',')[0].strip()
            # Map Chinese font names to English equivalents
            font_map = {
                "宋体": "SimSun",
                "SimSun": "SimSun",
                "黑体": "SimHei",
                "SimHei": "SimHei",
                "微软雅黑": "Microsoft YaHei",
                "Microsoft YaHei": "Microsoft YaHei",
                "楷体": "KaiTi",
                "KaiTi": "KaiTi",
                "仿宋": "FangSong",
                "FangSong": "FangSong",
                "方正小标宋简体": "方正小标宋简体",  # Keep as is
            }
            return font_map.get(raw_name, raw_name)

        # Check Chinese font
        if "chinese_font" in condition and contains_chinese(text):
            actual_font = normalize_font_name(font.get("name"))
            expected_font = normalize_font_name(condition["chinese_font"])
            if actual_font != expected_font:
                return False

        # Check English font
        if "english_font" in condition and contains_english(text):
            actual_font = normalize_font_name(font.get("name"))
            expected_font = normalize_font_name(condition["english_font"])
            if actual_font != expected_font:
                return False

        # Check Chinese font size
        if "chinese_size_pt" in condition and contains_chinese(text):
            expected_size = condition["chinese_size_pt"]
            actual_size = font.get("size_pt", 0)
            if abs(actual_size - expected_size) > 0.5:
                return False

        # Check English font size
        if "english_size_pt" in condition and contains_english(text):
            expected_size = condition["english_size_pt"]
            actual_size = font.get("size_pt", 0)
            if abs(actual_size - expected_size) > 0.5:
                return False

        return True

    def _match_paragraph_condition(self, target: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Match paragraph formatting condition."""
        formatting = target.get("formatting", {})

        # Check first line indent (allow tolerance for character-based measurement)
        if "first_line_indent_chars" in condition:
            actual_chars = formatting.get("first_line_indent_chars", 0)
            expected_chars = condition["first_line_indent_chars"]
            # Allow 0.5 character tolerance (character-based measurement has inherent variance)
            if abs(actual_chars - expected_chars) > 0.5:
                return False

        # Check line spacing (should use line_spacing_pt in points)
        if "paragraph_line_spacing" in condition:
            # Try line_spacing_pt first (points), fallback to line_spacing if needed
            actual_spacing_pt = formatting.get("line_spacing_pt")
            if actual_spacing_pt is None:
                # Fallback: if line_spacing is a number > 10, treat as points
                line_spacing = formatting.get("line_spacing", 0)
                if isinstance(line_spacing, (int, float)) and line_spacing > 10:
                    actual_spacing_pt = line_spacing
                else:
                    # Otherwise, it's a multiple, need to convert
                    # Get font size from paragraph or assume 12pt
                    font_size = 12
                    para_data = target  # Paragraph data should have font info
                    if "font" in para_data and para_data["font"].get("size_pt"):
                        font_size = para_data["font"]["size_pt"]
                    actual_spacing_pt = line_spacing * font_size if line_spacing else 0
            
            expected_spacing = condition["paragraph_line_spacing"]
            # Allow 2pt tolerance for line spacing
            if actual_spacing_pt and abs(actual_spacing_pt - expected_spacing) > 2:
                return False

        return True

    def _match_heading_condition(
        self,
        target: Dict[str, Any],
        condition: Dict[str, Any],
        match_type: str
    ) -> bool:
        """Match heading condition."""
        # 1. Check numbering style (for section match)
        if match_type == "section":
            if "number_style" in condition:
                text = target.get("text", "")
                if not re.match(r'^\d+(\.\d+)*', text.strip()):
                    return False
            return True

        # 2. Check style properties (font, size, alignment)
        # This logic was previously in match_type == "style"
        # Now we apply it to individual heading paragraphs
        level = target.get("level")
        level_key = f"level{level}"

        if level_key in condition:
            level_condition = condition[level_key]
            font = target.get("font", {})

            # If font info is incomplete (e.g., inherited from style), skip this heading check
            # This prevents false positives when font info cannot be directly extracted
            if font.get("name") is None or font.get("size_pt") is None:
                return True  # Skip check (pass) for headings with incomplete font info

            # Check font name
            if "font" in level_condition:
                # Handle potential EastAsia/Ascii font mapping
                # For simplicity, if actual font is None or empty, we might skip or fail
                # But DocxParser should extract it.
                if font.get("name") != level_condition["font"]:
                     # Try fallback: maybe font name is "SimHei" vs "黑体"
                     # For now, strict check
                     return False

            # Check font size
            if "size_pt" in level_condition:
                if abs(font.get("size_pt", 0) - level_condition["size_pt"]) > 0.5:
                    return False

            # Check bold
            if "bold" in level_condition:
                if font.get("bold") != level_condition["bold"]:
                    return False

            # Check alignment
            if "alignment" in level_condition:
                if target.get("alignment") != level_condition["alignment"]:
                    return False

        return True

    def _match_figure_condition(self, target: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Match figure/table condition."""
        # Check caption position
        if "caption_position" in condition:
            if target.get("caption_position") != condition["caption_position"]:
                return False

        # Check caption prefix
        if "caption_prefix" in condition:
            caption = target.get("caption") or ""
            if not caption.startswith(condition["caption_prefix"]):
                return False

        return True

    def _match_other_condition(self, target: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Match other category conditions."""
        # Check for required sections
        if "required" in condition:
            required = condition["required"]
            headings = target.get("headings", [])
            heading_texts = {h.get("text", "").lower() for h in headings}

            # Simple check - in production would be more sophisticated
            for req in required:
                if req not in heading_texts and req != "body":  # Skip body check for now
                    return False

        # Check citation style
        if "citation_style" in condition:
            # For MVP, skip complex citation checking
            pass

        return True

    def _match_generic_condition(self, target: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Generic condition matching."""
        for key, expected_value in condition.items():
            actual_value = target.get(key)
            if actual_value != expected_value:
                return False
        return True

    def _create_issue(
        self,
        rule: Dict[str, Any],
        target: Dict[str, Any],
        match_type: str
    ) -> Dict[str, Any]:
        """Create an issue record."""
        location = self._build_location(target, match_type)

        return {
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "category": rule["category"],
            "error_message": rule.get("error_message", "格式不符合规范"),
            "suggestion": rule.get("suggestion", ""),
            "fix_action": rule.get("fix_action"),
            "fix_params": rule.get("fix_params"),
            "location": location
        }

    def _build_location(self, target: Dict[str, Any], match_type: str) -> Dict[str, Any]:
        """Build location information for an issue."""
        location = {"type": match_type}

        if match_type == "paragraph":
            idx = target.get("index", 0)
            page = target.get("page_number", 1)
            start_line = target.get("start_line", 1)
            end_line = target.get("end_line", start_line)
            location["index"] = idx
            location["page_number"] = page
            location["start_line"] = start_line
            location["end_line"] = end_line
            location["description"] = f"第{page}页第{idx + 1}段({start_line}~{end_line}行)"
        elif match_type == "run":
            para_idx = target.get("paragraph_index", 0)
            page = target.get("page_number", 1)
            location["paragraph_index"] = para_idx
            location["page_number"] = page
            location["description"] = f"第{page}页第{para_idx + 1}段文本"
        elif match_type == "heading":
            location["level"] = target.get("level")
            location["text"] = target.get("text")
            location["paragraph_index"] = target.get("paragraph_index") # Add paragraph index for fixing
            location["description"] = f"标题: {target.get('text', '')}"
        elif match_type == "style":
            level = target.get("level", 1)
            location["level"] = level
            location["description"] = f"{level}级标题样式"
        elif match_type == "document":
            location["description"] = "文档整体设置"
        elif match_type == "figure":
            idx = target.get("index", 0)
            location["index"] = idx
            location["description"] = f"第{idx + 1}个图表"

        return location


# ============== Factory Functions ==============

def create_rule_engine(
    rules: List[Dict[str, Any]],
    ai_checker: Optional[Any] = None,
    enable_ai: bool = False
) -> RuleEngine:
    """Create a rule engine from a list of rule dictionaries."""
    return RuleEngine(rules, ai_checker=ai_checker, enable_ai=enable_ai)


def load_rules_from_db_objects(rule_objects) -> List[Dict[str, Any]]:
    """Convert database rule objects to dictionaries."""
    rules = []
    for rule_obj in rule_objects:
        rule_dict = {
            "id": rule_obj.id,
            "name": rule_obj.name,
            "category": rule_obj.category,
            "match": rule_obj.match,
            "condition": rule_obj.condition_json,
            "error_message": rule_obj.error_message,
            "suggestion": rule_obj.suggestion,
            "checker": rule_obj.checker or "deterministic",
            "prompt_template": rule_obj.prompt_template,
            "fix_action": rule_obj.fix_action,
            "fix_params": rule_obj.fix_params,
        }
        rules.append(rule_dict)
    return rules


def config_to_rules(config: Dict[str, Any], db_rules: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Convert a rule template config to rule dictionaries.

    Args:
        config: Rule template config with page, headings, body, and other settings
        db_rules: Optional list of database rules to match fix_action and fix_params

    Returns:
        List of rule dictionaries compatible with the rule engine
    """
    rules = []
    rule_id = 1000  # Start from 1000 to avoid conflict with DB rules
    
    # Create a mapping from rule characteristics to database rules for fix_action lookup
    # Map by known rule IDs that have fix_action
    db_rule_map = {}
    if db_rules:
        for db_rule in db_rules:
            rule_id_key = db_rule.get("id")
            if rule_id_key:
                db_rule_map[rule_id_key] = db_rule

    # Page settings rules
    page_config = config.get("page", {})
    if page_config:
        margins = page_config.get("margins", {})
        if margins:
            # Convert cm to mm
            rule = {
                "id": rule_id,
                "name": "页边距检查",
                "category": "page",
                "match": "document",
                "condition": {
                    "top_mm": margins.get("top_cm", 2.5) * 10,
                    "bottom_mm": margins.get("bottom_cm", 2.5) * 10,
                    "left_mm": margins.get("left_cm", 3.0) * 10,
                    "right_mm": margins.get("right_cm", 2.5) * 10,
                    "tolerance_mm": 2  # 2mm tolerance
                },
                "error_message": f"页边距不符合规范（上{margins.get('top_cm', 2.5)}cm/下{margins.get('bottom_cm', 2.5)}cm/左{margins.get('left_cm', 3.0)}cm/右{margins.get('right_cm', 2.5)}cm）",
                "suggestion": f"请设置页边距为：上{margins.get('top_cm', 2.5)}cm，下{margins.get('bottom_cm', 2.5)}cm，左{margins.get('left_cm', 3.0)}cm，右{margins.get('right_cm', 2.5)}cm",
                "checker": "deterministic"
            }
            # Try to match with PAGE_MARGIN_25 rule for fix_action
            if "PAGE_MARGIN_25" in db_rule_map:
                db_rule = db_rule_map["PAGE_MARGIN_25"]
                rule["fix_action"] = db_rule.get("fix_action")
                rule["fix_params"] = db_rule.get("fix_params")
            rules.append(rule)
            rule_id += 1

        # Paper size check
        paper_name = page_config.get("paper_name", "A4")
        if paper_name == "A4":
            rules.append({
                "id": rule_id,
                "name": "纸张大小检查",
                "category": "page",
                "match": "document",
                "condition": {"paper_name": "A4"},
                "error_message": "纸张大小应为A4（210mm × 297mm）",
                "suggestion": "请将纸张大小设置为A4",
                "checker": "deterministic"
            })
            rule_id += 1

    # Body text font rules
    body_config = config.get("body", {})
    if body_config:
        body_font = body_config.get("font")
        body_size = body_config.get("size_pt")
        if body_font and body_size:
            rule = {
                "id": rule_id,
                "name": "正文字体字号检查",
                "category": "font",
                "match": "run",
                "condition": {
                    "chinese_font": body_font,
                    "chinese_size_pt": body_size
                },
                "error_message": f"正文应使用{body_font} {body_size}pt字体",
                "suggestion": f"请将正文字体设置为{body_font}，字号{body_size}pt",
                "checker": "deterministic"
            }
            # Try to match with FONT_BODY_SONGTI rule for fix_action
            if "FONT_BODY_SONGTI" in db_rule_map:
                db_rule = db_rule_map["FONT_BODY_SONGTI"]
                rule["fix_action"] = db_rule.get("fix_action")
                rule["fix_params"] = db_rule.get("fix_params")
            rules.append(rule)
            rule_id += 1

        # Line spacing rule
        line_spacing = body_config.get("line_spacing_pt")
        if line_spacing:
            rules.append({
                "id": rule_id,
                "name": "正文行距检查",
                "category": "paragraph",
                "match": "paragraph",
                "condition": {
                    "paragraph_line_spacing": line_spacing
                },
                "error_message": f"正文行距应为{line_spacing}磅",
                "suggestion": f"请将正文行距设置为{line_spacing}磅",
                "checker": "deterministic"
            })
            rule_id += 1

        # First line indent rule
        first_line_indent = body_config.get("first_line_indent_chars")
        if first_line_indent:
            rule = {
                "id": rule_id,
                "name": "正文首行缩进检查",
                "category": "paragraph",
                "match": "paragraph",
                "condition": {
                    "first_line_indent_chars": first_line_indent
                },
                "error_message": f"正文首行应缩进{first_line_indent}字符",
                "suggestion": f"请将正文首行缩进设置为{first_line_indent}字符",
                "checker": "deterministic"
            }
            # Try to match with PARA_INDENT_2CHAR rule for fix_action
            if "PARA_INDENT_2CHAR" in db_rule_map:
                db_rule = db_rule_map["PARA_INDENT_2CHAR"]
                rule["fix_action"] = db_rule.get("fix_action")
                rule["fix_params"] = db_rule.get("fix_params")
            rules.append(rule)
            rule_id += 1

    # Heading style rules (support levels 1-4)
    headings_config = config.get("headings", [])
    for heading in headings_config:
        level = heading.get("level")
        font = heading.get("font")
        size_pt = heading.get("size_pt")
        bold = heading.get("bold")
        alignment = heading.get("alignment")

        if level and font and size_pt:
            level_condition = {
                "font": font,
                "size_pt": size_pt
            }
            if bold is not None:
                level_condition["bold"] = bold
            if alignment:
                level_condition["alignment"] = alignment

            rule = {
                "id": rule_id,
                "name": f"{level}级标题样式检查",
                "category": "heading",
                "match": "heading",
                "condition": {
                    f"level{level}": level_condition
                },
                "error_message": f"{level}级标题格式应为：{font} {size_pt}pt{'，加粗' if bold else ''}",
                "suggestion": f"请将{level}级标题设置为：字体{font}，字号{size_pt}pt{'，加粗' if bold else ''}",
                "checker": "deterministic"
            }
            # Try to match with HEADING_STYLES rule for fix_action
            if "HEADING_STYLES" in db_rule_map:
                db_rule = db_rule_map["HEADING_STYLES"]
                rule["fix_action"] = db_rule.get("fix_action")
                rule["fix_params"] = db_rule.get("fix_params")
            rules.append(rule)
            rule_id += 1

    # Page number settings (if specified)
    page_number_config = config.get("page_number", {})
    if page_number_config:
        pn_font = page_number_config.get("font")
        pn_size = page_number_config.get("size_pt")
        pn_alignment = page_number_config.get("alignment")

        if pn_font and pn_size:
            rules.append({
                "id": rule_id,
                "name": "页码格式检查",
                "category": "other",
                "match": "document",
                "condition": {
                    "_page_number_font": pn_font,
                    "_page_number_size_pt": pn_size,
                    "_page_number_alignment": pn_alignment
                },
                "error_message": f"页码应使用{pn_font} {pn_size}pt，{pn_alignment or '居中'}对齐",
                "suggestion": f"请将页码格式设置为：{pn_font}，{pn_size}pt，{pn_alignment or '居中'}对齐",
                "checker": "deterministic"
            })
            rule_id += 1

    # Table settings (if specified)
    # Note: Actual table checking requires docx_parser to extract table styles
    # This rule serves as a placeholder for future implementation
    table_config = config.get("table", {})
    if table_config:
        # Table rules would be added here when docx_parser supports table style extraction
        pass

    return rules
