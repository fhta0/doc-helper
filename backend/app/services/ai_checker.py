"""
AI Checker Service
Handles AI-based document format checking using OpenAI-compatible APIs.
"""
import json
import logging
from typing import Dict, List, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIChecker:
    """AI-based document checker using OpenAI-compatible APIs."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize the AI checker.

        Args:
            base_url: API base URL (defaults to settings.AI_BASE_URL)
            api_key: API key (defaults to settings.AI_API_KEY)
            model: Model name (defaults to settings.AI_MODEL)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url if base_url is not None else settings.AI_BASE_URL
        self.api_key = api_key if api_key is not None else settings.AI_API_KEY
        self.model = model if model is not None else settings.AI_MODEL
        self.timeout = timeout

        # Validate configuration
        if not self.api_key:
            logger.warning("AI_API_KEY is not configured, AI checking will be disabled")

    def is_enabled(self) -> bool:
        """Check if AI checking is enabled."""
        return bool(self.api_key)

    async def check_rule(
        self,
        doc_data: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check a single AI rule against the document.

        Args:
            doc_data: Parsed document data
            rule: Rule dictionary with prompt_template

        Returns:
            List of issues found by AI
        """
        if not self.is_enabled():
            logger.warning(f"AI checker not enabled, skipping rule: {rule.get('id')}")
            return []

        prompt_template = rule.get("prompt_template")
        if not prompt_template:
            logger.warning(f"Rule {rule.get('id')} has no prompt_template")
            return []

        try:
            # Build prompt from template and document data
            prompt = self._build_prompt(doc_data, prompt_template)

            # Call AI API
            response_text = await self._call_ai_api(prompt)

            # Parse response into issues
            issues = self._parse_ai_response(response_text, rule)

            return issues

        except Exception as e:
            logger.error(f"AI check failed for rule {rule.get('id')}: {e}")
            # Return empty list on failure - don't block the entire check
            return []

    def _build_prompt(
        self,
        doc_data: Dict[str, Any],
        prompt_template: str
    ) -> str:
        """
        Build prompt from template and document data.

        Args:
            doc_data: Parsed document data
            prompt_template: Prompt template string

        Returns:
            Formatted prompt string
        """
        # Extract relevant document info for the prompt
        context = self._extract_document_context(doc_data)

        # Simple template substitution
        # Support {doc_info}, {paragraphs}, {headings} placeholders
        prompt = prompt_template.format(**context)

        return prompt

    def _extract_document_context(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant context from document data for prompt.

        Args:
            doc_data: Full parsed document data

        Returns:
            Dictionary with context for prompt template
        """
        paragraphs = doc_data.get("paragraphs", [])
        headings = doc_data.get("headings", [])

        # Build a concise document summary
        doc_info = {
            "filename": doc_data.get("info", {}).get("filename", ""),
            "total_paragraphs": len(paragraphs),
            "total_headings": len(headings),
        }

        # Include paragraph texts (limit to first 50 for context window)
        paragraphs_text = "\n".join([
            f"{i+1}. {p.get('text', '')}"[:200]  # Truncate long paragraphs
            for i, p in enumerate(paragraphs[:50])
        ])

        # Include headings
        headings_text = "\n".join([
            f"{'#' * h.get('level', 1)} {h.get('text', '')}"
            for h in headings
        ])

        return {
            "doc_info": json.dumps(doc_info, ensure_ascii=False),
            "paragraphs": paragraphs_text,
            "headings": headings_text,
            "paragraphs_count": len(paragraphs),
            "headings_count": len(headings),
        }

    async def _call_ai_api(self, prompt: str) -> str:
        """
        Call the AI API with the given prompt.

        Args:
            prompt: Prompt string to send

        Returns:
            AI response text

        Raises:
            httpx.HTTPError: If API call fails
        """
        url = f"{self.base_url.rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的文档格式检查助手。请严格按照JSON格式返回检查结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Extract response text
            return data["choices"][0]["message"]["content"]

    def _parse_ai_response(
        self,
        response_text: str,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse AI response into issue list.

        Args:
            response_text: Raw AI response text
            rule: Rule dictionary

        Returns:
            List of issue dictionaries
        """
        issues = []

        try:
            # Try to parse as JSON array
            response_text = response_text.strip()

            # Handle markdown code blocks
            if response_text.startswith("```"):
                # Extract JSON from code block
                lines = response_text.split("\n")
                json_start = -1
                json_end = -1
                for i, line in enumerate(lines):
                    if "```json" in line or (json_start == -1 and "```" in line):
                        json_start = i + 1
                    elif json_start != -1 and "```" in line:
                        json_end = i
                        break

                if json_start != -1 and json_end != -1:
                    response_text = "\n".join(lines[json_start:json_end])
                else:
                    # Fallback: remove all ``` markers
                    response_text = response_text.replace("```json", "").replace("```", "")

            # Parse JSON
            parsed = json.loads(response_text)

            # Handle both array and single object responses
            if isinstance(parsed, list):
                items = parsed
            elif isinstance(parsed, dict):
                # Check for common response structures
                if "issues" in parsed:
                    items = parsed["issues"]
                elif "results" in parsed:
                    items = parsed["results"]
                else:
                    items = [parsed]
            else:
                logger.warning(f"Unexpected AI response format: {type(parsed)}")
                return []

            # Convert to issue format
            for item in items:
                issue = self._create_issue_from_ai_item(item, rule)
                if issue:
                    issues.append(issue)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            # Try to extract any meaningful text response
            if response_text and "问题" in response_text:
                # Fallback: create a generic issue from the response
                issues.append({
                    "rule_id": rule.get("id", "AI_UNKNOWN"),
                    "rule_name": rule.get("name", "AI检查"),
                    "category": rule.get("category", "other"),
                    "error_message": "AI检测发现潜在问题",
                    "suggestion": response_text[:500],
                    "location": {
                        "type": "document",
                        "description": "文档整体"
                    }
                })

        return issues

    def _create_issue_from_ai_item(
        self,
        item: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a standardized issue from AI response item.

        Args:
            item: AI response item
            rule: Original rule dictionary

        Returns:
            Issue dictionary or None if invalid
        """
        # Extract location info
        location = item.get("location", {})
        if not location:
            location = {
                "type": "document",
                "description": item.get("description", "文档整体")
            }

        return {
            "rule_id": rule.get("id", "AI_UNKNOWN"),
            "rule_name": rule.get("name", "AI检查"),
            "category": rule.get("category", "other"),
            "error_message": item.get("error_message", rule.get("error_message", "格式可能存在问题")),
            "suggestion": item.get("suggestion", rule.get("suggestion", "请检查相关内容")),
            "location": location
        }


# ============== Factory Functions ==============

def create_ai_checker() -> AIChecker:
    """Create an AI checker instance from settings."""
    return AIChecker()
