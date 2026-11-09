import json
import uuid
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd
import streamlit as st

# -----------------------------
# Configuração do aplicativo
# -----------------------------
st.set_page_config(
    page_title="Agenda de Estudos e Compromissos",
    page_icon="📚",
    layout="wide",
)

DATA_FILE = Path(__file__).with_name("agenda_estudos.json")
PRIORIDADE_ORDENADA = {"Alta": 0, "Média": 1, "Baixa": 2}


# -----------------------------
# Utilitários
# -----------------------------
def gerar_exemplo_inicial() -> list[dict]:
    hoje = date.today()
    return [
        {
            "id": uuid.uuid4().hex,
            "titulo": "Revisão de Matemática",
            "curso": "Matemática",
            "categoria": "Estudo",
            "data": (hoje).isoformat(),
            "hora": "08:00",
            "prioridade": "Alta",
            "status": "Pendente",
            "observacao": "Resolver exercícios de funções e derivadas.",
        },
        {
            "id": uuid.uuid4().hex,
            "titulo": "Prova de História",
            "curso": "História",
            "categoria": "Prova",
            "data": (hoje).isoformat(),
            "hora": "14:30",
            "prioridade": "Alta",
            "status": "Pendente",
            "observacao": "Estudar capítulos 5 e 6 do livro.",
        },
        {
            "id": uuid.uuid4().hex,
            "titulo": "Entrega do Trabalho de Química",
            "curso": "Química",
            "categoria": "Trabalho",
            "data": (hoje).isoformat(),
            "hora": "18:00",
            "prioridade": "Média",
            "status": "Pendente",
            "observacao": "Incluir introdução, metodologia e conclusão.",
        },
    ]


def normalizar_tarefas(tarefas: list[dict]) -> list[dict]:
    normalizadas = []
    for tarefa in tarefas:
        if not isinstance(tarefa, dict):
            continue

        item = {
            "id": tarefa.get("id") or uuid.uuid4().hex,
            "titulo": str(tarefa.get("titulo", "Sem título")).strip() or "Sem título",
            "curso": str(tarefa.get("curso", "Geral")).strip() or "Geral",
            "categoria": str(tarefa.get("categoria", "Outros")).strip() or "Outros",
            "data": str(tarefa.get("data", date.today().isoformat())),
            "hora": str(tarefa.get("hora", "08:00")).strip() or "08:00",
            "prioridade": str(tarefa.get("prioridade", "Média")).strip() or "Média",
            "status": str(tarefa.get("status", "Pendente")).strip() or "Pendente",
            "observacao": str(tarefa.get("observacao", "")).strip(),
        }
        normalizadas.append(item)
    return normalizadas


