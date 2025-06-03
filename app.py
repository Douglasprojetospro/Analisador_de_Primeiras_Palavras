import streamlit as st
import pandas as pd
import re
from collections import Counter
from io import BytesIO
import base64

# Configuração da página com CSS customizado
def inject_custom_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Palavras para ignorar (inicial)
DEFAULT_STOPWORDS = {
    'de', 'para', 'com', 'sem', 'em', 'por', 'que', 'os', 'as', 'um', 'uma',
    'ao', 'aos', 'do', 'da', 'dos', 'das', 'no', 'na', 'nos', 'nas', 'pelo',
    'pela', 'pelos', 'pelas', 'este', 'esta', 'estes', 'estas', 'esse',
    'essa', 'esses', 'essas', 'aquele', 'aquela', 'aqueles', 'aquelas',
    'ou', 'e', 'mas', 'porém', 'entretanto', 'contudo', 'quando', 'enquanto',
    'como', 'porque', 'pois', 'assim', 'então', 'logo', 'portanto', 'desse',
    'dessa', 'destes', 'destas', 'deste', 'isso', 'isto', 'aquilo'
}

def extract_first_word(text):
    if pd.isna(text):
        return None
    text = str(text).strip()
    if not text:
        return None
    first_word = re.sub(r'^[^a-zA-Z0-9áéíóúÁÉÍÓÚãõâêîôûàèìòùç]+', '', text).split(' ')[0]
    return first_word if first_word else None

def analyze_first_words(df, stopwords):
    first_words = []
    for text in df["Descrição"]:
        word = extract_first_word(text)
        if word and word.lower() not in stopwords and len(word) >= 3:
            first_words.append(word.lower())
    return Counter(first_words).most_common()

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    return output.getvalue()

def main():
    inject_custom_css()
    
    st.markdown("""
    <div class="header">
        <h1>🔍 Analisador de Primeiras Palavras</h1>
        <p class="subtitle">Identifique os termos mais usados no início das descrições</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🔧 Configurações</div>', unsafe_allow_html=True)
        
        # Adicionar palavras para ignorar
        st.markdown('<div class="sidebar-section">Palavras para Ignorar</div>', unsafe_allow_html=True)
        new_stopword = st.text_input("Adicionar nova palavra:", key="new_stopword")
        
        if st.button("Adicionar", key="add_stopword"):
            if 'custom_stopwords' not in st.session_state:
                st.session_state.custom_stopwords = set()
            if new_stopword:
                st.session_state.custom_stopwords.add(new_stopword.lower())
                st.rerun()
        
        # Lista de palavras ignoradas
        st.markdown('<div class="sidebar-section">Lista de Palavras Ignoradas</div>', unsafe_allow_html=True)
        all_stopwords = DEFAULT_STOPWORDS.copy()
        if 'custom_stopwords' in st.session_state:
            all_stopwords.update(st.session_state.custom_stopwords)
        
        st.markdown(f'<div class="stopwords-list">{" • ".join(sorted(all_stopwords))}</div>', unsafe_allow_html=True)
        
        if st.button("Limpar palavras adicionadas", key="clear_stopwords"):
            if 'custom_stopwords' in st.session_state:
                del st.session_state.custom_stopwords
            st.rerun()

    # Seção principal
    st.markdown("""
    <div class="section">
        <h2>📤 Baixar Modelo</h2>
        <p class="instructions">Preencha o modelo com suas descrições e faça upload para análise</p>
    </div>
    """, unsafe_allow_html=True)
    
    empty_df = pd.DataFrame({"ID": [], "Descrição": []})
    st.download_button(
        "⬇️ Baixar Modelo Vazio",
        data=to_excel(empty_df),
        file_name="modelo_descricoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Seção de análise
    st.markdown("""
    <div class="section">
        <h2>📊 Analisar Arquivo</h2>
        <p class="instructions">Faça upload do arquivo com as descrições para análise</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Selecione o arquivo (Excel ou CSV)", type=["xlsx", "csv"])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            if 'Descrição' not in df.columns:
                st.error("❌ O arquivo deve conter a coluna 'Descrição'")
                st.stop()
            
            st.success(f"✅ Arquivo carregado com sucesso! ({len(df)} registros)")
            
            current_stopwords = DEFAULT_STOPWORDS.copy()
            if 'custom_stopwords' in st.session_state:
                current_stopwords.update(st.session_state.custom_stopwords)
            
            with st.spinner("🔍 Analisando primeiras palavras..."):
                first_words = analyze_first_words(df, current_stopwords)
            
            if not first_words:
                st.warning("⚠️ Nenhuma palavra válida encontrada")
                st.stop()
            
            df_result = pd.DataFrame(first_words, columns=["Primeira Palavra", "Frequência"])
            
            st.markdown('<div class="results-header">📈 Resultados da Análise</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 3])
            
            with col1:
                st.markdown('<div class="table-container">', unsafe_allow_html=True)
                st.dataframe(df_result.head(50), height=600)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.bar_chart(df_result.set_index("Primeira Palavra").head(20), height=500)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.download_button(
                "📥 Exportar Resultados",
                data=to_excel(df_result),
                file_name="resultado_analise.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
