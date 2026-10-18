"""Dedicated reviewer entrypoint: investigator pages are not registered."""
import streamlit as st
st.session_state['reviewer_only'] = True
st.navigation([st.Page('streamlit_app.py', title='Reference review', default=True)], position='hidden').run()
