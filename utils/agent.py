"""
Agentic Question Generator - Autonomously explores data to generate analyst questions.
"""

import anthropic
from typing import Generator
from utils.tools import DataTools


class QuestionAgent:
    """Agent that uses tool calls to research data and generate tough analyst questions."""

    def __init__(self, api_key: str, data: dict, loader):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.tools = DataTools(data, loader)
        self.max_turns = 5

    def run(self) -> Generator[dict, None, None]:
        """Run the agent loop. Yields events: tool_call, tool_result, questions, error."""

        system_prompt = """You are helping Snowflake's Investor Relations team prepare for their upcoming earnings call.

YOUR GOAL: Generate the toughest questions that Wall Street analysts are likely to ask, so Snowflake executives can prepare strong responses.

STRATEGY (be efficient - 3 tool calls max):
1. Call check_anomalies() to find weaknesses analysts will probe
2. Call get_analyst_ratings() to see what sell-side is concerned about
3. Call generate_questions() with your findings

GOOD QUESTIONS (sharp, comparative, insight-driven):
- "Why did R&D headcount increase in Q3 more than historical quarters?" (10-Q Filing)
- "Datadog reports 12% AI-native revenue - what percentage of your revenue comes from AI workloads?" (DDOG Transcript)
- "Jefferies flagged cannibalization risk between AI/ML and core warehouse - how do you respond?" (Jefferies Research)
- "Your NRR declined from 178% to 165% - what's driving the slowdown vs peers?" (Q3 Filing)

BAD QUESTIONS (too generic - AVOID these):
- "How is revenue growth?" - No specific data
- "What's your outlook?" - Not insight-driven
- "Tell us about competition" - Not comparative

RULES:
- Only use numbers from tool results - don't make up data
- Each question needs a source citation in parentheses
- Frame questions as what analysts will ASK Snowflake
- Always capitalize "Snowflake" (never "snowflake")
- Call generate_questions() when ready"""

        messages = [{"role": "user", "content": "Research Snowflake's data and generate 5 tough analyst questions."}]
        tool_definitions = self.tools.get_tool_definitions()
        collected_data = []

        for turn in range(self.max_turns):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                tools=tool_definitions,
                messages=messages
            )

            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            tool_calls = [block for block in assistant_content if block.type == "tool_use"]

            if not tool_calls:
                text_blocks = [block.text for block in assistant_content if hasattr(block, 'text')]
                yield {"type": "complete", "content": "\n".join(text_blocks)}
                return

            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.name
                tool_input = tool_call.input

                yield {"type": "tool_call", "tool": tool_name, "input": tool_input}

                result = self.tools.execute_tool(tool_name, tool_input)

                # Final question generation
                if result.startswith("GENERATE_QUESTIONS:"):
                    findings = result.replace("GENERATE_QUESTIONS:", "")
                    actual_data = "\n\n".join(collected_data)
                    final_questions = self._generate_final_questions(findings, actual_data)
                    yield {"type": "questions", "content": final_questions}
                    return

                yield {"type": "tool_result", "content": result[:500] + "..." if len(result) > 500 else result}

                collected_data.append(f"[{tool_name}]:\n{result}")
                tool_results.append({"type": "tool_result", "tool_use_id": tool_call.id, "content": result})

            messages.append({"role": "user", "content": tool_results})

        yield {"type": "error", "content": "Max turns reached"}

    def _generate_final_questions(self, findings: str, actual_data: str) -> str:
        """Generate final questions using only the actual data collected."""

        prompt = f"""Generate 5 tough questions that Wall Street analysts will likely ask Snowflake's executives on the earnings call.

PURPOSE: Help Snowflake's IR team prepare responses for their toughest questions.

QUESTION STYLE - Make them COMPARATIVE and SPECIFIC:
- Compare Snowflake to competitors (DDOG, MDB, AWS, Azure)
- Reference specific trends or anomalies in the data
- Cite exact numbers from the data
- Ask "why" and "how" questions that probe weaknesses

EXAMPLE GOOD QUESTIONS:
- "Why did [metric] change by X% when peers like DDOG showed Y%?" (Source)
- "Analyst X flagged [concern] - how do you respond?" (Research Note)
- "Your [metric] declined from X to Y - what's the driver?" (Filing)

AVOID GENERIC QUESTIONS LIKE:
- "How is growth?" or "What's your outlook?"

CRITICAL:
- Only use numbers that appear in ACTUAL DATA. Don't make up numbers.
- Always capitalize "Snowflake" (never "snowflake").

AGENT SUMMARY:
{findings}

ACTUAL DATA (use these exact numbers):
{actual_data}

FORMAT (follow exactly):
QUESTION: [Sharp comparative question with specific data] (Source citation)
SOURCE_BUCKET: [1=Filings/Press, 2=Transcripts, 3=Analyst Research]
THREAT_LEVEL: [HIGH, MEDIUM, or LOW]
DATA_POINT: [The exact data point used]

Generate 5 questions:"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text


class DefenseAgent:
    """Agent that researches data to build executive defense responses."""

    def __init__(self, api_key: str, data: dict, loader):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.tools = DataTools(data, loader)
        self.max_turns = 4

    def run(self, question: str, kpis: dict) -> Generator[dict, None, None]:
        """Run defense agent. Yields events: tool_call, tool_result, defense."""

        kpi_summary = "\n".join([f"- {k}: {v}" for k, v in kpis.items() if k != 'Quarter'])

        system_prompt = f"""You are helping Snowflake's executive team prepare a strong response to a tough analyst question.

