import json
import google.generativeai as genai

from app.core.config import settings
from app.core.errors import AIServiceError
from app.schemas.ai import (
    GeneratedTask,
    TaskBreakdownResponse,
    PrioritySuggestResponse,
)


def _get_model() -> genai.GenerativeModel:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        generation_config=genai.GenerationConfig(temperature=0.4),
    )


def _call_gemini(system: str, user: str) -> str:
    try:
        model = _get_model()
        # Gemini uses a combined prompt — prepend system instructions to user message
        full_prompt = f"{system}\n\n{user}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        err = str(e).lower()
        if "api_key" in err or "invalid" in err or "permission" in err:
            raise AIServiceError(
                "Invalid Gemini API key. Check GEMINI_API_KEY in your environment."
            )
        if "quota" in err or "rate" in err or "429" in err:
            raise AIServiceError(
                "Gemini API rate limit reached. Please try again shortly."
            )
        raise AIServiceError(f"Gemini API error: {str(e)}")


def breakdown_goal(goal: str, max_tasks: int) -> TaskBreakdownResponse:
    system = (
        "You are a productivity assistant. Break down a user's high-level goal into concrete, "
        "actionable todo tasks. Respond ONLY with valid JSON — no markdown fences, no extra text. "
        "Return an object with a 'tasks' array. Each task object must have exactly these keys: "
        "title (string), description (string), priority (one of: low, medium, high), "
        "tags (array of strings)."
    )
    user = f"Break down this goal into at most {max_tasks} clear tasks:\n\nGoal: {goal}"

    raw = _call_gemini(system, user)

    # Strip markdown code fences Gemini sometimes adds despite instructions
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(raw)
        tasks = [GeneratedTask(**t) for t in data.get("tasks", [])]
    except Exception as e:
        raise AIServiceError(f"Could not parse AI response into tasks: {str(e)}")

    return TaskBreakdownResponse(goal=goal, tasks=tasks)


def suggest_priority(title: str, description: str | None, due_date: str | None) -> PrioritySuggestResponse:
    system = (
        "You are a productivity assistant. Analyze a todo task and suggest the best priority level. "
        'Respond ONLY with valid JSON (no markdown): {"priority": "low|medium|high", "reasoning": "one sentence"}.'
    )
    parts = [f"Title: {title}"]
    if description:
        parts.append(f"Description: {description}")
    if due_date:
        parts.append(f"Due date: {due_date}")

    raw = _call_gemini(system, "\n".join(parts))
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(raw)
        return PrioritySuggestResponse(
            suggested_priority=data["priority"],
            reasoning=data["reasoning"],
        )
    except (json.JSONDecodeError, KeyError) as e:
        raise AIServiceError(f"Could not parse priority suggestion: {str(e)}")
