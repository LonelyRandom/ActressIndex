import streamlit as st
from streamlit_gsheets import GSheetsConnection
from login_auth import log_in
from user_1 import complex_home, complex_actress, complex_film
from user_2 import simple_home, simple_actress, simple_film

user_1 = st.secrets.indicators.USER_1
user_2 = st.secrets.indicators.USER_2

conn = st.connection("gsheets", type=GSheetsConnection)

if 'page' not in st.session_state:
    st.session_state.page = 'login'
    # st.session_state.page = 'home'

if 'usn' not in st.session_state:
    st.session_state.usn = None
    # st.session_state.usn = 'vincent'

if 'check_login' not in st.session_state:
    st.session_state.check_login = None

if st.session_state.page == 'login':
    check_login, usn, page = log_in(conn)
    st.session_state.check_login = check_login
    st.session_state.usn = usn
    st.session_state.page = page

    if check_login:
        st.rerun()
    else:
        # Tetap di login page, jangan rerun
        st.stop()  

elif st.session_state.page == 'home':
    st.set_page_config(
        layout='wide',
        page_title='ActressIndex - Home',
        page_icon='🏠'
    )
    if st.session_state.usn == user_1:
        page = complex_home(conn)
    elif st.session_state.usn == user_2:
        page = simple_home(conn)

    if not page is None:
        st.session_state.page = page
        st.rerun()

elif st.session_state.page == 'film':
    st.set_page_config(
        layout='wide',
        page_title='ActressIndex - Film',
        page_icon='🎬'
    )
    if st.session_state.usn == user_1:
        complex_film(conn)
    elif st.session_state.usn == user_2:
        simple_film(conn)

elif st.session_state.page == 'actress':
    st.set_page_config(
        layout='wide',
        page_title='ActressIndex - Actress',
        page_icon='🌟'
    )
    if st.session_state.usn == user_1:
        page = complex_actress(conn)
    elif st.session_state.usn == user_2:
        page = simple_actress(conn)

    if not page is None:
        st.session_state.page = page
        st.rerun()

