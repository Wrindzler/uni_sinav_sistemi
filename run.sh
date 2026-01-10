#!/bin/bash
# ÜNİVERSİTE SINAV PROGRAMI - BAŞLATMA SCRIPTİ
# =============================================
# Bu script uygulamayı Linux/Mac'te çalıştırır.

echo ""
echo "========================================"
echo " Üniversite Sınav Programı Uygulaması"
echo "========================================"
echo ""

# Python'un yüklü olup olmadığını kontrol et
if ! command -v python3 &> /dev/null; then
    echo "[HATA] Python bulunamadı! Lütfen Python'u yükleyin."
    exit 1
fi

# Sanal ortam kontrolü (opsiyonel)
if [ -d "venv" ]; then
    echo "Sanal ortam aktifleştiriliyor..."
    source venv/bin/activate
fi

# Bağımlılıkları kontrol et
echo "Bağımlılıklar kontrol ediliyor..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Bağımlılıklar yükleniyor..."
    pip3 install -r requirements.txt
fi

# Uploads klasörünü oluştur
if [ ! -d "uploads" ]; then
    echo "Uploads klasörü oluşturuluyor..."
    mkdir -p uploads
fi

# Uygulamayı başlat
echo ""
echo "Uygulama başlatılıyor..."
echo "Tarayıcınızda http://localhost:5000 adresini açın"
echo ""
echo "Durdurmak için Ctrl+C tuşlarına basın"
echo ""

python3 app.py

