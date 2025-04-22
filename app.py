import streamlit as st
import os
import json
import base64
import firebase_admin
from firebase_admin import credentials, db

# Lê o JSON de credenciais do segredo codificado
cred_json = base64.b64decode(os.environ["firebase_credentials"]).decode("utf-8")
cred_dict = json.loads(cred_json)

# Inicializa o Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://denuncias-48660-default-rtdb.firebaseio.com/"
    })

# Referência do banco
ref = db.reference("/denuncias")

# Página
st.set_page_config(page_title="Sistema de Denúncias Epidemiológicas", layout="wide")
st.title("🦟 Sistema de Denúncias Epidemiológicas")

# Formulário
with st.form("denuncia_form"):
    st.subheader("📋 Registrar nova denúncia")

    col1, col2 = st.columns(2)
    with col1:
        bairro = st.text_input("Bairro")
        rua = st.text_input("Rua")
        numero = st.text_input("Número do imóvel")
        cep = st.text_input("CEP")
    with col2:
        tipo = st.selectbox("Tipo de denúncia", ["Arboviroses", "Escorpião", "Ratos", "Caramujo", "Sujidades", "Mato Alto"])
        descricao = st.text_area("Descrição")

    submit = st.form_submit_button("Registrar denúncia")

    if submit:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ano_atual = datetime.now().year

        dados_existentes = ref.get()
        numero_serie = 1

        if dados_existentes:
            protocolos_ano = [
                d.get("protocolo", "")
                for d in dados_existentes.values()
                if str(d.get("protocolo", "")).startswith(str(ano_atual))
            ]
            numero_serie = len(protocolos_ano) + 1

        protocolo = f"{ano_atual}{numero_serie}"

        dados = {
            "protocolo": protocolo,
            "data": now,
            "bairro": bairro,
            "rua": rua,
            "numero": numero,
            "cep": cep,
            "tipo": tipo,
            "descricao": descricao,
            "data_atendimento": "",
            "status": "",
            "relatorio": "",
        }

        ref.push(dados)
        st.success(f"✅ Denúncia registrada com sucesso! Protocolo: {protocolo}")

# Busca por protocolo
st.divider()
st.subheader("🔍 Buscar por número de protocolo")
protocolo_busca = st.text_input("Digite o número do protocolo")

# Dados
dados = ref.get()
if dados:
    df = pd.DataFrame(dados.values())

    if protocolo_busca:
        df = df[df["protocolo"].astype(str).str.contains(protocolo_busca, case=False, na=False)]

    # Garantir colunas
    colunas_ordenadas = [
        "protocolo", "data", "bairro", "rua", "numero", "cep", "tipo", "descricao",
        "data_atendimento", "status", "relatorio"
    ]
    for col in colunas_ordenadas:
        if col not in df.columns:
            df[col] = ""

    df = df[colunas_ordenadas]

    # Converter a coluna de data de atendimento (se não estiver vazia)
    df["data_atendimento"] = pd.to_datetime(df["data_atendimento"], errors="coerce")

    st.subheader("📄 Denúncias registradas")

    # Editor
    edited_df = st.data_editor(
        df,
        column_config={
            "data_atendimento": st.column_config.DateColumn("Data do atendimento"),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["", "Arquivada", "Auto de infração", "Auto de penalidade"],
            ),
            "relatorio": st.column_config.TextColumn("Relatório do atendimento"),
        },
        use_container_width=True,
        num_rows="dynamic",
        key="editor"
    )

    # Salvar alterações
    if st.button("💾 Salvar alterações"):
        dados_atualizados = ref.get()  # Pega os dados mais atualizados do Firebase

        for i, row in edited_df.iterrows():
            protocolo = str(row.get("protocolo", "")).strip()
            if not protocolo:
                continue  # pula se o protocolo estiver vazio

            chave_encontrada = None
            for key, valor in dados_atualizados.items():
                if valor.get("protocolo") == protocolo:
                    chave_encontrada = key
                    break

            if chave_encontrada:
                data_atendimento_str = (
                    row["data_atendimento"].strftime("%Y-%m-%d") if pd.notnull(row["data_atendimento"]) else ""
                )
                status_str = row["status"] if pd.notnull(row["status"]) else ""
                relatorio_str = row["relatorio"] if pd.notnull(row["relatorio"]) else ""

                ref.child(chave_encontrada).update({
                    "data_atendimento": data_atendimento_str,
                    "status": status_str,
                    "relatorio": relatorio_str,
                })

        st.success("✅ Informações complementares salvas com sucesso!")

else:
    st.info("Nenhuma denúncia registrada ainda.")
