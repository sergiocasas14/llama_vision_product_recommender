import asyncio
import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Product Recommender", page_icon="🛍️", layout="wide")

# ── Custom CSS ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .product-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        border-left: 4px solid #4CAF50;
    }
    .product-card h4 { margin: 0 0 0.4rem 0; color: #1a1a2e; }
    .product-card .reason { color: #444; font-size: 0.95rem; line-height: 1.5; }
    .product-card .meta { color: #888; font-size: 0.82rem; margin-top: 0.5rem; }
    .follow-up {
        background: #e8f5e9;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        font-style: italic;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛍️ Multimodal Product Recommender")
st.caption("Describe what you're looking for — optionally attach an image — and get AI-powered product recommendations.")

# ── Sidebar — settings ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    api_url = st.text_input("Backend API URL", value=API_URL)
    st.divider()
    ragas_enabled = st.toggle("📊 RAGAS Evaluation (debug)", value=False,
                              help="Run RAGAS metrics after each recommendation. Requires Ollama.")
    st.divider()
    st.markdown("**How it works**")
    st.markdown(
        "1. Enter a text prompt describing the product you want.\n"
        "2. Optionally upload an image of a similar product.\n"
        "3. The system uses multimodal embeddings + LLM reasoning to find the best matches."
    )

# ── Main input area ─────────────────────────────────────────────────────────
with st.form("recommend_form"):
    prompt = st.text_area(
        "What are you looking for?",
        placeholder="e.g. red leather boots for winter, a minimalist wooden desk lamp…",
        height=100,
    )
    image_file = st.file_uploader(
        "Attach a reference image (optional)",
        type=["jpg", "jpeg", "png", "webp"],
    )

    col_preview, col_submit = st.columns([3, 1])
    with col_preview:
        if image_file is not None:
            st.image(image_file, caption="Your reference image", width=200)
    with col_submit:
        submitted = st.form_submit_button("🔍 Recommend", use_container_width=True)

# ── Call backend & display results ──────────────────────────────────────────
if submitted:
    if not prompt.strip():
        st.warning("Please enter a text prompt.")
        st.stop()

    with st.spinner("Analysing your request and searching products…"):
        try:
            files = {}
            if image_file is not None:
                files["image"] = (image_file.name, image_file.getvalue(), image_file.type)

            resp = requests.post(
                f"{api_url.rstrip('/')}/recommend",
                data={"prompt": prompt},
                files=files if files else None,
                timeout=180,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to the backend at **{api_url}**. Is the server running?")
            st.stop()
        except requests.exceptions.HTTPError as exc:
            st.error(f"Backend error: {exc.response.status_code} — {exc.response.text[:500]}")
            st.stop()
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
            st.stop()

    result = data.get("result", {})
    recommendations = result.get("recommendations", [])
    follow_up = result.get("follow_up_question", "")
    retrieved = data.get("retrieved", [])
    plan = data.get("plan", {})

    # ── Top recommendations ─────────────────────────────────────────────────
    st.subheader("✨ Top Recommendations")

    if not recommendations:
        st.info("The model did not return any recommendations. Try rephrasing your prompt.")
    else:
        # Build a lookup from retrieved candidates for extra metadata
        retrieved_lookup = {str(c.get("item_id")): c for c in retrieved}

        for i, rec in enumerate(recommendations, 1):
            item_id = str(rec.get("item_id", ""))
            title = rec.get("title", "Unknown product")
            reason = rec.get("reason", "")
            candidate = retrieved_lookup.get(item_id, {})

            img_uri = rec.get("img_s3_uri") or candidate.get("img_s3_uri", "")
            brand = candidate.get("brand", "")
            color = candidate.get("color", "")
            material = candidate.get("material", "")
            product_type = candidate.get("product_type", "")

            # Humanize SCREAMING_SNAKE_CASE values
            if product_type:
                product_type = product_type.replace("_", " ").title()
            if material:
                material = material.replace("_", " ").title()

            # Convert S3 URI to public HTTPS URL for Berkeley Objects
            img_url = None
            if img_uri and img_uri.startswith("s3://amazon-berkeley-objects/"):
                img_url = img_uri.replace(
                    "s3://amazon-berkeley-objects/",
                    "https://amazon-berkeley-objects.s3.amazonaws.com/",
                )

            # Build metadata chips, join only non-empty ones
            meta_parts = []
            if brand:
                meta_parts.append(f"<b>Brand:</b> {brand}")
            if color:
                meta_parts.append(f"<b>Color:</b> {color}")
            if material:
                meta_parts.append(f"<b>Material:</b> {material}")
            if product_type:
                meta_parts.append(f"<b>Type:</b> {product_type}")
            meta_html = " &nbsp;|&nbsp; ".join(meta_parts)

            col_img, col_info = st.columns([1, 3])
            with col_img:
                if img_url:
                    st.image(img_url, use_container_width=True)
                else:
                    st.markdown("🖼️ *No image available*")
            with col_info:
                st.markdown(
                    f"""
                    <div class="product-card">
                        <h4>#{i} — {title}</h4>
                        <div class="reason">{reason}</div>
                        <div class="meta">{meta_html}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.divider()

    # ── Follow-up question ──────────────────────────────────────────────────
    if follow_up:
        st.markdown(f'<div class="follow-up">💬 <b>Suggestion:</b> {follow_up}</div>', unsafe_allow_html=True)

    # ── Retrieval plan (collapsible) ────────────────────────────────────────
    with st.expander("🔧 Retrieval Plan (debug)", expanded=False):
        st.json(plan)

    # ── All retrieved candidates (collapsible) ──────────────────────────────
    with st.expander(f"📦 Retrieved Candidates ({len(retrieved)})", expanded=False):
        for c in retrieved:
            cid = c.get("item_id", "")
            cname = c.get("item_name", "")
            dist = c.get("distance")
            st.markdown(
                f"- **{cname}** (id: `{cid}`, distance: `{dist:.4f}` )"
                if dist is not None
                else f"- **{cname}** (id: `{cid}`)"
            )
