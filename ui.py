"""Streamlit UI for translation pipeline - Modern Professional Design."""
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
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS matching the reference design
    st.markdown("""
    <style>
    /* Remove default Streamlit styling */
    .stApp {
        background: linear-gradient(180deg, #4A90E2 0%, #87CEEB 50%, #E0F2FE 100%);
        background-attachment: fixed;
    }
    
    /* Geometric pattern overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(30deg, rgba(255,255,255,0.05) 12%, transparent 12.5%, transparent 87%, rgba(255,255,255,0.05) 87.5%, rgba(255,255,255,0.05)),
            linear-gradient(150deg, rgba(255,255,255,0.05) 12%, transparent 12.5%, transparent 87%, rgba(255,255,255,0.05) 87.5%, rgba(255,255,255,0.05)),
            linear-gradient(30deg, rgba(255,255,255,0.05) 12%, transparent 12.5%, transparent 87%, rgba(255,255,255,0.05) 87.5%, rgba(255,255,255,0.05)),
            linear-gradient(150deg, rgba(255,255,255,0.05) 12%, transparent 12.5%, transparent 87%, rgba(255,255,255,0.05) 87.5%, rgba(255,255,255,0.05));
        background-size: 80px 140px;
        background-position: 0 0, 0 0, 40px 70px, 40px 70px;
        pointer-events: none;
        z-index: 0;
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    
    /* Header styling */
    .header-container {
        text-align: center;
        margin-bottom: 3rem;
        position: relative;
        z-index: 1;
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #4A5568;
        font-weight: 400;
        margin-top: 0.5rem;
    }
    
    /* White card container */
    .upload-card {
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        margin: 2rem auto;
        position: relative;
        z-index: 1;
    }
    
    /* Language selector styling */
    .lang-selector {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 2px solid #E2E8F0;
    }
    
    /* File upload area */
    .upload-area {
        min-height: 200px;
        border: 2px dashed #CBD5E0;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: #F7FAFC;
        transition: all 0.3s ease;
        margin-bottom: 1.5rem;
    }
    
    .upload-area:hover {
        border-color: #4A90E2;
        background: #EDF2F7;
    }
    
    /* File info display */
    .file-info-display {
        background: #F7FAFC;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #4A90E2;
    }
    
    .file-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2D3748;
        margin-bottom: 0.25rem;
    }
    
    .file-size {
        font-size: 0.9rem;
        color: #718096;
    }
    
    /* Primary button styling */
    .stButton>button {
        background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #357ABD 0%, #2A5F8F 100%);
        box-shadow: 0 6px 16px rgba(74, 144, 226, 0.4);
        transform: translateY(-2px);
    }
    
    /* Status box styling */
    .status-box {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .status-pending {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
    }
    
    .status-running {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
    }
    
    .status-success {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
    }
    
    .status-error {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
    }
    
    .status-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #2D3748;
    }
    
    .status-text {
        font-size: 1rem;
        color: #4A5568;
        margin-top: 0.5rem;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #4A90E2 0%, #357ABD 100%);
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Download button */
    .download-section {
        margin-top: 2rem;
        padding-top: 2rem;
        border-top: 2px solid #E2E8F0;
    }
    
    /* Footer */
    .footer-info {
        text-align: center;
        color: rgba(255,255,255,0.9);
        font-size: 0.9rem;
        margin-top: 3rem;
        position: relative;
        z-index: 1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header section
    st.markdown("""
    <div class="header-container">
        <h1 class="main-title">Traducteur IA</h1>
        <p class="subtitle">Traduit vos documents et fichiers audio de l'anglais vers le français avec l'intelligence artificielle</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ **Le serveur API n'est pas en cours d'exécution**")
        st.info("Veuillez démarrer le serveur API : `python start_api.py`")
        st.stop()
    
    # Main upload card
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    
    # Language selector (visual only, since we only do EN->FR)
    st.markdown("""
    <div class="lang-selector">
        <div style="flex: 1; text-align: center;">
            <div style="font-size: 0.9rem; color: #718096; margin-bottom: 0.5rem;">De</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #2D3748;">Anglais</div>
        </div>
        <div style="font-size: 1.5rem; color: #4A90E2;">⇄</div>
        <div style="flex: 1; text-align: center;">
            <div style="font-size: 0.9rem; color: #718096; margin-bottom: 0.5rem;">Vers</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #2D3748;">Français</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "job_id" not in st.session_state:
        st.session_state.job_id = None
    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None
    
    # File upload section
    if st.session_state.job_id is None:
        uploaded_file = st.file_uploader(
            "Télécharger un fichier",
            type=ALLOWED_TYPES,
            help="Formats supportés : PDF, DOCX, PPTX, MP3, MP4, WAV et plus",
            label_visibility="visible"
        )
        
        if uploaded_file is not None:
            st.markdown(f"""
            <div class="file-info-display">
                <div class="file-name">📄 {uploaded_file.name}</div>
                <div class="file-size">Taille : {format_file_size(uploaded_file.size)}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("TRADUIRE →", type="primary", use_container_width=True):
                with st.spinner("Téléchargement en cours..."):
                    result = upload_file(uploaded_file)
                
                if result:
                    st.session_state.job_id = result["job_id"]
                    st.session_state.uploaded_file_name = uploaded_file.name
                    st.rerun()
        else:
            st.markdown("""
            <div style="text-align: center; color: #718096; padding: 2rem 0;">
                <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">Glissez-déposez votre fichier ici</p>
                <p style="font-size: 0.9rem;">ou cliquez pour parcourir</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Progress and download section
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
                <div class="status-box status-pending">
                    <div class="status-title">⏳ Préparation de la traduction...</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(0)
                time.sleep(1.5)
                st.rerun()
            
            elif job_status == "running":
                st.markdown(f"""
                <div class="status-box status-running">
                    <div class="status-title">🔄 Traduction en cours...</div>
                    <div class="status-text">Traitement de {blocks_done} sur {blocks_total} segments</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(progress / 100)
                time.sleep(1.5)
                st.rerun()
            
            elif job_status == "done":
                st.markdown("""
                <div class="status-box status-success">
                    <div class="status-title">✅ Traduction terminée !</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(100)
                
                # Determine output filename
                filename = Path(uploaded_file_name).stem
                ext = Path(uploaded_file_name).suffix.lower()
                
                # For audio files, check if TTS is available (output might be audio or SRT)
                if ext in [".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac"]:
                    # Try to get audio file first, fallback to SRT
                    output_ext = ext
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
                    st.markdown('<div class="download-section">', unsafe_allow_html=True)
                    st.download_button(
                        label="📥 Télécharger le fichier traduit",
                        data=file_content,
                        file_name=output_filename,
                        mime="application/octet-stream",
                        type="primary",
                        use_container_width=True
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if st.button("🔄 Traduire un autre fichier", use_container_width=True):
                    st.session_state.job_id = None
                    st.session_state.uploaded_file_name = None
                    st.rerun()
            
            elif job_status == "failed":
                st.markdown(f"""
                <div class="status-box status-error">
                    <div class="status-title">❌ Échec de la traduction</div>
                    <div class="status-text">{error or "Une erreur inconnue s'est produite"}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔄 Réessayer", use_container_width=True):
                    st.session_state.job_id = None
                    st.session_state.uploaded_file_name = None
                    st.rerun()
        else:
            st.error("Impossible d'obtenir le statut de la traduction. Veuillez réessayer.")
            if st.button("🔄 Recommencer", use_container_width=True):
                st.session_state.job_id = None
                st.session_state.uploaded_file_name = None
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close upload-card
    
    # Footer
    st.markdown("""
    <div class="footer-info">
        <p>🔒 Tout le traitement est effectué localement sur votre machine</p>
        <p>Formats supportés : PDF • DOCX • PPTX • Fichiers audio/vidéo</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
