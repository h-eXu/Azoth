"""AI analysis engine — Groq + template-based auto-analysis with chunking."""

import re

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


# ── Chunking helpers ─────────────────────────────────────────────────────

# Groq free tier: 12K TPM para llama-3.3-70b-versatile
# Prompt do template + overhead ≈ 500 tokens
# Mantemos margem de segurança: max ~8K tokens de transcrição por bloco
_MAX_CHARS_PER_CHUNK = 28_000  # ~7K tokens (1 token ≈ 4 chars em pt-BR)


def _estimate_tokens(text: str) -> int:
    """Estimativa grosseira: 1 token ≈ 4 caracteres em português."""
    return len(text) // 4


def _split_text(text: str, max_chars: int = _MAX_CHARS_PER_CHUNK) -> list[str]:
    """Divide texto em blocos respeitando quebras de linha/parágrafo."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break

        # Tenta quebrar no último \n\n dentro do limite
        cut = remaining[:max_chars]
        split_pos = cut.rfind("\n\n")
        if split_pos < max_chars // 2:
            # Se não achou parágrafo bom, tenta \n
            split_pos = cut.rfind("\n")
        if split_pos < max_chars // 2:
            # Último recurso: quebra no último espaço
            split_pos = cut.rfind(" ")
        if split_pos < max_chars // 4:
            # Força o corte
            split_pos = max_chars

        chunks.append(remaining[:split_pos].strip())
        remaining = remaining[split_pos:].strip()

    return [c for c in chunks if c]


# ── Analysis agent wrapper ────────────────────────────────────────────────

class AnalysisAgentWrapper:
    """Wrapper that mimics an Agno agent for the chat window interface.
    Allows lazy loading/resolution of the underlying agent for chunked synthesis.
    """
    def __init__(self, get_agent_fn):
        self._get_agent_fn = get_agent_fn

    def run(self, *args, **kwargs):
        agent = self._get_agent_fn()
        if agent is None:
            raise ValueError("O agente de análise ainda não foi inicializado.")
        return agent.run(*args, **kwargs)


# ── Analysis engine ──────────────────────────────────────────────────────

class AnalysisEngine:
    def __init__(self, model_id="llama-3.3-70b-versatile"):
        self.model_id = model_id

    def _make_agent(self, system_instructions: str):
        """Create a minimal agent with given system instructions."""
        from agno.agent import Agent
        from agno.models.groq import Groq

        return Agent(
            model=Groq(id=self.model_id),
            markdown=True,
            instructions=system_instructions,
        )

    def create_agent(self, transcription_summary: str):
        """Create a chat agent pre-loaded with a summary for follow-up questions."""
        return self._make_agent(f"""\
Você é um assistente especializado em análise de transcrições de áudio e vídeo.
Responda sempre em português brasileiro.
Use o resumo da transcrição abaixo como contexto para responder as perguntas do usuário.

