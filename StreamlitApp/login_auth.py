# login.py
import streamlit as st
import hashlib
import time
import gspread
from google.oauth2.service_account import Credentials

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@st.cache_resource
def get_gsheet_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["connections"]["gsheets"],
        scopes=scope
    )

    return gspread.authorize(creds)

@st.cache_resource()
def login_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["spred_title"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_LOGIN"]
    )

    return worksheet

def log_in(conn):    
    if 'login_error' not in st.session_state:
        st.session_state.login_error = None
    st.set_page_config(
        page_title="Actress Note - Login",
        page_icon="🔐",
        layout="wide"
    )
    
    if 'login_data' not in st.session_state:
        st.session_state.login_data = conn.read(worksheet="Login", usecols=list(range(3)))
    
    # Default return values
    check_login = False
    usn = None
    page = "login"
    
    left, mid, right = st.columns([1.5, 1, 1.5])
    
    with mid:
        st.markdown("<h1 style='text-align: center; margin-bottom: 15px; font-weight:700'>Login</h1>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        login_button = st.button("Login", width="stretch", type="primary")
        
        # Inisialisasi status error di session state
        
        if login_button:
            pass_hash = hash_password(username+password)
            st.session_state.login_error = None
            
            user = st.session_state.login_data[
                st.session_state.login_data["Username"] == username
            ]
            
            if not user.empty and int(user['Login Attempt'].iloc[0]) < 3:
                stored_password = user["Password"].iloc[0]
                
                if pass_hash == stored_password:
                    st.toast("✅ Login Success!")
                    time.sleep(.5)
                    st.session_state.login_error = None
                    check_login = True
                    usn = username
                    page = 'home'
                    row = user.index[0]+ 2
                    if login_worksheet().update(f"C{row}", 0):
                        st.session_state.login_data['Login Attempt'].loc[user.index[0]] = 0
                else:
                    row = user.index[0]+ 2
                    st.session_state.login_error = "❌ Incorrect Password!"
                    if login_worksheet().update(f"C{row}", int(st.session_state.login_data['Login Attempt'].iloc[user.index[0]])+1):
                        st.session_state.login_data['Login Attempt'].loc[user.index[0]] += 1
                    
                    if st.session_state.login_data['Login Attempt'].iloc[user.index[0]] == 2:
                        st.warning('You only have 1 more chance to gues the password!')

            elif int(user['Login Attempt'].iloc[0]) >= 3:
                st.error('Blocked caused too many failed login attempt!')
            else:
                st.session_state.login_error = "❌ Username not found!"
        
        # Tampilkan error jika ada
        if st.session_state.login_error:
            st.error(st.session_state.login_error)
            check_login = False
            usn = None
            page = 'login'

    return check_login, usn, page

            
