import os
import streamlit as st
import pandas as pd
import re
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path

# Configuração de caminhos
def get_data_path():
    """Retorna o caminho para a pasta de dados"""
    data_path = Path(__file__).parent / "data"
    data_path.mkdir(exist_ok=True)
    return data_path

# Verifica se está rodando no Render
def is_render():
    return "RENDER" in os.environ

# Configuração da página
st.set_page_config(
    page_title="Analisador Avançado de Descrições",
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

def create_config_template():
    """Cria um template para configuração de atributos"""
    template = pd.DataFrame(columns=[
        "Atributo", 
        "Variações", 
        "Padrões de reconhecimento"
    ])
    
    examples = [
        {
            "Atributo": "Voltagem",
            "Variações": "110v",
            "Padrões de reconhecimento": "110v,110 v,110volts,110 volts,110-volts,110-volt,110 volt"
        },
        {
            "Atributo": "Voltagem",
            "Variações": "220v",
            "Padrões de reconhecimento": "220v,220 v,220volts,220 volts,220-volts,220-volt,220 volt"
        }
    ]
    
    return pd.concat([template, pd.DataFrame(examples)], ignore_index=True)

def create_category_template():
    """Cria um template para categorização de palavras"""
    template = pd.DataFrame(columns=["Palavra", "Categoria"])
    
    examples = [
        {"Palavra": "Maçã", "Categoria": "Alimentos"},
        {"Palavra": "Arroz", "Categoria": "Alimentos"},
        {"Palavra": "Parafuso", "Categoria": "Ferramentas"}
    ]
    
    return pd.concat([template, pd.DataFrame(examples)], ignore_index=True)

def create_ignore_words_template():
    """Cria um template para palavras/frases para ignorar"""
    template = pd.DataFrame({
        "Palavras/Frases para ignorar": [
            "cota",
            "ampla concorrência",
            "item",
            "produto",
            "modelo",
            "material permanente"
        ]
    })
    return template

def load_config(file):
    """Carrega configurações de um arquivo Excel"""
    try:
        config_df = pd.read_excel(file)
        config_dict = defaultdict(list)
        
        for _, row in config_df.iterrows():
            if pd.notna(row["Atributo"]) and pd.notna(row["Variações"]) and pd.notna(row["Padrões de reconhecimento"]):
                patterns = [p.strip().lower() for p in str(row["Padrões de reconhecimento"]).split(",")]
                config_dict[row["Atributo"]].append({
                    "variation": row["Variações"],
                    "patterns": patterns
                })
        
        return dict(config_dict)
    except Exception as e:
        st.error(f"Erro ao carregar configuração: {str(e)}")
        return None

def load_categories(file):
    """Carrega categorias de palavras de um arquivo Excel"""
    try:
        categories_df = pd.read_excel(file)
        return dict(zip(
            categories_df["Palavra"].str.lower(), 
            categories_df["Categoria"]
        ))
    except Exception as e:
        st.error(f"Erro ao carregar categorias: {str(e)}")
        return None

def load_ignore_words(file):
    """Carrega palavras/frases para ignorar de um arquivo Excel"""
    try:
        ignore_df = pd.read_excel(file)
        if "Palavras/Frases para ignorar" in ignore_df.columns:
            phrases = [str(phrase).strip().lower() for phrase in ignore_df["Palavras/Frases para ignorar"] if str(phrase).strip()]
            return set(phrases)
        return set()
    except Exception as e:
        st.error(f"Erro ao carregar palavras/frases para ignorar: {str(e)}")
        return None

def find_matches(text, config):
    """Encontra correspondências no texto com base na configuração"""
    if not text or not isinstance(text, str) or not config:
        return {}
    
    text_lower = text.lower()
    matches = defaultdict(list)
    
    for attribute, variations in config.items():
        for variation_data in variations:
            for pattern in variation_data["patterns"]:
                if re.search(rf'\b{re.escape(pattern)}\b', text_lower, re.IGNORECASE):
                    matches[attribute].append(variation_data["variation"])
                    break
    
    return {k: "/".join(sorted(set(v))) for k, v in matches.items()}

def extract_first_word(text, stopwords=None, ignore_phrases=None):
    """Extrai a primeira palavra válida do texto, ignorando frases específicas"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    
    text = text.strip()
    if not text:
        return None
    
    if ignore_phrases:
        sorted_phrases = sorted(ignore_phrases, key=len, reverse=True)
        for phrase in sorted_phrases:
            if text.lower().startswith(phrase.lower()):
                remaining_text = text[len(phrase):].strip()
                if remaining_text:
                    return extract_first_word(remaining_text, stopwords, ignore_phrases)
                return None
    
    first_word = re.sub(r'^[^a-zA-ZÀ-ÿ0-9]+', '', text).split()[0] if text else None
    
    if stopwords and first_word and first_word.lower() in stopwords:
        return None
    if first_word and len(first_word) < 3:
        return None
    
    return first_word if first_word else None

def to_excel(df):
    """Converte DataFrame para Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def main():
    st.title("🔍 Analisador Avançado de Descrições")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Attribute configuration
        st.subheader("Configuração de Atributos")
        st.download_button(
            "📥 Baixar Modelo de Atributos",
            data=to_excel(create_config_template()),
            file_name="modelo_atributos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        uploaded_config = st.file_uploader(
            "Carregar configuração de atributos",
            type=["xlsx"],
            key="config_uploader"
        )
        
        # Categories configuration
        st.subheader("Configuração de Categorias")
        st.download_button(
            "📥 Baixar Modelo de Categorias",
            data=to_excel(create_category_template()),
            file_name="modelo_categorias.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        uploaded_categories = st.file_uploader(
            "Carregar configuração de categorias",
            type=["xlsx"],
            key="categories_uploader"
        )
        
        # Ignore words/phrases
        st.subheader("Palavras/Frases para Ignorar")
        st.download_button(
            "📥 Baixar Modelo de Palavras/Frases",
            data=to_excel(create_ignore_words_template()),
            file_name="modelo_palavras_frases_ignorar.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        uploaded_ignore_words = st.file_uploader(
            "Carregar palavras/frases para ignorar",
            type=["xlsx"],
            key="ignore_words_uploader"
        )
        
        # Manual configuration
        st.subheader("Adição Manual")
        new_stopword = st.text_input("Digite uma palavra ou frase para ignorar:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Adicionar") and new_stopword:
                if 'custom_stopwords' not in st.session_state:
                    st.session_state.custom_stopwords = set()
                st.session_state.custom_stopwords.add(new_stopword.strip().lower())
                st.success(f"'{new_stopword}' adicionado com sucesso!")
        
        with col2:
            if st.button("Limpar adições manuais"):
                if 'custom_stopwords' in st.session_state:
                    del st.session_state.custom_stopwords
                    st.success("Itens removidos!")
        
        if 'custom_stopwords' in st.session_state and st.session_state.custom_stopwords:
            st.markdown("**Itens ignorados atualmente:**")
            for word in sorted(st.session_state.custom_stopwords):
                st.markdown(f"- `{word}`")
    
    # Load configurations
    config = load_config(uploaded_config) if uploaded_config else None
    categories = load_categories(uploaded_categories) if uploaded_categories else None
    ignore_phrases = load_ignore_words(uploaded_ignore_words) if uploaded_ignore_words else set()
    
    if 'custom_stopwords' in st.session_state:
        ignore_phrases.update(st.session_state.custom_stopwords)
    
    # Main section
    st.header("📤 Baixar Modelo de Dados")
    empty_df = pd.DataFrame({"ID": [], "Descrição": []})
    
    st.download_button(
        "⬇️ Baixar Modelo Vazio",
        data=to_excel(empty_df),
        file_name="modelo_descricoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.header("📊 Analisar Arquivo")
    uploaded_file = st.file_uploader(
        "Carregue seu arquivo de descrições", 
        type=["xlsx", "csv"]
    )
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            if 'Descrição' not in df.columns:
                st.error("Erro: O arquivo deve conter a coluna 'Descrição'")
            else:
                st.success(f"✅ Arquivo carregado com sucesso! ({len(df)} registros)")
                
                current_stopwords = DEFAULT_STOPWORDS.copy()
                
                with st.spinner("Processando descrições..."):
                    df['Primeira Palavra'] = df['Descrição'].apply(
                        lambda x: extract_first_word(x, current_stopwords, ignore_phrases)
                    )
                    
                    if categories:
                        df['Categoria'] = df['Primeira Palavra'].apply(
                            lambda x: categories.get(str(x).lower()) if pd.notna(x) else None
                        )
                    
                    if config:
                        matches = df['Descrição'].apply(
                            lambda x: find_matches(x, config)
                        )
                        for attribute in config.keys():
                            df[attribute] = matches.apply(
                                lambda x: x.get(attribute, None)
                            )
                
                st.subheader("📋 Dados Processados")
                st.dataframe(df)
                
                st.subheader("📈 Estatísticas")
                
                if not df['Primeira Palavra'].empty:
                    st.markdown("### Primeiras Palavras")
                    word_counts = Counter(df['Primeira Palavra'].dropna()).most_common()
                    df_stats_words = pd.DataFrame(word_counts, columns=["Primeira Palavra", "Frequência"])
                    
                    if categories:
                        df_stats_words['Categoria'] = df_stats_words['Primeira Palavra'].apply(
                            lambda x: categories.get(str(x).lower()) if pd.notna(x) else None
                        )
                    
                    col1, col2 = st.columns([2, 3])
                    
                    with col1:
                        st.dataframe(df_stats_words)
                    
                    with col2:
                        st.bar_chart(df_stats_words.set_index("Primeira Palavra").head(10))
                
                if categories and 'Categoria' in df.columns:
                    st.markdown("### Distribuição por Categoria")
                    category_counts = df['Categoria'].value_counts().reset_index()
                    category_counts.columns = ["Categoria", "Frequência"]
                    
                    col1, col2 = st.columns([2, 3])
                    
                    with col1:
                        st.dataframe(category_counts)
                    
                    with col2:
                        st.bar_chart(category_counts.set_index("Categoria"))
                
                st.markdown("### Exportar Resultados")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        "📥 Baixar Dados Completos",
                        data=to_excel(df),
                        file_name="dados_completos_analisados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                with col2:
                    if not df['Primeira Palavra'].empty:
                        st.download_button(
                            "📊 Exportar Estatísticas",
                            data=to_excel(df_stats_words),
                            file_name="estatisticas_analise.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")

if __name__ == "__main__":
    if is_render():
        import socket
        hostname = socket.gethostname()
        st.write(f"Running on Render instance: {hostname}")
    
    main()
