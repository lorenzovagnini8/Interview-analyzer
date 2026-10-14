import os
import tempfile
import streamlit as st
import pandas as pd
import plotly.express as px

from analyzer import analizza_intervista
from database import salva_analisi, carica_storico_analisi

st.set_page_config(
    page_title="ScoutRadar - Analisi Interviste",
    page_icon="🎙️",
    layout="wide"
)

st.title("🎙️ ScoutRadar — Behavioral & Interview Analyzer")
st.caption("Modulo di analisi psicologica, verbale, paraverbale e non verbale tramite Google Gemini API")

# Recupero configurazioni dai secrets o ambiente
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))

tab1, tab2 = st.tabs(["📤 Nuova Analisi", "📊 Storico & Report"])

with tab1:
    st.header("Carica Intervista")
    
    uploaded_file = st.file_uploader(
        "Seleziona un file multimediale (MP3, WAV, MP4, MOV)", 
        type=["mp3", "wav", "mp4", "mov", "m4a"]
    )
    
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        mime_type = f"video/{file_ext}" if file_ext in ["mp4", "mov"] else f"audio/{file_ext}"
        
        st.write(f"📁 **File caricato:** {uploaded_file.name} ({mime_type})")
        
        if st.button("🚀 Avvia Analisi Multimodale", type="primary"):
            if not GEMINI_API_KEY or not SUPABASE_URL:
                st.error("🔑 Verificare che GEMINI_API_KEY e SUPABASE_URL siano configurati correttamente nei secrets.")
            else:
                with st.spinner("Elaborazione in corso con Gemini... (potrebbe richiedere 15-30 secondi)"):
                    # Salvataggio temporaneo del file su disco locale per l'upload via SDK
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = tmp_file.name
                    
                    try:
                        # 1. Chiamata ad Analyzer
                        result = analizza_intervista(tmp_path, mime_type, GEMINI_API_KEY)
                        
                        # 2. Salvataggio su Supabase
                        salva_analisi(result, "video" if "video" in mime_type else "audio", SUPABASE_URL, SUPABASE_KEY)
                        st.success("✅ Analisi completata e salvata nel database!")
                        
                        # 3. Output Dettagliato
                        punteggi = result["punteggi"]
                        profilo = result["profilo_psicologico"]
                        analisi = result["analisi"]
                        
                        st.markdown("---")
                        col_score, col_chart = st.columns([1, 1])
                        
                        with col_score:
                            st.subheader(f"👤 {result.get('nome_intervistato')} ({result.get('ruolo')})")
                            st.metric("Score Qualità Complessivo", f"{punteggi['score_qualita_intervista']} / 10")
                            st.write(f"**Livello di Stress Percepito:** `{profilo['livello_stress_percepito']}`")
                            st.write("**Tratti di personalità:** " + ", ".join([f"`{t}`" for t in profilo.get("tratti_chiave", [])]))
                            st.info(f"**Profilo Psicologico:**\n{profilo['descrizione_sintetica']}")
                        
                        with col_chart:
                            # Grafico Radar dei voti
                            categories = ['Verbale', 'Paraverbale', 'Non Verbale']
                            values = [
                                punteggi['punteggio_verbale'], 
                                punteggi['punteggio_paraverbale'], 
                                punteggi['punteggio_non_verbale']
                            ]
                            df_radar = pd.DataFrame(dict(r=values, theta=categories))
                            fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, range_r=[0, 10])
                            fig.update_traces(fill='toself')
                            st.plotly_chart(fig, use_container_width=True)
                            
                        st.markdown("### 🔍 Dettaglio Canali Comunicativi")
                        st.accordion_state = True
                        with st.expander("💬 Comunicazione Verbale", expanded=True):
                            st.write(analisi["verbale"])
                        with st.expander("🎙️ Comunicazione Paraverbale", expanded=True):
                            st.write(analisi["paraverbale"])
                        with st.expander("👁️ Comunicazione Non Verbale", expanded=True):
                            st.write(analisi["non_verbale"])

                    except Exception as e:
                        st.error(f"Errore durante l'analisi: {str(e)}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

with tab2:
    st.header("📋 Storico Analisi Interviste")
    if SUPABASE_URL and SUPABASE_KEY:
        data = carica_storico_analisi(SUPABASE_URL, SUPABASE_KEY)
        if data:
            df = pd.DataFrame(data)
            st.dataframe(
                df[[
                    'created_at', 'speaker_name', 'speaker_role', 'score_qualita_totale', 
                    'livello_stress', 'tratti_chiave'
                ]],
                use_container_width=True
            )
        else:
            st.info("Nessuna analisi presente nel database.")
