"""
DECORATOR'LAR (KORUYUCU METOTLAR)
==================================
Yetkilendirme ve erişim kontrolü için decorator'lar.

Decorator Nedir?
----------------
Python'da fonksiyon/metodu öncesi/sonrası ekstra işlem yapan özel nesnedir.
Kullanımı: @decorator_adi

Flask Route'lar İçin Kullanım:
------------------------------
@app.route('/admin')
@admin_required        # Bu decorator, admin olmayan erişimi engeller
def admin_panel():
    return "Admin Paneli"

Temel İlke:
-----------
1. Authenticate (Kimsin?): Kullanıcı giriş yapmış mı?
2. Authorize (Ne yapabilirsin?): Kullanıcının yetkileri neler?

Decorator Türleri:
------------------
1. admin_required: Sadece admin kullanıcılara erişim
2. bolum_yetkilisi_required: Bölüm yetkilisi veya admin
3. hoca_required: Hoca, bölüm yetkilisi veya admin

Akış:
-----
Örnek: Kullanıcı /admin endpoint'ine gitmek istiyor
  ↓
HTTP isteği yapılır
  ↓
admin_required() decorator çalışır
  ↓
current_user.is_authenticated kontrol edilir
  ├─ Hayır → login sayfasına yönlendir
  ├─ Evet + Admin → İşleme devam et
  └─ Evet + Admin değil → Hata mesajı ve yönlendir

Güvenlik Notu:
--------------
- Decorator'lar istemci tarafında (JavaScript) değil, server tarafında çalışır
- Frontend validasyonu sadece UX iyileştirmesi içindir
- Asıl güvenlik her zaman sunucuda (backend) olmalıdır
"""

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def admin_required(f):
    """
    Sadece ADMIN kullanıcıların erişebileceği route'lar için decorator.
    
    Bu decorator uygulanmış bir route'a erişmeye çalışan:
    - Admin olmayan kullanıcılar: Engellenir, hata mesajı gösterilir
    - Oturum açmamış kullanıcılar: Login sayfasına yönlendirilir
    
    Kullanım:
    --------
    @app.route('/admin/panel')
    @admin_required
    def admin_panel():
        return "Admin Paneli"
    
    Kontrol Sırası:
    -----
    1. Kullanıcı authenticate edil mi? (is_authenticated)
    2. Kullanıcı admin mı? (is_admin())
    
    Başarısız Durumlar:
    ------------------
    - Oturum yok: /auth/login'e yönlendir
    - Oturum var, admin değil: Hata mesajı + eski sayfa
    
    Args:
        f: Korunacak fonksiyon
        
    Returns:
        function: Wrapper fonksiyonu
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ===== Oturum Kontrolü =====
        if not current_user.is_authenticated:
            # Oturum yok: Login sayfasına yönlendir
            flash('Lütfen giriş yapın!', 'info')
            return redirect(url_for('auth.login'))
        
        # ===== Admin Kontrolü =====
        if not current_user.is_admin():
            # Oturum var, fakat admin değil: Engelle
            flash('Bu sayfaya erişim yetkiniz yok! Sadece admin erişebilir.', 'error')
            return redirect(url_for('auth.login'))
        
        # ===== Tüm Kontroller Başarılı =====
        # Asıl fonksiyonu çalıştır
        return f(*args, **kwargs)
    
    return decorated_function


def bolum_yetkilisi_required(f):
    """
    Bölüm Yetkilisi veya ADMIN kullanıcıların erişebileceği route'lar için decorator.
    
    Kullanım Alanları:
    ------------------
    - Ders yönetimi
    - Bölüm bilgileri güncelleme
    - Kendi bölümüne ait raporlar
    
    İzin Verilen Roller:
    -------------------
    1. Admin: Her şeye erişir
    2. Bölüm Yetkilisi: Kendi bölümünü yönetir
    
    Engellenen Roller:
    -----------------
    1. Hoca
    2. Öğrenci
    3. Oturum açmayan kullanıcılar
    
    Kullanım:
    --------
    @app.route('/ders/ekle')
    @bolum_yetkilisi_required
    def ders_ekle():
        return "Yeni Ders Ekleme Formu"
    
    Kontrol Sırası:
    -----
    1. Kullanıcı authenticate edil mi?
    2. Kullanıcı bölüm yetkilisi veya admin mi?
    
    Args:
        f: Korunacak fonksiyon
        
    Returns:
        function: Wrapper fonksiyonu
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ===== Oturum Kontrolü =====
        if not current_user.is_authenticated:
            # Oturum yok: Login sayfasına yönlendir
            flash('Lütfen giriş yapın!', 'info')
            return redirect(url_for('auth.login'))
        
        # ===== Rol Kontrolü =====
        # is_bolum_yetkilisi() veya is_admin() true döndürmelidir
        if not (current_user.is_bolum_yetkilisi() or current_user.is_admin()):
            # İzin verilen rol değil: Engelle
            flash('Bu sayfaya erişim yetkiniz yok! Bölüm Yetkilisi olmalısınız.', 'error')
            return redirect(url_for('sinav.program'))
        
        # ===== Tüm Kontroller Başarılı =====
        return f(*args, **kwargs)
    
    return decorated_function


def hoca_required(f):
    """
    Hoca, Bölüm Yetkilisi veya ADMIN kullanıcıların erişebileceği route'lar için decorator.
    
    Kullanım Alanları:
    ------------------
    - Sınav programını görüntüleme
    - Kendi derslerinin sınav saatlerini kontrol etme
    - Öğrenci sonuçlarını görüntüleme
    
    İzin Verilen Roller:
    -------------------
    1. Admin: Tüm programı görebilir
    2. Bölüm Yetkilisi: Kendi bölümü görebilir
    3. Hoca: Kendi derslerini görebilir
    
    Engellenen Roller:
    -----------------
    1. Öğrenci (bazı sistem ayarlarına göre izin verilebilir)
    2. Oturum açmayan kullanıcılar
    
    Kullanım:
    --------
    @app.route('/sinav/program')
    @hoca_required
    def sinav_programi():
        return "Sınav Programı"
    
    Kontrol Sırası:
    -----
    1. Kullanıcı authenticate edil mi?
    2. Kullanıcı hoca/bölüm yetkilisi/admin mi?
    
    Args:
        f: Korunacak fonksiyon
        
    Returns:
        function: Wrapper fonksiyonu
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ===== Oturum Kontrolü =====
        if not current_user.is_authenticated:
            # Oturum yok: Login sayfasına yönlendir
            flash('Lütfen giriş yapın!', 'info')
            return redirect(url_for('auth.login'))
        
        # ===== Rol Kontrolü =====
        # Hoca, bölüm yetkilisi veya admin olmalı
        if not (current_user.is_hoca() or current_user.is_bolum_yetkilisi() or current_user.is_admin()):
            # İzin verilen rol değil: Engelle
            flash('Bu sayfaya erişim yetkiniz yok! Hoca olmalısınız.', 'error')
            return redirect(url_for('sinav.program'))
        
        # ===== Tüm Kontroller Başarılı =====
        return f(*args, **kwargs)
    
    return decorated_function

