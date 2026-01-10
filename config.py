"""
YAPILANDIRMA AYARLARI
=====================
Uygulamanın tüm yapılandırma ayarları burada tutulur.

Bu dosya:
- Güvenlik ayarlarını
- Veritabanı bağlantı bilgilerini
- Dosya yükleme ayarlarını
- Sınav planlama parametrelerini
- Diğer uygulama ayarlarını içerir

Ortam değişkenleri aracılığıyla geçersiz kılınabilir.
"""

import os
from pathlib import Path

# ============================================
# PROJE DİZİN AYARLARI
# ============================================

# Proje kök dizini (config.py'nin bulunduğu dizin)
BASE_DIR = Path(__file__).parent


class Config:
    """
    Temel yapılandırma sınıfı.
    
    Tüm ortamlar (geliştirme, test, üretim) için ortak ayarlar burada tanımlanır.
    Ortam özel ayarlar için bu sınıfı extend etmek önerilir.
    """
    
    # ============================================
    # GÜVENLIK AYARLARI
    # ============================================
    
    # Gizli anahtar: Flask oturumları ve CSRF koruması için kullanılır
    # ÖNEMLİ: Üretimde bu güçlü bir anahtar olmalı!
    # Ortam değişkeninden alınır, yoksa varsayılan kullanılır
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-degistirilmeli-uretimde'
    
    # ============================================
    # VERİTABANI AYARLARI
    # ============================================
    
    # Veritabanı URL'si
    # SQLite kullanıyoruz: Geliştirme için uygun, hafif ve kurulum gerektirmiyor
    # Üretimde: PostgreSQL, MySQL gibi daha güçlü veritabanları önerilir
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "universite_sinav.db"}'
    
    # SQLAlchemy model değişikliklerini otomatik olarak takip etme
    # False: Manuel migration kontrol, daha güvenli
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ============================================
    # OTURUM VE KİMLİK DOĞRULAMA AYARLARI
    # ============================================
    
    # Oturum çerezini yalnızca HTTPS üzerinden gönderin
    # Geliştirmede False, üretimde True olmalı
    SESSION_COOKIE_SECURE = False
    
    # Oturum çerezine JavaScript'ten erişilemesin (XSS koruması)
    SESSION_COOKIE_HTTPONLY = True
    
    # CSRF ve Clickjacking saldırılarından koruması için
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Oturum geçerlilik süresi (saniye)
    PERMANENT_SESSION_LIFETIME = 24 * 60 * 60  # 24 saat
    
    # ============================================
    # DOSYA YÜKLEME AYARLARI
    # ============================================
    
    # Maximum dosya yükleme boyutu: 16MB
    # CSV dosyaları ve benzeri yapılandırma dosyaları için
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Yüklenen dosyaların saklanacağı dizin
    # Örn: Öğrenci listeleri (CSV formatında)
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    
    # İzin verilen dosya uzantıları
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'txt'}
    
    # ============================================
    # SINAV PLANLAMA AYARLARI
    # ============================================
    
    # Sınav başlama saati: Sınavlar bu saatten erken başlayamaz
    # Örn: 09:00
    SINAV_BASLANGIC_SAATI = 9
    
    # Sınav bitiş saati: Sınavlar bu saatten sonra başlayamaz
    # Örn: 18:00 (bir sınav 18:00'de başlayıp 18:30'da bitilebilir)
    SINAV_BITIS_SAATI = 18
    
    # İki sınav arasındaki minimum aralık (dakika)
    # Hocaların bir derslikten diğerine geçebilmesi için zaman kazanması için
    # Değer: 30 dakika (opsiyonel: 15, 45 vb. olabilir)
    SINAV_ARALIGI = 30
    
    # İzin verilen sınav süreleri (dakika)
    SINAV_SURELERI = [30, 60, 90, 120]
    
    # İzin verilen sınav türleri
    SINAV_TURLERI = [
        'yazili',       # Yazılı sınav
        'uygulama',     # Uygulama sınavı
        'proje',        # Proje sunumu/savunması
        'sozlu',        # Sözlü sınav
        'quiz',         # Kısa sınav
        'laboratuvar',  # Laboratuvar sınavı
        'diger'         # Diğer
    ]
    
    # Sınavların yapılacağı çalışma günleri
    # Kısıtlama: Pazar günü sınav yapılmaz
    # Not: Özel durumlar belirtilerek farklı günler de kullanılabilir
    CALISMA_GUNLERI = [
        'Pazartesi',    # 0
        'Salı',         # 1
        'Çarşamba',     # 2
        'Perşembe',     # 3
        'Cuma',         # 4
        'Cumartesi',    # 5
        # 'Pazar'       # 6 - Pazar günü sınav yapılmaz
    ]
    
    # ============================================
    # SAYFALAMA AYARLARI
    # ============================================
    
    # Bir sayfada gösterilecek öğe sayısı
    # Listeler (dersler, öğrenciler, vb.) için
    ITEMS_PER_PAGE = 20
    
    # ============================================
    # RAPORLAMA AYARLARI
    # ============================================
    
    # Rapor formatları (PDF, Excel, vb. için)
    # PDF raporları için: reportlab, weasyprint
    # Excel raporları için: openpyxl, xlsxwriter
    REPORT_FORMATS = ['pdf', 'excel', 'csv']

