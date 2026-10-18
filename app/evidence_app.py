"""Standalone exploration entrypoint without investigator navigation."""
import streamlit as st
st.navigation([st.Page('visual_evidence.py', title='Visual evidence', default=True)], position='hidden').run()
