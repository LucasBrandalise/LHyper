# LHyper

Aplicativo desktop em Python + PySide6 para baixar vídeos do YouTube em MP4 ou extrair o áudio em MP3.

## Versão atual

0.2.6

## Como instalar (sem precisar entender de GitHub)

### 1. Baixe o app

1. Abra a página da [versão mais recente](https://github.com/LucasBrandalise/LHyper/releases/latest).
2. Role até o fim, na parte **Assets**, e clique em **LHyper-…-windows.zip**.
   Não clique em "Source code": aquilo é o código-fonte, não o app.

### 2. Extraia (passo obrigatório)

1. Abra a pasta **Downloads** e encontre o arquivo `LHyper-…-windows.zip`.
2. Clique nele com o botão direito e escolha **Extrair Tudo...**.
3. Em vez de deixar na pasta Downloads, troque o destino para **Documentos**: clique em **Procurar...**, escolha **Documentos** e depois **Extrair**.

> ⚠️ Não abra o app de dentro do `.zip` sem extrair: assim ele não funciona e mostra uma mensagem de erro.

### 3. Abra pela primeira vez

1. Na pasta extraída (**Documentos → LHyper**), dê dois cliques em **LHyper.exe**.
2. Se aparecer a tela azul *"O Windows protegeu o computador"*, clique em **Mais informações** e depois em **Executar assim mesmo**. Isso só acontece na primeira vez, porque o app ainda não tem assinatura digital.

### 4. Crie um atalho na área de trabalho

1. Na pasta **Documentos → LHyper**, clique com o botão direito em **LHyper.exe**.
2. No Windows 11, clique em **Mostrar mais opções**; no Windows 10, pule este passo.
3. Escolha **Enviar para → Área de trabalho (criar atalho)**.

Pronto: o ícone do LHyper aparece na área de trabalho.

> ⚠️ Não arraste o `LHyper.exe` para a área de trabalho: ele precisa ficar junto da pasta `_internal` para funcionar. Use sempre o atalho.

**Fixar na barra de tarefas (opcional):** com o app aberto, clique com o botão direito no ícone dele na barra de tarefas e escolha **Fixar na barra de tarefas**.

### 5. Para baixar MP3 (opcional)

Para converter para MP3 (e baixar vídeos na melhor qualidade), o app precisa do FFmpeg:

1. Clique com o botão direito no botão **Iniciar** e escolha **Terminal** (ou **Windows PowerShell**).
2. Cole o comando abaixo e aperte **Enter**:

   ```
   winget install Gyan.FFmpeg
   ```

3. Quando terminar, feche e abra o LHyper de novo.

### Onde ficam os arquivos baixados?

Na pasta **downloads**, dentro da pasta do app (**Documentos → LHyper → downloads**).

### Como atualizar para uma versão nova

Baixe e extraia a versão nova por cima da antiga, na mesma pasta (**Documentos**), e confirme **Substituir** quando o Windows perguntar. Seus downloads e o histórico são mantidos, e o atalho continua funcionando.

---

Para rodar a partir do código-fonte (desenvolvedores), siga a instalação abaixo.

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

## Lançar uma nova versão

O workflow [`.github/workflows/release.yml`](.github/workflows/release.yml) roda os testes, gera o `LHyper.exe` com PyInstaller, confere se ele abre e publica a Release com o `.zip`.

1. Atualize `APP_VERSION` em `app/core/constants.py` (ex.: `0.2.6`) e a versão no topo deste README, e faça commit.
2. Crie e envie a tag com o mesmo número:

   ```bash
   git tag v0.2.6
   git push origin main --tags
   ```

O build falha se a tag não bater com `APP_VERSION`. Cada build instala o yt-dlp mais recente, então quando o YouTube mudar algo e os downloads pararem, basta lançar uma versão nova.

Para gerar o executável localmente:

```bash
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller LHyper.spec --noconfirm
```

O resultado fica em `dist\LHyper\`.
