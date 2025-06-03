# app.py
import streamlit as st
import pandas as pd
import re
from collections import Counter
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Analisador de Primeiras Palavras",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    """Extrai a primeira palavra do texto"""
    if pd.isna(text):
        return None
    
    text = str(text).strip()
    if not text:
        return None
    
    # Remove caracteres especiais no início e pega a primeira palavra
    first_word = re.sub(r'^[^a-zA-Z0-9áéíóúÁÉÍÓÚãõâêîôûàèìòùç]+', '', text).split(' ')[0]
    return first_word if first_word else None

def analyze_first_words(df, stopwords):
    """Analisa as primeiras palavras ignorando as stopwords"""
    first_words = []
    for text in df["Descrição"]:
        word = extract_first_word(text)
        if word and word.lower() not in stopwords and len(word) >= 3:
            first_words.append(word.lower())  # Padroniza para minúsculas
    
    return Counter(first_words).most_common()

def to_excel(df):
    """Converte DataFrame para Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    processed_data = output.getvalue()
    return processed_data

def main():
    st.title("🔍 Analisador de Primeiras Palavras")
    
    # Painel de configuração na sidebar
    with st.sidebar:
        st.header("🔧 Configurações")
        
        # Adicionar palavras para ignorar
        st.subheader("Palavras para Ignorar")
        new_stopword = st.text_input("Adicionar nova palavra para ignorar:", 
                                    placeholder="Digite uma palavra e clique em Adicionar")
        
        if st.button("Adicionar") and new_stopword:
            if 'custom_stopwords' not in st.session_state:
                st.session_state.custom_stopwords = set()
            st.session_state.custom_stopwords.add(new_stopword.lower())
            st.rerun()
        
        # Lista de palavras ignoradas
        st.subheader("Lista de Palavras Ignoradas")
        all_stopwords = DEFAULT_STOPWORDS.copy()
        if 'custom_stopwords' in st.session_state:
            all_stopwords.update(st.session_state.custom_stopwords)
        
        st.write(sorted(all_stopwords))
        
        # Botão para limpar palavras personalizadas
        if st.button("Limpar palavras adicionadas"):
            if 'custom_stopwords' in st.session_state:
                del st.session_state.custom_stopwords
            st.rerun()
    
    # Seção principal
    st.header("📤 Baixar Modelo")
    st.markdown("""
    **Instruções:**
    1. Baixe o modelo abaixo
    2. Preencha com suas descrições na coluna 'Descrição'
    3. Faça upload do arquivo preenchido para análise
    """)
    
    empty_df = pd.DataFrame({"ID": [], "Descrição": []})
    
    st.download_button(
        "⬇️ Baixar Modelo Vazio (Excel)",
        data=to_excel(empty_df),
        file_name="modelo_descricoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.header("📊 Analisar Arquivo")
    uploaded_file = st.file_uploader(
        "Carregue seu arquivo (Excel ou CSV)", 
        type=["xlsx", "csv"],
        help="O arquivo deve conter uma coluna chamada 'Descrição'"
    )
    
    if uploaded_file:
        try:
            # Lê o arquivo
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Verifica se tem a coluna necessária
            if 'Descrição' not in df.columns:
                st.error("Erro: O arquivo deve conter a coluna 'Descrição'")
                st.stop()
            
            st.success(f"✅ Arquivo carregado com sucesso! ({len(df)} registros)")
            
            # Obter lista completa de stopwords
            current_stopwords = DEFAULT_STOPWORDS.copy()
            if 'custom_stopwords' in st.session_state:
                current_stopwords.update(st.session_state.custom_stopwords)
            
            # Análise
            with st.spinner("Analisando primeiras palavras..."):
                first_words = analyze_first_words(df, current_stopwords)
            
            if not first_words:
                st.warning("Nenhuma palavra válida encontrada no início das descrições")
                st.stop()
            
            # Mostra resultados
            df_result = pd.DataFrame(first_words, columns=["Primeira Palavra", "Frequência"])
            
            st.subheader("📈 Resultados da Análise")
            col1, col2 = st.columns([2, 3])
            
            with col1:
                st.dataframe(df_result.head(50), height=600)
            
            with col2:
                st.bar_chart(df_result.set_index("Primeira Palavra").head(20))
            
            # Botão de download
            st.download_button(
                "📥 Exportar Resultados (Excel)",
                data=to_excel(df_result),
                file_name="resultado_analise.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Clique para baixar os resultados completos em formato Excel"
            )
        
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")
            st.stop()

if __name__ == "__main__":
    main()
