@echo off
REM ÜNİVERSİTE SINAV PROGRAMI - BAŞLATMA SCRIPTİ
REM =============================================
REM Bu script uygulamayı Windows'ta çalıştırır.

echo.
echo ========================================
echo  Üniversite Sınav Programı Uygulaması
echo ========================================
echo.

REM Python'un yüklü olup olmadığını kontrol et
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadı! Lütfen Python'u yükleyin.
    pause
    exit /b 1
)

REM Sanal ortam kontrolü (opsiyonel)
if exist "venv\Scripts\activate.bat" (
    echo Sanal ortam aktifleştiriliyor...
    call venv\Scripts\activate.bat
)

REM Bağımlılıkları kontrol et
echo Bağımlılıklar kontrol ediliyor...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo Bağımlılıklar yükleniyor...
    pip install -r requirements.txt
)

REM Uploads klasörünü oluştur
if not exist "uploads" (
    echo Uploads klasörü oluşturuluyor...
    mkdir uploads
)

REM Uygulamayı başlat
echo.
echo Uygulama başlatılıyor...
echo Tarayıcınızda http://localhost:5000 adresini açın
echo.
echo Durdurmak için Ctrl+C tuşlarına basın
echo.

python app.py

pause

