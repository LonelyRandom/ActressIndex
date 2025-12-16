import streamlit as st
import cloudinary
import cloudinary.uploader

# pip install cloudinary

cloudinary.config(
    cloud_name=st.secrets.cloudinary.CLOUDINARY_CLOUD_NAME,
    api_key=st.secrets.cloudinary.CLOUDINARY_API_KEY,
    api_secret=st.secrets.cloudinary.CLOUDINARY_API_SECRET
)

def upload_to_database(uploaded_file, clean_name):
    with st.spinner("Uploading..."):
        try:
            # Upload ke Cloudinary
            result = cloudinary.uploader.upload(
                uploaded_file,
                public_id = clean_name,
                use_filename = False,
                uniquq_filename = False,
                overwrite = True
            )
            image_url = result['secure_url']
            
            return image_url
            
        except Exception as e:
            st.error(f"❌ Error: {e}")

def delete_cloudinary_image(public_id):
    try:
        result = cloudinary.uploader.destroy(public_id)
        if result.get('result') == 'ok':
            return True
        else:
            st.warning(f"⚠️ Gagal hapus gambar: {result.get('result')}")
            return True
    except Exception as e:
        st.error(f"❌ Error hapus gambar: {e}")
        return False

def rename_cloudinary_image(old_public_id, new_public_id):
    try:        
        # Rename di Cloudinary
        result = cloudinary.uploader.rename(
            old_public_id,
            new_public_id
        )
        image_url = result['secure_url']
        return image_url
    except Exception as e:
        return str(e)
    