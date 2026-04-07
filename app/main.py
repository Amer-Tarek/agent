"""
Story Teller – Streamlit UI
Run:  streamlit run ui/app.py
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.pipeline import pipeline, StoryTellerState

# ── Page config ──────────────────────────────
st.set_page_config(
    page_title="Story Teller",
    page_icon="📖",
    layout="centered",
)

# ── Custom CSS ───────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

h1 { font-family: 'Playfair Display', serif; font-size: 2.8rem !important; }

.story-box {
    background: #fdf6ec;
    border-left: 4px solid #c8902a;
    border-radius: 6px;
    padding: 1.4rem 1.6rem;
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    line-height: 1.8;
    color: #2d1f0e;
    white-space: pre-wrap;
}

.tag {
    display: inline-block;
    background: #c8902a22;
    color: #7a4f10;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    margin-bottom: .6rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────
st.markdown("# 📖 Story Teller")
st.markdown("*Give me an idea — I'll write the story and paint the scene.*")
st.divider()

# ── Input ────────────────────────────────────
user_input = st.text_area(
    "Your idea",
    placeholder="A lonely lighthouse keeper who discovers a message in a bottle…",
    height=100,
)

generate_btn = st.button("✨ Generate Story & Image", type="primary", use_container_width=True)

# ── Run pipeline ─────────────────────────────
if generate_btn:
    if not user_input.strip():
        st.warning("Please enter an idea first.")
    else:
        with st.spinner("Crafting your story and painting the scene…"):
            initial: StoryTellerState = {
                "user_input":   user_input.strip(),
                "story":        None,
                "image_output": None,
                "messages":     [],
                "next":         None,
            }
            result = pipeline.invoke(initial)

        st.divider()

        # Story
        story = result.get("story")
        if story:
            st.markdown('<div class="tag">📜 Story</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="story-box">{story}</div>', unsafe_allow_html=True)
            st.markdown("")

        # Image
        image_url = result.get("image_output")
        if image_url:
            st.markdown('<div class="tag">🎨 Generated Image</div>', unsafe_allow_html=True)
            st.image(image_url, use_container_width=True)
        elif story:
            st.info("Image generation skipped or unavailable.")

        if not story and not image_url:
            st.error("Something went wrong. Check your API keys in .env")