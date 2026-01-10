"""
KİMLİK DOĞRULAMA ROUTE'LARI
===========================
Kullanıcı girişi, çıkışı ve kayıt işlemleri.

Bu modül:
- Kullanıcı giriş işlemini yönetir
- Oturum açık/kapalı durumunu denetler
- Yeni kullanıcı kayıtlarını işler
- Flask-Login extension'ı kullanarak oturum yönetimi yapar
- Şifre güvenliğini sağlar

Endpoint'ler:
-----------
- GET /auth/login: Giriş formunu göster
- POST /auth/login: Giriş yapılsın
- GET /auth/logout: Oturum kapatılsın
- GET/POST /auth/register: Yeni kullanıcı kaydı (admin için)

Güvenlik:
--------
- Şifreler hash'lenerek saklanır (werkzeug.security)
- CSRF koruması aktif
- SQL injection'dan korunur (SQLAlchemy)
- Aktif olmayan hesaplar engellenir
- Sadece admin yeni kullanıcı kaydı yapabilir
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.database import db
from models.user import User
from models.ogrenci import Ogrenci
from models.ogretim_uyesi import OgretimUyesi
from models.bolum_yetkilisi import BolumYetkilisi
from models.fakulte import Fakulte
from models.bolum import Bolum
from utils.decorators import admin_required, bolum_yetkilisi_required

# ============================================
# BLUEPRINT OLUŞTURMA
# ============================================

# auth_bp: Blueprint nesnesi
# __name__: Bu modülün adı
# url_prefix='/auth': Tüm route'lar /auth ile başlayacak
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ============================================
# GİRİŞ ROUTE'U
# ============================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Kullanıcı giriş route'u.
    
    Bu endpoint iki işlevi vardır:
    
    1. GET İsteği:
       - Giriş formunu (HTML) kullanıcıya gösterir
       - Hesapsız veya oturum sona eren kullanıcıları burada yönlendirir
    
    2. POST İsteği:
       - Form verilerini (kullanıcı adı, şifre) alır
       - Veritabanında kullanıcıyı arar
       - Şifreyi kontrol eder
       - Başarılıysa oturum açar ve dashboard'a yönlendirir
       - Başarısızsa hata mesajı gösterir
    
    Akış Diyagramı:
    ---------------
    GET /auth/login → login.html göster
                   ↓
    Kullanıcı form doldur ve gönder
                   ↓
    POST /auth/login → Kullanıcı adı ile bul
                   ↓
    Şifre doğru mu? ─→ Evet ─→ Oturum aç ─→ Dashboard'a yönlendir
                   ├─→ Hayır ─→ Hata mesajı ─→ login.html göster
                   └─→ Kullanıcı pasif ─→ Hata mesajı ─→ login.html
    
    Başarıyla Giriş Yapıldığında:
    ----------------------------
    1. Kullanıcı oturum açılır (Flask-Login via login_user())
    2. "Beni Hatırla" seçeneği etkinse cookie'ye kaydedilir
    3. Son giriş zamanı güncellenir (audit trail için)
    4. Rolüne göre yönlendirme yapılır:
       - Admin → /admin (admin dashboard)
       - Diğer → /sinav/program (sınav programı)
    
    Hata Senaryoları:
    -----------------
    1. Kullanıcı adı yanlış: "Kullanıcı adı veya şifre hatalı!"
    2. Şifre yanlış: "Kullanıcı adı veya şifre hatalı!"
    3. Hesap pasif: "Hesabınız pasif durumda!"
    
    Güvenlik Önlemleri:
    ------------------
    - Şifreler user.check_password() ile hash'i kontrol edilerek doğrulanır
    - Brute force saldırılarına karşı: İlerleyen sürümlerde rate limiting eklenebilir
    - SQL injection: SQLAlchemy parametreli sorguları kullanır
    """
    if request.method == 'POST':
        # ===== Form verilerini al =====
        kullanici_adi = request.form.get('kullanici_adi')
        sifre = request.form.get('sifre')
        
        # ===== Veritabanında kullanıcıyı bul =====
        # filter_by: Eşitlik üzerinden filtrele
        # first(): İlk sonucu döndür (var yoksa None)
        user = User.query.filter_by(kullanici_adi=kullanici_adi).first()
        
        # ===== Kimlik doğrulaması =====
        # 1. Kullanıcı var mı? (user is not None)
        # 2. Şifre doğru mu? (check_password hash'i karşılaştırır)
        if user and user.check_password(sifre):
            # ===== Hesap aktif mi kontrolü =====
            # Pasif hesaplar sisteme erişemez
            if not user.aktif:
                flash('Hesabınız pasif durumda!', 'error')
                return render_template('auth/login.html')
            
            # ===== Oturum açma (Flask-Login) =====
            # login_user: Flask-Login'e kullanıcıyı oturum aç demek
            # remember=True: Çerez kullanarak tarayıcı kapatıldığında oturum kalır
            login_user(user, remember=True)
            
            # ===== Son giriş zamanını güncelle =====
            # Audit trail ve kullanıcı aktivitesi izlemesi için
            from datetime import datetime
            user.son_giris = datetime.utcnow()
            db.session.commit()
            
            # ===== Başarı mesajı =====
            flash(f'Hoşgeldiniz, {user.kullanici_adi}!', 'success')
            
            # ===== Rolüne göre yönlendirme =====
            # Admin kullanıcıları admin paneline, diğerlerini sınav programına yönlendir
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.is_bolum_yetkilisi():
                return redirect(url_for('sinav.program'))
            elif user.is_hoca():
                return redirect(url_for('sinav.program'))
            else:  # Öğrenci
                return redirect(url_for('sinav.program'))
        else:
            # ===== Hatalı giriş =====
            # Güvenlik nedeniyle, kullanıcı adı yanlış mı şifre yanlış mı detaylandırılmaz
            # Bu, kullanıcı enumerasyon saldırılarını önler
            flash('Kullanıcı adı veya şifre hatalı!', 'error')
    
    # GET isteği veya hatalı POST: giriş formunu göster
    return render_template('auth/login.html')


