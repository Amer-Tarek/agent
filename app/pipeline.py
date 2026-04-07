"""
Story Teller Pipeline
=====================
Graph:  START → orch → story_writer → orch → image_gen (loop) → orch → END

LLM  : Google Gemini Flash 2.5 (free tier via google-generativeai)
Image: Replicate – google/nano-banana  (swap for any free model)
"""

from __future__ import annotations

from huggingface_hub import InferenceClient
import base64, io
import os
from typing import Optional, List, Literal
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode

from langchain_core.messages import (
    AnyMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
)
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────
# State
# ──────────────────────────────────────────────

class StoryTellerState(TypedDict):
    user_input:   str
    story:        Optional[str]       # produced by story_writer
    image_output: Optional[str]       # produced by image_gen
    messages:     Optional[List[AnyMessage]]
    next:         Optional[str]       # orchestrator routing decision


# ──────────────────────────────────────────────
# LLM  (Gemini Flash 2.5 – free)
# ──────────────────────────────────────────────

def _gemini(temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",          # free-tier model
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


# ──────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────


def generate_image(prompt: str) -> str:
    """
    Generate an image using Hugging Face (free).
    Args:
        prompt (str): The text prompt describing the image to be generated.
    """
    client = InferenceClient(token=os.getenv("HF_TOKEN"))
    image = client.text_to_image(
        prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0"
    )
    path = "generated_image.png"
    image.save(path)
    print(f"[ImageGen] saved to {path}")
    return path

# ──────────────────────────────────────────────
# System Prompts
# ──────────────────────────────────────────────

ORCH_PROMPT = """
You are the Orchestrator of a Story Teller system.
You receive the user's request and decide what to do next.

Respond with EXACTLY one word (no punctuation):
- "story"  → if a story still needs to be written
- "image"  → if the story is ready but no image has been generated yet
- "end"    → if both story and image are done, or the user just wants to chat

Current context will be provided to you.
"""

STORY_PROMPT = """
You are a creative story writer.
Write a short, vivid story (150–250 words) based on the user's request.
Return ONLY the story text — no titles, no labels.
"""

IMAGE_PROMPT = """
You are an image-generation agent.
You will receive a story. Create a single rich visual prompt that captures
the most iconic scene, then call the 'generate_image' tool immediately.
"""


# ──────────────────────────────────────────────
# Nodes
# ──────────────────────────────────────────────

def orchestrator(state: StoryTellerState) -> StoryTellerState:
    """Decides the next step: story → image → end."""
    llm = _gemini(temperature=0.0)

    context = (
        f"User request: {state['user_input']}\n"
        f"Story written: {'YES' if state.get('story') else 'NO'}\n"
        f"Image generated: {'YES' if state.get('image_output') else 'NO'}"
    )

    response = llm.invoke([
        SystemMessage(content=ORCH_PROMPT),
        HumanMessage(content=context),
    ])

    decision = response.content.strip().lower()
    # Normalise
    if "story" in decision:
        decision = "story"
    elif "image" in decision:
        decision = "image"
    else:
        decision = "end"

    print(f"[Orch] → {decision}")
    return {**state, "next": decision}


def story_writer(state: StoryTellerState) -> StoryTellerState:
    """Writes a short story based on the user's request."""
    llm = _gemini(temperature=0.9)

    response = llm.invoke([
        SystemMessage(content=STORY_PROMPT),
        HumanMessage(content=state["user_input"]),
    ])

    story = response.content.strip()
    print(f"[StoryWriter] Written ({len(story)} chars)")

    messages = add_messages(
        state.get("messages") or [],
        [AIMessage(content=story)],
    )
    return {**state, "story": story, "messages": messages}


def image_gen(state: StoryTellerState) -> StoryTellerState:
    """Generates an image that illustrates the story."""
    llm = _gemini(temperature=0.4)
    llm_with_tools = llm.bind_tools([generate_image])

    story = state.get("story", state["user_input"])

    response = llm_with_tools.invoke([
        SystemMessage(content=IMAGE_PROMPT),
        HumanMessage(content=story),
    ])

    image_url = None
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            if tc["name"] == "generate_image":
                image_url = generate_image(**tc["args"])
                break

    messages = add_messages(
        state.get("messages") or [],
        [AIMessage(content=str(image_url))],
    )
    return {**state, "image_output": image_url, "messages": messages}


# ──────────────────────────────────────────────
# Routing
# ──────────────────────────────────────────────

def route_from_orch(state: StoryTellerState) -> Literal["story_writer", "image_gen", "__end__"]:
    decision = state.get("next", "end")
    if decision == "story":
        return "story_writer"
    if decision == "image":
        return "image_gen"
    return END


# ──────────────────────────────────────────────
# Graph
# ──────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(StoryTellerState)

    g.add_node("orch",         orchestrator)
    g.add_node("story_writer", story_writer)
    g.add_node("image_gen",    image_gen)

    g.set_entry_point("orch")

    g.add_conditional_edges("orch", route_from_orch, {
        "story_writer": "story_writer",
        "image_gen":    "image_gen",
        END:            END,
    })

    # Both agents loop back to orchestrator
    g.add_edge("story_writer", "orch")
    g.add_edge("image_gen",    "orch")

    return g.compile()


pipeline = build_graph()


# ──────────────────────────────────────────────
# Quick CLI test
# ──────────────────────────────────────────────

if __name__ == "__main__":
    result = pipeline.invoke({
        "user_input":   "A brave knight who discovers a dragon that just wants a friend",
        "story":        None,
        "image_output": None,
        "messages":     [],
        "next":         None,
    })
    print("\n══════ STORY ══════")
    print(result["story"])
    print("\n══════ IMAGE ══════")
    print(result["image_output"])