def salvar_tarefas(tarefas: list[dict]) -> None:
    DATA_FILE.write_text(
        json.dumps(normalizar_tarefas(tarefas), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def carregar_tarefas() -> list[dict]:
    if not DATA_FILE.exists():
        tarefas = gerar_exemplo_inicial()
        salvar_tarefas(tarefas)
        return tarefas

    try:
        conteudo = DATA_FILE.read_text(encoding="utf-8")
        dados = json.loads(conteudo)
        if isinstance(dados, list):
            return normalizar_tarefas(dados)
    except (json.JSONDecodeError, OSError):
        pass

    tarefas = gerar_exemplo_inicial()
    salvar_tarefas(tarefas)
    return tarefas


def formatar_data(data_str: str) -> str:
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return data_str


def calcular_status(data_str: str, status: str) -> str:
    if status == "Concluída":
        return "✅ Concluída"

    try:
        data_obj = date.fromisoformat(data_str)
    except ValueError:
        return "📌 Sem data"

    dias = (data_obj - date.today()).days
    if dias < 0:
        return f"❌ Atrasado há {abs(dias)} dia(s)"
    if dias == 0:
        return "⚠️ Hoje"
    if dias <= 3:
        return f"⏳ Faltam {dias} dia(s)"
    return f"🗓️ Faltam {dias} dia(s)"


def filtrar_tarefas(tarefas: list[dict], curso: str, categoria: str, status: str, busca: str) -> list[dict]:
    filtradas = []
    busca_lower = busca.lower().strip()

    for tarefa in tarefas:
        titulo = tarefa.get("titulo", "")
        if busca_lower and busca_lower not in titulo.lower() and busca_lower not in tarefa.get("curso", "").lower():
            continue
        if curso != "Todos" and tarefa.get("curso") != curso:
            continue
        if categoria != "Todas" and tarefa.get("categoria") != categoria:
            continue
        if status != "Todos" and tarefa.get("status") != status:
            continue
        filtradas.append(tarefa)

    filtradas.sort(
        key=lambda item: (
            item.get("data", date.today().isoformat()),
            PRIORIDADE_ORDENADA.get(item.get("prioridade", "Média"), 99),
            item.get("titulo", ""),
        )
    )
    return filtradas


# -----------------------------
# Estado inicial da sessão
# -----------------------------
if "tarefas" not in st.session_state:
    st.session_state.tarefas = carregar_tarefas()

# -----------------------------
# Interface
# -----------------------------
st.title("📚 Agenda de Estudos e Compromissos")
st.caption("Organize provas, tarefas, estudos e compromissos do seu dia a dia e do curso.")

# Sidebar para adicionar tarefa
with st.sidebar:
    st.header("➕ Novo compromisso")
    titulo = st.text_input("Título da atividade:", placeholder="Ex.: Revisão de química")
    curso = st.text_input("Curso / disciplina:", placeholder="Ex.: Matemática")
    categoria = st.selectbox(
        "Categoria:",
        ["Estudo", "Prova", "Trabalho", "Atividade do dia", "Prazo", "Outros"],
    )
    data_evento = st.date_input("Data:", min_value=date.today())
    hora_evento = st.time_input("Horário (opcional):", value=time(8, 0))
    prioridade = st.select_slider("Prioridade:", options=["Baixa", "Média", "Alta"], value="Média")
    observacao = st.text_area("Observações:", placeholder="Detalhes, material a revisar, lembretes...")

    if st.button("Salvar compromisso"):
        if titulo.strip():
            nova_tarefa = {
                "id": uuid.uuid4().hex,
                "titulo": titulo.strip(),
                "curso": curso.strip() or "Geral",
                "categoria": categoria,
                "data": data_evento.isoformat(),
                "hora": hora_evento.strftime("%H:%M"),
                "prioridade": prioridade,
                "status": "Pendente",
                "observacao": observacao.strip(),
            }
            st.session_state.tarefas.insert(0, nova_tarefa)
            salvar_tarefas(st.session_state.tarefas)
            st.success("Compromisso salvo com sucesso!")
            st.rerun()
        else:
            st.error("O título do compromisso não pode ficar vazio.")

# Resumo geral
pendentes = [t for t in st.session_state.tarefas if t.get("status") != "Concluída"]
hoje = [
    t for t in pendentes if date.fromisoformat(t.get("data", date.today().isoformat())) == date.today()
]
atrasadas = [
    t
    for t in pendentes
    if date.fromisoformat(t.get("data", date.today().isoformat())) < date.today()
]
proximas = [
    t
    for t in pendentes
    if 0 < (date.fromisoformat(t.get("data", date.today().isoformat())) - date.today()).days <= 3
]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total", len(st.session_state.tarefas))
col2.metric("Pendentes", len(pendentes))
col3.metric("Hoje", len(hoje))
col4.metric("Próximas 3 dias", len(proximas))

# Filtros
st.subheader("🔎 Filtros e pesquisa")
col_busca, col_curso, col_categoria, col_status = st.columns(4)
with col_busca:
    busca = st.text_input("Buscar por tarefa ou curso", placeholder="Ex.: prova, matemática")
with col_curso:
    cursos = ["Todos"] + sorted({t.get("curso", "Geral") for t in st.session_state.tarefas})
    filtro_curso = st.selectbox("Curso", cursos)
with col_categoria:
    categorias = ["Todas"] + sorted({t.get("categoria", "Outros") for t in st.session_state.tarefas})
    filtro_categoria = st.selectbox("Categoria", categorias)
with col_status:
    opcoes_status = ["Todos", "Pendente", "Concluída"]
    filtro_status = st.selectbox("Status", opcoes_status)

tarefas_filtradas = filtrar_tarefas(
    st.session_state.tarefas,
    curso=filtro_curso,
    categoria=filtro_categoria,
    status=filtro_status,
    busca=busca,
)

if not tarefas_filtradas:
    st.info("Nenhuma tarefa corresponde aos filtros atuais. Tente outro termo ou cadastre um novo compromisso.")
else:
    for tarefa in tarefas_filtradas:
        data_obj = date.fromisoformat(tarefa.get("data", date.today().isoformat()))
        dias = (data_obj - date.today()).days
        prioridade = tarefa.get("prioridade", "Média")
        estilo = {
            "Alta": "🔴",
            "Média": "🟠",
            "Baixa": "🟢",
        }.get(prioridade, "⚪")

        with st.expander(
            f"{estilo} {tarefa['titulo']} • {tarefa.get('curso', 'Geral')} • {formatar_data(tarefa['data'])} • {tarefa.get('status', 'Pendente')}"
        ):
            col_detalhe, col_acoes = st.columns([3, 1])

            with col_detalhe:
                st.write(f"**Curso:** {tarefa.get('curso', 'Geral')}")
                st.write(f"**Categoria:** {tarefa.get('categoria', 'Outros')}")
                st.write(f"**Data:** {formatar_data(tarefa['data'])} às {tarefa.get('hora', '08:00')}")
                st.write(f"**Prioridade:** {prioridade}")
                st.write(f"**Status:** {calcular_status(tarefa['data'], tarefa.get('status', 'Pendente'))}")
                if tarefa.get("observacao"):
                    st.write(f"**Observações:** {tarefa['observacao']}")

            with col_acoes:
                if tarefa.get("status") == "Pendente":
                    if st.button("Concluir", key=f"concluir_{tarefa['id']}"):
                        for item in st.session_state.tarefas:
                            if item["id"] == tarefa["id"]:
                                item["status"] = "Concluída"
                                break
                        salvar_tarefas(st.session_state.tarefas)
                        st.rerun()
                else:
                    if st.button("Reabrir", key=f"reabrir_{tarefa['id']}"):
                        for item in st.session_state.tarefas:
                            if item["id"] == tarefa["id"]:
                                item["status"] = "Pendente"
                                break
                        salvar_tarefas(st.session_state.tarefas)
                        st.rerun()

                if st.button("Excluir", key=f"excluir_{tarefa['id']}"):
                    st.session_state.tarefas = [item for item in st.session_state.tarefas if item["id"] != tarefa["id"]]
                    salvar_tarefas(st.session_state.tarefas)
                    st.rerun()

# Resumo por curso
st.markdown("---")
st.subheader("📊 Resumo por curso")
resumo = {}
for tarefa in st.session_state.tarefas:
    if tarefa.get("status") == "Concluída":
        continue
    curso = tarefa.get("curso", "Geral")
    resumo[curso] = resumo.get(curso, 0) + 1

if resumo:
    df_resumo = pd.DataFrame({"Curso": list(resumo.keys()), "Pendências": list(resumo.values())})
    df_resumo = df_resumo.sort_values("Pendências", ascending=False)
    st.bar_chart(df_resumo.set_index("Curso"), use_container_width=True)
else:
    st.info("Ainda não há pendências em nenhum curso.")

# Tabela completa
st.markdown("---")
st.subheader("📋 Lista completa")
if st.session_state.tarefas:
    tabela = []
    for tarefa in st.session_state.tarefas:
        tabela.append(
            {
                "Título": tarefa.get("titulo", ""),
                "Curso": tarefa.get("curso", "Geral"),
                "Categoria": tarefa.get("categoria", "Outros"),
                "Data": formatar_data(tarefa.get("data", date.today().isoformat())),
                "Hora": tarefa.get("hora", "08:00"),
                "Prioridade": tarefa.get("prioridade", "Média"),
                "Status": tarefa.get("status", "Pendente"),
            }
        )
    st.dataframe(pd.DataFrame(tabela), use_container_width=True)
else:
    st.info("Nenhum compromisso cadastrado.")
