"""Streamlit UI for translation pipeline."""
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
        st.error(f"Failed to get status: {e}")
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


def main():
    st.set_page_config(
        page_title="Document Translation Pipeline",
        page_icon="🌐",
        layout="wide"
    )
    
    st.title("🌐 Document Translation Pipeline")
    st.markdown("**English → French Translation (On-Premise)**")
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ API server is not running. Please start the API server first:")
        st.code("python api/app.py", language="bash")
        st.stop()
    
    st.success("✅ API server is running")
    
    # File uploader
    st.header("Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a file to translate",
        type=ALLOWED_TYPES,
        help="Supported formats: PDF, DOCX, PPTX, and audio files (MP3, MP4, WAV, etc.)"
    )
    
    if uploaded_file is not None:
        st.info(f"📄 Selected file: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")
        
        if st.button("🚀 Translate →", type="primary"):
            # Upload file
            with st.spinner("Uploading file..."):
                result = upload_file(uploaded_file)
            
            if result:
                job_id = result["job_id"]
                st.success(f"✅ Translation job started! Job ID: `{job_id}`")
                
                # Store job_id in session state
                st.session_state.job_id = job_id
                st.session_state.job_started = True
                st.rerun()
    
    # Progress tracking
    if "job_id" in st.session_state and st.session_state.get("job_started"):
        job_id = st.session_state.job_id
        
        st.header("Translation Progress")
        
        # Create placeholder for status
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        download_placeholder = st.empty()
        
        # Poll for status
        max_polls = 600  # Maximum 10 minutes (600 * 1.5s)
        poll_count = 0
        
        while poll_count < max_polls:
            status = get_job_status(job_id)
            
            if not status:
                st.error("Failed to get job status")
                break
            
            job_status = status["status"]
            progress = status["progress"]
            blocks_done = status["blocks_done"]
            blocks_total = status["blocks_total"]
            error = status.get("error")
            
            # Display status
            if job_status == "pending":
                status_placeholder.info("⏳ Job is queued...")
            elif job_status == "running":
                status_placeholder.info(f"🔄 Translating... ({blocks_done}/{blocks_total} blocks)")
            elif job_status == "done":
                status_placeholder.success("✅ Translation complete!")
                break
            elif job_status == "failed":
                status_placeholder.error(f"❌ Translation failed: {error}")
                break
            
            # Display progress bar
            progress_placeholder.progress(progress / 100)
            st.caption(f"Progress: {progress}% ({blocks_done}/{blocks_total} blocks)")
            
            # Wait before next poll
            time.sleep(1.5)
            poll_count += 1
        
        # Check final status
        final_status = get_job_status(job_id)
        if final_status and final_status["status"] == "done":
            # Show download button
            filename = Path(uploaded_file.name).stem
            ext = Path(uploaded_file.name).suffix
            
            # Determine output extension
            if ext.lower() in [".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac"]:
                output_ext = ".srt"
            else:
                output_ext = ext
            
            output_filename = f"{filename}_fr{output_ext}"
            
            download_placeholder.markdown("---")
            download_placeholder.header("Download Translated File")
            
            if st.button("📥 Download Translated File", type="primary"):
                file_content = download_file(job_id, output_filename)
                if file_content:
                    st.download_button(
                        label="⬇️ Click to download",
                        data=file_content,
                        file_name=output_filename,
                        mime="application/octet-stream"
                    )
            
            # Reset button
            if st.button("🔄 Translate Another File"):
                del st.session_state.job_id
                del st.session_state.job_started
                st.rerun()
    
    # Sidebar info
    with st.sidebar:
        st.header("ℹ️ Information")
        st.markdown("""
        **Supported Formats:**
        - PDF documents
        - Word documents (.docx, .doc)
        - PowerPoint presentations (.pptx, .ppt)
        - Audio/Video files (.mp3, .mp4, .wav, .m4a, .ogg, .flac)
        
        **Output:**
        - Documents: Translated version with original formatting
        - Audio: Translated SRT subtitle file
        
        **Note:** All processing is done locally. No data leaves your network.
        """)


if __name__ == "__main__":
    main()

