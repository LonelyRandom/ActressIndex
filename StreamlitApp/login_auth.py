# login.py
import streamlit as st

# Initialize connection - letakkan di luar fungsi

def log_in(conn):    
    st.set_page_config(
        page_title="Actress Note - Login",
        page_icon="🔐",
        layout="wide"
    )
    
    if 'login_data' not in st.session_state:
        st.session_state.login_data = conn.read(worksheet="Login", usecols=list(range(2)))
    
    # Default return values
    check_login = False
    usn = None
    page = "login"
    
    left, mid, right = st.columns([1.5, 1, 1.5])
    
    with mid:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        login_button = st.button("Login")
        
        # Inisialisasi status error di session state
        if 'login_error' not in st.session_state:
            st.session_state.login_error = None
        
        if login_button:
            # Reset error state
            st.session_state.login_error = None
            
            user = st.session_state.login_data[
                st.session_state.login_data["Username"] == username
            ]
            
            if not user.empty:
                stored_password = user["Password"].iloc[0]
                
                if password == stored_password:
                    st.success("Login berhasil!")
                    st.session_state.login_error = None
                    check_login = True
                    usn = username
                    page = 'home'
                else:
                    st.session_state.login_error = "❌ Password salah"
            else:
                st.session_state.login_error = "❌ Username tidak ditemukan"
        
        # Tampilkan error jika ada
        if st.session_state.login_error:
            st.error(st.session_state.login_error)
            check_login = False
            usn = None
            page = 'login'

    return check_login, usn, page

            