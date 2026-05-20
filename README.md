# ⚗️ Azoth

> *Na alquimia, Azoth é a essência primordial — o agente transformador universal. Aqui, ele transforma fala em conhecimento.*

Azoth é uma aplicação desktop com interface gráfica para **transcrição de áudio, diarização de falantes (quem falou o quê) e análise inteligente com IA**. Ele foi meticulosamente otimizado para rodar localmente de forma eficiente, mesmo em GPUs de entrada (como a GTX 1650 com 4GB de VRAM), coordenando o uso de memória de vídeo com APIs de IA robustas e gratuitas.

---

## ✨ Funcionalidades

| Função | Descrição |
|---|---|
| 🎙️ **Gravar do microfone** | Captura e transcreve áudio direto do microfone |
| 🖥️ **Gravar o áudio do sistema** | Captura reuniões, vídeos e qualquer som que toca no PC |
| 📁 **Importar arquivo** | Transcreve arquivos `.mp3`, `.mp4`, `.wav` e outros formatos |
| ▶️ **Download do YouTube** | Cola a URL, o Azoth baixa e transcreve automaticamente |
| 👤 **Diarização de Falantes** | Identifica quem falou cada trecho da transcrição (via `pyannote-audio`) |
| 🤖 **Análise com IA + Chat** | Chat conversacional estruturado via agente Agno + Groq com inteligência de chunking |
| 🗂️ **Histórico completo** | Todas as transcrições salvas localmente com busca e gerenciamento |

---

## 🚀 Otimizações Arquiteturais Recentes

Para viabilizar o uso do app de forma confortável em hardwares com 4GB de VRAM e em limites de API gratuitos (Groq Free Tier), implementamos as seguintes melhorias:

### 1. Gestão Extrema de VRAM (Whisper + Pyannote)
* **Lazy Loading / Unloading Sob Demanda**: O modelo Whisper não fica mais preso na GPU em estado ocioso. Ele é carregado na VRAM exclusivamente durante a transcrição e é **imediatamente movido para a CPU e deletado** antes de o modelo de Diarização (Pyannote) assumir. Isso evita sobreposição de memória e estouros de 4GB de VRAM.
* **Modelo Otimizado**: Alterado para o modelo `small` por padrão para português, equilibrando alta acurácia e baixo consumo (~1.0 GB VRAM).
* **Compatibilidade GTX 1650 (Estabilidade fp32)**: Placas de entrada (como a GTX 1650) carecem de Tensor Cores dedicados, gerando erros de `nan` logits ao usar `fp16=True`. Forçamos o uso estável de `fp16=False` (precisão simples fp32), mantendo a integridade e precisão absoluta da transcrição.

### 2. Chunking Inteligente & Resiliência a Rate Limit (Groq)
* **Segmentação por Parágrafo**: Áudios longos (como reuniões de 1h45 que chegam a 35K tokens) são fatiados em blocos de até 28.000 caracteres (~7.000 tokens) respeitando pontuações e quebras naturais de linha.
* **Consolidação/Síntese por Passes**: Os blocos são analisados individualmente, e uma chamada final unifica as análises parciais em um documento estruturado sob medida, respeitando o limite de **12K TPM** (Tokens Per Minute) do Groq Free.
* **Retries com Backoff Exponencial**: Caso a API do Groq atinja limites de requisição (HTTP 429), o motor de análise efetua pausas e re-tentativas automáticas de forma transparente para o usuário.
* **Contexto de Chat Compacto**: O histórico do chat pós-análise recebe uma síntese densa em suas diretivas de sistema ao invés do texto bruto completo, mantendo a janela de contexto limpa e otimizada.

### 3. Patches de Compatibilidade Dinâmicos (`compat.py`)
* Sistema inovador de auto-injeção de patches executado ao carregar os módulos, contornando quebras internas de bibliotecas sob PyTorch 2.6+/2.7+ e torchaudio, como o redirecionamento nativo do `torchaudio.load()` para decodificação via `soundfile` e desativação forçada de `weights_only` obsoletos.

---

## ⚙️ Requisitos

- Python **3.9+** (Recomendado 3.10 ou 3.11)
- **NVIDIA GPU** com CUDA 12.8+ (Altamente recomendado; CPU funciona, mas com velocidade reduzida)
- [uv](https://github.com/astral-sh/uv) — gerenciador de pacotes e ambientes ultrarrápido
- [ffmpeg](https://ffmpeg.org/) configurado nas variáveis de ambiente do sistema
- Chave de API do [Groq](https://console.groq.com/) (Gratuita, para análise e chat com IA)
- Token do [Hugging Face](https://huggingface.co/) (Apenas se optar pela Diarização de Falantes, para baixar o modelo do Pyannote)

> **Ambiente Benchmark:** Windows 11, GTX 1650 (4GB), CUDA 12.8, Python 3.11, Whisper `small` (Local) + `llama-3.3-70b-versatile` (Groq)

---

## 🚀 Instalação e Execução

### 1. Clonar e Acessar o Repositório
```bash
git clone https://github.com/h-eXu/Azoth.git
cd Azoth
```

### 2. Sincronizar Dependências com o `uv`
```bash
uv sync
```
> O `uv` criará o ambiente virtual `.venv` e instalará todas as dependências automaticamente, incluindo o PyTorch pré-compilado para a GPU com suporte CUDA.

### 3. Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
GROQ_API_KEY=gsk_sua_chave_aqui
HF_TOKEN=hf_seu_token_aqui_opcional
```

### 4. Instalar o FFMPEG
* **Windows**: Baixe a build mais recente no [ffmpeg.org](https://ffmpeg.org/download.html) e adicione a pasta `bin` ao PATH do sistema.
* **macOS**: `brew install ffmpeg`

### 5. Iniciar a Aplicação
```bash
uv run python -m azoth.main
```

---

## 🗂️ Estrutura de Diretórios

```
Azoth/
├── azoth/
│   ├── core/          # Inteligência: compatibilidade, áudio, Whisper, banco de dados, diarização e chunking
│   ├── gui/           # Apresentação: CustomTkinter (Home, Histórico, Transcrição, Chat)
│   └── main.py        # Ponto de entrada
├── pyproject.toml     # Configurações do ecossistema de dependências
├── .env               # Variáveis sensíveis e segredos (ignorado no git)
└── transcricoes.json  # Histórico persistido localmente (ignorado no git)
```

---

*Construído com obsessão técnica e carinho.*
