# LHyper

Aplicativo desktop em Python + PySide6 para baixar vídeos do YouTube em MP4 ou extrair o áudio em MP3.

## Versão atual

0.2.5

## Requisitos

- Windows 10 ou 11
- [Git](https://git-scm.com/downloads)
- Python 3.14
- FFmpeg (necessário para MP3 e para juntar vídeo + áudio em alta qualidade)

As bibliotecas Python (PySide6 e yt-dlp) são instaladas no passo 4.

## Instalação passo a passo

Todos os comandos abaixo são para o **PowerShell** ou o **Prompt de Comando**.

### 1. Instale o Python 3.14

Baixe em <https://www.python.org/downloads/> e, no instalador, marque **"Add python.exe to PATH"**.

Confira a instalação:

```bash
python --version
```

A saída deve começar com `Python 3.14`.

### 2. Instale o FFmpeg

```bash
winget install Gyan.FFmpeg
```

Feche e abra o terminal de novo e confira:

```bash
ffmpeg -version
```

> Sem o FFmpeg o app ainda baixa vídeos em MP4, mas em qualidade limitada, e a conversão para MP3 não funciona.

### 3. Baixe o projeto

```bash
git clone https://github.com/LucasBrandalise/LHyper.git
cd LHyper
```

### 4. Crie o ambiente virtual e instale as dependências

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 5. Abra o app

Dê dois cliques em **`LHyper.bat`** na pasta do projeto, ou rode:

```bash
.venv\Scripts\python.exe run.py
```

Os arquivos baixados ficam na pasta `downloads/`, e o histórico e o cache ficam em `app_data/`, ambos dentro da pasta do projeto.

### Opcional: atalho na área de trabalho

Clique com o botão direito em `LHyper.bat` → **Mostrar mais opções** → **Enviar para** → **Área de trabalho (criar atalho)**.

## Atualizar

Dentro da pasta do projeto:

```bash
git pull
.venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt
```

Atualizar o yt-dlp com frequência evita erros quando o YouTube muda algo no site.

## Problemas comuns

| Problema | Solução |
| --- | --- |
| `python` não é reconhecido | Reinstale o Python marcando "Add python.exe to PATH" e abra um terminal novo. |
| "FFmpeg não encontrado" ao baixar MP3 | Faça o passo 2 e reinicie o app. |
| `LHyper.bat` abre e fecha na hora | A pasta `.venv` não existe ou está incompleta: refaça o passo 4. |
| Download falha com erro do YouTube | Atualize o yt-dlp (veja "Atualizar"). |

## Testes

Os testes usam apenas `unittest` (biblioteca padrão) e rodam sem rede nem janela:

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -t .
```
