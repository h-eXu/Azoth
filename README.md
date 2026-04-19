# ⚗️ Azoth

> *Na alquimia, Azoth é a essência primordial — o agente transformador universal. Aqui, ele transforma fala em conhecimento.*

Azoth é uma aplicação desktop com interface gráfica para **transcrição local de áudio e análise com IA**. Ele roda o modelo Whisper diretamente na sua GPU (via PyTorch + CUDA), sem depender de APIs externas para transcrever. A análise inteligente é feita por um agente conversacional com contexto completo da transcrição.

---

## ✨ Funcionalidades

| Função | Descrição |
|---|---|
| 🎙️ **Gravar do microfone** | Captura e transcreve áudio direto do microfone |
| 🖥️ **Gravar o áudio do sistema** | Captura reuniões, vídeos e qualquer som que toca no PC |
| 📁 **Importar arquivo** | Transcreve arquivos `.mp3`, `.mp4`, `.wav` e outros formatos |
| ▶️ **Download do YouTube** | Cola a URL, Azoth baixa e transcreve automaticamente |
| 🤖 **Análise com IA** | Chat conversacional com contexto da transcrição via agente Agno + Groq |
| 🗂️ **Histórico completo** | Todas as transcrições salvas localmente com busca e gerenciamento |

---

## 🖼️ Interface

A GUI foi construída com **CustomTkinter** — leve, moderna e nativa. Todas as operações pesadas (transcrição, download, análise) rodam em **threads separadas** para não travar a interface.

---

## ⚙️ Requisitos

- Python **3.9+**
- **NVIDIA GPU** com CUDA 12.8+ (recomendado; CPU também funciona, mas é lento)
- [uv](https://github.com/astral-sh/uv) — gerenciador de pacotes e ambientes
- [ffmpeg](https://ffmpeg.org/) no PATH do sistema
- Chave de API do [Groq](https://console.groq.com/) (para o agente de análise)

> **Testado em:** Windows 11, GTX 1650, CUDA 12.8, Python 3.11

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/h-eXu/Azoth.git
cd Azoth
```

### 2. Crie o ambiente e instale as dependências

```bash
uv sync
```

> O `uv sync` lê o `pyproject.toml` e instala tudo automaticamente, incluindo o PyTorch com suporte CUDA.

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
GROQ_API_KEY=sua_chave_groq_aqui
```

> A chave Groq é usada pelo **agente de análise** (LLM). A **transcrição** roda 100% local com Whisper.

### 4. Instale o ffmpeg

**Windows:**
Baixe em [ffmpeg.org/download.html](https://ffmpeg.org/download.html) e adicione ao PATH do sistema.

**macOS:**
```bash
brew install ffmpeg
```

### 5. (Opcional) Configurar captura de áudio do sistema

Para gravar reuniões e vídeos que tocam no PC:

**Windows:** Instale [VB-Cable](https://vb-audio.com/Cable/) ou [VoiceMeeter](https://vb-audio.com/Voicemeeter/) e configure como dispositivo de gravação padrão.

**macOS:** Instale [BlackHole](https://existential.audio/blackhole/) e configure um Multi-Output Device no Utilitário de Áudio MIDI.

---

## ▶️ Como rodar

```bash
uv run python -m azoth.main
```

A janela da aplicação abre imediatamente. Escolha a fonte de áudio, inicie a transcrição e, ao terminar, acesse a análise com IA direto na interface.

---

## 🗂️ Estrutura do projeto

```
Azoth/
├── azoth/
│   ├── core/          # Lógica de transcrição, agente IA, banco de dados
│   ├── gui/           # Interface CustomTkinter
│   └── main.py        # Ponto de entrada
├── pyproject.toml     # Dependências e configuração do projeto
├── .env               # Chaves de API (não commitado)
└── transcricoes.json  # Histórico local (não commitado)
```

---

## 🧠 Stack técnica

| Componente | Tecnologia |
|---|---|
| Transcrição | [OpenAI Whisper](https://github.com/openai/whisper) (local, GPU) |
| Aceleração GPU | PyTorch + CUDA 12.8 |
| Agente de análise | [Agno](https://github.com/agno-agi/agno) + Groq (LLaMA) |
| Interface gráfica | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Diarização | [pyannote-audio](https://github.com/pyannote/pyannote-audio) |
| Download YouTube | [pytubefix](https://github.com/JuanBindez/pytubefix) |
| Gerenciador de pacotes | [uv](https://github.com/astral-sh/uv) |
| Banco de dados local | [TinyDB](https://github.com/msiemens/tinydb) |

---

## 📝 Observações

- O modelo Whisper roda **inteiramente local** — nenhum áudio é enviado para servidores externos
- O histórico de transcrições fica em `transcricoes.json` na raiz — mantenha no `.gitignore`
- Para melhor desempenho, use GPU NVIDIA com pelo menos 4GB de VRAM
- O agente de análise mantém contexto da conversa durante toda a sessão

---

*Construído com curiosidade e intenção.*
