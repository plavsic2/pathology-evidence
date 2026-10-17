"""Shared Swiss-style typography and Catppuccin Mocha presentation."""
import streamlit as st


def apply_theme():
    # Local system fonts only: no font downloads or commercial font redistribution.
    st.markdown("""
    <style>
    :root { --swiss-font: "Helvetica Neue", Helvetica, Arial, sans-serif; }
    .stApp { background: #1e1e2e; color: #cdd6f4; }
    [data-testid="stSidebar"] { background: #181825; border-right: 1px solid #313244; }
    [data-testid="stHeader"] { background: #1e1e2e; }
    [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"],
    [data-baseweb="select"], input, textarea, button, label {
        font-family: var(--swiss-font) !important;
    }
    h1, h2, h3, h4 { font-family: var(--swiss-font) !important; color: #cdd6f4;
        font-weight: 600 !important; letter-spacing: -0.035em; line-height: 1.15 !important; }
    h1 { font-size: clamp(2rem, 3.5vw, 3.1rem) !important; }
    h2, h3 { letter-spacing: -0.025em; }
    p { line-height: 1.6; }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #a6adc8 !important; }
    [data-testid="stAlert"] { background: #313244; border-radius: 8px; }
    [data-testid="stAlert"] p { color: #cdd6f4; }
    [data-testid="stMainBlockContainer"] { max-width: 1440px; padding-top: 3rem; }
    [data-testid="stForm"] { background: #181825; border-color: #45475a; border-radius: 12px; }
    [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button,
    [data-testid="stDownloadButton"] button { border: 1px solid #585b70; border-radius: 8px;
        background: #313244; color: #cdd6f4; font-weight: 600; }
    [data-testid="stButton"] button:hover, [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stDownloadButton"] button:hover { border-color: #cba6f7; color: #cba6f7; }
    [data-testid="stFormSubmitButton"] button:not(:disabled) {
        background: #cba6f7; color: #11111b; border-color: #cba6f7; }
    button:focus-visible, input:focus-visible, textarea:focus-visible {
        outline: 2px solid #89dceb !important; outline-offset: 3px; }
    a { color: #b4befe; }
    </style>
    """, unsafe_allow_html=True)
