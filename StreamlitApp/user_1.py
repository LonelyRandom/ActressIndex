import streamlit as st
from datetime import datetime, date
import time
import re
from upload_image import upload_to_database, delete_cloudinary_image, rename_cloudinary_image
import pandas as pd
from value_handling import values_handling, initial_load
from dateutil.relativedelta import relativedelta
from streamlit_scroll_to_top import scroll_to_here
import gspread
from google.oauth2.service_account import Credentials

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
def film_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["spred_title"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_CODE"]
    )

    return worksheet

@st.cache_resource()
def actress_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["spred_title"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_LIST"]
    )

    return worksheet

@st.cache_resource()
def tags_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["spred_title"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_TAGS"]
    )

    return worksheet

REVIEW_OPTS = [
    'Not Checked',
    'Pass',
    'Goat',
    'Drop',
    'S-Tier',
    'A-Tier',
    'B-Tier',
    'C-Tier',
    'D-Tier',
    'E-Tier',
    'F-Tier'
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

INFO_OPTS = [
    "Not Watched",
    "Watched",
    "Goat"
]

PASS_OPTS = [
    'Not Checked',
    'Pass',
    'Unsure',
    'Drop'
]

def load_data_actress(conn):
    try:
        df = conn.read(worksheet="NList", usecols=list(range(15)))
        df = values_handling(df,'actress')
        df = initial_load(df,'actress')
        return df
    except Exception as e:
        st.write(f'Error load data: {e}', e)
        st.stop()

def load_data_film(conn):
    try:

        df = conn.read(worksheet="NCode", usecols=list(range(11)))

        df = values_handling(df, 'film')
        df = initial_load(df, 'film')
        return df
    except Exception as e:
        return pd.DataFrame()
    
def load_data_tag(conn):
    try:
        df = conn.read(worksheet="NTags", usecols=list(range(1)))
        return df
    except Exception as e:
        return pd.DataFrame()
    
def update_google_sheets(df,conn,type):
    try:
        if not isinstance(df, pd.DataFrame):
            st.error("Data must be a pandas DataFrame")
            return False
        
        df_to_update = df.copy()
        if type == 'actress':
            sheet = 'NList'
        else:
            sheet = 'NCode'
            
        conn.update(
            worksheet=sheet, 
            data=df_to_update
        )
        
        st.toast("✅ Google Sheets updated successfully!")
        time.sleep(1)
        return True
    except:
        return False

def init_dataframe_actress(conn):
    """Inisialisasi DataFrame di session state"""
    if "actress_df" not in st.session_state:
        df = load_data_actress(conn)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Review', 'Picture', 'Name (Alphabet)', 'Name (Kanji)',
                'Birthdate', 'Debut Date', 'Size', 'Measurement',
                'Height (cm)', 'Notes', 'Age', 'Debut Period',
                'Retire Date', 'Status', 'Page'
            ])
        
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
                'Actress', 'Code', 'Title', 'Release Date', 'Picture', 'Tags', 'Info',
                'Release Status', 'Link', 'Preview Picture', 'A-Detector'
            ])
        
        st.session_state.film_df = df
        st.session_state.data_loaded = True
        return df
    else:
        return st.session_state.film_df

def init_dataframe_tags(conn):
    """Inisialisasi DataFrame di session state"""
    if "tag_df" not in st.session_state:
        df = load_data_tag(conn)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Tags'
            ])
        
        st.session_state.tag_df = df
        st.session_state.data_loaded = True
        return df
    else:
        return st.session_state.tag_df

