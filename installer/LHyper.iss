; Instalador do LHyper (Inno Setup 6).
;
; Gera dist\LHyper-<versão>-Setup.exe a partir de dist\LHyper\ (saída do PyInstaller):
;   ISCC.exe /DAppVersion=0.2.7 installer\LHyper.iss
;
; Instala só para o usuário atual (sem pedir senha de administrador), em
; %LOCALAPPDATA%\Programs\LHyper, com atalho no menu Iniciar e na área de trabalho.
; Usado pelo GitHub Actions (.github/workflows/release.yml).

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
; Não altere o AppId: é ele que faz o Windows reconhecer versões novas como atualização.
AppId={{B6EA74D4-8ECF-4832-BD6E-BA9513C520F2}
AppName=LHyper
AppVersion={#AppVersion}
AppVerName=LHyper {#AppVersion}
AppPublisher=Lucas Brandalise
AppPublisherURL=https://github.com/LucasBrandalise/LHyper
AppSupportURL=https://github.com/LucasBrandalise/LHyper/issues
AppUpdatesURL=https://github.com/LucasBrandalise/LHyper/releases/latest
PrivilegesRequired=lowest
DefaultDirName={autopf}\LHyper
DisableProgramGroupPage=yes
DisableDirPage=auto
OutputDir=..\dist
OutputBaseFilename=LHyper-{#AppVersion}-Setup
; Ícone do Setup.exe e, dentro do assistente, o mesmo óculos pixelado ampliado
; (gerado por installer\make_wizard_images.py).
SetupIconFile=..\assets\icons\favicon.ico
WizardSmallImageFile=build\wizard-small-64.png,build\wizard-small-128.png
UninstallDisplayIcon={app}\LHyper.exe
UninstallDisplayName=LHyper
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Fecha o LHyper aberto antes de atualizar os arquivos.
CloseApplications=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
; Marcado por padrão: o atalho na área de trabalho é o que a maioria espera.
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; Remove bibliotecas da versão anterior antes de copiar as novas.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\dist\LHyper\*"; DestDir: "{app}"; Excludes: "portable.txt,app_data,downloads"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; O AppUserModelID é o mesmo definido em run.py, para o ícone fixado na barra de tarefas
; abrir o app em vez de criar um segundo ícone.
Name: "{autoprograms}\LHyper"; Filename: "{app}\LHyper.exe"; AppUserModelID: "LHyper.Desktop"
Name: "{autodesktop}\LHyper"; Filename: "{app}\LHyper.exe"; AppUserModelID: "LHyper.Desktop"; Tasks: desktopicon

[Run]
Filename: "{app}\LHyper.exe"; Description: "{cm:LaunchProgram,LHyper}"; Flags: nowait postinstall skipifsilent
