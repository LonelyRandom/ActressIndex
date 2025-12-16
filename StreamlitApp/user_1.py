import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import re
from upload_image import upload_to_database, delete_cloudinary_image, rename_cloudinary_image
import pandas as pd
from value_handling import values_handling, initial_load
from dateutil.relativedelta import relativedelta

REVIEW_OPTS = [
    'Not Watched',
    'Watched',
    'Goat'
]

STATUS_OPTS = [
    "Active",
    "Retired",
    "No Info",
    "Problem",
    "Slow Release"
]

SIZE_OPTS = [
    "?", # No Info
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J"
]

INFO = [
    "Not Checked",
    "Pass",
    "Drop"
]

# Fungsi untuk membaca data dari Google Sheets ke DataFrame
def load_data_actress(conn):
    try:
        df = conn.read(worksheet="NList", usecols=list(range(14)))
        df = values_handling(df)
        df = initial_load(df)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Fungsi untuk update data ke Google Sheets dari DataFrame
def update_google_sheets(df, conn):
    try:
        # Pastikan data adalah DataFrame
        if not isinstance(df, pd.DataFrame):
            st.error("Data must be a pandas DataFrame")
            return False
        
        # Update ke Google Sheets
        conn.update(worksheet="NList", data=df)
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
                'Review', 'Picture', 'Name (Alphabet)', 'Name (Kanji)',
                'Birthdate', 'Debut Date', 'Size', 'Measurement',
                'Height (cm)', 'Notes', 'Age', 'Debut Period',
                'Retire Date', 'Status'
            ])
        
        # Simpan di session state
        st.session_state.actress_df = df
        st.session_state.data_loaded = True
        return df
    else:
        return st.session_state.actress_df

def complex_home(conn):
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Home Page</h1>", unsafe_allow_html=True)
    df_actress = init_dataframe(conn)

    left, right = st.columns(2)
    with left:
        with st.container(key='ActressList'):
            st.header('🌟 Actress List')
            with st.container(key='Actress Info 1', horizontal=True):
                st.metric('Actress Count' , len(df_actress))
                st.metric('Watched',len(df_actress[df_actress['Review'] == 'Watched']))
            with st.container(key='Actress Info 2', horizontal=True ):
                st.metric('Not Watched', len(df_actress[df_actress['Review'] == 'Not Watched']))
                st.metric('Goat', len(df_actress[df_actress['Review'] == 'Goat']))
            if st.button('Go To Actress →'):
                return 'actress'
    with right:
        with st.container(key='FilmList'):
            st.header('🎬 Film List')
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


def complex_film(conn):
    st.write('Later')