def display_film_card(df, tag_df):
    """
    Menampilkan DataFrame aktris dalam bentuk card yang menarik
    
    Args:
        df: DataFrame dengan kolom: Actress Name, Code, Release Date, Picture, Tags, Status
    """
    TAGS_OPTS = sorted(
        tag_df['Tags']
        .dropna()
        .unique()
        .tolist()
    )

    if 'film_page' not in st.session_state:
        st.session_state.film_page = 1

    if df.empty:
        st.warning("📭 No film data available!")
        return
    
    # Filter options
    if st.session_state.get('search_reset', False):
        st.session_state.search_reset = False
        st.session_state.search_bar = ''
        st.session_state.search_by = 'Code'
    
    if st.session_state.get('tags_reset', False):
        st.session_state.tags_reset = False
        st.session_state.tag_bar = []

    if st.session_state.get('set_search', False):
        st.session_state.set_search = False
        st.session_state.search_bar = st.session_state.search_text
        st.session_state.search_by = 'Actress'
        st.session_state.search_text = ''
    
        
    search_by = st.radio('Search By:', options=['Code', 'Actress', 'Title'], horizontal=True, key='search_by', on_change=reset_page)
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(horizontal=True, vertical_alignment='bottom'):
            search_name = st.text_input("🔍 Search Bar", placeholder="Name or Code...", key='search_bar', on_change=reset_page)
            if st.button('Clear', on_click=reset_page):
                st.session_state.search_reset = True
                st.rerun()
    with col2:
        info_filter = st.multiselect(
            "📊 Status Filter:",
            options=df['Info'].unique().tolist() if 'Info' in df.columns else [],
            default=['Watched', 'Goat', 'Not Watched']
        )
    with col3:
        with st.container(horizontal=True, vertical_alignment='bottom'):
            tags_filter = st.multiselect("Tags:", options=TAGS_OPTS, on_change=reset_page, key='tag_bar')
            if st.button('Clear', on_click=reset_page, key='tag_clear'):
                st.session_state.tags_reset = True
                st.rerun()
    
    sort_type = st.selectbox('Sort Type', options=['(A-Z)', '(Z-A)', 'Date Acs', 'Date Desc'], key='sort_type', on_change=reset_page)
    # Filter data
    filtered_df = df.copy()
    if sort_type == '(A-Z)':
        filtered_df = filtered_df.sort_values(by='Code', ascending=True)

    elif sort_type == '(Z-A)':
        filtered_df = filtered_df.sort_values(by='Code', ascending=False)

    elif sort_type == 'Date Acs':
        filtered_df['release_date'] = pd.to_datetime(
            filtered_df['Release Date'],
            format='%d/%m/%Y',
            errors='coerce'
        )
        filtered_df = filtered_df.sort_values(by='release_date', ascending=True)

    elif sort_type == 'Date Desc':
        filtered_df['release_date'] = pd.to_datetime(
            filtered_df['Release Date'],
            format='%d/%m/%Y',
            errors='coerce'
        )
        filtered_df = filtered_df.sort_values(by='release_date', ascending=False)
    if st.toggle('Date filter', key='date_filter'):
        with st.container(horizontal=True):
            select_date_type = st.selectbox('Date Search', options=['Date', 'Month/Year', 'Year'], key='date_type',width=150, on_change=reset_page)
            filtered_df['filtered_date'] = pd.to_datetime(
                filtered_df['Release Date'],
                format='%d/%m/%Y',
                errors='coerce'
            )
            selected_date = st.date_input('Filter by date:', key='calender_filter', min_value=filtered_df['filtered_date'].min(), on_change=reset_page)
        if selected_date:
            selected_date = pd.to_datetime(selected_date).date()
            if select_date_type == 'Date':
                st.write(f'Filter by {select_date_type} : {selected_date}')
                filtered_df = filtered_df[
                    filtered_df['filtered_date'].dt.date == selected_date
                ]
            elif select_date_type == 'Month/Year':
                st.write(f'Filter by {select_date_type} : {selected_date.strftime("%B")} {selected_date.year}')
                filtered_df = filtered_df[
                    (filtered_df['filtered_date'].dt.month == selected_date.month) &
                    (filtered_df['filtered_date'].dt.year == selected_date.year)
                ]
            elif select_date_type == 'Year':
                st.write(f'Filter by {select_date_type} : {selected_date.year}')
                filtered_df = filtered_df[
                    filtered_df['filtered_date'].dt.year == selected_date.year
                ]
    if st.session_state.width_option == 'Device 1':
        img_card_height = 215
        img_card_width = 115
    else:
        img_card_height = 202
        img_card_width = 106
    
    if search_name:
        if search_by == 'Code':
            search_name = search_name.split(' ')
            search_name = '-'.join(search_name)
            mask = filtered_df['Code'].str.contains(search_name, case=False, na=False)
        elif search_by == 'Actress':
            mask = filtered_df['Actress Name'].str.contains(search_name, case=False, na=False)
        else:
            mask = filtered_df['Title'].str.contains(search_name, case=False, na=False)

        filtered_df = filtered_df[mask]
    
    if info_filter and 'Info' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Info'].isin(info_filter)]
    
    if tags_filter:
        filtered_df = filtered_df[
            filtered_df["Tags"].apply(
                lambda x: any(tag.strip() in tags_filter for tag in x.split(","))
            )
        ]
        
    # Tampilkan statistik filter
    watched_count = len(filtered_df[filtered_df['Info'] == 'Watched']) if 'Info' in filtered_df.columns else 0
    goat_count = len(filtered_df[filtered_df['Info'] == 'Goat']) if 'Info' in filtered_df.columns else 0
    
    with st.container(horizontal=True):
        st.metric("Total Film", len(filtered_df))
        st.metric("Watched", watched_count)
        st.metric("Goat", goat_count)
    
    st.markdown("---")
    
    if filtered_df.empty:
        st.info("🤔 No results found.")
        return
    
    items_per_page = 3 * 10
    
    total_pages = max(1, (len(filtered_df) + items_per_page - 1) // items_per_page)

    def set_page(p):
        st.session_state.film_page = p
    st.markdown(
        f"<div style='text-align:center; font-weight:600;padding-bottom:15px'>Page {st.session_state.film_page}</div>",
        unsafe_allow_html=True
    )

    if total_pages <= 6:
        with st.container(key='page_button', horizontal=True, horizontal_alignment='center'):
            for i in range(1, total_pages + 1):
                st.button(
                    str(i),
                    key=f'page_top_{i}',
                    disabled=(i == st.session_state.film_page),
                    on_click=set_page,
                    args=(i,)
                )
    else:
        with st.container(key='page_button_top', horizontal=True, horizontal_alignment='center'):
            st.button('⬅️',key='previous_top', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(st.session_state.film_page-1,))
            
            start_page = max(1, st.session_state.film_page - 1)  
            end_page = min(total_pages, st.session_state.film_page + 2)  
            
            pages_to_show = range(start_page, end_page + 1)
            
            if len(pages_to_show) < 4:
                if start_page == 1:
                    pages_to_show = range(1, min(5, total_pages + 1))
                else:
                    pages_to_show = range(max(1, total_pages - 3), total_pages + 1)
            
            for i in pages_to_show:
                st.button(
                    str(i),
                    key=f'page_top_{i}',
                    disabled=(i == st.session_state.film_page),
                    on_click=set_page,
                    args=(i,)
                )
            
            st.button('➡️',key='next_top', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(st.session_state.film_page+1,))
        with st.container(horizontal=True):
            if st.button('First Page', width='stretch', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(1,)):
                st.session_state.scroll_to_here = True
                st.rerun()
            if st.button('Last Page', width='stretch', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(total_pages,)):
                st.session_state.scroll_to_here = True
                st.rerun()
    
    page = st.session_state.film_page
    
    start_idx = (page - 1) * items_per_page # page = 2 / Start idx = 8
    end_idx = min(start_idx + items_per_page, len(filtered_df)) # end idx = 16
    
    st.caption(f"Showing {start_idx+1}-{end_idx} from {len(filtered_df)} films")
    
    rows_to_display = filtered_df.iloc[start_idx:end_idx] #[8,15]
    
    with st.container(horizontal=True, horizontal_alignment='center'):
        for i in range(0, len(rows_to_display)): # len = 8 // i = [0,8]
            actress = rows_to_display.iloc[i]
            real_index = rows_to_display.index[i]  # ⬅️ INI KUNCI
            display_single_card(img_card_height, img_card_width, actress, real_index)
    st.markdown('---')
    if total_pages <= 6:
        with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
            for i in range(1, total_pages + 1):
                st.button(
                    str(i),
                    key=f'page_bottom_{i}',
                    disabled=(i == st.session_state.film_page),
                    on_click=set_page,
                    args=(i,)
                )
    else:
        with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
            st.button('⬅️',key='previous_bottom', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(st.session_state.film_page-1,))
            
            start_page = max(1, st.session_state.film_page - 1)  
            end_page = min(total_pages, st.session_state.film_page + 2)  
            
            pages_to_show = range(start_page, end_page + 1)
            
            if len(pages_to_show) < 4:
                if start_page == 1:
                    pages_to_show = range(1, min(5, total_pages + 1))
                else:
                    pages_to_show = range(max(1, total_pages - 3), total_pages + 1)
            
            for i in pages_to_show:
                st.button(
                    str(i),
                    key=f'page_bottom_{i}',
                    disabled=(i == st.session_state.film_page),
                    on_click=set_page,
                    args=(i,)
                )
            st.button('➡️', key='next_bottom', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(st.session_state.film_page+1,))
    st.markdown('---')
    

def display_single_card(img_card_height, img_card_width, actress, card_id):
    """
    Menampilkan single card untuk satu aktris
    """

    # st.write(actress['Code'])
    status_color = "#4CAF50" if actress['Info'] == 'Watched' else "#F44336" if actress['Info'] == 'Not Watched' else "#9E9E9E" if actress['Info'] == 'Drop' else "#9b59b6"
    
    if actress['Release Date'] == '?':
        release_date = '?'
    else:
        release_date = datetime.strptime(actress['Release Date'], '%d/%m/%Y').strftime('%b, %d %Y') if pd.notna(actress['Release Date']) else "Unknown"
    
    if actress['A-Detector'] == 1:
        card_html = f"""<div class="actress-card" id="card_{card_id}" 
            style="border: 2px solid {status_color}; border-radius: 15px; padding: 10px; 
            margin: 10px 0; background: linear-gradient(135deg, #ffffff 0%, #EDE8D0 100%); 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: all 0.3s ease; 
            height: {img_card_height}px; width: {img_card_width}px;display: flex; flex-direction: column;">
            <!-- Image Container -->
            <div style="
                height: 100%;  /* Atur tinggi tetap */
                width: 100%;
                overflow: hidden;
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 10px;
                border-radius: 10px;
                border : 2.5px solid {status_color};
            ">
                <img src="{actress['Picture']}" 
                    style="
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                        object-position: center;
                    ">
            </div>
            <!-- Separator -->
            <div style="width: {50}px; height: {3}px; background: linear-gradient(90deg, {status_color}, #FFD166); 
                    margin: 0 auto 10px auto; border-radius: 2px;"></div>
            <!-- Code and Date -->
            <div>
                <div style="display: flex; justify-content: center; margin-bottom: 1px;">
                    <span style="
                        background: linear-gradient(90deg, {status_color}, #FFD700);
                        color: white;
                        padding: 2px 10px;
                        border-radius: 12px;
                        font-size: 9px;
                        font-weight: bold;
                    ">
                        {actress['Info']}
                    </span>
                </div>
                <div style="display: flex; justify-content: center;">
                    <span style="color: #3498db; font-size:11px;">{release_date}</span>
                </div>
            </div>
        </div>"""
    else:
        card_html = f"""<div class="actress-card" id="card_{card_id}" 
            style="border: 2px solid {status_color}; border-radius: 15px; padding: 10px; 
            margin: 10px 0; background: linear-gradient(135deg, #ffffff 0%, #EDE8D0 100%); 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: all 0.3s ease; 
            height: {img_card_height}px; width: {img_card_width}px; display: flex; flex-direction: column;">
            <!-- Image Container -->
            <div style="
                height: 100%;  /* Atur tinggi tetap */
                width: 100%;
                overflow: hidden;
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 10px;
                border-radius: 10px;
                border : 2.5px solid {status_color};
            ">
                <img src="{actress['Picture']}" 
                    style="
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                        object-position: center;
                    ">
            </div>
            <!-- Separator -->
            <div style="width: {50}px; height: {3}px; background: linear-gradient(90deg, {status_color}, #FFD166); 
                    margin: 0 auto 15px auto; border-radius: 2px;"></div>
            <!-- Code and Date -->
            <div>
                <div style="display: flex; justify-content: center; margin-bottom: 1px;">
                    <span style="
                        background: {status_color};
                        color: white;
                        padding: 2px 10px;
                        border-radius: 12px;
                        font-size: 9px;
                        font-weight: bold;
                    ">
                        {actress['Info']}
                    </span>
                </div>
                <div style="display: flex; justify-content: center;">
                    <span style="color: #3498db; font-size:11px;">{release_date}</span>
                </div>
            </div>
        </div>"""

    with st.container(width=img_card_width):
        st.markdown(card_html, unsafe_allow_html=True)
    
        if st.button("View Details",key=f'view_film_{card_id}',width='stretch', type='primary'):
            st.session_state.viewing_film_index = card_id
            st.session_state.editing_film_index = None
            st.rerun()
def reset_calender_page():
    """Reset halaman ke 1"""
    st.session_state.calender_page = 1

def display_film_calender(df, conn):
    if 'calender_data' not in st.session_state:
        st.session_state.calender_data = conn.read(worksheet='Calender Scrap', usecols=list(range(5)))

    if 'calender_page' not in st.session_state:
        st.session_state.calender_page = 1
    
    if 'width_option' not in st.session_state:
        st.session_state.width_option = 'Device 1'
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

    if st.session_state.width_option == 'Device 1':
        image_width = 115
    else:
        image_width = 106
    
    if st.session_state.get('calender_search_reset', False):
        st.session_state.calender_search_reset = False
        st.session_state.calender_search_bar = ''

    calender_df = st.session_state.calender_data

    filtered_df = calender_df.copy()

    with st.container(horizontal=True, vertical_alignment='bottom'):
        calender_search = st.text_input("🔍 Search (Actress Name / Code):", 
                                  placeholder="Name or Code...", 
                                  key='calender_search_bar', on_change=reset_page)
        if st.button('Clear', on_click=reset_calender_page):
            st.session_state.calender_search_reset = True
            st.rerun()
    
    with st.container(horizontal=True):
        select_date_type = st.selectbox('Date Search', options=['Date', 'Month/Year', 'Year'], key='date_type',width=150, on_change=reset_calender_page)
        filtered_df['filtered_date'] = pd.to_datetime(
            filtered_df['Month'],
            format='%d/%m/%Y',
            errors='coerce'
        )
        selected_date = st.date_input('Filter by date:', key='calender_filter', min_value=filtered_df['filtered_date'].min(), on_change=reset_calender_page)

    selected_flag = st.selectbox('Flag', options=['All', 'Pass','Drop', 'Not Checked'], width='stretch', on_change=reset_calender_page)
    if selected_date:
        selected_date = pd.to_datetime(selected_date).date()
        if select_date_type == 'Date':
            st.write(f'Filter by {select_date_type} : {selected_date.strftime("%d %B %Y")}')
            filtered_df = filtered_df[
                filtered_df['filtered_date'].dt.date == selected_date
            ]
        elif select_date_type == 'Month/Year':
            st.write(f'Filter by {select_date_type} : {selected_date.strftime("%B %Y")}')
            filtered_df = filtered_df[
                (filtered_df['filtered_date'].dt.month == selected_date.month) &
                (filtered_df['filtered_date'].dt.year == selected_date.year)
            ]
        elif select_date_type == 'Year':
            st.write(f'Filter by {select_date_type} : {selected_date.year}')
            filtered_df = filtered_df[
                filtered_df['filtered_date'].dt.year == selected_date.year
            ]
    
    if selected_flag != 'All':
        filtered_df = filtered_df[filtered_df['Flag'] == selected_flag]

    if calender_search:
        calender_search = calender_search.split(' ')
        calender_search = '-'.join(calender_search)
        mask = filtered_df['Code'].str.contains(calender_search, case=False, na=False)
        filtered_df = filtered_df[mask].copy()

    def set_save_edit():
        conn.update(worksheet='Calender Scrap', data=calender_df)
        st.session_state.calender_data = calender_df
        st.success('✅ Succesfully update data!')

    def set_all_drop():
        calender_df.loc[calender_df['Flag'] == 'Not Checked', 'Flag'] = 'Drop'
        conn.update(worksheet='Calender Scrap', data=calender_df)
        st.session_state.calender_data = calender_df
        st.success('✅ Succesfully drop all not checked data!')
    
    def set_match():
        calender_df.loc[calender_df['Code'].isin(df['Code'].values), 'Flag'] = 'Pass'
        conn.update(worksheet='Calender Scrap', data=calender_df)
        st.session_state.calender_data = calender_df
        st.success('✅ Succesfully match data!')
    
    def set_sent_data():
        pass_data = calender_df[calender_df['Flag'] == 'Pass']
        new_rows = []
        for i in range(len(pass_data)):
            data = pass_data.iloc[i]
            if data['Code'] not in df['Code'].values:
                new_rows.append([
                    'Not Listed',
                    data['Code'],
                    '--',
                    '--',
                    '--',
                    'No Tags',
                    'Not Watched',
                    0,
                    '--',
                    '--',
                    False
                ])
        
        new_row_df = pd.DataFrame(new_rows, columns=df.columns)
        final_df = pd.concat([df,new_row_df], ignore_index=True)
        conn.update(worksheet='NCode', data=final_df)
        st.success('✅ Succesfully sent data to database!')        
            


    st.button('Save edit',width='stretch', type='primary', on_click=set_save_edit)
    with st.container(horizontal=True):
        st.button('Drop All', on_click=set_all_drop, width='stretch')
        st.button('Match', on_click=set_match, width='stretch')
    st.subheader('Sent "Pass" to database?')
    st.button('Send ⏭️', on_click=set_sent_data, width='stretch')
    if st.session_state.scroll_to_here:
        scroll_to_here(0,key='here')  # Scroll to the top of the page
        st.session_state.scroll_to_here = False
    
    st.markdown('---')
    
    total_calender_pages = max(1, (len(filtered_df) + 60 - 1) // 60)

    def set_calender_page(p):
        st.session_state.calender_page = p
    
    if not filtered_df.empty:
        st.markdown(
            f"<div style='text-align:center; font-weight:600;padding-bottom:15px'>Page {st.session_state.calender_page}</div>",
            unsafe_allow_html=True
        )

        if total_calender_pages <= 6:
            with st.container(key='page_button', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_calender_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.calender_page),
                        on_click=set_calender_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
        else:
            with st.container(key='page_button_top', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_top', disabled=(st.session_state.calender_page == 1), on_click=set_calender_page, args=(st.session_state.calender_page-1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
                start_page = max(1, st.session_state.calender_page - 1)  
                end_page = min(total_calender_pages, st.session_state.calender_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_calender_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_calender_pages - 3), total_calender_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.calender_page),
                        on_click=set_calender_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_top', disabled=(st.session_state.calender_page == total_calender_pages), on_click=set_calender_page, args=(st.session_state.calender_page+1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()

            with st.container(horizontal=True):
                if st.button('First Page', width='stretch', disabled=(st.session_state.calender_page == 1), on_click=set_calender_page, args=(1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                if st.button('Last Page', width='stretch', disabled=(st.session_state.calender_page == total_calender_pages), on_click=set_calender_page, args=(total_calender_pages,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
        page = st.session_state.calender_page
        
        start_idx = (page - 1) * 60 
        end_idx = min(start_idx + 60, len(filtered_df)) 
        st.markdown("---")
        st.caption(f"Showing {start_idx+1}-{end_idx} from {len(filtered_df)} films")
        
        rows_to_display = filtered_df.iloc[start_idx:end_idx] 

        with st.container(horizontal=True, horizontal_alignment='center'):
            for i in range(len(rows_to_display)):
                with st.container(width=image_width):
                    film = rows_to_display.iloc[i]
                    real_index = rows_to_display.index[i]

                    if film['Flag'] == 'Not Checked':
                        flag_idx = 2
                    elif film['Flag'] == 'Drop':
                        flag_idx = 1
                    else:
                        flag_idx = 0
                    st.image(film['Picture'], caption=film['Code'])
                    edit_flag = st.radio('Flag', options=['✅ Pass','❌ Drop','❔ Not Yet'], index=flag_idx, key=f'{film["Code"]}_radio', horizontal=False)
                    st.link_button('Detail', film['Link'], type='primary', width='stretch')
                    if edit_flag == '✅ Pass':
                        edit_flag = 'Pass'
                    elif edit_flag == '❌ Drop':
                        edit_flag = 'Drop'
                    else:
                        edit_flag = 'Not Checked'
                    calender_df.at[real_index, 'Flag'] = edit_flag
                    st.markdown('---')
        st.markdown('---')
        if total_calender_pages <= 6:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_calender_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.calender_page),
                        on_click=set_calender_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
        else:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_bottom', disabled=(st.session_state.calender_page == 1), on_click=set_calender_page, args=(st.session_state.calender_page-1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
                start_page = max(1, st.session_state.calender_page - 1)  
                end_page = min(total_calender_pages, st.session_state.calender_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_calender_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_calender_pages - 3), total_calender_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.calender_page),
                        on_click=set_calender_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_bottom', disabled=(st.session_state.calender_page == total_calender_pages), on_click=set_calender_page, args=(st.session_state.calender_page+1,)):
                    st.session_state.scroll_to_here = True    
                    st.rerun()             
    else:
        st.info('No film match the filter')
    if st.button('⬆️ Back to top', width='stretch'):
        st.session_state.scroll_to_here = True                   


    

    
def reset_page():
    """Reset halaman ke 1"""
    st.session_state.film_page = 1

def reset_page_actress():
    """Reset halaman ke 1"""
    st.session_state.actress_page = 1

# --- FUNGSI ALTERNATIF: Grid Layout tanpa Pagination ---
def display_film_grid(df, tag_df):
    """
    Menampilkan semua card sekaligus dalam grid
    """
    TAGS_OPTS = sorted(
        tag_df['Tags']
        .dropna()
        .unique()
        .tolist()
    )

    if 'film_page' not in st.session_state:
        st.session_state.film_page = 1
    if 'width_option' not in st.session_state:
        st.session_state.width_option = 'Device 1'
    
    st.markdown(
        """
        <style>
        button[data-testid="stBaseButton-primary"] p {
            font-size: 13px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if st.session_state.get('search_reset', False):
        st.session_state.search_reset = False
        st.session_state.search_bar = ''
        st.session_state.search_by = 'Code'

    if st.session_state.get('tags_reset', False):
        st.session_state.tags_reset = False
        st.session_state.tag_bar = ''

    if st.session_state.get('set_search', False):
        st.session_state.set_search = False
        st.session_state.search_bar = st.session_state.search_text
        st.session_state.search_text = ''
        st.session_state.search_by = 'Actress'

    if st.session_state.width_option == 'Device 1':
        image_width = 115
        image_heigth = 164
    else:
        image_width = 106
        image_heigth = 151
        
    with st.container(horizontal=True):
        search_by = st.radio('Search By :', options=['Code', 'Actress', 'Title'], key='search_by', width='content', horizontal=False)    
        filters = st.radio(
                "Type :",
                ["Watched", "Not Watched"],
                horizontal=False,
                on_change=reset_page,
                width='content'
            )

    # Filter data dan simpan index asli
    if filters == 'Watched':
        filtered_df = df[df['Info'] != 'Not Watched'].copy()
        filtered_df['badge_icon'] = filtered_df['Info'].map({
            'Watched': '🟢',
            'Goat': '🟣'
        }).fillna('⚪')
        filtered_df['badge_color'] = filtered_df['Info'].map({
            'Watched': 'green',
            'Goat': 'violet'
        }).fillna('⚪')
    elif filters == 'Not Watched':
        filtered_df = df[df['Info'] == 'Not Watched'].copy()
        filtered_df['is_release'] = filtered_df['Release Status'].map({
            1: 'Released',
            0: 'Not Released'
        }).fillna('Unknown')
        filtered_df['badge_icon'] = filtered_df['Release Status'].map({
            1: '🟢',
            0: '🔴'
        }).fillna('⚪')
        filtered_df['badge_color'] = filtered_df['Release Status'].map({
            1: 'green',
            0: 'red'
        }).fillna('grey')

    
    # Reset index dan simpan index asli dalam kolom baru
    filtered_df = filtered_df.reset_index(drop=False)  # ini akan membuat kolom 'index' dengan index asli
    # Rename kolom index agar tidak bentrok
    filtered_df = filtered_df.rename(columns={'index': 'original_index'})
    

    with st.container(horizontal=True, vertical_alignment='bottom'):
        search_name = st.text_input("🔍 Search (Actress Name / Code):", 
                                  placeholder="Name or Code...", 
                                  key='search_bar', on_change=reset_page)
        if st.button('Clear', on_click=reset_page):
            st.session_state.search_reset = True
            st.rerun()

    with st.container(horizontal=True, vertical_alignment='bottom'):
        tags_filter = st.multiselect(
            "Tags:", 
            options=TAGS_OPTS, 
            on_change=reset_page)
        if st.button('Clear', on_click=reset_page, key='tag_clear'):
                st.session_state.search_reset = True
                st.rerun()
    sort_type = st.selectbox('Sort Type', options=['(A-Z)', '(Z-A)', 'Date Acs', 'Date Desc'], key='sort_type', on_change=reset_page)
    # Filter data
    if sort_type == '(A-Z)':
        filtered_df = filtered_df.sort_values(by='Code', ascending=True)

    elif sort_type == '(Z-A)':
        filtered_df = filtered_df.sort_values(by='Code', ascending=False)

    elif sort_type == 'Date Acs':
        filtered_df['release_date'] = pd.to_datetime(
            filtered_df['Release Date'],
            format='%d/%m/%Y',
            errors='coerce'
        )
        filtered_df = filtered_df.sort_values(by='release_date', ascending=True)

    elif sort_type == 'Date Desc':
        filtered_df['release_date'] = pd.to_datetime(
            filtered_df['Release Date'],
            format='%d/%m/%Y',
            errors='coerce'
        )
        filtered_df = filtered_df.sort_values(by='release_date', ascending=False)
    if st.toggle('Date filter', key='date_filter'):
        with st.container(horizontal=True):
            select_date_type = st.selectbox('Date Search', options=['Date', 'Month/Year', 'Year'], key='date_type',width=150, on_change=reset_page)
            filtered_df['filtered_date'] = pd.to_datetime(
                filtered_df['Release Date'],
                format='%d/%m/%Y',
                errors='coerce'
            )
            selected_date = st.date_input('Filter by date:', key='calender_filter', min_value=date(1980,1,1), on_change=reset_page)
            if selected_date:
                selected_date = pd.to_datetime(selected_date).date()
                if select_date_type == 'Date':
                    st.write(f'Filter by {select_date_type} : {selected_date}')
                    filtered_df = filtered_df[
                        filtered_df['filtered_date'].dt.date == selected_date
                    ]
                elif select_date_type == 'Month/Year':
                    st.write(f'Filter by {select_date_type} : {selected_date.strftime("%B")} {selected_date.year}')
                    filtered_df = filtered_df[
                        (filtered_df['filtered_date'].dt.month == selected_date.month) &
                        (filtered_df['filtered_date'].dt.year == selected_date.year)
                    ]
                elif select_date_type == 'Year':
                    st.write(f'Filter by {select_date_type} : {selected_date.year}')
                    filtered_df = filtered_df[
                        filtered_df['filtered_date'].dt.year == selected_date.year
                    ]


    if search_name:
        if search_by == 'Code':
            search_name = search_name.split(' ')
            search_name = '-'.join(search_name)
            mask = filtered_df['Code'].str.contains(search_name, case=False, na=False)
        elif search_by == 'Actress':
            mask = filtered_df['Actress Name'].str.contains(search_name, case=False, na=False)
        else:
            mask = filtered_df['Title'].str.contains(search_name, case=False, na=False)
        filtered_df = filtered_df[mask].copy()

    if tags_filter:
        filtered_df = filtered_df[
            filtered_df["Tags"].apply(
                lambda x: any(tag.strip() in tags_filter for tag in x.split(","))
            )
        ]
    
    total_pages = max(1, (len(filtered_df) + 30 - 1) // 30)

    def set_page(p):
        st.session_state.film_page = p
    
    
    if st.session_state.scroll_to_here:
        scroll_to_here(0,key='here')  # Scroll to the top of the page
        st.session_state.scroll_to_here = False
    st.markdown('---')
    if not filtered_df.empty:
        st.markdown(
            f"<div style='text-align:center; font-weight:600;padding-bottom:15px'>Page {st.session_state.film_page}</div>",
            unsafe_allow_html=True
        )

        if total_pages <= 6:
            with st.container(key='page_button', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
        else:
            with st.container(key='page_button_top', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_top', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(st.session_state.film_page-1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
                start_page = max(1, st.session_state.film_page - 1)  
                end_page = min(total_pages, st.session_state.film_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_pages - 3), total_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_top', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(st.session_state.film_page+1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()

            with st.container(horizontal=True):
                if st.button('First Page', width='stretch', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                if st.button('Last Page', width='stretch', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(total_pages,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
        page = st.session_state.film_page
        
        start_idx = (page - 1) * 30 
        end_idx = min(start_idx + 30, len(filtered_df)) 
        st.markdown("---")
        st.caption(f"Showing {start_idx+1}-{end_idx} from {len(filtered_df)} films")
        
        rows_to_display = filtered_df.iloc[start_idx:end_idx] 
        with st.container(horizontal=True, horizontal_alignment='center'):
            for i in range(0, len(rows_to_display)):
                with st.container(horizontal=True, width=image_width):
                    with st.container():
                        if i < len(rows_to_display):
                            film = rows_to_display.iloc[i]
                            real_index = rows_to_display.index[i]

                            with st.container(horizontal_alignment='center', horizontal=True):
                                if film['A-Detector'] == 1:
                                    film['badge_color'] = 'yellow'

                                if filters == 'Not Watched':
                                    st.badge(film['is_release'], icon=film['badge_icon'], color=film['badge_color'])
                                else:
                                    st.badge(film['Info'], icon=film['badge_icon'], color=film['badge_color'])

                            # Tambahkan wrapper dengan fixed height
                            st.markdown(f"""
                                <div style="
                                    height: {image_heigth}px;  /* Atur tinggi tetap */
                                    width: 100%;
                                    overflow: hidden;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    margin-bottom: 10px;
                                    border-radius: 5px;
                                ">
                                    <img src="{film['Picture']}" 
                                        style="
                                            width: 100%;
                                            height: 100%;
                                            object-fit: cover;
                                            object-position: center;
                                        ">
                                </div>
                            """, unsafe_allow_html=True)

                            if st.button(f'{film["Code"]}', key=f'film_edit_{real_index}', width='stretch', type='primary'):
                                st.session_state.viewing_film_index = film['original_index']
                                st.rerun()
                            st.space('small')
        st.markdown('---')
        if total_pages <= 6:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
        else:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_bottom', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(st.session_state.film_page-1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
                start_page = max(1, st.session_state.film_page - 1)  
                end_page = min(total_pages, st.session_state.film_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_pages - 3), total_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_bottom', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(st.session_state.film_page+1,)):
                    st.session_state.scroll_to_here = True    
                    st.rerun()             
    else:
        st.info('No film match the filter')
    if st.button('⬆️ Back to top', width='stretch'):
        st.session_state.scroll_to_here = True                   

def complex_home(conn):
    if 'log_out_btn' not in st.session_state:
        st.session_state.log_out_btn = False
    if 'first_load_film' not in st.session_state:
        st.session_state.first_load_film = True
    if 'first_load_actress' not in st.session_state:
        st.session_state.first_load_actress = True
        
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Home Page</h1>", unsafe_allow_html=True)
    df_actress = init_dataframe_actress(conn)
    df_film = init_dataframe_film(conn)

    left, right = st.columns(2)
    with left:
        with st.container(key='ActressList'):
            st.header('🌟 Actress List')
            with st.container(horizontal=True):
                with st.container(key='Actress Info 1', horizontal=False):
                    st.metric('Actress Count' , len(df_actress))
                    st.metric('Pass',len(df_actress[(df_actress['Review'] != 'Not Check') & (df_actress['Review'] != 'Drop')]))
                with st.container(key='Actress Info 2', horizontal=False):
                    st.metric('Not Checked', len(df_actress[df_actress['Review'] == 'Not Checked']))
                    st.metric('Drop', len(df_actress[df_actress['Review'] == 'Drop']))
            if st.button('Go To Actress →'):
                return 'actress'
    with right:
        with st.container(key='FilmList'):
            st.header('🎬 Film List')
            with st.container(horizontal=True):
                with st.container(key='Film Info 1', horizontal=False):
                    st.metric('Film Count', len(df_film))
                    st.metric('Watched', len(df_film[df_film['Info'] == 'Watched']))
                with st.container(key='Film Info 2', horizontal=False):
                    st.metric('Not Watched', len(df_film[df_film['Info'] == 'Not Watched']))
                    st.metric('Goat', len(df_film[df_film['Info'] == 'Goat']))
            if st.button('Go To Film →'):
                st.session_state.first_load_film = True
                return 'film'
    
    if st.session_state.log_out_btn == False:
        if st.button('🔐 Logout', width='stretch', type='primary'):
            st.session_state.log_out_btn = True
            st.rerun()
    else:
        st.warning('Are you sure want to logout?')
        with st.container(horizontal=True):
            if st.button('Yes', width='stretch'):
                st.session_state.clear()
                return 'login'
            if st.button('No', width='stretch'):
                st.session_state.log_out_btn = False
                st.rerun()
    
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


def complex_film(conn, device):
    # Inisialisasi variabel kontrol
    if "editing_film_index" not in st.session_state:
        st.session_state.editing_film_index = None
    if "viewing_film_index" not in st.session_state:
        st.session_state.viewing_film_index = None
    if 'scroll_to_top' not in st.session_state:
        st.session_state.scroll_to_top = False
    if 'scroll_to_here' not in st.session_state:
        st.session_state.scroll_to_here = False
    if 'film_simple_edit' not in st.session_state:
        st.session_state.film_simple_edit = False
    if 'prev_pic_page' not in st.session_state:
        st.session_state.prev_pic_page = 1
    if 'film_layout' not in st.session_state:
        st.session_state.film_layout = 'Detailed'
    if 'width_option' not in st.session_state:
        st.session_state.width_option = device

    if st.session_state.scroll_to_top:
        scroll_to_here(0,key='top')  # Scroll to the top of the page
        st.session_state.scroll_to_top = False  # Reset the state after scrolling

    df = init_dataframe_film(conn)
    actress_df = init_dataframe_actress(conn)
    tag_df = init_dataframe_tags(conn)

    TAGS_OPTS = sorted(
        tag_df['Tags']
        .dropna()
        .unique()
        .tolist()
    )

    ACTRESS_OPTS = ['Many', 'Not Listed'] + sorted(
        actress_df.loc[~actress_df['Name (Alphabet)'].isin(['Many', 'Not Listed']), 'Name (Alphabet)']
        .dropna()
        .unique()
        .tolist()
    )

    @st.dialog("🎬 Film Details", width='small')
    def show_film_details():
        index = st.session_state.viewing_film_index

        if index is None or index >= len(df):
            st.warning("No film selected")
            st.stop()
        
        if st.session_state.editing_film_index == index:
            show_edit_film(index)
        else:
            show_view_film(index)

    def show_view_film(index):
        def reset_pic():
            st.session_state.prev_pic = 0

        def set_prev_pic(pic):
            st.session_state.prev_pic = pic


        film = df.iloc[index]

        with st.container(key='poster_code', horizontal_alignment='center'):
            st.markdown(f"<h1 style='text-align: center;'>{film['Code']}</h1>", unsafe_allow_html=True)
            st.image(film['Picture'], width=200)
        
        st.markdown('### Title')
        st.write(film['Title'])
        st.markdown(
            """
            <style>
            button[data-testid="stBaseButton-tertiary"] p {
                font-size: 14px !important;
                color: #d6cfc7 !important;
            }
            """,
            unsafe_allow_html=True
        )
        
        st.markdown('### Actress')
        if 'Not Listed' not in film['Actress Name'] and 'Many' not in film['Actress Name']:
            actress_list = film['Actress Name'].split(', ')
            matching_actresses = actress_df[actress_df['Name (Alphabet)'].isin(actress_list)]
            if len(matching_actresses)>2:
                is_center = 'center'
            else:
                is_center = 'left'
            with st.container(horizontal=True, horizontal_alignment=is_center):
                for idx in matching_actresses.index:
                    actress_name = matching_actresses['Name (Alphabet)'][idx]
                    container_key = f"{actress_name}_{index}"

                    with st.container(width=80, key=container_key):
                        # Display image as circle using HTML
                        st.markdown(f"""
                            <div style="
                                width: 70px;
                                height: 70px;
                                border-radius: 50%;
                                overflow: hidden;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                margin: 0 auto 8px auto;
                                background: white;
                            ">
                                <img src="{matching_actresses['Picture'][idx]}" 
                                    style="
                                        width: 100%;
                                        height: 100%;
                                        object-fit: cover;
                                    ">
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Button
                        if st.button(actress_name, width='stretch', type='tertiary', key=f"{actress_name}_{idx}_{idx}", on_click=reset_page):
                            st.session_state.viewing_film_index = None
                            st.session_state.editing_film_index = None
                            st.session_state.search_text = actress_name
                            st.session_state.set_search = True
                            st.session_state.scroll_to_top = True
                            st.rerun()
        elif 'Many' in film['Actress Name']:
            with st.container(width=80):
                st.markdown(f"""
                    <div style="
                        width: 70px;
                        height: 70px;
                        border-radius: 50%;
                        overflow: hidden;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin: 0 auto 8px auto;
                        background: white;
                    ">
                        <img src="{st.secrets.indicators.PLACEHOLDER_IMG}" 
                            style="
                                width: 100%;
                                height: 100%;
                                object-fit: cover;
                            ">
                    </div>
                """, unsafe_allow_html=True)
                if st.button('Many', width='stretch', type='tertiary', key="many_profile", on_click=reset_page):
                    st.session_state.viewing_film_index = None
                    st.session_state.editing_film_index = None
                    st.session_state.search_text = 'Many'
                    st.session_state.set_search = True
                    st.session_state.scroll_to_top = True
                    st.rerun()
        elif 'Not Listed' in film['Actress Name']:
            with st.container(width=80):
                st.markdown(f"""
                    <div style="
                        width: 70px;
                        height: 70px;
                        border-radius: 50%;
                        overflow: hidden;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin: 0 auto 8px auto;
                        background: white;
                    ">
                        <img src="{st.secrets.indicators.PLACEHOLDER_IMG}" 
                            style="
                                width: 100%;
                                height: 100%;
                                object-fit: cover;
                            ">
                    </div>
                """, unsafe_allow_html=True)
                if st.button('Not Listed', width='stretch', type='tertiary', key="not_listed_profile", on_click=reset_page):
                    st.session_state.viewing_film_index = None
                    st.session_state.editing_film_index = None
                    st.session_state.search_text = 'Not Listed'
                    st.session_state.set_search = True
                    st.session_state.scroll_to_top = True
                    st.rerun()

        if film['Release Date'] != '?':
            release_date_text = datetime.strptime(film['Release Date'], '%d/%m/%Y').strftime("%b, %d %Y")
        else:
            release_date_text = '?'

        st.markdown('### Release Date')
        st.write(release_date_text)

        st.markdown('### Status')
        icons = ''
        colors = ''
        if film['Info'] == 'Goat':
            icons = '🟣'
            colors = 'violet'
        elif film['Info'] == 'Watched':
            icons = '🟢'
            colors = 'green'
        else:
            icons = '🔴'
            colors = 'red'
            
        with st.container(horizontal=True):
            st.badge(label=film['Info'], icon=icons, color=colors)
            if film['A-Detector'] == 1:
                st.badge(label='', icon='⭐', color='yellow')


        st.markdown('### Tags')
        st.write(film['Tags'])

        st.markdown('### Gallery')
        if st.checkbox('Show', on_change=reset_pic):
            if film['Preview Picture'] != 'No Pics' and film['Preview Picture'] != '--':
                if 'prev_pic' not in st.session_state:  
                    st.session_state.prev_pic = 0
                
                pics = film['Preview Picture'].split(', ')
                count = len(pics)

                st.markdown(
                    """
                    <style>
                    div[data-testid="stVerticalBlock"] { padding-top: 0rem; padding-bottom: 0rem; }

                    .img-fit {
                        margin-top: -13px; 
                        padding-top: 0; 
                        display: flex;             /* gunakan flexbox */
                        justify-content: center;   /* horizontal center */
                        align-items: center;       /* vertical center jika container tinggi ditentukan */
                        background-color: #ffffff;
                        border-radius: 5px;
                        margin-bottom: 15px;
                    }

                    .img-fit img {
                        max-width: 100%;
                        height: 400px;
                        width: auto;
                        object-fit: contain;
                        display: none;  /* default hidden semua gambar */
                    }

                    .img-fit img.active {
                        display: block; /* hanya gambar active yang terlihat */
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                # HTML untuk semua gambar, preload semuanya
                img_html = '<div class="img-fit">'
                for i, pic in enumerate(pics):
                    active_class = 'active' if i == st.session_state.prev_pic else ''
                    img_html += f'<img src="{pic}" class="{active_class}" id="img_{i}">'
                img_html += '</div>'

                st.markdown(img_html, unsafe_allow_html=True)


                with st.container(horizontal=True):
                    # Tombol navigasi
                    st.button('⬅️ Previous', disabled=(st.session_state.prev_pic == 0), args=(st.session_state.prev_pic - 1,), on_click=set_prev_pic, width='stretch')
                    st.button('➡️ Next', disabled=(st.session_state.prev_pic == count-1), args=(st.session_state.prev_pic + 1,), on_click=set_prev_pic, width='stretch')
            else:
                st.warning('Picture Unavailable')


                        
        if pd.isna(film['Link']) :
            st.button('🔗 No Link Found!', type='primary', width='stretch')
        else:
            st.link_button("🎬 Preview", film['Link'], width='stretch', type='primary')
        with st.container(key='view_film_edit_container_button', horizontal=True):
            if st.button('✏️ Edit', width='stretch', key='edited'):
                st.session_state.editing_film_index = index
                st.rerun()
            if st.button('❌ Close', width='stretch'):
                st.session_state.viewing_film_index = None
                st.session_state.editing_film_index = None
                st.rerun()

    def show_edit_film(index):
        df = st.session_state.film_df
        film = df.iloc[index]

        info_index = INFO_OPTS.index(film['Info']) if film['Info'] in INFO_OPTS else 0

        with st.container(horizontal_alignment='center'): 
            st.markdown(f"### ✏️ Editing: {film['Code']}")
            st.image(film['Picture'], width=250)
            new_pic = st.file_uploader('Change Image', type=['png', 'jpg', 'jpeg'], key=f'film_picture_{index}')
            if new_pic is not None:
                st.image(new_pic, width=250)
    
        
        st.subheader("Basic Information")

        edited_a = st.toggle('✨', value=film['A-Detector'])
        if edited_a:
            edited_a = True
        else:
            edited_a = False
        film_link = film['Link']

        if film_link == '--':
            film_link = ''

        edited_link = st.text_input('Link Page', key=f'film_link_{index}', placeholder='https://...', value=film_link)

        if edited_link == '':
            edited_link = '--'  

        selected_actress = st.multiselect(
            'Actress', 
            options = ACTRESS_OPTS, 
            default = [
                j.strip() for j in film['Actress Name'].split(',')
                if j.strip() in ACTRESS_OPTS
            ]
        )

        edited_actress = ", ".join(selected_actress)

        if st.checkbox('New Actress', key='new_actress_check'):
            edited_actress = '?'
            edited_actress_input = st.text_input('New Actress Name*', placeholder='Alphabet, Kanji')
            if edited_actress_input:
                try:
                    edited_actress_name, edited_actress_kanji = edited_actress_input.split(', ')
                    st.write('Name: ', edited_actress_name)
                    st.write('Kanji: ', edited_actress_kanji)
                except Exception as e:
                    st.error(f'Error new actress: {e}')
        elif selected_actress:
            edited_actress = ", ".join(selected_actress)
            edited_actress_input = '?'
        else:
            edited_actress = 'Not Listed'
            edited_actress_input = '?'

        edited_code = st.text_input('Code', placeholder='Enter film code (e.g. MIDV-791)', value=film['Code'], key=f'film_code_{index}')
        edited_code = edited_code.upper().replace(' ','-')

        edited_title = st.text_area('Title', placeholder='Enter film title..', value=film['Title'], key=f'film_title_{index}')
        
        if film['Release Date'] == '?':
            release_date = date.today()
        else:
            release_date = datetime.strptime(film["Release Date"], "%d/%m/%Y").date()

        edited_release_date = st.date_input('Release Date', value=release_date, min_value=date(1980,1,1), disabled=(film['Release Date'] == '?'))

        if st.checkbox('No Info', value=(film['Release Date'] == '?'), key=f'check_release_date_{index}'):
            edited_release_date = '?'
            edited_status = '?'
        else:
            if edited_release_date < date.today():
                edited_status = 1
            else:
                edited_status = 0
            edited_release_date = edited_release_date.strftime('%d/%m/%Y')

        edited_info = st.selectbox('Info', options=INFO_OPTS, index= info_index)

        if edited_info == 'Watched' or edited_info == 'Goat':
            if 'Not Listed' not in selected_actress and 'Many' not in selected_actress:
                new_review = []
                actress_list = selected_actress
                matching_actresses = actress_df[actress_df['Name (Alphabet)'].isin(actress_list)]

                for i in matching_actresses.index:
                    review_index = REVIEW_OPTS.index(actress_df['Review'].iloc[i]) if actress_df['Review'].iloc[i] in REVIEW_OPTS else 0
                    with st.container(horizontal=True):
                        with st.container(width=80):
                            st.image(actress_df['Picture'].iloc[i],width=80)
                        with st.container():
                            new_review.append((i,st.selectbox(f'Review "{actress_df["Name (Alphabet)"].iloc[i]}"', options=REVIEW_OPTS, index=review_index, key=f'review_{index}_{i}')))

        if film['Tags'] == 'No Tags':
            tags = []
        else:
            tags = [
                j.strip() for j in film['Tags'].split(',')
                if j.strip() in TAGS_OPTS
            ]

        edited_selected_tags = st.multiselect(
            'Tags', 
            options=TAGS_OPTS, 
            default=tags, 
            key=f'film_Tags_{index}'
        )

        if edited_selected_tags:
            edited_tags = ', '.join(edited_selected_tags)
        else:
            edited_tags = 'No Tags'

        st.write(edited_tags)
        # Tombol aksi
        if 'delete_btn' not in st.session_state:
            st.session_state.delete_btn = False
        


        with st.container(horizontal=True):
            if st.button("💾 Save", width='stretch', type="primary", key=f"save_{index}"):
                join_code = edited_code.upper()
                clean_code = re.sub(r'[^\w]', '', join_code)
                clean_code = "N" + clean_code

                old_filename = str(film['Picture']).split('/')[-1]
                old_public_id = old_filename.split('.')[0]

                if ((edited_actress!='?')or(edited_actress_input!='?')):
                    if edited_actress_input!='?':
                        # Create edited row data
                        edited_row = pd.DataFrame([{
                            'Review': 'Not Checked',
                            'Name (Alphabet)': edited_actress_name,
                            'Name (Kanji)': edited_actress_kanji,
                            'Picture': st.secrets.indicators.PLACEHOLDER_IMG,
                            'Birthdate': '?',
                            'Debut Date': '?',
                            'Size': '?',
                            'Measurement': '?',
                            'Height (cm)': '? cm',
                            'Notes': '--',
                            'Age': '?',
                            'Debut Period': '?',
                            'Retire Date': '?',
                            'Status': 'Active'
                        }])


                        # Add to DataFrame
                        edited_name_kanji = edited_row['Name (Kanji)'].iloc[0]
                        df_actress = st.session_state.actress_df

                        if edited_name_kanji in df_actress['Name (Kanji)'].values:
                            st.warning(f"⚠️ Actress '{edited_name_kanji}' already exist in database with name!")
                            st.stop()
                        else:
                            df_actress = pd.concat([df_actress, edited_row], ignore_index=True)   
                            df_actress = df_actress.sort_values('Name (Alphabet)', key=lambda col: col.str.lower(), ascending=True, ignore_index=True)
                            # Update ke Google Sheets
                            if update_google_sheets(df_actress,conn,'actress'):
                                st.success("✅ edited actress added successfully to Google Sheets!")
                                st.session_state.actress_df = values_handling(df_actress,'actress')  # Update session state
                            else:
                                st.error("❌ Failed to add edited actress to Google Sheets")
                                st.stop()
                        edited_actress = edited_actress_name
                # kalau cuma ganti foto
                if new_pic and (edited_code.upper() == film['Code']):
                    if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower() and "pics.dmm.co.jp" not in str(film['Picture']).lower():
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
                    if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower() and "pics.dmm.co.jp" not in str(film['Picture']).lower():
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
                    if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower() and "pics.dmm.co.jp" not in str(film['Picture']).lower():
                        try:
                            final_picture_url = rename_cloudinary_image(old_public_id, clean_code)
                        except Exception as e:
                            st.warning(f'Could not rename old image: {e}')
                            st.stop()
                    else:
                        final_picture_url = film['Picture']
                else:
                    final_picture_url = film['Picture']
                

                # Update data di DataFrame
                row = index + 2
                new_values = [
                    edited_actress,
                    edited_code,
                    edited_title,
                    edited_release_date,
                    final_picture_url,
                    edited_tags,
                    edited_info,
                    edited_status,
                    edited_link,
                    film['Preview Picture'],
                    edited_a
                ]

                if edited_info != 'Not Watched':
                    if 'Not Listed' not in selected_actress and 'Many' not in selected_actress:
                        for review in new_review:
                            actress_worksheet().update(f'A{int(review[0]+2)}', review[1])
                            actress_df.at[review[0], 'Review'] = review[1]
                
                film_worksheet().update(f"A{row}:K{row}", [new_values])

                df.loc[index] = new_values

                st.session_state.film_df = values_handling(df,'film')
                st.session_state.editing_film_index = None
                st.toast("✅ Data edited successfully!")
                time.sleep(1)
                st.rerun()
        
            if st.button('❌ Close', width='stretch'):
                st.session_state.viewing_film_index = None
                st.session_state.editing_film_index = None
                st.rerun()

        if st.session_state.delete_btn == False:
            if st.button("🗑️ Delete Film", width='stretch', type="secondary", key=f"delete_{index}"):
                st.session_state.delete_btn = True
                st.rerun()
        else:
            st.warning('Are you sure want to delete this movie?')
            with st.container(horizontal=True):
                if st.button('Yes', width='stretch'):
                    st.session_state.delete_btn = False
                    delete_film(index)
                    st.rerun()
                if st.button('No', width='stretch'):
                    st.session_state.delete_btn = False
                    st.rerun()
    
    def delete_film(index):
        df = st.session_state.film_df
        film = df.loc[index]
        pic_filename = str(film['Picture']).split('/')[-1]
        pic_id = pic_filename.split('.')[0]

        if 'placeholder' not in pic_id and "pics.dmm.co.jp" not in str(film['Picture']).lower():
            delete_cloudinary_image(pic_id)

        df.drop(index, inplace=True)    
        df.reset_index(drop=True, inplace=True)

        film_worksheet().delete_row(int(index)+2)

        st.session_state.film_df = values_handling(df,'film')
    
        st.session_state.editing_film_index = None
        st.session_state.viewing_film_index = None
        st.toast("✅ Data deleted successfully!")
        time.sleep(1)
        st.rerun()

    @st.dialog("➕ Add New Film", width='small')
    def add_new_film():
        st.session_state.film_simple_edit = st.toggle('Simple Input', value=st.session_state.film_simple_edit)
        is_simple = st.session_state.film_simple_edit

        new_actress_input = '?'

        if st.session_state.get('film_reset', False):
            st.session_state.film_reset = False
            st.session_state.new_actresses = ''
            st.session_state.new_code = ''
            st.session_state.new_release = date.today()
            st.session_state.new_info = INFO_OPTS[0]

        if 'new_film_reset' not in st.session_state:
            st.session_state.new_film_reset = 0
        
        reset_film = st.session_state.new_film_reset

        new_picture = st.file_uploader('Image', type=['png', 'jpg', 'jpeg'], key=f'new_film_picture_{reset_film}')
        
        if not new_picture is None:
            with st.container(horizontal_alignment='center'):
                st.image(new_picture, width=200)
        
        if not is_simple:
            new_link = st.text_input('Link Page', key='new_link', placeholder='https://...')
            if not new_link:
                new_link = '--'

        selected_actress = st.multiselect('Actress*', key='new_actresses', options=ACTRESS_OPTS)

        if st.checkbox('New Actress', key='new_actress_check'):
            new_actress = '?'
            new_actress_input = st.text_input('New Actress Name*', placeholder='Alphabet, Kanji')
            if new_actress_input:
                new_actress_name, new_actress_kanji = new_actress_input.split(', ')
                st.write('Name: ', new_actress_name)
                st.write('Kanji: ', new_actress_kanji)
        elif selected_actress:
            new_actress = ", ".join(selected_actress)
            new_actress_input = '?'
        else:
            new_actress = '?'
            new_actress_input = '?'

        new_code = st.text_input('Code*', key='new_code', placeholder='MIDV-791, MIDV 791, midv 791 or midv-791')
        new_code = new_code.upper().replace(' ','-')

        if not is_simple:
            new_title = st.text_area('Title*', key='new_title', placeholder='Enter movie title...')

            new_release = st.date_input('Release Date', key='new_release', min_value=date(1980,1,1))
            if new_release < date.today():
                new_status = 0
            else:
                new_status = 1

            if st.checkbox('No Info', key='film_code_check'):
                new_release = '?'
                new_status = '?'
            else:
                st.write(new_release.strftime("%b, %d %Y"))
                new_release = new_release.strftime('%d/%m/%Y')

            new_tags = st.multiselect('Tags', key='new_tags', options=TAGS_OPTS)

            if st.checkbox('New Tags', key='add_new_tags'):
                new_new_tags = st.text_input('New Tag', placeholder='Enter new tag...', key='add_film_new_tag')
                if new_new_tags != '' or new_new_tags != None:
                    new_tags = new_new_tags
            else:
                new_tags = ', '.join(new_tags)

        new_info = st.selectbox('Info', key='new_info', options=INFO_OPTS)

        new_a = st.toggle('✨')

        if is_simple:
            new_link = '--'
            new_title = '--'
            new_release = '?'
            new_status = '?'
            new_tags = 'No Tags'

        with st.container(key='film_new_button'):
            if st.button('💾 Add Film', width='stretch'):
                if new_code and ((new_actress!='?')or(new_actress_input!='?')) and new_title:
                    if new_actress_input!='?':
                        # Create new row data
                        new_row = pd.DataFrame([{
                            'Review': 'Not Checked',
                            'Name (Alphabet)': new_actress_name,
                            'Name (Kanji)': new_actress_kanji,
                            'Picture': st.secrets.indicators.PLACEHOLDER_IMG,
                            'Birthdate': '?',
                            'Debut Date': '?',
                            'Size': '?',
                            'Measurement': '?',
                            'Height (cm)': '? cm',
                            'Notes': '--',
                            'Age': '?',
                            'Debut Period': '?',
                            'Retire Date': '?',
                            'Status': 'Active'
                        }])


                        # Add to DataFrame
                        new_name_kanji = new_row['Name (Kanji)'].iloc[0]
                        df_actress = st.session_state.actress_df

                        if new_name_kanji in df_actress['Name (Kanji)'].values:
                            st.warning(f"⚠️ Actress '{new_name_kanji}' already exist in database with name!")
                            st.stop()
                        else:
                            df_actress = pd.concat([df_actress, new_row], ignore_index=True)   
                            df_actress = df_actress.sort_values('Name (Alphabet)', key=lambda col: col.str.lower(), ascending=True, ignore_index=True)
                            # Update ke Google Sheets
                            if update_google_sheets(df_actress,conn,'actress'):
                                st.success("✅ New actress added successfully to Google Sheets!")
                                st.session_state.actress_df = values_handling(df_actress,'actress')  # Update session state
                            else:
                                st.error("❌ Failed to add new actress to Google Sheets")
                                st.stop()
                        new_actress = new_actress_name

                    df = st.session_state.film_df
                    new_film_code = new_code

                    if new_film_code in df['Code'].values:
                        st.warning(f'⚠️ Code {new_film_code} already exist in database')
                        st.stop()
                    else:
                        if new_picture:
                            join_name = new_code.upper()
                            clean_name = re.sub(r'[^\w]', '', join_name)
                            clean_name = "N" + clean_name
                            picture_url = upload_to_database(new_picture, clean_name)
                        else:
                            picture_url = st.secrets.indicators.PLACEHOLDER_IMG_POSTER

                        new_row = [
                            new_actress,
                            new_code,
                            new_title,
                            new_release,
                            picture_url,
                            new_tags,
                            new_info,
                            new_status,
                            new_link,
                            '--',
                            new_a
                        ]

                        film_data = film_worksheet()

                        film_data.append_row(new_row)
                        new_row_df = pd.DataFrame([new_row], columns=df.columns)

                        df = pd.concat([df, new_row_df], ignore_index=True)

                        st.session_state.film_df = values_handling(df,'film')
                        st.toast("✅ Data added successfully!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error('Fill mandatory fields first! (*)')
                    st.stop()

            if st.button('Close', type='primary', width='stretch'):
                st.rerun()

    with st.sidebar:
        if st.button('⬅️ Back', width='stretch'):
            st.session_state.first_load_film = True
            return 'home'
        st.markdown('---')
        with st.expander('Gacha'):
            if device == 'Device 1':
                img_width_percentage = 45
                img_height = 216
            else:
                img_width_percentage = 40
                img_height = 176

            actress_gacha = st.multiselect('Actress Filter', key='new_actresses', options=ACTRESS_OPTS)
            gacha_df = df.copy()
            if actress_gacha:
                pattern = '|'.join([f'(?:^|, ){a}(?:,|$)' for a in actress_gacha])
                gacha_df = gacha_df[(gacha_df['Actress Name'].str.contains(pattern, na=False, regex=True)) & (gacha_df['Info'] == 'Not Watched')]
            else:
                gacha_df = gacha_df[gacha_df['Info'] == 'Not Watched']
            if st.button('Gacha', width='stretch'):
                random_row = gacha_df.sample(n=1)
                st.subheader('Result')
                st.markdown("""
                    <style>
                    .centered-container {
                        display: flex;
                        justify-content: center;
                        width: 100%;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                    <div class="centered-container">
                        <div style="
                            height: {img_height}px;
                            width: {img_width_percentage}%;
                            overflow: hidden;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            margin-bottom: 10px;
                            border-radius: 5px;
                        ">
                            <img src="{random_row['Picture'].values[0]}" 
                                style="
                                    width: 100%;
                                    height: 100%;
                                    object-fit: cover;
                                    object-position: center;
                                ">
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align: center;'>{random_row['Code'].values[0]}</h3>", unsafe_allow_html=True)
                st.write('**Title :**', random_row['Title'].values[0])
                st.write('**Actress :**', random_row['Actress Name'].values[0])
                st.write('**Review :**', random_row['Info'].values[0])

        with st.expander('Add Tags'):
            if st.session_state.get('reset_tag', False):
                st.session_state.reset_tag = False
                st.session_state.add_new_tag = ''
                st.session_state.film_playlist = []
            new_tag = st.text_input('Tag', placeholder='Enter tag... (tag1, tag2, tag3, ..)', key='add_new_tag')
            if st.button('Save Tag', width='stretch'):
                if not new_tag.isspace() and new_tag:
                    new_tags = []
                    tag_error = False
                    new_tag = new_tag.split(', ')

                    for tag in new_tag:
                        if tag in st.session_state.tag_df['Tags'].values:
                            tag_error = True        
                        else:
                            new_tags.append([tag])

                    if not tag_error:
                        new_tag_df = pd.DataFrame({'Tags': new_tag})
                        st.session_state.tag_df = pd.concat([tag_df, new_tag_df], ignore_index=True)
                        tags_worksheet().append_rows(new_tags)
                        st.session_state.reset_tag = True
                        st.rerun()
                    else:
                        st.warning(f'{tag} already in Tags')
                else:
                    st.warning('Tag cannot be empty')
            
            opts = st.session_state.tag_df['Tags'].values

            test_new_tags = st.multiselect(
                'Test Tags', 
                options=opts, 
                key=f'film_playlist'
            )

            if st.button('Delete Tags', width='stretch'):
                if test_new_tags:
                    tag_df = st.session_state.tag_df
                    rows_to_delete = tag_df[
                        tag_df['Tags'].isin(test_new_tags)
                    ].index.tolist()

                    for index in sorted(rows_to_delete, reverse=True):
                        tags_worksheet().delete_row(int(index)+2)

                    tag_df = tag_df[
                        ~tag_df['Tags'].isin(test_new_tags)
                    ].reset_index(drop=True)

                    st.session_state.tag_df = tag_df

                    st.session_state.reset_tag = True   

                    st.rerun()
                else:
                    st.warning('No Tags selectec above')
                        

        st.markdown('---')
        st.header("⚙️ Display Settings")
        display_mode = st.radio(
            "View Mode",
            ["Detailed", "Simple", "Not Watched", "Calender Scrap"],
            on_change=reset_page,
            horizontal=False,
            key='film_layout'
        )

        st.markdown('---')
        show_a = st.toggle('✨')
        
        st.markdown('---')
        if st.button('➕ Add New Film', width='stretch'):
            add_new_film()
        if st.session_state.log_out_btn == False:
            if st.button('🔐 Logout', width='stretch'):
                st.session_state.log_out_btn = True
                st.rerun()
        else:
            st.warning('Are you sure want to logout?')
            with st.container(horizontal=True):
                if st.button('Yes', width='stretch'):
                    st.session_state.clear()
                    return 'login'
                if st.button('No', width='stretch'):
                    st.session_state.log_out_btn = False
                    st.rerun()

        if st.button('⬆️ Back to top', width='stretch'):
            st.session_state.scroll_to_top = True
    
    # Main
    st.space('small')
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Film List</h1>", unsafe_allow_html=True)
    if st.session_state.viewing_film_index is not None:
        show_film_details()
    
    if st.session_state.first_load_film:
        st.session_state.scroll_to_top = True
        st.session_state.first_load_film = False
    
    filtered_df = df.copy()
    filtered_df = filtered_df.sort_values(by='Code', ascending=True)

    if show_a:
        filtered_df = filtered_df[filtered_df['A-Detector'] == 1]
    
    if display_mode == "Detailed":
        display_film_card(filtered_df, tag_df)
    elif display_mode == "Simple":
        display_film_grid(filtered_df, tag_df)
    elif display_mode == "Calender Scrap":
        display_film_calender(df, conn)
    else:  # Table View
        filtered_df = values_handling(filtered_df, 'film')
        filtered_df = initial_load(filtered_df, 'film')
        filtered_df = filtered_df.loc[filtered_df['Info'] == 'Not Watched'].copy() 

        # Tambahkan search box
        if st.session_state.get('search_reset', False):
            st.session_state.search_reset = False
            st.session_state.search_bar = ''
        
        search_by = st.radio('Search By: ', options=['Code', 'Actress', 'Title'], horizontal=True, key='search_by')
        with st.container(horizontal=True, vertical_alignment='bottom'):
            search_term = st.text_input("🔍 Search (Actress Name / Code):", placeholder="Name or Code...", key='search_bar')
            if st.button('Clear'):
                st.session_state.search_reset = True
                st.rerun()

        # Terapkan filter search jika ada input
        if search_term:
            if search_by == 'Code':
                search_term = search_term.split(' ')
                search_term = '-'.join(search_term)
                mask =  filtered_df['Code'].astype(str).str.contains(search_term, case=False, na=False)
            elif search_by == 'Actress':
                mask = filtered_df['Actress Name'].str.contains(search_term, case=False, na=False)
            else:
                mask = filtered_df['Title'].str.contains(search_term, case=False, na=False)

            filtered_df = filtered_df[mask]

        # Buat kolom baru dengan badge HTML/CSS
        filtered_df['Release'] = filtered_df['Release Status'].apply(
            lambda x: '🟢 Yes' if x == 1 else '🔴 No' if x == 0 else '⚪ ?'
        )

        show_df = filtered_df[['Release', 'Code', 'Actress Name']]

        selected = st.dataframe(
            show_df,
            width='stretch',
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True
        )

        with st.container(horizontal=True):
            with st.container(width='content'):
                if selected:
                    try:
                        pics = filtered_df['Picture'].iloc[selected.selection.rows[0]]
                    except:
                        pics = st.secrets.indicators.PLACEHOLDER_IMG_POSTER

                st.markdown(f"""
                    <div style="
                        height: 250px;  /* Atur tinggi tetap */
                        width: 175px;
                        overflow: hidden;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin-bottom: 10px;
                        border-radius: 5px;
                    ">
                        <img src="{pics}" 
                            style="
                                width: 100%;
                                height: 100%;
                                object-fit: cover;
                                object-position: center;
                            ">
                    </div>
                """, unsafe_allow_html=True)

            with st.container(width='stretch'):
                if st.button('Edit', width='stretch'):
                    if selected.selection.rows:
                        row_index = selected.selection.rows[0]
                        data_index = filtered_df.index[row_index]
                        st.session_state.viewing_film_index = data_index
                        st.session_state.editing_film_index = data_index
                        show_film_details()
                        st.rerun()
                    else:
                        st.error('No rows is selected on the dataframe!')
                        st.stop()

                if selected.selection.rows:
                    row_index = selected.selection.rows[0]
                    link_url = filtered_df.iloc[row_index]['Link']
                    title = filtered_df.iloc[row_index]['Code']
            
                    # Tombol yang akan membuka di tab baru
                    if link_url != '--':
                        st.link_button(f"{title} Preview", link_url, width='stretch', type='primary')
                    else:
                        st.write('No link found!')

                    st.write(filtered_df.iloc[row_index]['Title'])
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

def complex_actress(conn, device):
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Actress List</h1>", unsafe_allow_html=True)

    if 'initial' not in st.session_state:
        st.session_state.initial = False
    if 'delete_btn_actress' not in st.session_state:
        st.session_state.delete_btn_actress = False
    if 'width_option' not in st.session_state:
        st.session_state.width_option = device
    if 'scroll_to_here' not in st.session_state:
        st.session_state.scroll_to_here = False
    if 'display_actress' not in st.session_state:
        st.session_state.display_actress = 'Gallery' 

        
    # Fungsi untuk refresh data dari Google Sheets
    def refresh_data(conn):
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
        df = init_dataframe_actress(conn)

    # Inisialisasi variabel kontrol
    if "editing_index" not in st.session_state:
        st.session_state.editing_index = None
    if "viewing_index" not in st.session_state:
        st.session_state.viewing_index = None
    if "actress_film_index" not in st.session_state:
        st.session_state.actress_film_index = None
    if "adding_new" not in st.session_state:
        st.session_state.adding_new = False
    if "is_simple" not in st.session_state:
        st.session_state.is_simple = False

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
        elif st.session_state.actress_film_index:
            actress_view_film(st.session_state.actress_film_index)
        else:
            show_view_mode(index)
    
    def actress_view_film(index):
        def reset_pic():
            st.session_state.prev_pic = 0

        def set_prev_pic(pic):
            st.session_state.prev_pic = pic


        film = st.session_state.film_df.iloc[index]

        with st.container(key='poster_code', horizontal_alignment='center'):
            st.markdown(f"<h1 style='text-align: center;'>{film['Code']}</h1>", unsafe_allow_html=True)
            st.image(film['Picture'], width=200)
        
        st.markdown('### Title')
        st.write(film['Title'])
        st.markdown(
            """
            <style>
            button[data-testid="stBaseButton-tertiary"] p {
                font-size: 14px !important;
                color: #d6cfc7 !important;
            }
            """,
            unsafe_allow_html=True
        )
        
        st.markdown('### Actress')
        if 'Not Listed' not in film['Actress Name'] and 'Many' not in film['Actress Name']:
            actress_list = film['Actress Name'].split(', ')
            matching_actresses = df[df['Name (Alphabet)'].isin(actress_list)]
            if len(matching_actresses)>2:
                is_center = 'center'
            else:
                is_center = 'left'
            with st.container(horizontal=True, horizontal_alignment=is_center):
                for idx in matching_actresses.index:
                    actress_name = matching_actresses['Name (Alphabet)'][idx]
                    container_key = f"{actress_name}_{index}"

                    with st.container(width=80, key=container_key):
                        # Display image as circle using HTML
                        st.markdown(f"""
                            <div style="
                                width: 70px;
                                height: 70px;
                                border-radius: 50%;
                                overflow: hidden;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                margin: 0 auto 8px auto;
                                background: white;
                            ">
                                <img src="{matching_actresses['Picture'][idx]}" 
                                    style="
                                        width: 100%;
                                        height: 100%;
                                        object-fit: cover;
                                    ">
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Button
                        if st.button(actress_name, width='stretch', type='tertiary', key=f"{actress_name}_{idx}_{idx}", on_click=reset_page):
                            st.session_state.viewing_film_index = None
                            st.session_state.editing_film_index = None
                            st.session_state.search_text = actress_name
                            st.session_state.set_search = True
                            st.session_state.scroll_to_top = True
                            st.rerun()
        elif 'Many' in film['Actress Name']:
            with st.container(width=80):
                st.markdown(f"""
                    <div style="
                        width: 70px;
                        height: 70px;
                        border-radius: 50%;
                        overflow: hidden;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin: 0 auto 8px auto;
                        background: white;
                    ">
                        <img src="{st.secrets.indicators.PLACEHOLDER_IMG}" 
                            style="
                                width: 100%;
                                height: 100%;
                                object-fit: cover;
                            ">
                    </div>
                """, unsafe_allow_html=True)
                if st.button('Many', width='stretch', type='tertiary', key="many_profile", on_click=reset_page):
                    st.session_state.viewing_film_index = None
                    st.session_state.editing_film_index = None
                    st.session_state.search_text = 'Many'
                    st.session_state.set_search = True
                    st.session_state.scroll_to_top = True
                    st.rerun()
        elif 'Not Listed' in film['Actress Name']:
            with st.container(width=80):
                st.markdown(f"""
                    <div style="
                        width: 70px;
                        height: 70px;
                        border-radius: 50%;
                        overflow: hidden;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin: 0 auto 8px auto;
                        background: white;
                    ">
                        <img src="{st.secrets.indicators.PLACEHOLDER_IMG}" 
                            style="
                                width: 100%;
                                height: 100%;
                                object-fit: cover;
                            ">
                    </div>
                """, unsafe_allow_html=True)
                if st.button('Not Listed', width='stretch', type='tertiary', key="not_listed_profile", on_click=reset_page):
                    st.session_state.viewing_film_index = None
                    st.session_state.editing_film_index = None
                    st.session_state.search_text = 'Not Listed'
                    st.session_state.set_search = True
                    st.session_state.scroll_to_top = True
                    st.rerun()

        if film['Release Date'] != '?':
            release_date_text = datetime.strptime(film['Release Date'], '%d/%m/%Y').strftime("%b, %d %Y")
        else:
            release_date_text = '?'

        st.markdown('### Release Date')
        st.write(release_date_text)

        st.markdown('### Status')
        icons = ''
        colors = ''
        if film['Info'] == 'Goat':
            icons = '🟣'
            colors = 'violet'
        elif film['Info'] == 'Watched':
            icons = '🟢'
            colors = 'green'
        else:
            icons = '🔴'
            colors = 'red'
            
        with st.container(horizontal=True):
            st.badge(label=film['Info'], icon=icons, color=colors)
            if film['A-Detector'] == 1:
                st.badge(label='', icon='⭐', color='yellow')


        st.markdown('### Tags')
        st.write(film['Tags'])

        st.markdown('### Gallery')
        if st.checkbox('Show', on_change=reset_pic):
            if film['Preview Picture'] != 'No Pics' and film['Preview Picture'] != '--':

                if 'prev_pic' not in st.session_state:  
                    st.session_state.prev_pic = 0
                
                pics = film['Preview Picture'].split(', ')
                count = len(pics)

                st.markdown(
                    """
                    <style>
                    div[data-testid="stVerticalBlock"] { padding-top: 0rem; padding-bottom: 0rem; }

                    .img-fit {
                        margin-top: -13px; 
                        padding-top: 0; 
                        display: flex;             /* gunakan flexbox */
                        justify-content: center;   /* horizontal center */
                        align-items: center;       /* vertical center jika container tinggi ditentukan */
                        background-color: #ffffff;
                        border-radius: 5px;
                        margin-bottom: 15px;
                    }

                    .img-fit img {
                        max-width: 100%;
                        height: 400px;
                        width: auto;
                        object-fit: contain;
                        display: none;  /* default hidden semua gambar */
                    }

                    .img-fit img.active {
                        display: block; /* hanya gambar active yang terlihat */
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                # HTML untuk semua gambar, preload semuanya
                img_html = '<div class="img-fit">'
                for i, pic in enumerate(pics):
                    active_class = 'active' if i == st.session_state.prev_pic else ''
                    img_html += f'<img src="{pic}" class="{active_class}" id="img_{i}">'
                img_html += '</div>'

                st.markdown(img_html, unsafe_allow_html=True)


                with st.container(horizontal=True):
                    # Tombol navigasi
                    st.button('⬅️ Previous', disabled=(st.session_state.prev_pic == 0), args=(st.session_state.prev_pic - 1,), on_click=set_prev_pic, width='stretch')
                    st.button('➡️ Next', disabled=(st.session_state.prev_pic == count-1), args=(st.session_state.prev_pic + 1,), on_click=set_prev_pic, width='stretch')
            else:
                st.warning('Picture Unavailable')


                        
        if pd.isna(film['Link']) :
            st.button('🔗 No Link Found!', type='primary', width='stretch')
        else:
            st.link_button("🎬 Preview", film['Link'], width='stretch', type='primary')
        if st.button('❌ Close', width='stretch'):
            st.session_state.actress_film_index = None
            st.rerun()

    def show_view_mode(index):
        actress = df.iloc[index]
        film_df = st.session_state.film_df
        film_watched_df = film_df[
            (film_df['Actress Name'].str.contains(
        actress['Name (Alphabet)'],
        na=False)) &
            (film_df['Info'] != 'Not Watched')
        ]
        film_not_watched_df = film_df[
            (film_df['Actress Name'].str.contains(
        actress['Name (Alphabet)'],
        na=False)) &
            (film_df['Info'] == 'Not Watched')
        ]

        # Layout utama dengan gambar dan info dasar
        col1, col2 = st.columns([1, 2])
        
        with col1:
            with st.container(horizontal_alignment='center'):
                st.image(actress['Picture'] if pd.notna(actress['Picture']) else "", width=200)
                # st.markdown(f"### {actress['Name (Alphabet)']}")
                # st.markdown(f"# {actress['Name (Kanji)'] if pd.notna(actress['Name (Kanji)']) else ''}")
            
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <h2>{actress['Name (Alphabet)']}</h2>
                    <h2>{actress['Name (Kanji)'] if pd.notna(actress['Name (Kanji)']) else ''}</h1>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Tombol Edit dan Close
            button_container = st.container(key='view_edit_close', horizontal=True)
            with button_container:
                if st.button("✏️ Edit", width='stretch', key=f"edit_btn_{index}"):
                    st.session_state.editing_index = index
                    st.rerun()

                if st.button("❌ Close", width='stretch', key=f"close_{index}"):
                    st.session_state.viewing_index = None
                    st.session_state.editing_index = None
                    st.rerun()
            pages = actress['Page']
            if pages == '--':
                if st.button('Actress Page', width='stretch', type='primary'):
                    st.warning('No link found')
            else:
                st.link_button(f"Actress Page", actress['Page'], width='stretch', type='primary')
            
        
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
                with st.container():
                    st.markdown("#### 🎭 Debut")
                    st.write(debut_date_text)
            
        with timeline_col2:
            if pd.notna(actress['Debut Period']) and actress['Debut Period']:
                with st.container():
                    st.markdown("#### ⏳ Experience")
                    st.write(str(actress['Debut Period']))
        
        with timeline_col3:
            if pd.notna(actress['Retire Date']) and actress['Retire Date']:
                with st.container():
                    st.markdown("#### 🏁 Retire Date")
                    if actress['Retire Date'] == '?':
                        st.write('Still Active')
                    else:
                        st.write(datetime.strptime(actress['Retire Date'], '%d/%m/%Y').strftime("%b, %d %Y"))
            else:
                with st.container():
                    st.markdown("#### 🏁 Retire Date")
                    st.write("Still Active")
        
        st.markdown("---")
        st.markdown("### 🎬 Filmography")
        if st.session_state.width_option == 'Device 1':
            img_width = 140
            img_height = 199
        else:
            img_width = 127
            img_height = 181
        with st.expander("### ✅ Watched Movies"):
            with st.container(horizontal=True):
                for idx in film_watched_df.index:
                    with st.container(width=img_width):
                        st.markdown(f"""
                                <div style="
                                    height: {img_height}px;  /* Atur tinggi tetap */
                                    width: 100%;
                                    overflow: hidden;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    margin-bottom: 10px;
                                    border-radius: 5px;
                                ">
                                    <img src="{film_watched_df['Picture'][idx]}" 
                                        style="
                                            width: 100%;
                                            height: 100%;
                                            object-fit: cover;
                                            object-position: center;
                                        ">
                                </div>
                            """, unsafe_allow_html=True)
                        if st.button(film_watched_df['Code'][idx], key=f'{film_watched_df["Code"][idx]}', type='secondary', width='stretch'):
                            st.session_state.actress_film_index = idx
                            st.rerun()
        with st.expander("### ❌ Unwatched Movies"):
            with st.container(horizontal=True):
                for idx in film_not_watched_df.index:
                    with st.container(width=img_width):
                        st.markdown(f"""
                                <div style="
                                    height: {img_height}px;  /* Atur tinggi tetap */
                                    width: 100%;
                                    overflow: hidden;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    margin-bottom: 10px;
                                    border-radius: 5px;
                                ">
                                    <img src="{film_not_watched_df['Picture'][idx]}" 
                                        style="
                                            width: 100%;
                                            height: 100%;
                                            object-fit: cover;
                                            object-position: center;
                                        ">
                                </div>
                            """, unsafe_allow_html=True)
                        if st.button(film_not_watched_df['Code'][idx], key=f'{film_not_watched_df["Code"][idx]}', type='secondary', width='stretch'):
                            st.session_state.actress_film_index = idx
                            st.rerun()

        st.markdown("---")
        
        # Notes/Review
        st.markdown("### 📝 Notes")
        if pd.notna(actress['Notes']) and actress['Notes']:
            st.warning(actress['Notes'])
        else:
            st.warning('--')
        
        st.markdown("---")
        
        # Personal Notes Section
        st.write("### 📖 Your Personal Notes")

        if st.session_state.get('reset_notes', False):
            st.session_state.reset_notes = False
            key = f'personal_notes_{index}'
            if key in st.session_state:
                st.session_state[key] = None


        personal_notes = st.text_input(
            "Add your own notes about this actress...", 
            placeholder="Write your thoughts, reviews, or observations about this actress...",
            key=f"personal_notes_{index}"
        )
        
        button_container = st.container(horizontal=True, horizontal_alignment='center', key='view_editNotes')
        with button_container:
            if st.button("💾 Save Notes", width='stretch', key=f"save_{index}"):
                st.session_state.reset_notes = True
                if personal_notes:
                    current_notes = df['Notes'].iloc[index]
                    if current_notes == '' or current_notes == '--':
                        edited_notes = f'- {personal_notes}'
                    else:
                        edited_notes = f'{current_notes}\n - {personal_notes}'
                    df.at[index, 'Notes'] = edited_notes
                
                    if update_google_sheets(df,conn,'actress'):
                        st.session_state.actress_df = values_handling(df,'actress')  # Update session state
                    else:
                        st.error("❌ Failed to update Google Sheets")
                        st.stop()
                    st.rerun()
                else:
                    st.warning('Note empty!')
                    st.stop()
                

            if st.button("Close", width='stretch', key=f'cancel_{index}', type='primary'):
                st.session_state.viewing_index = None
                st.session_state.editing_index = None
                st.rerun()

    def show_edit_mode(index):
        df = st.session_state.actress_df
        actress = df.iloc[index]
        
        st.markdown(f"### ✏️ Editing: {actress['Name (Alphabet)']}")
        
        # Layout columns
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display current image
            with st.container(horizontal_alignment='center'):
                if pd.notna(actress['Picture']) and actress['Picture']:
                    st.image(actress['Picture'], width=200)
                else:
                    st.write("No picture available")
            
            # Image uploader
            new_pic = st.file_uploader("Change Image", type=['png', 'jpg', 'jpeg'], key=f"uploader_{index}")
            if new_pic is not None:
                with st.container(horizontal_alignment='center'):
                    st.subheader('New Image')
                    st.image(new_pic, width=200)
            
            # Tombol aksi
            if st.button("← Back to View", width='stretch', key=f"back_{index}"):
                st.session_state.editing_index = None
                st.rerun()
            
            if st.button("Close", width='stretch', key=f"close_{index}"):
                st.session_state.viewing_index = None
                st.session_state.editing_index = None
                st.rerun()
            
            if st.session_state.delete_btn_actress == False:
                if st.button("🗑️ Delete Actress", width='stretch', type="secondary", key=f"delete_{index}"):
                    st.session_state.delete_btn_actress = True
                    st.rerun()
            else:
                st.warning('Are you sure want to delete this actress?')
                with st.container(horizontal=True):
                    if st.button('Yes', width='stretch'):
                        st.session_state.delete_btn_actress = False
                        delete_actress(index)
                        st.rerun()
                    if st.button('No', width='stretch'):
                        st.session_state.delete_btn_actress = False
                        st.rerun()
        
        with col2:
            # Basic Information
            st.subheader("Basic Information")
            review_index = REVIEW_OPTS.index(actress['Review']) if actress['Review'] in REVIEW_OPTS else 0
            size_index = SIZE_OPTS.index(actress['Size']) if actress['Size'] in SIZE_OPTS else 0
            status_index = STATUS_OPTS.index(actress['Status']) if actress['Status'] in STATUS_OPTS else 0

            if actress['Page'] == '--':
                pages = ''
            else:
                pages = actress['Page']

            edited_link = st.text_input('Actress Page', placeholder='Enter your actress link page...', value=pages)
            if not edited_link:
                edited_link = '--'

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
                key=f"birthdate_{index}",
                min_value=date(1981,1,1)
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
                key=f"retire_date_{index}"
            )

            retire_date = edited_retire_date
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
            period = relativedelta(retire_date, edited_debut_date)

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

            if height == '?':
                height = '130'
            
            edited_height = st.number_input(
                "Height (cm)",
                value=int(height),
                key=f"height_{index}"
            )

            if st.checkbox('No Info', value=(actress['Height (cm)'] == '?'), key='Height Check'):
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
        if st.button("💾 Save Changes", width='stretch', type="primary", key=f"save_{index}"):
            if edited_measurement != '?':
                edited_measurement = f"B{b} / W{w} / H{h}"
            
            # Generate clean name untuk public_id
            join_name = edited_name
            clean_name = re.sub(r'[^\w]', '', join_name)
            clean_name = "N" + clean_name

            old_filename = str(actress['Picture']).split('/')[-1]
            old_public_id = old_filename.split('.')[0]
            if new_pic and (edited_kanji == actress['Name (Kanji)']):
                if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture']).lower():
                    try:
                        delete_cloudinary_image(old_public_id)
                    except Exception as e:
                        st.warning(f"Could not delete old image: {e}")
                        st.stop()
                
                final_picture_url = upload_to_database(new_pic, clean_name)
                if not final_picture_url:
                    st.error("Failed to upload new image")
                    st.stop()
                    return
            # kalau ganti foto dan code
            elif new_pic and (edited_kanji != actress['Name (Kanji)']):
                if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture']).lower():
                    if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture']).lower():
                        try:
                            delete_cloudinary_image(old_public_id)
                        except Exception as e:
                            st.warning(f"Could not delete old image: {e}")
                            st.stop()
                    
                    final_picture_url = upload_to_database(new_pic, clean_name)
                    if not final_picture_url:
                        st.error("Failed to upload new image")
                        st.stop()
                        return
            # kalau cuma ganti code
            elif not new_pic and (edited_kanji != actress['Name (Kanji)']):
                if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture']).lower():
                    try:
                        final_picture_url = rename_cloudinary_image(old_public_id, clean_name)
                    except Exception as e:
                        st.warning(f'Could not rename old image: {e}')
                        st.stop()
            
            elif not new_pic and (edited_kanji == actress['Name (Kanji)']):
                try:
                    final_picture_url = actress['Picture']
                except Exception as e:
                    st.warning(f'Could not rename old image: {e}')
                    st.stop()

            new_values = [
                edited_review,
                final_picture_url,
                edited_name,
                edited_kanji,
                edited_birthdate,
                edited_debut_date,
                edited_size,
                edited_measurement,
                edited_height,
                edited_notes,
                age,
                debut,
                edited_retire_date,
                edited_status,
                edited_link
            ]

            row = index + 2
            actress_worksheet().update(f"A{row}:O{row}", [new_values])

            df.loc[index] = new_values

            st.session_state.actress_df = values_handling(df,'actress')  # Update session state
            st.session_state.editing_index = None
            st.rerun()
            

    def delete_actress(index):
        # Hapus data dari DataFrame
        df = st.session_state.actress_df
        actress = df.loc[index]
        pic_filename = str(actress['Picture']).split('/')[-1]
        pic_id = pic_filename.split('.')[0]

        if 'placeholder' not in pic_id.lower():
            delete_cloudinary_image(pic_id)

        df.drop(index, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        actress_worksheet().delete_row(int(index)+2)

        st.session_state.actress_df = values_handling(df,'actress')  # Update session state
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
            st.session_state.is_simple = st.toggle('Simple Input', value=st.session_state.is_simple)
            simple_trigger = st.session_state.is_simple

            # Basic Information
            st.subheader("Basic Information")

            if not simple_trigger:
                new_picture = st.file_uploader("Image", type=['png', 'jpg', 'jpeg'], key=f'new_picture_{reset_pic}')

                if not new_picture is None:
                    st.image(new_picture, width=200)    
                
                new_page = st.text_input('Actress Page', placeholder='Enter your actress link page...', key='new_page')
                new_review = st.selectbox("Review", options=REVIEW_OPTS, key='new_review')
            new_name = st.text_input("Name (Alphabet)*", placeholder="Enter name in alphabet", key='new_name')
            new_kanji = st.text_input("Name (Kanji)*", placeholder="Enter name in kanji", key='new_kanji')
            
            if not simple_trigger:
                new_birthdate = st.date_input("Birthdate", min_value=date(1980,1,1), key='new_birthdate')
                if st.checkbox('No Info', key='New Birthdate', value=(new_birthdate == None)):
                    new_birthdate = '?'
                    new_age = '?'
                elif new_birthdate != None:
                    new_age = relativedelta(date.today(), new_birthdate).years        
                    new_birthdate = new_birthdate.strftime('%d/%m/%Y')
                else:
                    new_birthdate = '?'
                    new_age = '?'

                with col2:
                    # Career Information
                    st.subheader("Career Information")
                    new_debut_date = st.date_input("Debut Date", min_value=date(1980,1,1), key='new_debut_date')
                    if st.checkbox('No Info', key='New Debut Date', value=(new_debut_date == None)):
                        new_debut_date= '?'
                    elif new_debut_date == None:
                        new_debut_date = '?'

                    new_status = st.selectbox("Status", options=STATUS_OPTS, key='new_status')
                    if new_status == 'Retired':
                        new_retire_date = st.date_input("Retire Date*", min_value=date(1980,1,1), key='new_retire_date')
                        if new_retire_date != None:
                            new_retire_date = new_retire_date.strftime('%d/%m/%Y')
                        else:
                            st.error('Please input the Retire Date')
                    else:
                        new_retire_date = '?'
                    
                    # Physical Information
                    st.subheader("Physical Information")
                    new_size = st.selectbox("Size", options=SIZE_OPTS, key='new_size')

                    new_measurement = st.text_input("Measurement", placeholder="e.g., 75-56-80", key='new_measurement')
                    if st.checkbox('No Info',  key='New Measurement') or new_measurement == '':
                        new_measurement = '?'
                    elif new_measurement != '?':
                        b,w,h = new_measurement.split('-')
                        new_measurement = f'B{b} / W{w} / H{h}'
                    else:
                        new_measurement = '?'

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

                if not new_notes:
                    new_notes = '--'

        if simple_trigger:
            # Create new row data
            new_review = 'Not Checked'
            new_picture = ''
            new_birthdate = '?'
            new_debut_date = '?'
            new_size = '?'
            new_measurement = '?'
            new_height = '? cm'
            new_notes = '--'
            new_age = '?'
            new_debut_period = '?'
            new_retire_date = '?'
            new_status = 'Active'
            new_page = '--'

        
        # Tombol submit
        with st.container(horizontal=True):
            submit_new = st.button("💾 Add Actress", width='stretch')
            cancel_new = st.button("❌ Cancel", width='stretch')
        
        if submit_new:
            if new_name and new_kanji and new_retire_date:
                if new_picture:
                    join_name = new_name
                    clean_name = re.sub(r'[^\w]', '', join_name)
                    clean_name = "N" + clean_name
                    picture_url = upload_to_database(new_picture, clean_name)
                else:
                    picture_url = st.secrets.indicators.PLACEHOLDER_IMG

                # Create new row data
                new_row = [
                    new_review,
                    picture_url,
                    new_name,
                    new_kanji,
                    new_birthdate,
                    new_debut_date,
                    new_size,
                    new_measurement,
                    new_height,
                    new_notes,
                    new_age,
                    new_debut_period,
                    new_retire_date,
                    new_status,
                    new_page
                ]

                df = st.session_state.actress_df

                if new_kanji in df['Name (Kanji)'].values:
                    st.warning(f"⚠️ Aktris '{new_kanji}' sudah ada di database!")
                    st.stop()
                else:
                    actress_worksheet().append_row(new_row)
                    new_row_df = pd.DataFrame([new_row], columns=df.columns)
                    
                    df = pd.concat([df, new_row_df], ignore_index=True)   
                    df = df.sort_values('Name (Alphabet)', key=lambda col: col.str.lower(), ascending=True, ignore_index=True)
                    st.session_state.actress_df = values_handling(df,'actress')  # Update session state
                    st.session_state.adding_new = False
                    st.rerun()
            else:
                st.error('Fill mandatory fields first! (*)') # Error disini
                st.stop()
        
        if cancel_new:
            st.session_state.adding_new = False
            st.rerun()


    # Sidebar
    with st.sidebar:
        if st.button('⬅️ Back', width='stretch'):
            return 'home'
        st.header(f'Actress Listed : {len(st.session_state.actress_df)}')
        st.markdown("---")
        st.session_state.display_actress = st.radio(
            "View Mode",
            ["Gallery", "Detailed"],
            key='display_mode_radio',
            index=0 if st.session_state.display_actress == "Gallery" else 1
        )
        st.markdown("---")
        with st.container(key='filter_container', horizontal=True):
            with st.container(key='status_filter'):
                st.header("Status Filters")
                show_active = st.checkbox("Active", value=True, on_change=reset_page_actress)
                show_retired = st.checkbox("Retired", value=True, on_change=reset_page_actress)
                show_no_info = st.checkbox("No Info", value=True, on_change=reset_page_actress)
                show_slow_release = st.checkbox("Slow Release", value=True, on_change=reset_page_actress)
                show_problem = st.checkbox("Problem", value=True, on_change=reset_page_actress)
            with st.container(key='review_filter'):
                st.header("Review Filters")
                show_review_not_checked = st.checkbox("Not Checked",value=False, on_change=reset_page_actress)
                show_review_s = st.checkbox("S-Tier",value=True, on_change=reset_page_actress)
                show_review_a = st.checkbox("A-Tier",value=True, on_change=reset_page_actress)
                show_review_b = st.checkbox("B-Tier",value=True, on_change=reset_page_actress)
                show_review_c = st.checkbox("C-Tier",value=True, on_change=reset_page_actress)
                show_review_d = st.checkbox("D-Tier",value=True, on_change=reset_page_actress)
                show_review_e = st.checkbox("E-Tier",value=True, on_change=reset_page_actress)
                show_review_f = st.checkbox("F-Tier",value=True, on_change=reset_page_actress)
                show_review_drop = st.checkbox("Drop",value=False, on_change=reset_page_actress)
        
        st.markdown("---")
        st.subheader("Management")
        if st.button("➕ Add New Actress", width='stretch'):
            st.session_state.adding_new = True
        
        # # Tombol refresh data
        # if st.button("🔄 Refresh Data", width='stretch'):
        #     refresh_data()
        #     st.rerun()
        
        if st.session_state.log_out_btn == False:
            if st.button('🔐 Logout', width='stretch'):
                st.session_state.log_out_btn = True
                st.rerun()
        else:
            st.warning('Are you sure want to logout?')
            with st.container(horizontal=True):
                if st.button('Yes', width='stretch'):
                    st.session_state.clear()
                    return 'login'
                if st.button('No', width='stretch'):
                    st.session_state.log_out_btn = False
                    st.rerun()

    # Tampilkan dialog add new jika needed
    if st.session_state.adding_new:
        add_new_actress()

    # Tampilkan dialog details jika needed
    if st.session_state.viewing_index is not None:
        show_actress_details()
        # st.session_state.viewing_index = Nonex

    # # Tampilkan grid actress
    # with mid:
    if not df.empty and 'Picture' in df.columns:
        if st.session_state.get('search_reset', False):
            st.session_state.search_reset = False
            st.session_state.search_bar = ''
        
        search_container = st.container(horizontal=True, vertical_alignment='bottom')

        if st.session_state.scroll_to_here:
            scroll_to_here(0,key='here')  # Scroll to the top of the page
            st.session_state.scroll_to_here = False
        with search_container:
            search_query = st.text_input("🔍 Search actress by Name (Alphabet / Kanji):", 
                            placeholder="Type name to search...", key='search_bar', on_change=reset_page_actress)
            if st.button('Clear', on_click=reset_page_actress):
                st.session_state.search_reset = True
                st.rerun()

        if device == 'Device 1':
            img_width = 110
        else:
            img_width = 101

        # Filter DataFrame berdasarkan status
        filtered_df = df.copy()

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
        
        review_conditions = []
        if show_review_drop:
            review_conditions.append(filtered_df['Review'].str.lower() == 'drop')
        if show_review_not_checked:
            review_conditions.append(filtered_df['Review'].str.lower() == 'not checked')
        if show_review_s:
            review_conditions.append(filtered_df['Review'].str.lower() == 's-tier')
        if show_review_a:
            review_conditions.append(filtered_df['Review'].str.lower() == 'a-tier')
        if show_review_b:
            review_conditions.append(filtered_df['Review'].str.lower() == 'b-tier')
        if show_review_c:
            review_conditions.append(filtered_df['Review'].str.lower() == 'c-tier')
        if show_review_d:
            review_conditions.append(filtered_df['Review'].str.lower() == 'd-tier')
        if show_review_e:
            review_conditions.append(filtered_df['Review'].str.lower() == 'e-tier')
        if show_review_f:
            review_conditions.append(filtered_df['Review'].str.lower() == 'f-tier')

        
        if status_conditions:
            status_mask = status_conditions[0]
            for cond in status_conditions[1:]:
                status_mask |= cond
        else:
            status_mask = pd.Series(False, index=filtered_df.index)
        
        if review_conditions:
            review_mask = review_conditions[0]
            for cond in review_conditions[1:]:
                review_mask |= cond
        else:
            review_mask = pd.Series(False, index=filtered_df.index)
        
        final_mask = status_mask & review_mask
        filtered_df = filtered_df[final_mask]
        if search_query and not search_query.isspace() and not filtered_df.empty:
            search_lower = search_query.lower().strip()
            search_mask = (
                filtered_df['Name (Alphabet)'].fillna('').str.lower().str.contains(search_lower, na=False) |
                filtered_df['Name (Kanji)'].fillna('').str.contains(search_query.strip(), na=False)
            )
            filtered_df = filtered_df[search_mask]
        filtered_df = filtered_df.sort_values('Name (Alphabet)', key=lambda col: col.str.lower(), ascending=True, ignore_index=False)

        total_actress_pages = max(1, (len(filtered_df) + 30 - 1) // 30)
        st.markdown('---')
        if 'actress_page' not in st.session_state:
            st.session_state.actress_page = 1

        def set_page(p):
            st.session_state.actress_page = p
        st.markdown(
            f"<div style='text-align:center; font-weight:600;padding-bottom:15px'>Page {st.session_state.actress_page}</div>",
            unsafe_allow_html=True
        )

        if total_actress_pages <= 6:
            with st.container(key='page_button', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_actress_pages + 1):
                    st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.actress_page),
                        on_click=set_page,
                        args=(i,)
                    )
        else:
            with st.container(key='page_button_top', horizontal=True, horizontal_alignment='center'):
                st.button('⬅️',key='previous_top', disabled=(st.session_state.actress_page == 1), on_click=set_page, args=(st.session_state.actress_page-1,))
                
                start_page = max(1, st.session_state.actress_page - 1)  
                end_page = min(total_actress_pages, st.session_state.actress_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_actress_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_actress_pages - 3), total_actress_pages + 1)
                
                for i in pages_to_show:
                    st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.actress_page),
                        on_click=set_page,
                        args=(i,)
                    )
                
                st.button('➡️',key='next_top', disabled=(st.session_state.actress_page == total_actress_pages), on_click=set_page, args=(st.session_state.actress_page+1,))
                
        
        page = st.session_state.actress_page
        
        start_idx = (page - 1) * 30 # page = 2 / Start idx = 8
        end_idx = min(start_idx + 30, len(filtered_df)) # end idx = 16
        
        st.caption(f"Showing {start_idx+1}-{end_idx} from {len(filtered_df)} films")
        
        rows_to_display = filtered_df.iloc[start_idx:end_idx] #[8,15]
        if search_query and not search_query.isspace() and not filtered_df.empty:
            st.info(f'Showing {len(filtered_df)} results')
        elif search_query and not search_query.isspace() and filtered_df.empty:
            st.warning("No actresses match the selected filters.")
        
        if st.session_state.display_actress == 'Detailed':
            with st.container(horizontal=True, horizontal_alignment='center'):
                for idx in rows_to_display.index:
                    actress = df.iloc[idx]    
                    try:
                        with st.container(width='content'):
                            cat_url = actress['Picture'] if pd.notna(actress['Picture']) else ""
                            name_text = actress['Name (Alphabet)'] if pd.notna(actress['Name (Alphabet)']) else ""
                            kanji_text = actress['Name (Kanji)'] if pd.notna(actress['Name (Kanji)']) else ""
                            
                            review_class = actress["Review"].lower().strip().replace(" ", "-")
                            # Buat card dengan HTML lengkap
                            card_html = f"""
                            <div class="card-wrapper">
                                <div class="cat-card review-{review_class}">
                                    <div class="badge-stack">
                                        <div class="review-badge review-{review_class}">
                                            {actress["Review"]}
                                        </div>
                                    </div>
                                    <div class="cat-image-container">
                                        <img src="{cat_url}" class="cat-image review-{review_class}" width="150" height="150">
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
                            if st.button("View Details", key=f"view_{idx}", type='primary', width='stretch'):
                                st.session_state.viewing_index = idx
                                st.session_state.editing_index = None
                                st.rerun()
                                    
                    except Exception as e:
                        # with col:
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
            with st.container(horizontal=True,horizontal_alignment='center'):
                for idx in rows_to_display.index:
                    actress = df.iloc[idx]
                    with st.container(width=img_width+5):
                        st.markdown(f"""
                                <div class="review-avatar review-{'-'.join(actress['Review'].lower().split(' '))}" style="
                                    width: {img_width}px;
                                    height: {img_width}px;
                                    border-radius: 50%;
                                    overflow: hidden;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    margin: 0 auto 8px auto;
                                    background: white;
                                ">
                                    <img src="{actress['Picture']}" 
                                        style="
                                            width: 100%;
                                            height: 100%;
                                            object-fit: cover;
                                        ">
                                    <div class="review-badge-gallery review-{'-'.join(actress['Review'].lower().split(' '))}">
                                        {actress['Review'].replace('-Tier','')}
                                    </div>

                                </div>
                            """, unsafe_allow_html=True)
                        if st.button(actress['Name (Alphabet)'], width='stretch', type='tertiary'):
                            st.session_state.viewing_index = idx
                            st.session_state.editing_index = None
                            st.rerun()
        st.markdown('---')
        if total_actress_pages <= 6:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_actress_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.actress_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
        else:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_bottom', disabled=(st.session_state.actress_page == 1), on_click=set_page, args=(st.session_state.actress_page-1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
                start_page = max(1, st.session_state.actress_page - 1)  
                end_page = min(total_actress_pages, st.session_state.actress_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_actress_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_actress_pages - 3), total_actress_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.actress_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_bottom', disabled=(st.session_state.actress_page == total_actress_pages), on_click=set_page, args=(st.session_state.actress_page+1,)):
                    st.session_state.scroll_to_here = True    
                    st.rerun()
    else:
        st.info("No actress data available. Click 'Add New Actress' to get started!")
    
    # CSS untuk styling card yang estetik
    st.markdown("""
    <style>
        /* Container untuk beberapa badge */
        .badge-stack {
            position: absolute;
            top: 15px;
            right: 10px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            gap: 6px;
            z-index: 10;
        }

        /* Review badge */
        .review-badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            text-align: center;
            color: white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }

        /* Warna review */
        .review-drop { background-color: #7f8c8d !important; }
        .review-not-checked {
            background-color: #bdc3c7 !important;
            color: #2c3e50 !important;
        }
        .review-s-tier { 
            background-color: #FFD700 !important; 
            color: #2c3e50 !important;
        }

        .review-a-tier { background-color: #9b59b6 !important; }
        .review-b-tier { background-color: #3498db !important; }
        .review-c-tier { 
            background-color: #2ecc71 !important; 
            color: #2c3e50 !important;
        }
        .review-d-tier { background-color: #e67e22 !important; }
        .review-e-tier { background-color: #ff8c42 !important; }
        .review-f-tier { background-color: #e74c3c !important; }

        /* Supaya badge nempel di card */
        .cat-card {
            position: relative;
        }

        .cat-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 15px 15px;
            margin-bottom: 15px;
            border-radius: 15px;
            border: 2px solid transparent;   /* ⬅ penting */
            background: linear-gradient(135deg, #ffffff 0%, #e8ebee 100%);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            min-height: 260px;
            width: 100%;
            max-width: 190px;
            cursor: pointer;
        }
        /* ===== BORDER BASED ON TIER ===== */
        .review-wrapper {
            position: relative;
            display: inline-block;
        }

        .review-avatar {
            border-radius: 50%;
            overflow: hidden;
            border: 4px solid transparent;
        }

        .review-badge-gallery {
            position: absolute;
            top: -5px;
            right: 8px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: bold;
            border-radius: 50%;
            background: white;
            box-shadow: 0 3px 8px rgba(0,0,0,0.3);
            z-index: 20;
        }

        .review-s-tier { border-color: #FFD700 !important; }
        .review-a-tier { border-color: #9b59b6 !important; }
        .review-b-tier { border-color: #3498db !important; }
        .review-c-tier { border-color: #2ecc71 !important; }
        .review-d-tier { border-color: #e67e22 !important; }
        .review-e-tier { border-color: #ff8c42 !important; }
        .review-f-tier { border-color: #e74c3c !important; }
        .cat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        }
        .cat-image-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 15px;
            width: 115px;
            height: 115px;
            overflow: hidden;
            border-radius: 10px;
            background: linear-gradient(135deg, #F5E5E1 0%, #f8f9fa 100%);
        }
        .cat-image {
            border-radius: 10px;
            object-fit: cover;
            max-width: 115px;
            max-height: 115px;
            border: 2px solid transparent;
        }
        .cat-name {
            font-weight: 700;
            font-size: 13px;
            color: #2c3e50;
            margin: 5px 0;
            line-height: 1.3;
        }
        .cat-kanji {
            font-size: 15px;
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

    st.markdown("""
    <style>
    /* ================= DESKTOP ================= */
    @media (min-width: 768px) {
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100% !important;
            width: 400px !important;
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