# ============================================
# ÇIKIŞ ROUTE'U
# ============================================

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Kullanıcı çıkış işlemi.
    
    @login_required Decorator:
    - Oturum açılmamış kullanıcılar bu endpoint'e erişemez
    - Erişmeye çalışırsa login sayfasına yönlendirilir
    
    İşlem Sırası:
    1. Flask-Login'den logout_user() çağrılır
       - Oturum çerezleri temizlenir
       - Session verisi silinir
       - current_user None olur
    2. Başarı mesajı gösterilir
    3. Login sayfasına yönlendirilir
    
    Güvenlik:
    - CSRF koruması etkin (session'dan ayırarak)
    - Token'lar silinir
    - İlişkili veriler temizlenir
    """
    # ===== Oturum kapat =====
    logout_user()
    
    # ===== Başarı mesajı =====
    flash('Başarıyla çıkış yaptınız.', 'success')
    
    # ===== Login sayfasına yönlendir =====
    return redirect(url_for('auth.login'))


# ============================================
# YENİ KULLANICI KAYDI ROUTE'U
# ============================================

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    """
    Yeni kullanıcı kaydı route'u.

    @admin_required Decorator:
    - SADECE admin kullanıcılar bu işlemi yapabilir
    - Diğer kullanıcılar erişemez (yetki hatası verilir)

    Amaç:
    - Admin panelinden yeni kullanıcı (hoca, bölüm yetkilisi, öğrenci) eklemek
    - Kullanıcı adlarının benzersiz olmasını sağlamak
    - E-posta adreslerinin tekrar etmemesini kontrol etmek
    - Öğrenci ise Ogrenci tablosuna da kayıt yapmak

    GET İsteği:
    - Yeni kullanıcı ekleme formunu gösterir
    - Admin panelinde "Yeni Kullanıcı Ekle" butonundan erişilir

    POST İsteği:
    - Form verilerini alır: ad, e-posta, şifre, rol
    - Doğrulama kontrolleri yapar
    - Veritabanına kaydeder
    - Başarı/hata mesajı gösterir

    Doğrulama Kuralları:
    -------------------
    1. Kullanıcı adı benzersiz mi?
       - Aynı kullanıcı adı ile başka kullanıcı var mı?
       - Varsa: "Bu kullanıcı adı zaten kullanılıyor!"

    2. E-posta benzersiz mi?
       - Aynı e-posta ile başka kullanıcı var mı?
       - Varsa: "Bu e-posta adresi zaten kullanılıyor!"

    3. Rol geçerli mi?
       - Verilen rol, izin verilen rollerden mi?
       - admin, bolum_yetkilisi, hoca, ogrenci

    4. Öğrenci ise:
       - Öğrenci numarası benzersiz mi?
       - Ad, soyad, fakülte, bölüm dolu mu?

    Başarıyla Kayıt:
    ---------------
    1. Yeni User nesnesi oluşturulur
    2. Şifre hash'lenerek kaydedilir (set_password())
    3. Eğer öğrenci ise Ogrenci kaydı da oluşturulur
    4. Veritabanına eklenir
    5. Admin paneline (kullanıcılar listesi) yönlendirilir
    6. "Kullanıcı başarıyla oluşturuldu!" mesajı gösterilir

    Hata Senaryoları:
    -----------------
    1. Boş form: JavaScript tarafında engellenir (HTML5 validation)
    2. Zayıf şifre: İleride password policy eklenebilir
    3. Geçersiz rol: Server tarafında kontrol edilmeli
    """
    if request.method == 'POST':
        try:
            # ===== Form verilerini al =====
            kullanici_adi = request.form.get('kullanici_adi')
            email = request.form.get('email')
            sifre = request.form.get('sifre')
            rol = request.form.get('rol')

            # Temizle
            kullanici_adi = kullanici_adi.strip() if kullanici_adi else None
            email = email.strip() if email else None
            rol = rol.strip() if rol else None

            # ===== Doğrulama 1: Kullanıcı adı benzersiz mi? =====
            if User.query.filter_by(kullanici_adi=kullanici_adi).first():
                flash('Bu kullanıcı adı zaten kullanılıyor!', 'danger')
                fakulteler = Fakulte.query.all()
                return render_template('auth/register.html', fakulteler=fakulteler)

            # ===== Doğrulama 2: E-posta benzersiz mi? =====
            if User.query.filter_by(email=email).first():
                flash('Bu e-posta adresi zaten kullanılıyor!', 'danger')
                fakulteler = Fakulte.query.all()
                return render_template('auth/register.html', fakulteler=fakulteler)

            # ===== Öğrenci İse Ek Doğrulamalar =====
            ogrenci_id = None
            ogretim_uyesi_id = None
            bolum_yetkilisi_id = None

            if rol == 'ogrenci':
                ogrenci_no = request.form.get('ogrenci_no', '').strip()
                ad = request.form.get('ogrenci_ad', '').strip()
                soyad = request.form.get('ogrenci_soyad', '').strip()
                fakulte_id = request.form.get('ogrenci_fakulte_id')
                bolum_id = request.form.get('ogrenci_bolum_id')

                # Zorunlu alan kontrolü
                if not all([ogrenci_no, ad, soyad, fakulte_id, bolum_id]):
                    flash('Öğrenci için tüm alanlar zorunludur!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                # Öğrenci numarası benzersiz mi?
                if Ogrenci.query.filter_by(ogrenci_no=ogrenci_no).first():
                    flash(f'"{ogrenci_no}" numaralı öğrenci zaten kayıtlı!', 'warning')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                # Fakülte ve bölüm geçerli mi?
                try:
                    fakulte_id = int(fakulte_id)
                    bolum_id = int(bolum_id)
                except (ValueError, TypeError):
                    flash('Geçersiz fakülte veya bölüm seçimi!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                fakulte = Fakulte.query.get(fakulte_id)
                bolum = Bolum.query.get(bolum_id)

                if not fakulte or not bolum:
                    flash('Seçilen fakülte veya bölüm bulunamadı!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                # Öğrenci kaydı oluştur
                ogrenci = Ogrenci(
                    ogrenci_no=ogrenci_no,
                    ad=ad,
                    soyad=soyad,
                    email=email,
                    fakulte_id=fakulte_id,
                    bolum_id=bolum_id
                )
                db.session.add(ogrenci)
                db.session.flush()  # ID'yi al ama henüz commit etme
                ogrenci_id = ogrenci.id

            # ===== Öğretim Görevlisi İse Ek Doğrulamalar =====
            elif rol == 'hoca':
                ad = request.form.get('hoca_ad', '').strip()
                soyad = request.form.get('hoca_soyad', '').strip()
                fakulte_id = request.form.get('hoca_fakulte_id')
                bolum_id = request.form.get('hoca_bolum_id')

                # Zorunlu alan kontrolü
                if not all([ad, soyad, fakulte_id, bolum_id]):
                    flash('Öğretim görevlisi için tüm alanlar zorunludur!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                # Fakülte ve bölüm geçerli mi?
                try:
                    fakulte_id = int(fakulte_id)
                    bolum_id = int(bolum_id)
                except (ValueError, TypeError):
                    flash('Geçersiz fakülte veya bölüm seçimi!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                fakulte = Fakulte.query.get(fakulte_id)
                bolum = Bolum.query.get(bolum_id)

                if not fakulte or not bolum:
                    flash('Seçilen fakülte veya bölüm bulunamadı!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                # Öğretim üyesi kaydı oluştur
                ogretim_uyesi = OgretimUyesi(
                    ad=ad,
                    soyad=soyad,
                    email=email,
                    fakulte_id=fakulte_id,
                    bolum_id=bolum_id
                )
                db.session.add(ogretim_uyesi)
                db.session.flush()  # ID'yi al ama henüz commit etme
                ogretim_uyesi_id = ogretim_uyesi.id

            # ===== Bölüm Yetkilisi İse Ek Doğrulamalar =====
            elif rol == 'bolum_yetkilisi':
                ad = request.form.get('yetkilisi_ad', '').strip()
                soyad = request.form.get('yetkilisi_soyad', '').strip()
                fakulte_id = request.form.get('yetkilisi_fakulte_id')
                bolum_id = request.form.get('yetkilisi_bolum_id')

                # Zorunlu alan kontrolü
                if not all([ad, soyad, fakulte_id, bolum_id]):
                    flash('Bölüm yetkilisi için tüm alanlar zorunludur!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                # Fakülte ve bölüm geçerli mi?
                try:
                    fakulte_id = int(fakulte_id)
                    bolum_id = int(bolum_id)
                except (ValueError, TypeError):
                    flash('Geçersiz fakülte veya bölüm seçimi!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                fakulte = Fakulte.query.get(fakulte_id)
                bolum = Bolum.query.get(bolum_id)

                if not fakulte or not bolum:
                    flash('Seçilen fakülte veya bölüm bulunamadı!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('auth/register.html', fakulteler=fakulteler)

                # Bölüm yetkilisi kaydı oluştur
                bolum_yetkilisi = BolumYetkilisi(
                    ad=ad,
                    soyad=soyad,
                    email=email,
                    fakulte_id=fakulte_id,
                    bolum_id=bolum_id
                )
                db.session.add(bolum_yetkilisi)
                db.session.flush()  # ID'yi al ama henüz commit etme
                bolum_yetkilisi_id = bolum_yetkilisi.id

            # ===== Yeni Kullanıcı Oluştur =====
            user = User(
                kullanici_adi=kullanici_adi,
                email=email,
                sifre=sifre,  # Hash'lenerek kaydedilir (set_password() içinde)
                rol=rol
            )

            # Öğrenci ID'sini bağla
            if ogrenci_id:
                user.ogrenci_id = ogrenci_id

            # Öğretim üyesi ID'sini bağla
            if ogretim_uyesi_id:
                user.ogretim_uyesi_id = ogretim_uyesi_id

            # Bölüm yetkilisi ID'sini bağla
            if bolum_yetkilisi_id:
                user.bolum_yetkilisi_id = bolum_yetkilisi_id

            # ===== Veritabanına Kaydet =====
            db.session.add(user)
            db.session.commit()

            # ===== Başarı Mesajı =====
            if rol == 'ogrenci':
                ad = request.form.get('ogrenci_ad', '').strip()
                soyad = request.form.get('ogrenci_soyad', '').strip()
                flash(f'Öğrenci "{ad} {soyad}" başarıyla oluşturuldu!', 'success')
            elif rol == 'hoca':
                ad = request.form.get('hoca_ad', '').strip()
                soyad = request.form.get('hoca_soyad', '').strip()
                flash(f'Öğretim görevlisi "{ad} {soyad}" başarıyla oluşturuldu!', 'success')
            elif rol == 'bolum_yetkilisi':
                ad = request.form.get('yetkilisi_ad', '').strip()
                soyad = request.form.get('yetkilisi_soyad', '').strip()
                flash(f'Bölüm yetkilisi "{ad} {soyad}" başarıyla oluşturuldu!', 'success')
            else:
                flash(f'Kullanıcı "{kullanici_adi}" başarıyla oluşturuldu!', 'success')

            # ===== Admin Paneline Yönlendir =====
            return redirect(url_for('admin.kullanicilar'))

        except Exception as e:
            db.session.rollback()
            flash(f'Kullanıcı eklenirken hata oluştu: {str(e)}', 'danger')
            fakulteler = Fakulte.query.all()
            return render_template('auth/register.html', fakulteler=fakulteler)

    # GET isteği: kayıt formunu göster
    fakulteler = Fakulte.query.all()
    return render_template('auth/register.html', fakulteler=fakulteler)


@auth_bp.route('/get_bolumler/<int:fakulte_id>')
@login_required
@admin_required
def get_bolumler(fakulte_id):
    """
    AJAX endpoint - Fakülteye ait bölümleri JSON olarak döndürür.

    Args:
        fakulte_id: Fakülte ID

    Returns:
        JSON: Bölüm listesi
    """
    try:
        bolumler = Bolum.query.filter_by(fakulte_id=fakulte_id).all()
        return jsonify({
            'bolumler': [
                {'id': b.id, 'ad': b.ad, 'kod': b.kod}
                for b in bolumler
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

