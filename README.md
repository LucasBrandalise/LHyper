# LHyper

Aplicativo desktop em Python + PySide6 para baixar vídeos e converter áudio.

## Versão atual

0.2.5

## Requisitos

- Python 3.14
- PySide6
- yt-dlp
- FFmpeg

## Como executar

```bash
python run.py
```

Ou, usando a venv do projeto:

```bash
.venv\Scripts\python.exe run.py
```

## Testes

Os testes usam apenas `unittest` (biblioteca padrão) e rodam sem rede nem janela:

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

## Status

Primeira versão inicial da interface desktop.
