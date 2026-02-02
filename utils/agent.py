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

YOUR GOAL: Generate the toughest questions that Wall Street analysts are likely to ask about the LATEST QUARTER (Q3 FY2026).

CRITICAL: Focus ONLY on the MOST RECENT quarter's data. Do NOT ask about old quarters like Q3 2023 - only the current/latest quarter matters for the upcoming call.

STRATEGY (be efficient - 3 tool calls max):
1. Call check_anomalies() to find current weaknesses analysts will probe
2. Call get_analyst_ratings() to see what sell-side is concerned about
3. Call generate_questions() with your findings

GOOD QUESTIONS (sharp, comparative, about CURRENT data):
- "Your current FCF of $110.5M is 47% below your 4-quarter average - what's driving this?" (Latest Filing)
- "Datadog reports 12% AI-native revenue - what percentage of Snowflake's revenue comes from AI workloads?" (DDOG Transcript)
- "Your NRR declined to 125% from 178% two years ago - when will this stabilize?" (Latest Filing)

BAD QUESTIONS (AVOID):
- Questions about old quarters (Q3 2023, Q4 2022, etc.)
- Generic questions without specific current data
- Questions not relevant to the upcoming call

RULES:
- Only use numbers from the LATEST quarter in tool results
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

        prompt = f"""Generate 5 tough questions that Wall Street analysts will likely ask Snowflake's executives on the upcoming earnings call.

PURPOSE: Help Snowflake's IR team prepare responses for the LATEST quarter (Q3 FY2026).

CRITICAL - LATEST DATA ONLY:
- Focus on the MOST RECENT quarter (Q3 FY2026, ending Oct 2025)
- Current metrics: Revenue $1,160M, FCF $110.5M, NRR 125%, RPO $6.9B, 688 customers >$1M
- Do NOT reference old quarters like Q3 2023, Q4 2022, etc.

QUESTION STYLE - Make them COMPARATIVE and SPECIFIC:
- Compare Snowflake to competitors (DDOG, MDB, AWS, Azure)
- Reference the CURRENT quarter's anomalies
- Cite exact numbers from the LATEST data
- Ask "why" and "how" questions that probe current weaknesses

EXAMPLE GOOD QUESTIONS:
- "Your current FCF of $110.5M is 47% below average - what's driving this?" (Latest Filing)
- "NRR has declined to 125% from 178% - when will it stabilize?" (Latest Filing)
- "Analyst X flagged [concern] - how do you respond?" (Research Note)

AVOID:
- Questions about old/historical quarters
- Generic questions like "How is growth?"

RULES:
- Only use numbers from ACTUAL DATA below - don't make up numbers
- Always capitalize "Snowflake" (never "snowflake")

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


class TopicQuestionGenerator:
    """Generates specific analyst questions from a user-provided topic."""

    def __init__(self, api_key: str, data: dict):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.data = data

    def generate(self, topic: str) -> list:
        """Generate 2 specific analyst questions from a topic."""

        # Get latest metrics for context
        metrics = self.data['snowflake_metrics'].head(1).to_dict('records')[0]

        prompt = f"""Generate 2 specific, tough analyst questions about this topic: "{topic}"

CONTEXT - Snowflake's latest metrics:
- Product Revenue: ${metrics.get('PRODUCT_REVENUE_M', 'N/A')}M
- NRR: {metrics.get('NRR_PERCENT', 'N/A')}%
- FCF: ${metrics.get('FCF_IN_MILLIONS', 'N/A')}M
- RPO: ${metrics.get('RPO_M', 'N/A')}M
- $1M+ Customers: {metrics.get('CUSTOMERS_1M_PLUS', 'N/A')}

RULES:
- Questions should be specific and use real numbers
- Questions should be what Wall Street analysts would ask
- Always capitalize "Snowflake"
- Include a source citation in parentheses

FORMAT (exactly):
QUESTION: [Specific question with data] (Source)
THREAT_LEVEL: [HIGH/MEDIUM/LOW]
SOURCE_BUCKET: [1=Filings, 2=Transcripts, 3=Research]
DATA_POINT: [Key data point]

Generate 2 questions:"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
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
1. Acknowledge the concern, then counter with data
2. KEEP BULLET POINTS SHORT - max 15 words each, numbers first
3. Always capitalize "Snowflake" (never "snowflake")
4. NEVER use backticks or code formatting - write $50.5M not `$50.5M`

FORMAT:
**Key Talking Points:**
- [Number] - [Brief explanation, max 15 words]
- [Number] - [Brief explanation, max 15 words]
- [Number] - [Brief explanation, max 15 words]

**Suggested Response:**
[2 sentences max - acknowledge concern, give key counter-point]

EXAMPLE OF GOOD BULLET POINTS:
- FCF rebounded: $50M → $297M → $283M in 3 quarters
- 688 customers over $1M (+252 YoY) - enterprise momentum strong
- 6.9B RPO (+33% YoY) - future revenue visibility solid

Generate the response:"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