def complex_actress(conn):
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Actress List</h1>", unsafe_allow_html=True)

    if 'initial' not in st.session_state:
        st.session_state.initial = False

    # Fungsi untuk refresh data dari Google Sheets
    def refresh_data():
        """Refresh data dari Google Sheets ke session state"""
        df = load_data_actress(conn)
        if not df.empty:
           if not df.empty:
            # Clear session state terlebih dahulu
            if "actress_df" in st.session_state:
                del st.session_state.actress_df
            if "data_loaded" in st.session_state:
                del st.session_state.data_loaded
            
            # Update session state dengan data baru
            st.session_state.actress_df = df
            st.session_state.data_loaded = True
            
            # Force reset editing/viewing states
            st.session_state.editing_index = None
            st.session_state.viewing_index = None
            st.session_state.adding_new = False
            
            st.success("✅ Data refreshed successfully from Google Sheets!")
            st.rerun()  # Penting: trigger rerun untuk update UI
        else:
            st.warning("No data found in Google Sheets")

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

    # Fungsi untuk menghitung usia berdasarkan birthdate
    def calculate_age(birthdate_str):
        try:
            if not birthdate_str or pd.isna(birthdate_str):
                return None
                
            # Handle format "30/09/1992"
            if '/' in str(birthdate_str):
                birth_date = datetime.strptime(str(birthdate_str), '%d/%m/%Y')
            else:
                birth_date = datetime.strptime(str(birthdate_str), '%B %d, %Y')
            
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except:
            return None

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
            st.markdown(f"### {actress['Name (Alphabet)']}")
            st.markdown(f"# {actress['Name (Kanji)'] if pd.notna(actress['Name (Kanji)']) else ''}")
            
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
            
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                # Review
                review_text = actress['Review'] if pd.notna(actress['Review']) else "N/A"
                st.metric("Review", review_text)
                
                # Age
                age_text = actress['Age'] if pd.notna(actress['Age']) else ""
                if not age_text and pd.notna(actress['Birthdate']):
                    calculated_age = calculate_age(actress['Birthdate'])
                    if calculated_age:
                        age_text = f"{calculated_age}"
                
                if age_text:
                    st.metric("Age", f"{age_text} years")

                # Birthdate
                if actress['Birthdate'] != '?':
                    birthdate_text = datetime.strptime(str(actress['Birthdate']), '%d/%m/%Y').date().strftime("%b, %d %Y")
                else:
                    birthdate_text = '?'

                st.metric("Birthdate", str(birthdate_text))
            
            with info_col2:
                # Height
                height_text = actress['Height (cm)'] if pd.notna(actress['Height (cm)']) else "N/A"
                st.metric("Height", height_text)
                
                # Size
                size_text = actress['Size'] if pd.notna(actress['Size']) else "N/A"
                st.metric("Size", size_text)

                # Status dengan badge warna
                status_text = actress['Status'] if pd.notna(actress['Status']) else "Active"
                if str(status_text).lower() == "active":
                    st.metric("Status", f"🟢 {status_text}")
                elif str(status_text).lower() == "retired":
                    st.metric("Status", f"🔴 {status_text}")
                else:
                    st.metric("Status", f"⚪ {status_text}")

        st.markdown("---")
        
        # Measurement dan Physical Info
        st.markdown("### Physical Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            if pd.notna(actress['Measurement']) and actress['Measurement']:
                st.markdown("#### 📏 Measurements")
                st.info(actress['Measurement'])
        
        with col4:
            # Additional physical info
            if pd.notna(actress['Size']) and actress['Size']:
                st.markdown("#### 📐 Size")
                st.info(f"**{actress['Size']}**")
        
        st.markdown("---")
        
        # Career Timeline
        st.markdown("### Career Timeline")
        
        timeline_col1, timeline_col2, timeline_col3 = st.columns(3)
        
        with timeline_col1:
            if actress['Debut Date'] != '?':
                debut_date_text = datetime.strptime(actress['Debut Date'], '%d/%m/%Y').strftime("%b, %d %Y")
            else:
                debut_date_text = '?'

            if pd.notna(actress['Debut Date']) and actress['Debut Date']:
                st.markdown("#### 🎭 Debut")
                st.write(debut_date_text)
            

        
        with timeline_col2:
            if pd.notna(actress['Debut Period']) and actress['Debut Period']:
                st.markdown("#### ⏳ Experience")
                st.write(str(actress['Debut Period']))
        
        with timeline_col3:
            if pd.notna(actress['Retire Date']) and actress['Retire Date']:
                st.markdown("#### 🏁 Retire Date")
                if actress['Retire Date'] == '?':
                    st.write('?')
                else:
                    st.write(datetime.strptime(actress['Retire Date'], '%d/%m/%Y').strftime("%b, %d %Y"))
            else:
                st.markdown("#### 🏁 Retire Date")
                st.write("Still Active")
        
        st.markdown("---")
        
        # Notes/Review
        if pd.notna(actress['Notes']) and actress['Notes']:
            st.markdown("### 📝 Notes")
            st.warning(actress['Notes'])
        
        st.markdown("---")
        
        # Personal Notes Section
        st.write("### 📖 Your Personal Notes")

        personal_notes = st.text_input(
            "Add your own notes about this actress...", 
            placeholder="Write your thoughts, reviews, or observations about this actress...",
            key=f"personal_notes_{index}"
        )
        
        col7, col8 = st.columns(2)
        with col7:
            if st.button("💾 Save Notes", use_container_width=True, key=f"save_{index}"):
                if personal_notes:
                    current_notes = df['Notes'].iloc[index]
                    edited_notes = f'{current_notes}\n - {personal_notes}'
                    df.at[index, 'Notes'] = edited_notes
                
                if update_google_sheets(df,conn):
                    st.session_state.actress_df = values_handling(df)  # Update session state
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
        
        with col2:
            # Basic Information
            st.subheader("Basic Information")
            review_index = REVIEW_OPTS.index(actress['Review']) if actress['Review'] in REVIEW_OPTS else 0
            size_index = SIZE_OPTS.index(actress['Size']) if actress['Size'] in SIZE_OPTS else 0
            status_index = STATUS_OPTS.index(actress['Status']) if actress['Status'] in STATUS_OPTS else 0

            edited_review = st.selectbox(
                "Review", 
                options=REVIEW_OPTS,
                index=review_index,
                key=f"review_{index}"
            )
            
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

            # Handle '?' Value
            if actress['Birthdate'] == '?':
                birth_date = date.today()
            else:
                birth_date = datetime.strptime(actress["Birthdate"], "%d/%m/%Y").date()

            # Birthdate
            edited_birthdate = st.date_input(
                "Birthdate",
                value=birth_date,
                key=f"birthdate_{index}"
            )
            if edited_birthdate != '?':
                age = relativedelta(date.today(), edited_birthdate).years
            else:
                age = '?'
            
            st.write('Age : ', str(age))
            
            if st.checkbox('No Info', value=(actress['Birthdate'] == '?'), key=f'check_birthdate_{index}'):
                edited_birthdate = '?'
            else:
                edited_birthdate = edited_birthdate.strftime('%d/%m/%Y')
            
        
        st.markdown("---")
        
        # Career Information
        st.subheader("Career Information")
        
        # Handle '?' value
        if actress['Debut Date'] == '?':
            debut_date = date.today()
        else:
            debut_date = datetime.strptime(actress["Debut Date"], "%d/%m/%Y").date()

        # Debut Date
        edited_debut_date = st.date_input(
            "Debut Date",
            value=debut_date,
            key=f"debut_date_{index}"
        )
        debut_no_info = st.checkbox('No Info', value = (actress['Debut Date'] == '?'), key='debut check')

        edited_status = st.selectbox(
            "Status", 
            options=STATUS_OPTS, 
            index=status_index,
            key=f"status_{index}"
        )
        
        # Retire Date (hanya muncul jika status Retired)
        if edited_status == "Retired":
            if actress['Retire Date'] == '?':
                retire_date = date.today()
            else:
                retire_date = datetime.strptime(actress["Retire Date"], "%d/%m/%Y").date()

            edited_retire_date = st.date_input(
                "Retire Date",
                value=retire_date,
                placeholder="e.g., 15/08/2024 or August 15, 2024",
                key=f"retire_date_{index}"
            )

            edited_retire_date = edited_retire_date.strftime('%d/%m/%Y')
        else:
            edited_retire_date = '?'
        
        # Debut Period
        if edited_debut_date != '?' and edited_retire_date == '?':
            period = relativedelta(date.today(), edited_debut_date)

            if period.months == 0:
                debut = f"{period.years} Year"
            else:
                debut = f"{period.years} Year {period.months} Month"

            st.write("Debut Period : ", debut)
        elif edited_debut_date != '?' and edited_retire_date != '?':
            period = relativedelta(edited_retire_date, edited_debut_date)

            if period.months == 0:
                debut = f'{period.years} Year'
            else:
                debut = f'{period.years} Year {period.months} Month'
            
        if debut_no_info:
            edited_debut_date = '?'
        else:
            edited_debut_date = edited_debut_date.strftime('%d/%m/%Y')  
        
        st.markdown("---")
        
        # Physical Information
        st.subheader("Physical Information")
        
        physical_col1, physical_col2 = st.columns([1,1])
        
        with physical_col1:
            edited_size = st.selectbox(
                "Size", 
                options=SIZE_OPTS,
                index=size_index,
                key=f"size_{index}"
            )
            
            size_raw = re.findall(r"\d+", actress['Measurement'])
            size_converted = "-".join(size_raw)
            edited_measurement = st.text_input(
                "Measurement", 
                value=size_converted,
                placeholder="e.g., 75-56-80",
                key=f"measurement_{index}"
            )

            if st.checkbox('No Info', value=(actress['Measurement'] == '?'), key='Measurement Check') or edited_measurement == '':
                edited_measurement = '?'
            else:
                b, w, h = edited_measurement.split("-")
        
        with physical_col2:
            height = actress['Height (cm)'].replace(' cm','')
            
            edited_height = st.number_input(
                "Height (cm)",
                value=int(height),
                key=f"height_{index}"
            )

            if st.checkbox('No Info', value=(actress['Measurement'] == '?'), key='Height Check'):
                edited_height = '?'
            else:
                edited_height = str(edited_height) + ' cm'

        
        st.markdown("---")
        
        # Notes
        st.subheader("Additional Notes")
        edited_notes = st.text_area(
            "Notes", 
            value=actress['Notes'] if pd.notna(actress['Notes']) else "",
            placeholder="Enter any additional notes...",
            key=f"notes_{index}"
        )
        
        # Save changes
        if st.button("💾 Save Changes", use_container_width=True, type="primary", key=f"save_{index}"):
            if edited_kanji not in df['Name (Kanji)'].values:
                if edited_measurement != '?':
                    edited_measurement = f"B{b} / W{w} / H{h}"
                if new_pic:
                    # Handle measurement

                    
                    # Generate clean name untuk public_id
                    join_name = edited_name
                    clean_name = re.sub(r'[^\w]', '', join_name)
                    clean_name = "N" + clean_name
                    
                    # Jika ada gambar baru yang diupload
                    if new_pic is not None:
                        # Hapus gambar lama jika bukan placeholder
                        if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture']).lower():
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
                    
                    # Update data di DataFrame
                    df.at[index, 'Review'] = edited_review
                    df.at[index, 'Name (Alphabet)'] = edited_name
                    df.at[index, 'Name (Kanji)'] = edited_kanji
                    df.at[index, 'Picture'] = final_picture_url
                    df.at[index, 'Birthdate'] = edited_birthdate
                    df.at[index, 'Debut Date'] = edited_debut_date
                    df.at[index, 'Size'] = edited_size
                    df.at[index, 'Measurement'] = edited_measurement
                    df.at[index, 'Height (cm)'] = edited_height
                    df.at[index, 'Notes'] = edited_notes
                    df.at[index, 'Age'] = age
                    df.at[index, 'Debut Period'] = debut
                    df.at[index, 'Retire Date'] = edited_retire_date
                    df.at[index, 'Status'] = edited_status
                    
                    # Update ke Google Sheets
                    if update_google_sheets(df,conn):
                        st.success("✅ Data updated successfully in Google Sheets!")
                        st.session_state.actress_df = values_handling(df)  # Update session state
                    else:
                        st.error("❌ Failed to update Google Sheets")
                    
                    st.session_state.editing_index = None
                    st.rerun()
                else:
                    # Update data di DataFrame
                    df.at[index, 'Review'] = edited_review
                    df.at[index, 'Name (Alphabet)'] = edited_name
                    df.at[index, 'Name (Kanji)'] = edited_kanji
                    df.at[index, 'Birthdate'] = edited_birthdate
                    df.at[index, 'Debut Date'] = edited_debut_date
                    df.at[index, 'Size'] = edited_size
                    df.at[index, 'Measurement'] = edited_measurement
                    df.at[index, 'Height (cm)'] = edited_height
                    df.at[index, 'Notes'] = edited_notes
                    df.at[index, 'Age'] = age
                    df.at[index, 'Debut Period'] = debut
                    df.at[index, 'Retire Date'] = edited_retire_date
                    df.at[index, 'Status'] = edited_status

                    # Update ke Google Sheets
                    if update_google_sheets(df, conn):
                        st.success("✅ Data updated successfully in Google Sheets!")
                        st.session_state.actress_df = values_handling(df)  # Update session state
                    else:
                        st.error("❌ Failed to update Google Sheets")
                    
                    st.session_state.editing_index = None
                    st.rerun()
            else:
                st.warning(f"⚠️ Aktris '{edited_kanji}' sudah ada di database!")
                st.stop()

    def delete_actress(index):
        # Hapus data dari DataFrame
        df.drop(index, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Update ke Google Sheets
        if update_google_sheets(df,conn):
            st.success("✅ Actress deleted successfully from Google Sheets!")
            st.session_state.actress_df = values_handling(df)  # Update session state
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
            st.session_state.new_review = REVIEW_OPTS[0]
            st.session_state.new_name = ''
            st.session_state.new_kanji = ''
            st.session_state.new_birthdate = date.today()
            st.session_state.new_debut_date = date.today()
            st.session_state.new_status = STATUS_OPTS[0]
            st.session_state.new_retire_date = date.today()
            st.session_state.new_size = SIZE_OPTS[0]
            st.session_state.new_measurement = ''
            st.session_state.new_height = 130
            st.session_state.new_notes = ''
        
        if 'new_pic_reset' not in st.session_state:
            st.session_state.new_pic_reset = 0
        
        reset_pic = st.session_state.new_pic_reset        
        col1, col2 = st.columns(2)
        
        with col1:
            # Basic Information
            st.subheader("Basic Information")

            new_picture = st.file_uploader("Image", type=['png', 'jpg', 'jpeg'], key=f'new_picture_{reset_pic}')

            if not new_picture is None:
                st.image(new_picture, width=200)    
            else:
                new_picture = st.secrets.indicators.PLACEHOLDER_IMG

            new_review = st.selectbox("Review", options=REVIEW_OPTS, key='new_review')
            new_name = st.text_input("Name (Alphabet)*", placeholder="Enter name in alphabet", key='new_name')
            new_kanji = st.text_input("Name (Kanji)*", placeholder="Enter name in kanji", key='new_kanji')
            new_birthdate = st.date_input("Birthdate", min_value=date(1980,1,1), key='new_birthdate')
            if st.checkbox('No Info', key='New Birthdate', value=(new_birthdate is None)):
                new_birthdate = '?'
                new_age = '?'
            else:
                new_age = relativedelta(date.today(), new_birthdate).years        
                new_birthdate = new_birthdate.strftime('%d/%m/%Y')

        with col2:
            # Career Information
            st.subheader("Career Information")
            new_debut_date = st.date_input("Debut Date", min_value=date(1980,1,1), key='new_debut_date')
            if st.checkbox('No Info', key='New Debut Date'):
                new_debut_date= '?'

            new_status = st.selectbox("Status", options=STATUS_OPTS, key='new_status')
            if new_status == 'Retired':
                new_retire_date = st.date_input("Retire Date", min_value=date(1980,1,1), key='new_retire_date')
                new_retire_date = new_retire_date.strftime('%d/%m/%Y')
            else:
                new_retire_date = '?'
            
            # Physical Information
            st.subheader("Physical Information")
            new_size = st.selectbox("Size", options=SIZE_OPTS, key='new_size')

            new_measurement = st.text_input("Measurement", placeholder="e.g., 75-56-80", key='new_measurement')
            if st.checkbox('No Info',  key='New Measurement') or new_measurement == '':
                new_measurement = '?'
            else:
                b,w,h = new_measurement.split('-')
                new_measurement = f'B{b} / W{w} / H{h}'

            new_height = st.number_input("Height (cm)", min_value=130, key='new_height')
            if st.checkbox('No Info', key='New Height'):
                new_height = '? cm'
            else:
                new_height = str(new_height) + ' cm'
            
            if new_debut_date != '?':
                if new_status != 'Retired':
                    debut_period = relativedelta(date.today(), new_debut_date)
                elif new_status == 'Retired':
                    debut_period = relativedelta(new_retire_date, new_debut_date)
                
                if debut_period.months == 0:
                    new_debut_period = f'{debut_period.years} Year'
                else:
                    new_debut_period = f'{debut_period.years} Year {debut_period.months} Month'
                new_debut_date = new_debut_date.strftime('%d/%m/%Y')
            else:
                new_debut_period = '?'
        # Notes
        st.subheader("Additional Notes")
        new_notes = st.text_area("Notes", placeholder="Enter any additional notes...", key='new_notes')
        
        # Tombol submit
        with st.container(horizontal=True):
            submit_new = st.button("💾 Add Actress", use_container_width=True)
            cancel_new = st.button("❌ Cancel", use_container_width=True)
        
        if submit_new:
            if new_name and new_kanji:
                if new_picture:
                    join_name = new_name
                    clean_name = re.sub(r'[^\w]', '', join_name)
                    clean_name = "N" + clean_name
                    picture_url = upload_to_database(new_picture, clean_name)
                else:
                    picture_url = st.secrets.indicators.PLACEHOLDER_IMG

                # Create new row data
                new_row = pd.DataFrame([{
                    'Review': new_review,
                    'Name (Alphabet)': new_name,
                    'Name (Kanji)': new_kanji,
                    'Picture': picture_url,
                    'Birthdate': new_birthdate,
                    'Debut Date': new_debut_date,
                    'Size': new_size,
                    'Measurement': new_measurement,
                    'Height (cm)': new_height,
                    'Notes': new_notes,
                    'Age': new_age,
                    'Debut Period': new_debut_period,
                    'Retire Date': new_retire_date,
                    'Status': new_status
                }])

                # Add to DataFrame
                df = st.session_state.actress_df
                new_name_kanji = new_row['Name (Kanji)'].iloc[0]

                if new_name_kanji in df['Name (Kanji)'].values:
                    st.warning(f"⚠️ Aktris '{new_name_kanji}' sudah ada di database!")
                    st.stop()
                else:
                    df = pd.concat([df, new_row], ignore_index=True)       
                    # Update ke Google Sheets
                    if update_google_sheets(df, conn):
                        st.success("✅ New actress added successfully to Google Sheets!")
                        st.session_state.actress_df = values_handling(df)  # Update session state
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
        show_active = st.checkbox("Active", value=True)
        show_retired = st.checkbox("Retired", value=True)
        show_no_info = st.checkbox("No Info", value=True)
        show_slow_release = st.checkbox("Slow Release", value=True)
        show_problem = st.checkbox("Problem", value=True)
        
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
        if show_active:
            status_conditions.append(filtered_df['Status'].str.lower() == 'active')
        if show_retired:
            status_conditions.append(filtered_df['Status'].str.lower() == 'retired')
        if show_no_info:
            status_conditions.append(filtered_df['Status'].str.lower() == 'no info')
        if show_slow_release:
            status_conditions.append(filtered_df['Status'].str.lower() == 'slow release')
        if show_problem:
            status_conditions.append(filtered_df['Status'].str.lower() == 'problem')
        
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