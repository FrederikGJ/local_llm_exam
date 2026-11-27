"""Streamlit user interface. Run from the project root: python -m streamlit run app/ui.py"""

import streamlit as st

# Swap this import for the real answer function when LLM-9 is ready.
from app.fake_answer import answer_question


st.title("Newcomer helper")
st.write("Ask about moving to Denmark, for example CPR, MitID, health insurance or renting.")

with st.form("question_form"):
    question = st.text_input("Your question")
    asked = st.form_submit_button("Ask")

if asked and question.strip():
    with st.spinner("Looking in the guides..."):
        answer = answer_question(question)
    st.markdown(answer)
