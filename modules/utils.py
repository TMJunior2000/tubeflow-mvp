import streamlit as st
import time
import re

# Configurazione Rate Limit (Anti-Abuso)
MAX_REQUESTS_PER_SESSION = 5
TIME_WINDOW = 3600

def check_rate_limit():
    """Controlla che l'utente non stia spammando richieste."""
    if 'req_count' not in st.session_state:
        st.session_state['req_count'] = 0
        st.session_state['start_time'] = time.time()
    
    # Reset ogni ora
    if time.time() - st.session_state['start_time'] > TIME_WINDOW:
        st.session_state['req_count'] = 0
        st.session_state['start_time'] = time.time()
        
    if st.session_state['req_count'] >= MAX_REQUESTS_PER_SESSION:
        st.error("⏳ Hai raggiunto il limite di 5 script per ora. Torna più tardi! (Serve per mantenere il servizio gratuito per tutti).")
        st.stop()
    
    st.session_state['req_count'] += 1

def footer_legal():
    """Il disclaimer legale per l'Italia 2026."""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
            <strong>⚖️ Note Legali & Trasparenza AI</strong><br>
            Questo tool è un orchestratore automatizzato. I testi sono generati da IA (Google Gemini) e potrebbero contenere inesattezze.<br>
            Gli asset video sono forniti tramite API di Pexels. L'utente è tenuto a verificare la licenza (CC0/Pexels License) prima dell'uso commerciale.<br>
            <strong>Privacy:</strong> Nessun dato viene salvato sui nostri server. La sessione è effimera.
        </div>
        """, unsafe_allow_html=True
    )