"""Shared scientific-studio presentation for the Streamlit analyst sandbox."""

import streamlit as st


def apply_studio_theme() -> None:
    """Apply the shared visual language without changing calculation behavior."""
    st.markdown(
        """
        <style>
        :root {
          --studio-ink: #18222D;
          --studio-paper: #F8F7F2;
          --studio-surface: #EEF1EC;
          --studio-accent: #B4472D;
          --studio-data: #176B74;
        }
        .stApp {
          color: var(--studio-ink);
          background-color: var(--studio-paper);
          background-image:
            linear-gradient(rgba(24,34,45,.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(24,34,45,.035) 1px, transparent 1px);
          background-size: 32px 32px;
        }
        [data-testid="stSidebar"] { background: var(--studio-surface); }
        h1, h2, h3 { letter-spacing: -.025em; }
        h1 { font-family: Georgia, serif; font-size: clamp(2.6rem, 5vw, 4.8rem) !important; }
        div[data-testid="stMetric"] {
          border: 1px solid rgba(24,34,45,.16);
          background: rgba(255,255,255,.8);
          padding: 1rem;
        }
        div[data-testid="stExpander"], div[data-testid="stForm"] {
          border-radius: 0;
          border-color: rgba(24,34,45,.18);
        }
        .studio-kicker {
          margin: 0 0 .45rem;
          color: var(--studio-accent);
          font: 600 .72rem/1.4 monospace;
          letter-spacing: .15em;
          text-transform: uppercase;
        }
        .studio-question {
          max-width: 850px;
          margin: .4rem 0 2rem;
          color: rgba(24,34,45,.68);
          font-size: 1.08rem;
          line-height: 1.65;
        }
        .studio-note {
          border-left: 3px solid var(--studio-data);
          background: rgba(23,107,116,.07);
          padding: 1rem 1.2rem;
          font-size: .86rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_workbench_intro(kicker: str, title: str, question: str) -> None:
    """Render a domain page as an actuarial question rather than a calculator."""
    st.markdown(f'<p class="studio-kicker">{kicker}</p>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="studio-question">{question}</p>', unsafe_allow_html=True)