THE QUESTION ANALYSTS WILL ASK:
{question}

SNOWFLAKE'S CURRENT METRICS:
{kpi_summary}

YOUR TASK:
1. Research data that supports Snowflake's position
2. Find positive metrics, competitive advantages, recent wins
3. Draft a confident executive response with specific numbers

STRATEGY (2-3 tool calls max):
1. Call get_snowflake_metrics() to find positive trends
2. Call get_press_releases() or search_transcripts() for recent wins
3. Call generate_defense() with your talking points

RESPONSE GUIDELINES:
- Acknowledge the concern directly - don't dodge
- Counter with specific Snowflake data points
- Highlight strategic strengths and momentum
- Keep it concise (2-3 paragraphs)

Start researching now."""

        messages = [{"role": "user", "content": f"Research and defend against this question: {question}"}]
        tool_definitions = self._get_defense_tools()
        collected_data = []

        for turn in range(self.max_turns):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                tools=tool_definitions,
                messages=messages
            )

            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            tool_calls = [block for block in assistant_content if block.type == "tool_use"]

            if not tool_calls:
                text_blocks = [block.text for block in assistant_content if hasattr(block, 'text')]
                yield {"type": "complete", "content": "\n".join(text_blocks)}
                return

            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.name
                tool_input = tool_call.input

                yield {"type": "tool_call", "tool": tool_name, "input": tool_input}

                # Handle generate_defense specially
                if tool_name == "generate_defense":
                    talking_points = tool_input.get("talking_points", "")
                    actual_data = "\n\n".join(collected_data)
                    final_defense = self._generate_final_defense(question, talking_points, actual_data, kpis)
                    yield {"type": "defense", "content": final_defense}
                    return

                result = self.tools.execute_tool(tool_name, tool_input)
                yield {"type": "tool_result", "content": result[:500] + "..." if len(result) > 500 else result}

                collected_data.append(f"[{tool_name}]:\n{result}")
                tool_results.append({"type": "tool_result", "tool_use_id": tool_call.id, "content": result})

            messages.append({"role": "user", "content": tool_results})

        yield {"type": "error", "content": "Max turns reached"}

    def _get_defense_tools(self) -> list:
        """Return subset of tools useful for defense."""
        all_tools = self.tools.get_tool_definitions()

        # Filter to defense-relevant tools + add generate_defense
        defense_tool_names = [
            "get_snowflake_metrics", "search_transcripts", "get_press_releases",
            "check_anomalies", "compare_to_competitor"
        ]

        tools = [t for t in all_tools if t["name"] in defense_tool_names]

        # Add generate_defense tool
        tools.append({
            "name": "generate_defense",
            "description": "Call this when you have enough data to defend. Generates the final executive response.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "talking_points": {
                        "type": "string",
                        "description": "Key talking points and data to include in the defense"
                    }
                },
                "required": ["talking_points"]
            }
        })

        return tools

    def _generate_final_defense(self, question: str, talking_points: str, actual_data: str, kpis: dict) -> str:
        """Generate final executive defense response."""

        kpi_summary = "\n".join([f"- {k}: {v}" for k, v in kpis.items() if k != 'Quarter'])

        prompt = f"""Draft an executive-ready response for Snowflake's CFO or CEO to deliver on the earnings Q&A.

ANALYST QUESTION: {question}

TALKING POINTS:
{talking_points}

ACTUAL DATA (use these exact numbers):
{actual_data}

CURRENT METRICS:
{kpi_summary}

RESPONSE GUIDELINES:
1. Start by acknowledging the question directly - don't dodge
2. Provide data-backed rebuttal with specific numbers from above
3. Highlight strategic strengths, momentum, or competitive advantages
4. End with forward-looking confidence
5. Use bullet points with key talking points (not paragraphs)
6. Use executive tone - confident but not dismissive
7. Always capitalize "Snowflake" (never "snowflake")
8. CRITICAL: NEVER use backticks, code blocks, or monospace formatting. Write all numbers as plain text. Wrong: `$50.5M` or `110.5M`. Correct: $50.5M or 110.5M

FORMAT:
**Key Talking Points:**
- [Point 1 with specific data]
- [Point 2 with specific data]
- [Point 3 with specific data]

**Suggested Response:**
[Brief 2-3 sentence executive response]

Generate the response:"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
