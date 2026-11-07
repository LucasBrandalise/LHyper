# LHyper

Aplicativo desktop em Python + PySide6 para baixar vídeos do YouTube em MP4 ou extrair o áudio em MP3.

## Versão atual

0.2.6

## Como instalar (sem precisar entender de GitHub)

### 1. Baixe o instalador

1. Abra a página da [versão mais recente](https://github.com/LucasBrandalise/LHyper/releases/latest).
2. Role até o fim, na parte **Assets**, e clique em **LHyper-…-Setup.exe**.
   Não clique em "Source code": aquilo é o código-fonte, não o app.

### 2. Instale

1. Abra a pasta **Downloads** e dê dois cliques em **LHyper-…-Setup.exe**.
2. Se aparecer a tela azul *"O Windows protegeu o computador"*, clique em **Mais informações** e depois em **Executar assim mesmo**. Isso acontece porque o app ainda não tem assinatura digital.
3. Clique em **Avançar** até o fim e depois em **Concluir**. Não precisa de senha de administrador.

Pronto: o LHyper aparece na **área de trabalho** e no **menu Iniciar**.

**Fixar na barra de tarefas (opcional):** com o app aberto, clique com o botão direito no ícone dele na barra de tarefas e escolha **Fixar na barra de tarefas**.

### 3. Para baixar MP3 (opcional)

Para converter para MP3 (e baixar vídeos na melhor qualidade), o app precisa do FFmpeg:

1. Clique com o botão direito no botão **Iniciar** e escolha **Terminal** (ou **Windows PowerShell**).
2. Cole o comando abaixo e aperte **Enter**:

   ```
   winget install Gyan.FFmpeg
   ```

3. Quando terminar, feche e abra o LHyper de novo.

### Onde ficam os arquivos baixados?

Na pasta **Downloads → LHyper**. No app, a página **Configurações** mostra as pastas e abre cada uma com um clique.

### Como atualizar para uma versão nova

Baixe o instalador da versão nova e abra, como no passo 2. Ele substitui a versão antiga; seus downloads e o histórico são mantidos.

### Como desinstalar

**Configurações do Windows → Aplicativos → Aplicativos instalados**, procure **LHyper** e clique em **Desinstalar**. Os arquivos que você baixou continuam na pasta **Downloads → LHyper**.

### Versão portátil (sem instalar)

Para usar sem instalar, por exemplo num pendrive, baixe **LHyper-…-portatil.zip**:

1. Clique com o botão direito no arquivo → **Extrair Tudo...** → escolha onde extrair → **Extrair**.
2. Abra o **LHyper.exe** da pasta extraída.

Nessa versão os downloads e o histórico ficam dentro da própria pasta, em `downloads`.

> ⚠️ Não abra o app de dentro do `.zip` sem extrair, e não tire o `LHyper.exe` da pasta: ele precisa da pasta `_internal` ao lado. Para ter um atalho, clique com o botão direito no `LHyper.exe` → **Mostrar mais opções** (Windows 11) → **Enviar para → Área de trabalho (criar atalho)**.

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

O workflow [`.github/workflows/release.yml`](.github/workflows/release.yml) roda os testes, gera o `LHyper.exe` com PyInstaller, monta o instalador com Inno Setup, testa o instalador (instala, abre o app, desinstala) e a versão portátil, e publica a Release com o `Setup.exe` e o `.zip`.

1. Atualize `APP_VERSION` em `app/core/constants.py` (ex.: `0.2.7`) e a versão no topo deste README, e faça commit.
2. Crie e envie a tag com o mesmo número:

   ```bash
   git tag v0.2.7
   git push origin main --tags
   ```

O build falha se a tag não bater com `APP_VERSION`. Cada build instala o yt-dlp mais recente, então quando o YouTube mudar algo e os downloads pararem, basta lançar uma versão nova.

Para gerar localmente (requer o [Inno Setup 6](https://jrsoftware.org/isdl.php): `winget install JRSoftware.InnoSetup`):

```bash
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller LHyper.spec --noconfirm
.venv\Scripts\python.exe installer\make_wizard_images.py
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" /DAppVersion=0.2.7 installer\LHyper.iss
```

O app fica em `dist\LHyper\` e o instalador em `dist\LHyper-0.2.7-Setup.exe`.

### Onde o app guarda os dados

| Como roda | Downloads | Histórico e cache |
| --- | --- | --- |
| Instalado (`Setup.exe`) | `Downloads\LHyper` | `%LOCALAPPDATA%\LHyper` |
| Portátil (`.zip`, tem `portable.txt`) | `downloads\` ao lado do `LHyper.exe` | `app_data\` ao lado do `LHyper.exe` |
| Código-fonte (`python run.py`) | `downloads\` na pasta do projeto | `app_data\` na pasta do projeto |

Quem extraiu o `.zip` da v0.2.6 continua no modo portátil, porque o app reconhece a pasta `app_data` ao lado do executável.
