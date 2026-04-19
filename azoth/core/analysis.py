"""AI analysis engine — Groq + auto-analysis prompt."""

from agno.agent import Agent
from agno.models.groq import Groq

AUTO_ANALYSIS_PROMPT = """\
Analise a transcrição a seguir e gere um documento estruturado com:

1. **Resumo Executivo** — Síntese em 2-3 parágrafos do conteúdo
2. **Pontos-Chave** — Lista dos principais tópicos abordados
3. **Tarefas Identificadas** — Ações mencionadas ou que precisam ser realizadas
4. **Encaminhamentos** — Decisões tomadas ou direcionamentos dados
5. **Próximos Passos** — O que precisa acontecer a seguir

Responda em português brasileiro. Seja objetivo e preciso.
"""


class AnalysisEngine:
    def __init__(self, model_id="llama-3.3-70b-versatile"):
        self.model_id = model_id

    def create_agent(self, transcription):
        """Create a new agent pre-loaded with the transcription context."""
        return Agent(
            model=Groq(id=self.model_id),
            add_history_to_messages=True,
            num_history_runs=5,
            markdown=True,
            instructions=f"""\
Você é um assistente especializado em análise de transcrições de áudio e vídeo.
Responda sempre em português brasileiro.
Analise a transcrição fornecida e responda as perguntas do usuário com precisão.

Transcrição:
{transcription}
""",
        )

    def auto_analyze_stream(self, transcription):
        """Run auto-analysis with streaming. Returns (agent, response_stream)."""
        agent = self.create_agent(transcription)
        response = agent.run(AUTO_ANALYSIS_PROMPT, stream=True)
        return agent, response

    def chat_stream(self, agent, message):
        """Send a chat message and return streaming response."""
        return agent.run(message, stream=True)
