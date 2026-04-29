"""
Tool Executor — ينفذ الـ tool calls من المودل ويرجع النتايج.

When the LLM calls search_kb_by_verse("6:5"), this module:
1. Parses the tool call
2. Executes it against the KB
3. Returns formatted results back to the LLM
"""

import logging

from al_furqan.kb.tafsir.kb_tools import TafsirKBTools, KBEntry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes KB tool calls from the LLM and returns formatted results.
    """

    def __init__(self, kb_tools: TafsirKBTools):
        self.kb = kb_tools
        self._call_log: list[dict] = []  # Track all tool calls for feedback

    @property
    def call_log(self) -> list[dict]:
        """Get the log of all tool calls made during this session."""
        return self._call_log

    def reset_log(self):
        """Reset the call log for a new question."""
        self._call_log = []

    def execute(self, tool_name: str, arguments: dict) -> str:
        """
        Execute a tool call and return formatted results.

        Args:
            tool_name: Name of the tool (e.g., "search_kb_by_verse")
            arguments: Tool arguments as a dict

        Returns:
            Formatted string result for the LLM.
        """
        logger.info("Tool call: %s(%s)", tool_name, arguments)

        handler = {
            "search_kb_by_verse": self._handle_search_by_verse,
            "search_kb_by_topic": self._handle_search_by_topic,
            "search_kb_by_relation": self._handle_search_by_relation,
            "get_verse_context": self._handle_get_verse_context,
        }.get(tool_name)

        if not handler:
            result = f"❌ أداة غير معروفة: {tool_name}"
            self._log_call(tool_name, arguments, result, success=False)
            return result

        try:
            result = handler(arguments)
            self._log_call(tool_name, arguments, result, success=True)
            return result
        except Exception as e:  # pylint: disable=broad-exception-caught
            error_msg = f"❌ خطأ في تنفيذ {tool_name}: {str(e)}"
            logger.error(error_msg)
            self._log_call(tool_name, arguments, error_msg, success=False)
            return error_msg

    def _log_call(self, tool_name: str, arguments: dict, result: str, success: bool):
        """Log a tool call for feedback tracking."""
        self._call_log.append(
            {
                "tool": tool_name,
                "arguments": arguments,
                "result_length": len(result),
                "success": success,
            }
        )

    def _format_entries(self, entries: list[KBEntry], max_entries: int = 10) -> str:
        """Format KB entries for LLM consumption."""
        if not entries:
            return "لم يُعثر على نتائج في قاعدة المعرفة."

        lines = [f"عدد النتائج: {len(entries)}\n"]
        for i, entry in enumerate(entries[:max_entries], 1):
            lines.append(f"--- [{i}] ---")
            lines.append(entry.format_for_llm())

        if len(entries) > max_entries:
            lines.append(f"\n... و {len(entries) - max_entries} نتائج إضافية")

        return "\n".join(lines)

    # --- Tool Handlers ---

    def _handle_search_by_verse(self, args: dict) -> str:
        verse_ref = args.get("verse_ref", "")
        if not verse_ref:
            return "❌ يجب تحديد رقم الآية (verse_ref)"
        entries = self.kb.search_by_verse(verse_ref)
        return (
            f"## نتائج البحث عن الآية {verse_ref}:\n\n{self._format_entries(entries)}"
        )

    def _handle_search_by_topic(self, args: dict) -> str:
        topic = args.get("topic", "")
        if not topic:
            return "❌ يجب تحديد الموضوع (topic)"
        entries = self.kb.search_by_topic(topic)
        return f'## نتائج البحث عن موضوع "{topic}":\n\n{self._format_entries(entries)}'

    def _handle_search_by_relation(self, args: dict) -> str:
        verse_ref = args.get("verse_ref", "")
        relation_type = args.get("relation_type", "")
        if not verse_ref or not relation_type:
            return "❌ يجب تحديد الآية (verse_ref) ونوع العلاقة (relation_type)"
        entries = self.kb.search_by_relation(verse_ref, relation_type)
        return (
            f"## نتائج البحث عن {relation_type} للآية {verse_ref}:\n\n"
            f"{self._format_entries(entries)}"
        )

    def _handle_get_verse_context(self, args: dict) -> str:
        verse_ref = args.get("verse_ref", "")
        verse_range = args.get("verse_range", 3)
        if not verse_ref:
            return "❌ يجب تحديد رقم الآية (verse_ref)"
        ctx = self.kb.get_verse_context(verse_ref, verse_range=verse_range)
        if "error" in ctx:
            return f"❌ {ctx['error']}"

        entries = ctx.get("entries", [])
        return (
            f"## سياق الآية {verse_ref} (المدى: {ctx['range']}):\n\n"
            f"عدد المعلومات المتاحة: {ctx['entry_count']}\n\n"
            f"{self._format_entries(entries)}"
        )


def parse_tool_calls_from_response(response_text: str) -> list[dict]:
    """
    Parse tool calls from LLM response text (for non-function-calling models).

    Looks for patterns like:
    - search_kb_by_verse("6:5")
    - search_kb_by_topic("السنة الإلهية")

    Returns list of {"name": str, "arguments": dict}
    """
    import re  # pylint: disable=import-outside-toplevel

    calls = []
    # Pattern: tool_name("arg1", "arg2") or tool_name(key="value")
    pattern = r'(search_kb_by_verse|search_kb_by_topic|search_kb_by_relation|get_verse_context)\s*\(\s*"([^"]*)"'  # pylint: disable=line-too-long

    for m in re.finditer(pattern, response_text):
        tool_name = m.group(1)
        first_arg = m.group(2)

        if tool_name == "search_kb_by_verse":
            calls.append({"name": tool_name, "arguments": {"verse_ref": first_arg}})
        elif tool_name == "search_kb_by_topic":
            calls.append({"name": tool_name, "arguments": {"topic": first_arg}})
        elif tool_name == "search_kb_by_relation":
            # Try to find second argument
            full_match = response_text[m.start() :]
            rel_match = re.search(r'"([^"]*)",\s*"([^"]*)"', full_match)
            if rel_match:
                calls.append(
                    {
                        "name": tool_name,
                        "arguments": {
                            "verse_ref": rel_match.group(1),
                            "relation_type": rel_match.group(2),
                        },
                    }
                )
            else:
                calls.append({"name": tool_name, "arguments": {"verse_ref": first_arg}})
        elif tool_name == "get_verse_context":
            calls.append({"name": tool_name, "arguments": {"verse_ref": first_arg}})

    return calls
