"""AI analysis engine — Groq + template-based auto-analysis."""

from agno.agent import Agent
from agno.models.groq import Groq


TEMPLATES = {
    "geral": {
        "label": "📋 Geral",
        "prompt": """\
Você é um assistente especialista em síntese de conteúdo falado.

Analise a transcrição fornecida e produza um documento estruturado. \
Seja direto e objetivo — não repita informações, não adicione conteúdo que não esteja na transcrição.

## Resumo Executivo
Síntese do conteúdo em 2-3 parágrafos. O que foi discutido, no contexto geral.

## Pontos-Chave
Lista dos principais tópicos abordados. Um item por linha, começando com verbo ou substantivo.

## Tarefas Identificadas
Ações mencionadas ou implícitas que precisam ser realizadas. Se nenhuma foi mencionada, escreva "Nenhuma identificada."

## Encaminhamentos
Decisões tomadas ou direcionamentos dados. Se nenhum, escreva "Nenhum identificado."

## Próximos Passos
O que precisa acontecer a seguir, em ordem de prioridade.

Responda em português brasileiro.
""",
    },
    "reuniao": {
        "label": "🤝 Reunião de equipe",
        "prompt": """\
Você é um assistente de produtividade especializado em reuniões corporativas.

Analise a transcrição desta reunião e produza uma ata estruturada. \
Foque em decisões concretas e ações atribuídas — ignore conversas de preenchimento e repetições. \
Não invente responsáveis ou prazos que não foram mencionados.

## Resumo da Reunião
O que foi discutido em 2-3 parágrafos. Contexto, objetivo e resultado geral.

## Decisões Tomadas
Lista de cada decisão confirmada durante a reunião. Se nenhuma foi tomada, diga explicitamente.

## Tarefas Atribuídas
Formato: "• [Tarefa] — Responsável: [nome ou 'não definido'] — Prazo: [data ou 'não definido']"

## Pontos em Aberto
Questões levantadas que não foram resolvidas. Perguntas sem resposta. Tópicos adiados.

## Próxima Reunião
Data, pauta ou gatilho mencionados. Se não foi mencionado, escreva "Não definido."

Responda em português brasileiro.
""",
    },
    "aula": {
        "label": "🎓 Aula / Palestra",
        "prompt": """\
Você é um assistente pedagógico especializado em síntese de conteúdo educacional.

Analise a transcrição desta aula ou palestra e produza material de estudo estruturado. \
Preserve a precisão técnica — não simplifique termos especializados. \
Não adicione definições ou exemplos que não estejam na transcrição.

## Tema Central
O assunto principal em 1-2 frases. Qual problema ou conceito a aula se propõe a explicar.

## Conceitos-Chave
Lista dos conceitos ensinados. Formato: "• **[Conceito]**: [definição conforme apresentada na aula]"

## Exemplos e Analogias
Ilustrações usadas para explicar os conceitos. Se nenhuma foi usada, omita esta seção.

## Glossário
Termos técnicos ou novos mencionados com seus significados. Apenas termos que aparecem na transcrição.

## Para Revisar
Os 3-5 pontos mais importantes para fixar. O que o ouvinte não pode esquecer.

Responda em português brasileiro.
""",
    },
    "entrevista": {
        "label": "🎙️ Entrevista",
        "prompt": """\
Você é um assistente jornalístico especializado em análise de entrevistas.

Analise a transcrição desta entrevista e produza um documento de referência. \
Mantenha fidelidade ao que foi dito — parafrasear é permitido, mas não distorça posições. \
Se o entrevistado não for identificado na transcrição, deixe o campo em branco.

## Perfil do Entrevistado
Quem é, área de atuação e contexto da entrevista, conforme mencionado.

## Tópicos Abordados
Lista dos assuntos tratados, na ordem em que apareceram na conversa.

## Citações Relevantes
As 3-5 falas mais significativas. Formato: "• '[frase ou paráfrase fiel]'"

## Posições e Opiniões
Pontos de vista, crenças ou argumentos expressos pelo entrevistado. Apenas o que foi dito explicitamente.

## Destaques
O que há de mais valioso, surpreendente ou acionável nesta entrevista. 2-3 itens.

Responda em português brasileiro.
""",
    },
}


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

    def auto_analyze_stream(self, transcription, template="geral"):
        """Run auto-analysis with streaming. Returns (agent, response_stream)."""
        prompt = TEMPLATES.get(template, TEMPLATES["geral"])["prompt"]
        agent = self.create_agent(transcription)
        response = agent.run(prompt, stream=True)
        return agent, response

    def chat_stream(self, agent, message):
        """Send a chat message and return streaming response."""
        return agent.run(message, stream=True)