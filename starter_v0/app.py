from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import streamlit as st

from chat import run_model_tool_loop
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools


ROOT = Path(__file__).parent
ARTIFACTS = ROOT / "artifacts"
load_lab_env(ROOT)

# Streamlit Community Cloud keeps credentials in st.secrets instead of .env.
# Local development still uses the ignored .env file above.
for secret_name in (
    "DEEPSEEK_API_KEY",
    "TAVILY_API_KEY",
    "FIRECRAWL_API_KEY",
    "RAPIDAPI_KEY",
    "RAPIDAPI_TWITTER_HOST",
):
    try:
        cloud_value = st.secrets.get(secret_name)
    except Exception:
        cloud_value = None
    if not os.getenv(secret_name) and cloud_value:
        os.environ[secret_name] = str(cloud_value)


@st.cache_resource
def load_agent_resources() -> tuple[Any, str, list[dict[str, Any]]]:
    provider = make_provider("deepseek")
    system_prompt = (ARTIFACTS / "system_prompt.md").read_text(encoding="utf-8")
    declarations = load_tool_declarations(ARTIFACTS / "tools.yaml")
    return provider, system_prompt, to_openai_tools(declarations)


st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="centered")
title_col, action_col = st.columns([5, 1])
with title_col:
    st.title("Research Agent")
    st.caption("Tìm nguồn, đọc tài liệu và tổng hợp thông tin bằng AI.")
with action_col:
    st.write("")
    if st.button("Làm mới", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

provider, system_prompt, tools = load_agent_resources()
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("tool_events"):
            with st.expander("Chi tiết công cụ"):
                st.json(message["tool_events"])

if user_text := st.chat_input("Nhập yêu cầu nghiên cứu..."):
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    history = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.messages[-10:]
    ]
    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=[{"role": "system", "content": system_prompt}, *history],
                    tools=tools,
                    model="deepseek-flash",
                    max_tool_rounds=4,
                )
                answer = result["assistant_text"] or "Agent chưa trả về nội dung."
                st.markdown(answer)
                if result["tool_events"]:
                    with st.expander("Chi tiết công cụ"):
                        st.json(result["tool_events"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "tool_events": result["tool_events"],
                })
            except Exception as exc:
                st.error(f"Không thể gọi agent: {type(exc).__name__}: {exc}")
