import streamlit as st
from streamlit_gsheets import GSheetsConnection


st.session_state.conns = st.connection("gsheets", type=GSheetsConnection)

conn = st.session_state.conns

if 'film_df' not in st.session_state:
    st.session_state.film_df = conn.read(worksheet="NCode", usecols=list(range(11)))


st.write(st.session_state.film_df)