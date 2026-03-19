import json
from groq import Groq, AuthenticationError, RateLimitError, APIError

from app.core.config import settings
from app.core.errors import AIServiceError
from app.schemas.ai import (
    GeneratedTask,
    TaskBreakdownResponse,
    PrioritySuggestResponse,
)


def _get_client() -> Groq:
    return Groq(api_key=settings.GROQ_API_KEY)


def _call_groq(system: str, user: str, max_tokens: int = 1024) -> str:
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content
    except AuthenticationError:
        raise AIServiceError(
            "Invalid Groq API key. Check GROQ_API_KEY in your environment."
        )
    except RateLimitError:
        raise AIServiceError(
            "Groq API rate limit reached. Please try again shortly."
        )
    except APIError as e:
        raise AIServiceError(f"Groq API error: {str(e)}")


def _parse_json(raw: str, context: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
    cleaned = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise AIServiceError(f"Could not parse AI response for {context}: {str(e)}")


def breakdown_goal(goal: str, max_tasks: int) -> TaskBreakdownResponse:
    system = (
        "You are a productivity assistant. Break down a user's high-level goal into concrete, "
        "actionable todo tasks. Respond ONLY with valid JSON — no markdown fences, no extra text. "
        "Return an object with a 'tasks' array. Each task object must have exactly these keys: "
        "title (string), description (string), priority (one of: low, medium, high), "
        "tags (array of strings)."
    )
    user = f"Break down this goal into at most {max_tasks} clear tasks:\n\nGoal: {goal}"

    raw = _call_groq(system, user, max_tokens=1200)
    data = _parse_json(raw, "task breakdown")

    try:
        tasks = [GeneratedTask(**t) for t in data.get("tasks", [])]
    except Exception as e:
        raise AIServiceError(f"Invalid task structure in AI response: {str(e)}")

    return TaskBreakdownResponse(goal=goal, tasks=tasks)


def suggest_priority(
    title: str, description: str | None, due_date: str | None
) -> PrioritySuggestResponse:
    system = (
        "You are a productivity assistant. Analyze a todo task and suggest the best priority level. "
        'Respond ONLY with valid JSON, no markdown: {"priority": "low|medium|high", "reasoning": "one sentence"}.'
    )
    parts = [f"Title: {title}"]
    if description:
        parts.append(f"Description: {description}")
    if due_date:
        parts.append(f"Due date: {due_date}")

    raw = _call_groq(system, "\n".join(parts), max_tokens=300)
    data = _parse_json(raw, "priority suggestion")

    try:
        return PrioritySuggestResponse(
            suggested_priority=data["priority"],
            reasoning=data["reasoning"],
        )
    except KeyError as e:
        raise AIServiceError(f"Missing field in priority response: {str(e)}")
