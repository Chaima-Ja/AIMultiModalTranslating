"""Streamlit UI for translation pipeline - Simplified and User-Friendly."""
import streamlit as st
import requests
import time
from pathlib import Path

# API base URL
API_BASE_URL = "http://localhost:8000"

# Allowed file types
ALLOWED_TYPES = [
    "pdf", "docx", "doc",
    "pptx", "ppt",
    "mp3", "mp4", "wav", "m4a", "ogg", "flac"
]


def check_api_health():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def upload_file(file):
    """Upload file to API and return job_id."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(f"{API_BASE_URL}/translate", files=files, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None


def get_job_status(job_id):
    """Get status of a translation job."""
    try:
        response = requests.get(f"{API_BASE_URL}/status/{job_id}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


def download_file(job_id, filename):
    """Download translated file."""
    try:
        response = requests.get(f"{API_BASE_URL}/download/{job_id}", timeout=30, stream=True)
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"Download failed: {e}")
        return None


def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def main():
    st.set_page_config(
        page_title="AI Translator",
        page_icon="🌍",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for cleaner look
    st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-size: 1.1rem;
    }
    .file-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .status-box {
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("<h1 style='text-align: center; margin-bottom: 0.5rem;'>🌍 AI Translator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; margin-bottom: 2rem;'>Translate your documents and audio files from English to French</p>", unsafe_allow_html=True)
    
    # Check API health (minimal indicator)
    if not check_api_health():
        st.error("⚠️ **API server is not running**")
        st.info("Please start the API server: `python start_api.py`")
        st.stop()
    
    # Main content area
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Initialize session state
        if "job_id" not in st.session_state:
            st.session_state.job_id = None
        if "uploaded_file_name" not in st.session_state:
            st.session_state.uploaded_file_name = None
        
        # Step 1: File Upload
        if st.session_state.job_id is None:
            st.markdown("### 📤 Step 1: Upload Your File")
            
            uploaded_file = st.file_uploader(
                "",
                type=ALLOWED_TYPES,
                help="Supported: PDF, DOCX, PPTX, MP3, MP4, WAV, and more",
                label_visibility="collapsed"
            )
            
            if uploaded_file is not None:
                st.markdown(f"""
                <div class="file-info">
                    <strong>📄 {uploaded_file.name}</strong><br>
                    <small>Size: {format_file_size(uploaded_file.size)}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🚀 Translate Now", type="primary", use_container_width=True):
                    with st.spinner("Uploading..."):
                        result = upload_file(uploaded_file)
                    
                    if result:
                        st.session_state.job_id = result["job_id"]
                        st.session_state.uploaded_file_name = uploaded_file.name
                        st.rerun()
        
        # Step 2: Progress & Download
        else:
            job_id = st.session_state.job_id
            uploaded_file_name = st.session_state.uploaded_file_name
            
            # Get current status
            status = get_job_status(job_id)
            
            if status:
                job_status = status["status"]
                progress = status.get("progress", 0)
                blocks_done = status.get("blocks_done", 0)
                blocks_total = status.get("blocks_total", 0)
                error = status.get("error")
                
                # Show status
                if job_status == "pending":
                    st.markdown("""
                    <div class="status-box" style="background-color: #e3f2fd;">
                        <h3>⏳ Preparing translation...</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(0)
                    time.sleep(1.5)
                    st.rerun()
                
                elif job_status == "running":
                    st.markdown(f"""
                    <div class="status-box" style="background-color: #fff3e0;">
                        <h3>🔄 Translating...</h3>
                        <p>Processing {blocks_done} of {blocks_total} segments</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(progress / 100)
                    time.sleep(1.5)
                    st.rerun()
                
                elif job_status == "done":
                    st.markdown("""
                    <div class="status-box" style="background-color: #e8f5e9;">
                        <h3>✅ Translation Complete!</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(100)
                    
                    # Determine output filename
                    filename = Path(uploaded_file_name).stem
                    ext = Path(uploaded_file_name).suffix.lower()
                    
                    # For audio files, check if TTS is available (output might be audio or SRT)
                    if ext in [".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac"]:
                        # Try to get audio file first, fallback to SRT
                        output_ext = ext  # Try original extension first
                        output_filename = f"{filename}_fr{output_ext}"
                        file_content = download_file(job_id, output_filename)
                        
                        # If audio download fails, try SRT
                        if not file_content:
                            output_ext = ".srt"
                            output_filename = f"{filename}_fr{output_ext}"
                            file_content = download_file(job_id, output_filename)
                    else:
                        output_ext = ext
                        output_filename = f"{filename}_fr{output_ext}"
                        file_content = download_file(job_id, output_filename)
                    
                    if file_content:
                        st.download_button(
                            label="📥 Download Translated File",
                            data=file_content,
                            file_name=output_filename,
                            mime="application/octet-stream",
                            type="primary",
                            use_container_width=True
                        )
                    
                    st.markdown("---")
                    if st.button("🔄 Translate Another File", use_container_width=True):
                        st.session_state.job_id = None
                        st.session_state.uploaded_file_name = None
                        st.rerun()
                
                elif job_status == "failed":
                    st.markdown(f"""
                    <div class="status-box" style="background-color: #ffebee;">
                        <h3>❌ Translation Failed</h3>
                        <p>{error or "Unknown error occurred"}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🔄 Try Again", use_container_width=True):
                        st.session_state.job_id = None
                        st.session_state.uploaded_file_name = None
                        st.rerun()
            else:
                st.error("Unable to get translation status. Please try again.")
                if st.button("🔄 Start Over", use_container_width=True):
                    st.session_state.job_id = None
                    st.session_state.uploaded_file_name = None
                    st.rerun()
    
    # Footer with minimal info
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; font-size: 0.9rem; padding: 1rem;'>
        <p>🔒 All processing is done locally on your machine</p>
        <p>Supports: PDF • DOCX • PPTX • Audio/Video files</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
