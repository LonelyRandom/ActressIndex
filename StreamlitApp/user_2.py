import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import re
from upload_image import upload_to_database, delete_cloudinary_image, rename_cloudinary_image
import pandas as pd
from dateutil.relativedelta import relativedelta

STATUS_OPTS = [
    "Not Checked",
    "Pass",
    "Drop"
]

# Fungsi untuk membaca data dari Google Sheets ke DataFrame
def load_data_actress(conn):
    try:
        df = conn.read(worksheet="VList", usecols=list(range(4)))
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def load_data_film(conn):
    try:
        df = conn.read(worksheet="VCode", usecols=list(range(2)))
        return df
    except Exception as e:
        return pd.DataFrame()

# Fungsi untuk update data ke Google Sheets dari DataFrame
def update_google_sheets(df, conn):
    try:
        # Pastikan data adalah DataFrame
        if not isinstance(df, pd.DataFrame):
            st.error("Data must be a pandas DataFrame")
            return False
        
        # Update ke Google Sheets
        conn.update(worksheet="VList", data=df)
        return True
    except Exception as e:
        st.error(f"Error updating Google Sheets: {e}")
        return False

# Fungsi untuk inisialisasi/maintain DataFrame di session state
def init_dataframe(conn):
    """Inisialisasi DataFrame di session state"""
    if "actress_df" not in st.session_state:
        # Load data dari Google Sheets
        df = load_data_actress(conn)
        if df.empty:
            # Jika kosong, buat DataFrame dengan struktur yang benar
            df = pd.DataFrame(columns=[
                'Picture', 'Name (Alphabet)', 'Name (Kanji)', 'Status'
            ])
        
        # Simpan di session state
        st.session_state.actress_df = df
        st.session_state.data_loaded = True
        return df
    else:
        return st.session_state.actress_df

def init_dataframe_film(conn):
    """Inisialisasi DataFrame di session state"""
    if "film_df" not in st.session_state:
        df = load_data_film(conn)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Code', 'Picture'
            ])
        
        st.session_state.film_df = df
        st.session_state.data_loaded = True
        return df
    else:
        return st.session_state.film_df

# --- FUNGSI ALTERNATIF: Grid Layout tanpa Pagination ---
def display_film_grid(df, cards_per_row=4):
    """
    Menampilkan semua card sekaligus dalam grid
    """

    # Hitung berapa baris yang dibutuhkan
    n_rows = (len(df) + cards_per_row - 1) // cards_per_row
    # Filter data
    filtered_df = df.copy()
    if st.session_state.get('search_reset', False):
            st.session_state.search_reset = False
            st.session_state.search_bar = ''
    with st.container(horizontal=True, vertical_alignment='bottom'):
        search_name = st.text_input("🔍 Cari nama aktris:", placeholder="Nama atau kode...", key='search_bar')
        if st.button('Clear'):
            st.session_state.search_reset = True
            st.rerun()

    if search_name:
        mask = (filtered_df['Actress Name'].str.contains(search_name, case=False, na=False) | 
                filtered_df['Code'].str.contains(search_name, case=False, na=False))
        filtered_df = filtered_df[mask]
          
    for row in range(n_rows):
        cols = st.columns(cards_per_row)
        
        for col_idx in range(cards_per_row):
            idx = row * cards_per_row + col_idx
            if idx < len(filtered_df):
                actress = filtered_df.iloc[idx]
                with cols[col_idx]:
                    # Versi sederhana tanpa HTML
                    st.image(
                        actress['Picture'],
                        caption=actress['Code']
                    )

                    with st.container(horizontal=True):
                        if st.button('✏️ Edit', key=f'film_edit_{idx}', use_container_width=True):
                            st.session_state.viewing_film_index = idx
                            st.session_state.editing_film_index = idx
                            st.rerun()
                        if st.button('🗑️ Delete', key=f'film_delete_{idx}', use_container_width=True):
                            delete_film()
                            st.rerun()
                    st.space('small')