Resumo da transcrição:
{transcription_summary}
""")

    def auto_analyze_stream(self, transcription, template="geral"):
        """Run auto-analysis with streaming and chunking.
        Returns (agent_wrapper, response_stream).
        For long texts, runs chunked analysis and returns combined results."""
        prompt_template = TEMPLATES.get(template, TEMPLATES["geral"])["prompt"]
        chunks = _split_text(transcription)

        if len(chunks) == 1:
            # Texto cabe em uma chamada — fluxo original
            agent = self._make_agent(
                "Você é um assistente especializado em análise de transcrições. "
                "Responda sempre em português brasileiro."
            )
            full_prompt = f"{prompt_template}\n\n---\nTranscrição:\n{transcription}"
            response = agent.run(full_prompt, stream=True)
            wrapper = AnalysisAgentWrapper(lambda: agent)
            return wrapper, response
        else:
            # Texto longo — análise em blocos
            return self._chunked_analysis(chunks, prompt_template)

    def _chunked_analysis(self, chunks, prompt_template):
        """Analyze in chunks, then synthesize. Returns (agent_wrapper, generator)."""
        agent_holder = [None]

        def _stream_generator():
            import time
            partial_results = []
            total = len(chunks)

            # Helper para rodar chamadas não-streaming com retry automático em caso de rate limit (429)
            def _run_non_stream_with_retry(agent, prompt):
                delay = 3
                for attempt in range(3):
                    try:
                        return agent.run(prompt, stream=False)
                    except Exception as e:
                        err_str = str(e).lower()
                        if "rate limit" in err_str or "429" in err_str or "tpm" in err_str:
                            # Se for rate limit, espera mais tempo (tempo exponencial)
                            time.sleep(delay)
                            delay *= 2
                            continue
                        # Se for outro erro mas não for o último attempt, tenta esperar um pouco
                        if attempt < 2:
                            time.sleep(2)
                            continue
                        raise e
                # Fallback final se esgotar as tentativas
                return agent.run(prompt, stream=False)

            for i, chunk in enumerate(chunks, 1):
                # Yield status update
                yield type("Msg", (), {"content": f"\n⏳ Analisando parte {i}/{total}...\n\n"})()

                # Espaçamento de requisições para evitar rate limit de cara no Groq Free
                if i > 1:
                    time.sleep(3)

                agent = self._make_agent(
                    "Você é um assistente especializado em análise de transcrições. "
                    "Responda sempre em português brasileiro."
                )
                chunk_prompt = (
                    f"Esta é a PARTE {i} de {total} de uma transcrição longa. "
                    f"Analise apenas esta parte:\n\n"
                    f"---\n{chunk}\n---\n\n"
                    f"{prompt_template}"
                )

                response = _run_non_stream_with_retry(agent, chunk_prompt)
                partial_text = response.content if hasattr(response, 'content') else str(response)
                partial_results.append(partial_text)

            # Síntese final
            yield type("Msg", (), {"content": "\n⏳ Consolidando análise final...\n\n"})()

            # Sleep generoso antes de consolidar a análise para dar tempo de zerar o TPM
            time.sleep(4)

            combined = "\n\n---\n\n".join(
                f"## Análise da Parte {i}\n{r}" for i, r in enumerate(partial_results, 1)
            )

            synthesis_agent = self._make_agent(
                "Você é um assistente especializado em síntese de conteúdo. "
                "Responda sempre em português brasileiro."
            )
            synthesis_prompt = (
                f"Abaixo estão análises parciais de diferentes trechos de uma mesma transcrição. "
                f"Consolide todas em UM ÚNICO documento coeso seguindo EXATAMENTE este formato:\n\n"
                f"{prompt_template}\n\n"
                f"Análises parciais:\n\n{combined}"
            )

            # Stream a síntese final. Se falhar, tentamos novamente com delay maior sem streaming
            try:
                final_response = synthesis_agent.run(synthesis_prompt, stream=True)
                for msg in final_response:
                    if msg.content:
                        yield msg
            except Exception as e:
                err_str = str(e).lower()
                if "rate limit" in err_str or "429" in err_str or "tpm" in err_str:
                    yield type("Msg", (), {"content": "\n⚠️ Rate limit atingido. Aguardando 5 segundos para tentar novamente sem streaming...\n"})()
                    time.sleep(5)
                    final_response = _run_non_stream_with_retry(synthesis_agent, synthesis_prompt)
                    final_text = final_response.content if hasattr(final_response, 'content') else str(final_response)
                    yield type("Msg", (), {"content": final_text})()
                else:
                    raise e

            # O agente de chat fica sendo o de síntese, com o contexto combinado
            # Criamos um agente de chat com um resumo compacto
            agent_holder[0] = self.create_agent(combined[:_MAX_CHARS_PER_CHUNK])

        gen = _stream_generator()
        wrapper = AnalysisAgentWrapper(lambda: agent_holder[0])
        return wrapper, gen

    def chat_stream(self, agent, message):
        """Send a chat message and return streaming response."""
        return agent.run(message, stream=True)