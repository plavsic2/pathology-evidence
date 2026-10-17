"""Shared Swiss-style typography and black-and-yellow presentation."""
import streamlit as st


def apply_theme():
    # Local system fonts only: no font downloads or commercial font redistribution.
    st.markdown("""
    <style>
    :root { --swiss-font: "Helvetica Neue", Helvetica, Arial, sans-serif; }
    .stApp { background: #101010; color: #F2F0E8; }
    [data-testid="stSidebar"] { background: #191919; border-right: 1px solid #343434; }
    [data-testid="stHeader"] { background: #101010; }
    [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"],
    [data-baseweb="select"], input, textarea, button, label {
        font-family: var(--swiss-font) !important;
    }
    h1, h2, h3, h4 { font-family: var(--swiss-font) !important; color: #F2F0E8;
        font-weight: 600 !important; letter-spacing: -0.035em; line-height: 1.15 !important; }
    h1 { font-size: clamp(2rem, 3.5vw, 3.1rem) !important; }
    h2, h3 { letter-spacing: -0.025em; }
    p { line-height: 1.6; }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #AAA79D !important; }
    [data-testid="stAlert"] { background: #343434; border-radius: 8px; }
    [data-testid="stAlert"] p { color: #F2F0E8; }
    [data-testid="stMainBlockContainer"] { max-width: 1440px; padding-top: 3rem; }
    [data-testid="stForm"] { background: #191919; border-color: #343434; border-radius: 12px; }
    [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button,
    [data-testid="stDownloadButton"] button { border: 1px solid #343434; border-radius: 8px;
        background: #343434; color: #F2F0E8; font-weight: 600; }
    [data-testid="stButton"] button:hover, [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stDownloadButton"] button:hover { border-color: #F5C518; color: #F5C518; }
    [data-testid="stFormSubmitButton"] button:not(:disabled) {
        background: #F5C518; color: #101010; border-color: #F5C518; }
    button:focus-visible, input:focus-visible, textarea:focus-visible {
        outline: 2px solid #FFDA47 !important; outline-offset: 3px; }
    [data-testid="stFormSubmitButton"] button:not(:disabled):hover {
        background: #FFDA47; color: #101010; border-color: #FFDA47; }
    a { color: #F5C518; }
    </style>
    """, unsafe_allow_html=True)
