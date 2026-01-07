@echo off
echo ==========================================
echo       Compilando Honorarios Contabeis
echo ==========================================

REM Ativar virtualenv se existir
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo Instalando dependencias...
pip install -r honorarios/requirements.txt

echo Limpando builds anteriores...
rmdir /s /q build
rmdir /s /q dist

echo Compilando...
pyinstaller --noconfirm --onefile --windowed --clean ^
    --name "HonorariosContabeis" ^
    --icon "honorarios/data/logo.ico" ^
    --paths "honorarios" ^
    --add-data "honorarios/data;honorarios/data" ^
    --hidden-import "database" ^
    --hidden-import "utils" ^
    --hidden-import "utils.theme" ^
    --hidden-import "utils.updater" ^
    --hidden-import "utils.toast" ^
    --hidden-import "utils.pdf_recibo" ^
    --hidden-import "utils.excel_export" ^
    --hidden-import "sqlite3" ^
    --hidden-import "requests" ^
    --hidden-import "babel.numbers" ^
    --collect-all "flet" ^
    honorarios/app_flet.py

echo.
echo ==========================================
echo       Organizando Arquivos
echo ==========================================

echo Criando pasta Data...
mkdir "dist\Data" 2>nul

echo Copiando arquivos externos...
copy /Y "honorarios\data\*.*" "dist\Data\"
copy /Y "logo.png" "dist\Data\"

if exist dist\HonorariosContabeis.exe (
    echo.
    echo ==========================================
    echo [SUCESSO] Executavel gerado em dist\HonorariosContabeis.exe
    echo ==========================================
) else (
    echo [ERRO] Falha na compilacao!
)
pause
