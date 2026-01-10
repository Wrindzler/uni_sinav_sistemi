"""
ÜNİVERSİTE SINAV PROGRAMI HAZIRLAMA UYGULAMASI
===============================================
Ana uygulama dosyası.

Bu dosya:
- Flask uygulamasını başlatır
- Tüm modülleri (routes, models, vb.) birleştirir
- Veritabanı bağlantısını kurar
- Kullanıcı oturum yönetimini ayarlar
- Hata işlemesini tanımlar

Proje Özeti:
-----------
Üniversitelerde sınav programlarının otomatik olarak oluşturulmasını sağlayan
web tabanlı bir uygulamadır. Sistem tüm kısıtlamalara (çakışma, kapasite, vb.)
uygun sınav programları oluşturur.

Başlıca Bileşenler:
-------------------
1. Models: Veritabanı şemasını tanımlar (Ders, Öğrenci, Sınav, vb.)
2. Routes: URL adreslerini ve işlemleri tanımlar
3. Algorithms: Sınav planlama algoritmasını içerir
4. Utils: Yardımcı fonksiyonlar (formatting, validasyon, vb.)
5. Templates: HTML arayüzünü oluşturur

Kullanıcı Rolleri:
------------------
- Admin: Tüm sistemi kontrol eder
- Bölüm Yetkilisi: Kendi bölümünü yönetir
- Hoca: Sadece sınav programını görebilir
- Öğrenci: Sadece sınav programını görebilir
"""

# ============================================
# İMPORT AYARLARI
# ============================================

from flask import Flask, render_template, redirect
from flask_login import LoginManager, current_user
from config import Config
from models.database import db
from models.user import User
from routes import (
    auth_bp, ders_bp, derslik_bp, sinav_bp,
    planlama_bp, rapor_bp, admin_bp, ogrenci_bp, ozel_durum_bp
)

# ============================================
# FLASK UYGULAMASI OLUŞTURMA
# ============================================

# Flask uygulaması oluştur
# __name__: Uygulamanın modül adı (statik dosyaları bulmak için kullanılır)
app = Flask(__name__)

# Config sınıfından ayarları yükle
# Veritabanı, güvenlik ve diğer ayarlar buradan alınır
app.config.from_object(Config)

# ============================================
# VERİTABANI AYARLARI
# ============================================

# SQLAlchemy veritabanı nesnesini app ile başlat
# Bu, tüm model'lerin veritabanı ile bağlantı kurmasını sağlar
db.init_app(app)

# ============================================
# KULLANICI OTURUM YÖNETİMİ (FLASK-LOGIN)
# ============================================

# Flask-Login extension'ını oluştur ve başlat
# Kullanıcı oturumlarını ve kimlik doğrulamayı yönetir
login_manager = LoginManager()
login_manager.init_app(app)

# Oturum açılmamış kullanıcıları yönlendirecek sayfa
login_manager.login_view = 'auth.login'

# Oturum açılmamış kullanıcıya gösterilecek mesaj
login_manager.login_message = 'Lütfen giriş yapın!'

# Mesaj kategorisi (Flask'ın flash() mesajları için)
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """
    Kullanıcı yükleme callback fonksiyonu.
    
    Flask-Login, oturum cookie'sinden user_id'yi çıkartıp bu fonksiyonu
    çağırır. Veritabanından kullanıcıyı bulup geri döner.
    
    Bu fonksiyon uygulama başlatıldığında ve her request'te çağrılır.
    
    Args:
        user_id (str): Oturum cookie'sinden çıkartılan kullanıcı ID'si
        
    Returns:
        User: Kullanıcı nesnesi, veya None (bulunamadıysa)
        
    Örnek:
        >>> load_user('5')
        <User admin (admin)>
    """
    try:
        # user_id'yi integer'a çevir ve veritabanından bul
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        # Hatalı user_id (integer değilse) None döner
        return None


# ============================================
# BLUEPRINT'LERI KAYDETME
# ============================================

# Tüm Blueprint'leri Flask uygulamasına kaydet
# Blueprint'ler, URL route'larını grup halinde organize etmeyi sağlar

# Kimlik Doğrulama (Login, Logout, Register)
app.register_blueprint(auth_bp)

# Ders Yönetimi
app.register_blueprint(ders_bp)

# Derslik Yönetimi
app.register_blueprint(derslik_bp)

# Sınav Programı Görüntüleme
app.register_blueprint(sinav_bp)

# Otomatik Sınav Planlama
app.register_blueprint(planlama_bp)

# Rapor Oluşturma (PDF, Excel)
app.register_blueprint(rapor_bp)

# Admin Paneli
app.register_blueprint(admin_bp)

# Öğrenci İşlemleri
app.register_blueprint(ogrenci_bp)

# Öğretim Üyesi İşlemleri
from routes.ogretim_uyesi import ogretim_uyesi_bp
app.register_blueprint(ogretim_uyesi_bp)

# Özel Durum Yönetimi
app.register_blueprint(ozel_durum_bp)


