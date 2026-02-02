import streamlit as st

# La funzione check_rate_limit è stata rimossa per permettere uso illimitato.

def footer_legal():
    """Il disclaimer legale per l'Italia 2026."""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
            <strong>⚖️ Note Legali & Trasparenza AI</strong><br>
            Questo tool è un orchestratore automatizzato. I testi sono generati da IA e potrebbero contenere inesattezze.<br>
            Gli asset video sono forniti tramite API di Pexels/Pixabay. L'utente è tenuto a verificare la licenza prima dell'uso commerciale.<br>
            <strong>Privacy:</strong> Nessun dato viene salvato sui nostri server. La sessione è effimera.
        </div>
        """, unsafe_allow_html=True
    )