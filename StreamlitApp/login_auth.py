# login.py
import streamlit as st
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def log_in_auth():    
    st.set_page_config(
        page_title="Actress Note - Login",
        page_icon="🔐",
        layout="wide"
    )
    
    left, mid, right = st.columns([1.5, 1, 1.5])
    
    with mid:
        st.markdown("<h1 style='text-align: center; margin-bottom: 15px;'>Authentication</h1>", unsafe_allow_html=True)

        if st.button("Google Authenticator", width="stretch", type="primary"):
            st.login('google')

    if hasattr(st, "user") and st.user is not None:
        if st.user.is_logged_in:
            user = hash_password(st.user.given_name+st.user.family_name)
            return st.user.is_logged_in, user
    return False, 'empty'