# ============================================
# ANA ROUTE'LAR
# ============================================

@app.route('/kostu.png')
def serve_logo():
    """
    Logo dosyasını serve etme route'u.
    Uygulamanın kök dizinindeki kostu.png dosyasını döner.
    """
    from flask import send_file
    from os.path import join, dirname
    logo_path = join(dirname(__file__), 'kostu.png')
    return send_file(logo_path, mimetype='image/png')

@app.route('/')
def index():
    """
    Ana sayfa (root route).
    
    Kullanıcının oturum durumuna göre uygun sayfaya yönlendirir:
    - Oturum açıldıysa: Dashboard (admin) veya Sınav Programı (diğer)
    - Oturum açılmadıysa: Login sayfası
    
    Returns:
        Redirect: Uygun sayfaya yönlendirme
    """
    if current_user.is_authenticated:
        # Kullanıcı oturum açmışsa
        if current_user.is_admin():
            # Admin ise admin dashboard'una yönlendir
            return redirect('/admin')
        else:
            # Diğer kullanıcılar sınav programı sayfasına yönlendirilir
            return redirect('/sinav/program')
    
    # Oturum açılmamışsa login sayfasına yönlendir
    return redirect('/auth/login')


# ============================================
# HATA AYARLARI (ERROR HANDLERS)
# ============================================

@app.errorhandler(404)
def not_found_error(error):
    """
    404 Hata İşleyicisi - Sayfa Bulunamadı.
    
    Kullanıcı var olmayan bir URL'ye erişmeye çalışırsa
    bu fonksiyon çağrılır.
    
    Args:
        error: Flask tarafından iletilen hata nesnesi
        
    Returns:
        tuple: (HTML şablonu, HTTP durum kodu)
        
    Örnek:
        Kullanıcı /invalid/page adresine giderse
        -> templates/errors/404.html gösterilir
    """
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """
    500 Hata İşleyicisi - Sunucu Hatası.
    
    Uygulama içinde beklenmeyen bir hata oluşursa
    bu fonksiyon çağrılır.
    
    Veritabanı session'ını rollback'ler:
    - Hatalı işlemi geri alır
    - Sonraki işlemleri gerçekleştirebilir hale getirir
    
    Args:
        error: Flask tarafından iletilen hata nesnesi
        
    Returns:
        tuple: (HTML şablonu, HTTP durum kodu)
        
    Örnek:
        Veritabanı bağlantısı kesirlirse
        -> templates/errors/500.html gösterilir
    """
    # Veritabanı transaction'ını geri al (rollback)
    # Böylece hatalı veriler veritabanına yazılmaz
    db.session.rollback()
    
    # Hata sayfasını göster
    return render_template('errors/500.html'), 500


# ============================================
# YARDIMCI FONKSIYONLAR
# ============================================

def init_db():
    """
    Veritabanını başlat ve varsayılan veriler ekle.
    
    Bu fonksiyon:
    1. Tüm tabloları oluşturur (ilk çalıştırmada)
    2. Varsayılan admin kullanıcısını oluşturur
    
    Çağrıldığı Yer:
        Script doğrudan çalıştırıldığında (__main__)
        veya init_db.py scripti ile
    
    Not:
        Üretimde bu fonksiyon güvenlik nedeniyle
        manuel migration araçları (Alembic) kullanılmalı.
    """
    with app.app_context():
        # Uygulama context'inde veritabanı işlemleri yap
        # Flask'ın current_app ve current_user gibi proxy'leri kullanabirlir
        
        # Tüm tabloları oluştur
        # Eğer tablo zaten varsa hiçbir şey yapmaz
        db.create_all()
        
        # Varsayılan admin kullanıcısı oluştur (eğer yoksa)
        if not User.query.filter_by(kullanici_adi='admin').first():
            admin = User(
                kullanici_adi='admin',
                email='admin@universite.edu.tr',
                sifre='admin123',
                rol='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('✓ Varsayılan admin kullanıcısı oluşturuldu')
            print('  Kullanıcı Adı: admin')
            print('  Şifre: admin123')
            print('  NOT: Üretimde şifreyi değiştirin!')


# ============================================
# UYGULAMA BAŞLATMA
# ============================================

if __name__ == '__main__':
    """
    Uygulama doğrudan çalıştırıldığında (python app.py)
    bu blok çalışır.
    """
    
    # Veritabanını başlat
    init_db()
    
    # Flask geliştirme sunucusunu başlat
    # Parametreler:
    # - debug=True: Kodda değişiklik yapıldığında otomatik restart, hata detayları göster
    # - host='0.0.0.0': Tüm ağ arayüzlerinden erişime açık (localhost dışından da erişilsin)
    # - port=5000: Varsayılan Flask portu
    
    # UYARI: debug=True sadece GELIŞTIRME ortamında kullanılmalı!
    # Üretimde debug=False olmalı ve uygulama gunicorn, uWSGI gibi ürün sunucusuyla çalıştırılmalı
    app.run(debug=True, host='0.0.0.0', port=5000)