def simple_home(conn):
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Home Page</h1>", unsafe_allow_html=True)
    df_actress = init_dataframe(conn)
    df_film = init_dataframe_film(conn)

    left, right = st.columns(2)
    with left:
        with st.container(key='ActressList'):
            st.header('🌟 Actress List')
            with st.container(key='Actress Info 1', horizontal=True):
                st.metric('Actress Count' , len(df_actress))
                st.metric('Not Checked',len(df_actress[df_actress['Status'] == 'Not Checked']))
            with st.container(key='Actress Info 2', horizontal=True ):
                st.metric('Pass', len(df_actress[df_actress['Status'] == 'Pass']))
                st.metric('Drop', len(df_actress[df_actress['Status'] == 'Drop']))
            if st.button('Go To Actress →'):
                return 'actress'
    with right:
        with st.container(key='FilmList'):
            st.header('🎬 Film List')
            with st.container(horizontal=True):
                with st.container(key='Film Info 1', horizontal=False):
                    st.metric('Film Count', len(df_film))
            if st.button('Go To Film →'):
                return 'film'
    
    if st.button('🔐 Logout', use_container_width=True, type='primary'):
        st.session_state.clear()
        return 'login'
    
    # CSS custom untuk container tertentu
    st.markdown("""
    <style>
    /* Container dengan key ActressList */
    .st-key-ActressList {
        background-color: #ffc629; /* Pink soft */
        padding: 30px 20px 50px 20px;
        border-radius: 10px;
    }

    .st-key-MainContainer {
        background-color: #e6e7f2; /* Pink soft */
        padding: 30px 20px 50px 20px;
        border-radius: 10px;
    }
                
    /* Container dengan key FilmList */
    .st-key-FilmList {
        background-color: #40b3ff; /* Pink soft */
        padding: 30px 20px 50px 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def simple_film(conn):
    # Inisialisasi variabel kontrol
    if "editing_film_index" not in st.session_state:
        st.session_state.editing_film_index = None
    if "viewing_film_index" not in st.session_state:
        st.session_state.viewing_film_index = None

    df = init_dataframe_film(conn)

    @st.dialog("🎬 Film Details", width='small')
    def show_film_details():
        index = st.session_state.viewing_film_index

        if index is None or index >= len(df):
            st.warning("No film selected")
            st.stop()
        
        if st.session_state.editing_film_index == index:
            show_edit_film(index)

    def show_edit_film(index):
        film = df.iloc[index]

        with st.container(horizontal_alignment='center'): 
            st.markdown(f"### ✏️ Editing: {film['Code']}")
            st.image(film['Picture'], width=250)
            new_pic = st.file_uploader('Change Image', type=['png', 'jpg', 'jpeg'], key=f'film_picture_{index}')
            if new_pic is not None:
                st.image(new_pic, width=250)
    
        edited_code = st.text_input('Code', placeholder='Enter film code (e.g. MIDV-791)', value=film['Code'], key=f'film_code_{index}')
        
        # Tombol aksi
        if st.button("🗑️ Delete Actress", use_container_width=True, type="secondary", key=f"delete_{index}"):
            delete_film(index)

        with st.container(horizontal=True):
            if st.button("💾 Save", use_container_width=True, type="primary", key=f"save_{index}"):
                join_code = edited_code.upper()
                clean_code = re.sub(r'[^\w]', '', join_code)
                clean_code = "V" + clean_code

                old_filename = str(film['Picture']).split('/')[-1]
                old_public_id = old_filename.split('.')[0]
                # kalau cuma ganti foto
                if new_pic and (edited_code.upper() == film['Code']):
                    if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower():
                        try:
                            delete_cloudinary_image(old_public_id)
                        except Exception as e:
                            st.warning(f"Could not delete old image: {e}")
                            st.stop()
                    final_picture_url = upload_to_database(new_pic, clean_code)
                    if not final_picture_url:
                        st.error("Failed to upload new image")
                        st.stop()
                # kalau ganti foto dan code
                elif new_pic and (film['Code'] != edited_code.upper()):
                    if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower():
                        try:
                            delete_cloudinary_image(old_public_id)
                        except Exception as e:
                            st.warning(f"Could not delete old image: {e}")
                            st.stop()
                        final_picture_url = upload_to_database(new_pic, clean_code)
                        if not final_picture_url:
                            st.error("Failed to upload new image")
                            st.stop()
                # kalau cuma ganti code
                elif not new_pic and (film['Code'] != edited_code.upper()):
                    if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower():
                        try:
                            final_picture_url = rename_cloudinary_image(old_public_id, clean_code)
                        except Exception as e:
                            st.warning(f'Could not rename old image: {e}')
                            st.stop()
                else:
                    final_picture_url = film['Picture']
                    
                # Update data di DataFrame
                df.at[index, 'Picture'] = final_picture_url
                df.at[index, 'Code'] = edited_code
                
                # Update ke Google Sheets
                if update_google_sheets(df,conn,'film'):
                    st.session_state.film_df = df  # Update session state
                else:
                    st.error("❌ Failed to update Google Sheets")
                    st.stop()
                
                st.session_state.editing_film_index = None
                st.rerun()
                
            if st.button('❌ Close', use_container_width=True):
                st.session_state.editing_film_index = None
                st.rerun()
    
    def delete_film(index):
        film = df.loc[index]
        pic_filename = str(film['Picture']).split('/')[-1]
        pic_id = pic_filename.split('.')[0]

        if 'placeholder' not in pic_id:
            delete_cloudinary_image(pic_id)

        df.drop(index, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Update ke Google Sheets
        if update_google_sheets(df,conn,'film'):
            st.session_state.film_df = df
        else:
            st.error("❌ Failed to delete actress from Google Sheets")
            st.stop()
        
        st.session_state.editing_film_index = None
        st.rerun()
    
    @st.dialog("➕ Add New Film", width='small')
    def add_new_film():
        if st.session_state.get('film_reset', False):
            st.session_state.film_reset = False
            st.session_state.new_code = ''

        if 'new_film_reset' not in st.session_state:
            st.session_state.new_film_reset = 0
        
        reset_film = st.session_state.new_film_reset

        new_picture = st.file_uploader('Image', type=['png', 'jpg', 'jpeg'], key=f'new_film_picture_{reset_film}')
        
        if not new_picture is None:
            with st.container(horizontal_alignment='center'):
                st.image(new_picture, width=200)
        else:
            new_picture = st.secrets.indicators.PLACEHOLDER_IMG

        new_code = st.text_input('Code*', key='new_code', placeholder='MIDV-791, MIDV 791, midv 791 or midv-791')
        
        with st.container(key='film_new_button', horizontal=True):
            if st.button('💾 Add Film', use_container_width=True):
                if new_code:
                    if new_picture:
                        join_name = new_code.upper()
                        clean_name = re.sub(r'[^\w]', '', join_name)
                        clean_name = "V" + clean_name
                        picture_url = upload_to_database(new_picture, clean_name)
                    else:
                        picture_url = st.secrets.indicators.PLACEHOLDER_IMG_POSTER
                    
                    new_row = pd.DataFrame([{
                        'Code': new_code,
                        'Picture': picture_url
                    }])

                    df = st.session_state.film_df
                    new_film_code = new_row['Code'].iloc[0]

                    if new_film_code in df['Code'].values:
                        st.warning(f'⚠️ Code {new_film_code} already exist in database')
                        st.stop()
                    else:
                        df = pd.concat([df,new_row], ignore_index=True)
                        if update_google_sheets(df,conn,'film'):
                            st.session_state.film_df = df
                    
                    st.rerun()
                else:
                    st.error('Fill mandatory fields first! (*)')
                    st.stop()
    with st.sidebar:
        if st.button('⬅️ Back', use_container_width=True):
            return 'home'
        st.markdown('---')
        if st.button('➕ Add New Film', use_container_width=True):
            add_new_film()
        if st.button('🔐 Logout', use_container_width=True):
            st.session_state.clear()
            return 'login'
    
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Film List</h1>", unsafe_allow_html=True)

    if st.session_state.viewing_film_index is not None:
        show_film_details()
    
    cards_per_row=4
    # Hitung berapa baris yang dibutuhkan
    n_rows = (len(df) + cards_per_row - 1) // cards_per_row
    # Filter data
    filtered_df = df.copy()
    if st.session_state.get('search_reset', False):
            st.session_state.search_reset = False
            st.session_state.search_bar = ''
    with st.container(horizontal=True, vertical_alignment='bottom'):
        search_name = st.text_input("🔍 Cari nama aktris:", placeholder="Nama atau kode...", key='search_bar')
        if st.button('Clear'):
            st.session_state.search_reset = True
            st.rerun()

    if search_name:
        mask = (filtered_df['Actress Name'].str.contains(search_name, case=False, na=False) | 
                filtered_df['Code'].str.contains(search_name, case=False, na=False))
        filtered_df = filtered_df[mask]
          
    for row in range(n_rows):
        cols = st.columns(cards_per_row)
        
        for col_idx in range(cards_per_row):
            idx = row * cards_per_row + col_idx
            if idx < len(filtered_df):
                actress = filtered_df.iloc[idx]
                with cols[col_idx]:
                    # Versi sederhana tanpa HTML
                    st.image(
                        actress['Picture'],
                        caption=actress['Code']
                    )

                    with st.container(horizontal=True):
                        if st.button('✏️ Edit', key=f'film_edit_{idx}', use_container_width=True):
                            st.session_state.viewing_film_index = idx
                            st.session_state.editing_film_index = idx
                            st.rerun()
                        if st.button('🗑️ Delete', key=f'film_delete_{idx}', use_container_width=True):
                            delete_film(idx)
                            st.rerun()
                    st.space('small')
    st.markdown("""
    <style>
    /* Hover effect untuk card */
    .actress-card:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
        border-color: #004cff !important;
    }
    
    /* Smooth transition */
    .actress-card {
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .actress-card {
            height: 420px !important;
        }
    }
    
    /* Custom scrollbar untuk container */
    .st-emotion-cache-1jicfl2 {
        scrollbar-width: thin;
        scrollbar-color: #888 #f1f1f1;
    }
    
    /* Better button styling */
    .stButton > button {
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* ================= DESKTOP ================= */
    @media (min-width: 768px) {
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100% !important;
            width: 300px !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease-in-out;
            z-index: 999999 !important;
            box-shadow: 2px 0 20px rgba(0,0,0,0.2) !important;
        }

        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0) !important;
        }

        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
    }

    /* ================= MOBILE ================= */
    @media (max-width: 767px) {
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            width: 100vw !important;
            max-width: 100vw !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease-in-out;
            z-index: 999999 !important;
        }

        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0) !important;
        }

        .stSidebarCollapseButton button {
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 1000000 !important;
            font-size: 24px !important;
            padding: 14px !important;
            background: rgba(0,0,0,0.1) !important;
            border-radius: 50% !important;
        }

        .main .block-container {
            padding: 1rem !important;
        }
    }

    /* ================= OVERLAY ================= */
    .sidebar-overlay {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.5);
        z-index: 999998;
        backdrop-filter: blur(2px);
    }

    /* Hide default arrow */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>

    <script>
    document.addEventListener('DOMContentLoaded', function () {

        const waitForSidebar = setInterval(() => {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            const closeBtn = sidebar?.querySelector('button[kind="header"]');

            if (sidebar && closeBtn) {
                clearInterval(waitForSidebar);

                /* ===== AUTO CLOSE ON FIRST LOAD ===== */
                if (sidebar.getAttribute('aria-expanded') === 'true') {
                    closeBtn.click();
                }

                /* ===== CREATE OVERLAY ===== */
                const overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                document.body.appendChild(overlay);

                /* ===== OBSERVE SIDEBAR STATE ===== */
                const observer = new MutationObserver(() => {
                    const expanded = sidebar.getAttribute('aria-expanded') === 'true';
                    overlay.style.display = expanded ? 'block' : 'none';
                    document.body.style.overflow = expanded ? 'hidden' : 'auto';
                });

                observer.observe(sidebar, { attributes: true });

                /* ===== CLICK OVERLAY TO CLOSE ===== */
                overlay.addEventListener('click', () => closeBtn.click());

                /* ===== ESC KEY TO CLOSE ===== */
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape' && overlay.style.display === 'block') {
                        closeBtn.click();
                    }
                });
            }
        }, 100);
    });
    </script>
    """, unsafe_allow_html=True)

def simple_actress(conn):
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Actress List</h1>", unsafe_allow_html=True)

    if 'initial' not in st.session_state:
        st.session_state.initial = False

    # Fungsi untuk refresh data dari Google Sheets
    def refresh_data():
        """Refresh data dari Google Sheets ke session state"""
        try:
            with st.spinner("🔄 Refreshing data from Google Sheets..."):
                # Load data baru
                st.cache_data.clear()
                df = load_data_actress(conn)
    
                if not df.empty:
                    # Clear dan update session state
                    st.session_state.actress_df = df
                    st.session_state.data_loaded = True
                    
                    # Clear editing/viewing states
                    if "editing_index" in st.session_state:
                        st.session_state.editing_index = None
                    if "viewing_index" in st.session_state:
                        st.session_state.viewing_index = None
                    if "adding_new" in st.session_state:
                        st.session_state.adding_new = False
                    
                    st.rerun()
                else:
                    st.warning("⚠️ No data found in Google Sheets")
                    st.stop()
        except Exception as e:
            st.error(f"❌ Error refreshing data: {e}")
            st.stop()

    # Inisialisasi DataFrame
    if st.session_state.initial == False:
        df = init_dataframe(conn)

    # Inisialisasi variabel kontrol
    if "editing_index" not in st.session_state:
        st.session_state.editing_index = None
    if "viewing_index" not in st.session_state:
        st.session_state.viewing_index = None
    if "adding_new" not in st.session_state:
        st.session_state.adding_new = False
   
    # Dialog untuk menampilkan detail lengkap
    @st.dialog("🎬 Actress Details", width="medium")
    def show_actress_details():
        index = st.session_state.viewing_index
        
        if index is None or index >= len(df):
            st.warning("No actress selected")
            return
            
        if st.session_state.editing_index == index:
            show_edit_mode(index)
        else:
            show_view_mode(index)

    def show_view_mode(index):
        actress = df.iloc[index]
        
        # Layout utama dengan gambar dan info dasar
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(actress['Picture'] if pd.notna(actress['Picture']) else "", width=200)
            
            # Tombol Edit dan Close
            col_edit, col_close = st.columns(2)
            with col_edit:
                if st.button("✏️ Edit", use_container_width=True, key=f"edit_btn_{index}"):
                    st.session_state.editing_index = index
                    st.rerun()
            with col_close:
                if st.button("❌ Close", use_container_width=True, key=f"close_{index}"):
                    st.session_state.viewing_index = None
                    st.session_state.editing_index = None
                    st.rerun()
        
        with col2:
            # Info dasar dalam metrics
            st.markdown("### Basic Information")
            st.metric("Name (Alphabet)", actress['Name (Alphabet)'])
            st.metric("Name (Kanji)", actress['Name (Kanji)'])

            # Status dengan badge warna
            status_text = actress['Status'] if pd.notna(actress['Status']) else "Active"
            if str(status_text).lower() == "pass":
                st.metric("Status", f"🟢 {status_text}")
            elif str(status_text).lower() == "drop":
                st.metric("Status", f"🔴 {status_text}")
            else:
                st.metric("Status", f"⚪ {status_text}")

        st.markdown("---")
        
        col7, col8 = st.columns(2)
        with col7:
            if st.button("💾 Save Notes", use_container_width=True, key=f"save_{index}"):
                
                if update_google_sheets(df,conn):
                    st.session_state.actress_df = df  # Update session state
                else:
                    st.error("❌ Failed to update Google Sheets")
                
                st.rerun()
        
        with col8:
            if st.button("Close", use_container_width=True, key=f'cancel_{index}', type='primary'):
                st.session_state.viewing_index = None
                st.session_state.editing_index = None
                st.rerun()

    def show_edit_mode(index):
        actress = df.iloc[index]
        
        st.markdown(f"### ✏️ Editing: {actress['Name (Alphabet)']}")
        
        # Layout columns
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display current image
            if pd.notna(actress['Picture']) and actress['Picture']:
                st.image(actress['Picture'], width=200)
            else:
                st.write("No picture available")
            
            # Image uploader
            new_pic = st.file_uploader("Change Image", type=['png', 'jpg', 'jpeg'], key=f"uploader_{index}")
            if new_pic is not None:
                st.image(new_pic, width=200)
            
        
        with col2:
            # Basic Information
            st.subheader("Basic Information")
            status_index = STATUS_OPTS.index(actress['Status']) if actress['Status'] in STATUS_OPTS else 0

            edited_name = st.text_input(
                "Name (Alphabet)", 
                value=actress['Name (Alphabet)'] if pd.notna(actress['Name (Alphabet)']) else "",
                placeholder="Enter name in alphabet",
                key=f"name_{index}"
            )
            
            edited_kanji = st.text_input(
                "Name (Kanji)", 
                value=actress['Name (Kanji)'] if pd.notna(actress['Name (Kanji)']) else "",
                placeholder="Enter name in kanji",
                key=f"kanji_{index}"
            )

            edited_status = st.selectbox(
                "Status", 
                options=STATUS_OPTS, 
                index=status_index,
                key=f"status_{index}"
            )
        
            # Tombol aksi
            if st.button("← Back to View", use_container_width=True, key=f"back_{index}"):
                st.session_state.editing_index = None
                st.rerun()
            
            if st.button("Close", use_container_width=True, key=f"close_{index}"):
                st.session_state.viewing_index = None
                st.session_state.editing_index = None
                st.rerun()
                
            if st.button("🗑️ Delete Actress", use_container_width=True, type="secondary", key=f"delete_{index}"):
                delete_actress(index)

        # Save changes
        if st.button("💾 Save Changes", use_container_width=True, type="primary", key=f"save_{index}"):
            if edited_name not in df['Name (Alphabet)'].values:
                # Generate clean name untuk public_id
                join_name = edited_name
                clean_name = re.sub(r'[^\w]', '', join_name)
                clean_name = "V" + clean_name

                if new_pic:
                    # Hapus gambar lama jika bukan placeholder
                    if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture'].iloc[0]).lower():
                        try:
                            old_filename = str(actress['Picture']).split('/')[-1]
                            old_public_id = old_filename.split('.')[0]
                            delete_cloudinary_image(old_public_id)
                        except Exception as e:
                            st.warning(f"Could not delete old image: {e}")
                    
                    # Upload gambar baru
                    final_picture_url = upload_to_database(new_pic, clean_name)
                    if not final_picture_url:
                        st.error("Failed to upload new image")
                        return
                elif actress['Name (Alphabet)'] != edited_name:
                    try:
                        old_filename = str(actress['Picture']).split('/')[-1]
                        old_public_id = old_filename.split('.')[0]

                        final_picture_url = rename_cloudinary_image(old_public_id, clean_name)
                    except Exception as e:
                        st.warning(f'Could not rename old image: {e}')
                        st.stop()

                    
                # Update data di DataFrame
                df.at[index, 'Name (Alphabet)'] = edited_name
                df.at[index, 'Picture'] = final_picture_url
                df.at[index, 'Status'] = edited_status
                df.at[index, 'Name (Kanji)'] = edited_kanji
                
                # Update ke Google Sheets
                if update_google_sheets(df,conn):
                    st.success("✅ Data updated successfully in Google Sheets!")
                    st.session_state.actress_df = df  # Update session state
                else:
                    st.error("❌ Failed to update Google Sheets")
                
                st.session_state.editing_index = None
                st.rerun()
            else:
                st.warning(f"⚠️ Aktris '{edited_kanji}' sudah ada di database!")
                st.stop()

    def delete_actress(index):
        # Hapus data dari DataFrame
        actress = df.loc[index]
        pic_filename = str(actress['Picture']).split('/')[-1]
        pic_id = pic_filename.split('.')[0]

        if 'placeholder' not in pic_id:
            delete_cloudinary_image(pic_id)

        df.drop(index, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Update ke Google Sheets
        if update_google_sheets(df,conn):
            st.success("✅ Actress deleted successfully from Google Sheets!")
            st.session_state.actress_df = df
        else:
            st.error("❌ Failed to delete actress from Google Sheets")
        
        st.session_state.editing_index = None
        st.session_state.viewing_index = None
        st.rerun()
    
        
    # Dialog untuk menambah aktris baru
    @st.dialog("➕ Add New Actress", width="large")
    def add_new_actress():
        if st.session_state.get('reset_flag', False):
            st.session_state.reset_flage = False
            st.session_state.new_name = ''
            st.session_state.new_kanji = ''
            st.session_state.new_status = STATUS_OPTS[0]
        
        if 'new_pic_reset' not in st.session_state:
            st.session_state.new_pic_reset = 0
        
        reset_pic = st.session_state.new_pic_reset        
 
        # Basic Information
        st.subheader("Basic Information")

        new_picture = st.file_uploader("Image", type=['png', 'jpg', 'jpeg'], key=f'new_picture_{reset_pic}')

        if not new_picture is None:
            st.image(new_picture, width=200)    
        else:
            new_picture = st.secrets.indicators.PLACEHOLDER_IMG

        new_name = st.text_input("Name (Alphabet)*", placeholder="Enter name in alphabet", key='new_name')
        new_kanji = st.text_input("Name (Kanji)*", placeholder="Enter name in kanji", key='new_kanji')
        new_status = st.selectbox("Status", options=STATUS_OPTS, key='new_status')
           
        # Tombol submit
        with st.container(horizontal=True):
            submit_new = st.button("💾 Add Actress", use_container_width=True)
            cancel_new = st.button("❌ Cancel", use_container_width=True)
        
        if submit_new:
            if not new_name and not new_kanji:
                if new_picture:
                    join_name = new_name
                    clean_name = re.sub(r'[^\w]', '', join_name)
                    clean_name = "N" + clean_name
                    picture_url = upload_to_database(new_picture, clean_name)
                else:
                    picture_url = st.secrets.indicators.PLACEHOLDER_IMG

                # Create new row data
                new_row = pd.DataFrame([{
                    'Name (Alphabet)': new_name,
                    'Name (Kanji)': new_kanji,
                    'Picture': picture_url,
                    'Status': new_status
                }])

                # Add to DataFrame
                df = st.session_state.actress_df
                new_name_alpha = new_row['Name (Alphabet)'].iloc[0]

                if new_name_alpha in df['Name (Kanji)'].values:
                    st.warning(f"⚠️ Aktris '{new_name_alpha}' sudah ada di database!")
                    st.stop()
                else:
                    df = pd.concat([df, new_row], ignore_index=True)       
                    # Update ke Google Sheets
                    if update_google_sheets(df, conn):
                        st.success("✅ New actress added successfully to Google Sheets!")
                        st.session_state.actress_df = df  # Update session state
                    else:
                        st.error("❌ Failed to add new actress to Google Sheets")
                    
                    st.session_state.adding_new = False
                    st.rerun()
            else:
                st.error('Fill mandatory fields first!') # Error disini
                st.stop()
        
        if cancel_new:
            st.session_state.adding_new = False
            st.rerun()

    # Sidebar
    with st.sidebar:
        if st.button('⬅️ Back', use_container_width=True):
            return 'home'
        st.header(f'Actress Listed : {len(st.session_state.actress_df)}')
        st.markdown("---")

        st.header("Filters")
        show_not_checked = st.checkbox("Not Checked", value=True)
        show_pass = st.checkbox("Pass", value=True)
        show_drop = st.checkbox("Drop", value=True)
        
        st.markdown("---")
        st.subheader("Management")
        if st.button("➕ Add New Actress", use_container_width=True):
            st.session_state.adding_new = True
        
        # Tombol refresh data
        if st.button("🔄 Refresh Data", use_container_width=True):
            refresh_data()
            st.rerun()
        
        if st.button('🔐 Logout', use_container_width=True):
            st.session_state.clear()
            return 'login'


    # Tampilkan dialog add new jika needed
    if st.session_state.adding_new:
        add_new_actress()

    # Tampilkan dialog details jika needed
    if st.session_state.viewing_index is not None:
        show_actress_details()

    # # Tampilkan grid actress
    # with mid:
    if not df.empty and 'Picture' in df.columns:
        if st.session_state.get('search_reset', False):
            st.session_state.search_reset = False
            st.session_state.search_bar = ''
        
        search_container = st.container(horizontal=True, vertical_alignment='bottom')

        with search_container:
            search_query = st.text_input("🔍 Search actress by Name (Alphabet / Kanji):", 
                            placeholder="Type name to search...", key='search_bar')
            if st.button('Clear'):
                st.session_state.search_reset = True
                st.rerun()

        # Filter DataFrame berdasarkan status
        filtered_df = df.copy()
        filtered_df = filtered_df.sort_values(by='Name (Alphabet)', ascending=True)

        # Buat kondisi filter
        status_conditions = []
        if show_not_checked:
            status_conditions.append(filtered_df['Status'].str.lower() == 'not checked')
        if show_pass:
            status_conditions.append(filtered_df['Status'].str.lower() == 'pass')
        if show_drop:
            status_conditions.append(filtered_df['Status'].str.lower() == 'drop')
        
        if status_conditions:
            # Gabungkan kondisi dengan OR
            mask = status_conditions[0]
            for condition in status_conditions[1:]:
                mask = mask | condition
            
            filtered_df = filtered_df[mask]
        else:
            filtered_df = pd.DataFrame()  # Kosongkan jika tidak ada filter yang dipilih
        
        if not search_query and not search_query.isspace() and not filtered_df.empty:
            n_rows = (len(filtered_df) + 5 - 1) // 5
            rows = [st.columns(5) for _ in range(n_rows)]
            cols = [column for row in rows for column in row]
            
            for i, (col, idx) in enumerate(zip(cols, filtered_df.index)):
                actress = df.iloc[idx]
                
                try:
                    with col:
                        cat_url = actress['Picture'] if pd.notna(actress['Picture']) else ""
                        name_text = actress['Name (Alphabet)'] if pd.notna(actress['Name (Alphabet)']) else ""
                        kanji_text = actress['Name (Kanji)'] if pd.notna(actress['Name (Kanji)']) else ""
                        
                        # Buat card dengan HTML lengkap
                        card_html = f"""
                        <div class="card-wrapper">
                            <div class="cat-card">
                                <div class="cat-image-container">
                                    <img src="{cat_url}" class="cat-image" width="150" height="150">
                                </div>
                                <div class="card-divider"></div>"""
                        
                        if name_text and kanji_text:
                            card_html += f"""<div class="cat-name">{name_text}</div>
                                <div class="cat-kanji">{kanji_text}</div>
                            """
                        elif name_text:
                            card_html += f'<div class="cat-name">{name_text}</div>'
                        elif kanji_text:
                            card_html += f'<div class="cat-kanji">{kanji_text}</div>'
                        
                        card_html += """</div>
                        </div>
                        """
                        
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Button container untuk View Details
                        if st.button("View Details", key=f"view_{idx}", use_container_width=True):
                            st.session_state.viewing_index = idx
                            st.session_state.editing_index = None
                            st.rerun()
                            
                except Exception as e:
                    with col:
                        error_html = """
                        <div class="card-wrapper">
                            <div class="cat-card">
                                <div style="text-align: center; color: #e74c3c;">
                                    <div style="font-size: 24px; margin-bottom: 10px;">😿</div>
                                    <div style="font-size: 14px;">Failed to load image</div>
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(error_html, unsafe_allow_html=True)
        elif search_query and not search_query.isspace() and not filtered_df.empty:
            search_lower = search_query.lower().strip()
            search_mask = (
                filtered_df['Name (Alphabet)'].fillna('').str.lower().str.contains(search_lower, na=False) |
                filtered_df['Name (Kanji)'].fillna('').str.contains(search_query.strip(), na=False)
            )
            filtered_df = filtered_df[search_mask]
            n_rows = (len(filtered_df) + 5 - 1) // 5
            rows = [st.columns(5) for _ in range(n_rows)]
            cols = [column for row in rows for column in row]
            
            for i, (col, idx) in enumerate(zip(cols, filtered_df.index)):
                actress = df.iloc[idx]
                
                try:
                    with col:
                        cat_url = actress['Picture'] if pd.notna(actress['Picture']) else ""
                        name_text = actress['Name (Alphabet)'] if pd.notna(actress['Name (Alphabet)']) else ""
                        kanji_text = actress['Name (Kanji)'] if pd.notna(actress['Name (Kanji)']) else ""
                        
                        # Buat card dengan HTML lengkap
                        card_html = f"""
                        <div class="card-wrapper">
                            <div class="cat-card">
                                <div class="cat-image-container">
                                    <img src="{cat_url}" class="cat-image" width="150" height="150">
                                </div>
                                <div class="card-divider"></div>"""
                        
                        if name_text and kanji_text:
                            card_html += f"""<div class="cat-name">{name_text}</div>
                                <div class="cat-kanji">{kanji_text}</div>
                            """
                        elif name_text:
                            card_html += f'<div class="cat-name">{name_text}</div>'
                        elif kanji_text:
                            card_html += f'<div class="cat-kanji">{kanji_text}</div>'
                        
                        card_html += """</div>
                        </div>
                        """
                        
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Button container untuk View Details
                        if st.button("View Details", key=f"view_{idx}", use_container_width=True):
                            st.session_state.viewing_index = idx
                            st.session_state.editing_index = None
                            st.rerun()
                            
                except Exception as e:
                    with col:
                        error_html = """
                        <div class="card-wrapper">
                            <div class="cat-card">
                                <div style="text-align: center; color: #e74c3c;">
                                    <div style="font-size: 24px; margin-bottom: 10px;">😿</div>
                                    <div style="font-size: 14px;">Failed to load image</div>
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(error_html, unsafe_allow_html=True)
        else:
            st.warning("No actresses match the selected filters.")
    else:
        st.info("No actress data available. Click 'Add New Actress' to get started!")

    # CSS untuk styling card yang estetik
    st.markdown("""
    <style>
        .cat-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 20px 15px;
            margin: 10px;
            border-radius: 15px;
            border: 2px solid #e0e0e0;
            background: linear-gradient(135deg, #F5E5E1 0%, #f8f9fa 100%);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            min-height: 280px;
            width: 100%;
            max-width: 220px;
            cursor: pointer;
        }
        .cat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
            border-color: #ff6b6b;
        }
        .cat-image-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 15px;
            width: 130px;
            height: 130px;
            overflow: hidden;
            border-radius: 10px;
            background: linear-gradient(135deg, #F5E5E1 0%, #f8f9fa 100%);
        }
        .cat-image {
            border-radius: 10px;
            object-fit: cover;
            max-width: 130px;
            max-height: 130px;
            border: 2px solid #ff6b6b;
        }
        .cat-name {
            font-weight: 700;
            font-size: 16px;
            color: #2c3e50;
            margin: 5px 0;
            line-height: 1.3;
        }
        .cat-kanji {
            font-size: 18px;
            color: #e74c3c;
            margin: 5px 0;
            font-weight: 500;
            line-height: 1.3;
        }
        .card-divider {
            width: 50px;
            height: 2px;
            background: linear-gradient(90deg, #ff6b6b, #ffa726);
            margin: 8px 0;
            border-radius: 2px;
        }
        .card-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 5px;
            width: 100%;
        }
        .button-container {
            display: flex;
            gap: 5px;
            margin-top: 10px;
            width: 100%;
        }
        .button-container button {
            flex: 1;
        }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar akan muncul sebagai overlay tanpa menggeser content
    st.markdown("""
    <style>
    /* ================= DESKTOP ================= */
    @media (min-width: 768px) {
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100% !important;
            width: 300px !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease-in-out;
            z-index: 999999 !important;
            box-shadow: 2px 0 20px rgba(0,0,0,0.2) !important;
        }

        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0) !important;
        }

        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
    }

    /* ================= MOBILE ================= */
    @media (max-width: 767px) {
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            width: 100vw !important;
            max-width: 100vw !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease-in-out;
            z-index: 999999 !important;
        }

        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0) !important;
        }

        .stSidebarCollapseButton button {
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 1000000 !important;
            font-size: 24px !important;
            padding: 14px !important;
            background: rgba(0,0,0,0.1) !important;
            border-radius: 50% !important;
        }

        .main .block-container {
            padding: 1rem !important;
        }
    }

    /* ================= OVERLAY ================= */
    .sidebar-overlay {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.5);
        z-index: 999998;
        backdrop-filter: blur(2px);
    }

    /* Hide default arrow */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>

    <script>
    document.addEventListener('DOMContentLoaded', function () {

        const waitForSidebar = setInterval(() => {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            const closeBtn = sidebar?.querySelector('button[kind="header"]');

            if (sidebar && closeBtn) {
                clearInterval(waitForSidebar);

                /* ===== AUTO CLOSE ON FIRST LOAD ===== */
                if (sidebar.getAttribute('aria-expanded') === 'true') {
                    closeBtn.click();
                }

                /* ===== CREATE OVERLAY ===== */
                const overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                document.body.appendChild(overlay);

                /* ===== OBSERVE SIDEBAR STATE ===== */
                const observer = new MutationObserver(() => {
                    const expanded = sidebar.getAttribute('aria-expanded') === 'true';
                    overlay.style.display = expanded ? 'block' : 'none';
                    document.body.style.overflow = expanded ? 'hidden' : 'auto';
                });

                observer.observe(sidebar, { attributes: true });

                /* ===== CLICK OVERLAY TO CLOSE ===== */
                overlay.addEventListener('click', () => closeBtn.click());

                /* ===== ESC KEY TO CLOSE ===== */
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape' && overlay.style.display === 'block') {
                        closeBtn.click();
                    }
                });
            }
        }, 100);
    });
    </script>
    """, unsafe_allow_html=True)