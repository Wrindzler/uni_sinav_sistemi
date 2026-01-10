"""
ADMİN YÖNETİM ROUTE'LARI
=========================
Admin paneli işlemleri.

Sadece admin kullanıcılar erişebilir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import inspect
from models.database import db
from models.user import User
from models.fakulte import Fakulte
from models.bolum import Bolum
from models.ogretim_uyesi import OgretimUyesi
from models.ders import Ders
from models.derslik import Derslik
from models.sinav import Sinav
from models.ogrenci import Ogrenci
from models.ogrenci_ders import OgrenciDers
from models.ozel_durum import OzelDurum
from utils.decorators import admin_required

# Blueprint oluştur
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """
    Admin ana sayfası (dashboard).
    
    Sistem istatistiklerini gösterir.
    """
    # İstatistikler
    istatistikler = {
        'toplam_kullanici': User.query.count(),
        'toplam_fakulte': Fakulte.query.count(),
        'toplam_bolum': Bolum.query.count(),
        'toplam_ders': Ders.query.filter_by(aktif=True).count(),
        'toplam_ogretim_uyesi': OgretimUyesi.query.count(),
        'toplam_derslik': Derslik.query.filter_by(sinav_icin_uygun=True).count(),
        'toplam_sinav': Sinav.query.filter_by(durum='planlandi').count()
    }
    
    return render_template('admin/dashboard.html', istatistikler=istatistikler)


@admin_bp.route('/kullanicilar')
@login_required
@admin_required
def kullanicilar():
    """
    Kullanıcı listesi sayfası.
    
    Tüm kullanıcıları listeler.
    """
    kullanicilar = User.query.all()
    return render_template('admin/kullanicilar.html', kullanicilar=kullanicilar)


@admin_bp.route('/fakulteler', methods=['GET', 'POST'])
@login_required
@admin_required
def fakulteler():
    """
    Fakülte yönetimi sayfası.

    Fakülteleri listeler ve yönetim işlemleri yapar.
    """
    if request.method == 'POST':
        action = request.form.get('action', 'fakulte_ekle')

        # FAKÜLTE EKLEME
        if action == 'fakulte_ekle':
            try:
                # Yeni fakülte ekle
                ad = request.form.get('ad')
                kod = request.form.get('kod')
                aciklama = request.form.get('aciklama')

                # Boş veya sadece boşluk içeren değerleri temizle
                ad = ad.strip() if ad else None
                kod = kod.strip() if kod else None
                aciklama = aciklama.strip() if aciklama else None

                # Validasyon
                if not ad:
                    flash('Fakülte adı boş bırakılamaz!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('admin/fakulteler.html', fakulteler=fakulteler)

                # Aynı isimde fakülte var mı kontrol et
                existing = Fakulte.query.filter_by(ad=ad).first()
                if existing:
                    flash(f'"{ad}" isimli fakülte zaten mevcut!', 'warning')
                    fakulteler = Fakulte.query.all()
                    return render_template('admin/fakulteler.html', fakulteler=fakulteler)

                # Kod girilmişse benzersizlik kontrolü
                if kod:
                    existing_kod = Fakulte.query.filter_by(kod=kod).first()
                    if existing_kod:
                        flash(f'"{kod}" kodlu fakülte zaten mevcut!', 'warning')
                        fakulteler = Fakulte.query.all()
                        return render_template('admin/fakulteler.html', fakulteler=fakulteler)

                fakulte = Fakulte(ad=ad, kod=kod, aciklama=aciklama)
                db.session.add(fakulte)
                db.session.commit()

                flash(f'"{ad}" fakültesi başarıyla eklendi!', 'success')
                return redirect(url_for('admin.fakulteler'))

            except Exception as e:
                db.session.rollback()
                flash(f'Fakülte eklenirken hata oluştu: {str(e)}', 'danger')

        # BÖLÜM EKLEME
        elif action == 'bolum_ekle':
            try:
                # Bölüm bilgilerini al
                bolum_ad = request.form.get('bolum_ad')
                bolum_kod = request.form.get('bolum_kod')
                fakulte_id = request.form.get('fakulte_id')
                bolum_aciklama = request.form.get('bolum_aciklama')

                # Boş veya sadece boşluk içeren değerleri temizle
                bolum_ad = bolum_ad.strip() if bolum_ad else None
                bolum_kod = bolum_kod.strip() if bolum_kod else None
                bolum_aciklama = bolum_aciklama.strip() if bolum_aciklama else None

                # Validasyon - bölüm adı kontrolü
                if not bolum_ad:
                    flash('Bölüm adı boş bırakılamaz!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('admin/fakulteler.html', fakulteler=fakulteler)

                # Validasyon - fakülte ID kontrolü
                if not fakulte_id:
                    flash('Fakülte bilgisi eksik!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('admin/fakulteler.html', fakulteler=fakulteler)

                try:
                    fakulte_id = int(fakulte_id)
                except (ValueError, TypeError):
                    flash('Geçersiz fakülte bilgisi!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('admin/fakulteler.html', fakulteler=fakulteler)

                # Fakülte mevcut mu kontrol et
                fakulte = Fakulte.query.get(fakulte_id)
                if not fakulte:
                    flash('Seçilen fakülte bulunamadı!', 'danger')
                    fakulteler = Fakulte.query.all()
                    return render_template('admin/fakulteler.html', fakulteler=fakulteler)

                # Aynı fakültede aynı isimde bölüm var mı kontrol et
                existing = Bolum.query.filter_by(ad=bolum_ad, fakulte_id=fakulte_id).first()
                if existing:
                    flash(f'"{fakulte.ad}" fakültesinde "{bolum_ad}" isimli bölüm zaten mevcut!', 'warning')
                    fakulteler = Fakulte.query.all()
                    return render_template('admin/fakulteler.html', fakulteler=fakulteler)

                # Bölüm ekle
                bolum = Bolum(ad=bolum_ad, kod=bolum_kod, fakulte_id=fakulte_id, aciklama=bolum_aciklama)
                db.session.add(bolum)
                db.session.commit()

                flash(f'"{bolum_ad}" bölümü "{fakulte.ad}" fakültesine başarıyla eklendi!', 'success')
                return redirect(url_for('admin.fakulteler'))

            except Exception as e:
                db.session.rollback()
                flash(f'Bölüm eklenirken hata oluştu: {str(e)}', 'danger')

    fakulteler = Fakulte.query.all()
    return render_template('admin/fakulteler.html', fakulteler=fakulteler)


@admin_bp.route('/ogretim_uyeleri', methods=['GET', 'POST'])
@login_required
@admin_required
def ogretim_uyeleri():
    """
    Öğretim üyesi yönetimi sayfası.
    
    Öğretim üyelerini listeler ve yönetim işlemleri yapar.
    """
    if request.method == 'POST':
        try:
            # Yeni öğretim üyesi ekle
            ad = request.form.get('ad')
            soyad = request.form.get('soyad')
            email = request.form.get('email')
            bolum_ids = request.form.getlist('bolum_ids')  # Çoklu bölüm seçimi
            
            # Boş veya sadece boşluk içeren değerleri temizle
            ad = ad.strip() if ad else None
            soyad = soyad.strip() if soyad else None
            email = email.strip() if email else None
            
            # Validasyon - ad kontrolü
            if not ad:
                flash('Ad boş bırakılamaz!', 'danger')
                ogretim_uyeleri = OgretimUyesi.query.all()
                bolumler = Bolum.query.all()
                return render_template('admin/ogretim_uyeleri.html', ogretim_uyeleri=ogretim_uyeleri, bolumler=bolumler)
            
            # Validasyon - soyad kontrolü
            if not soyad:
                flash('Soyad boş bırakılamaz!', 'danger')
                ogretim_uyeleri = OgretimUyesi.query.all()
                bolumler = Bolum.query.all()
                return render_template('admin/ogretim_uyeleri.html', ogretim_uyeleri=ogretim_uyeleri, bolumler=bolumler)
            
            # Validasyon - en az bir bölüm seçilmeli
            if not bolum_ids:
                flash('En az bir bölüm seçmelisiniz!', 'danger')
                ogretim_uyeleri = OgretimUyesi.query.all()
                bolumler = Bolum.query.all()
                return render_template('admin/ogretim_uyeleri.html', ogretim_uyeleri=ogretim_uyeleri, bolumler=bolumler)
            
            # Email girilmişse benzersizlik kontrolü
            if email:
                existing_email = OgretimUyesi.query.filter_by(email=email).first()
                if existing_email:
                    flash(f'"{email}" e-posta adresi zaten kayıtlı! Lütfen farklı bir e-posta kullanın.', 'warning')
                    ogretim_uyeleri = OgretimUyesi.query.all()
                    bolumler = Bolum.query.all()
                    return render_template('admin/ogretim_uyeleri.html', ogretim_uyeleri=ogretim_uyeleri, bolumler=bolumler)
                
                # Kullanıcı tablosunda da kontrol et
                existing_user_email = User.query.filter_by(email=email).first()
                if existing_user_email:
                    flash(f'"{email}" e-posta adresi başka bir kullanıcı tarafından kullanılıyor!', 'warning')
                    ogretim_uyeleri = OgretimUyesi.query.all()
                    bolumler = Bolum.query.all()
                    return render_template('admin/ogretim_uyeleri.html', ogretim_uyeleri=ogretim_uyeleri, bolumler=bolumler)
            
            # Seçilen bölümleri al
            secilen_bolumler = Bolum.query.filter(Bolum.id.in_([int(b) for b in bolum_ids])).all()
            
            # İlk bölümü ana bölüm olarak al
            ana_bolum = secilen_bolumler[0] if secilen_bolumler else None
            fakulte_id = ana_bolum.fakulte_id if ana_bolum else None
            
            ogretim_uyesi = OgretimUyesi(
                ad=ad,
                soyad=soyad,
                email=email,
                fakulte_id=fakulte_id,
                bolum_id=ana_bolum.id if ana_bolum else None
            )
            db.session.add(ogretim_uyesi)
            db.session.flush()  # ID'yi almak için
            
            # Çoklu bölümleri ekle
            for bolum in secilen_bolumler:
                ogretim_uyesi.bolumler.append(bolum)
            
            db.session.commit()
            
            bolum_adlari = ', '.join([b.ad for b in secilen_bolumler])
            flash(f'"{ad} {soyad}" öğretim üyesi başarıyla eklendi! Bölümler: {bolum_adlari}', 'success')
            return redirect(url_for('admin.ogretim_uyeleri'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Öğretim üyesi eklenirken hata oluştu: {str(e)}', 'danger')
    
    ogretim_uyeleri = OgretimUyesi.query.all()
    bolumler = Bolum.query.all()
    return render_template('admin/ogretim_uyeleri.html', ogretim_uyeleri=ogretim_uyeleri, bolumler=bolumler)


@admin_bp.route('/ogretim_uyesi/bolum-guncelle/<int:ogretim_uyesi_id>', methods=['POST'])
@login_required
@admin_required
def ogretim_uyesi_bolum_guncelle(ogretim_uyesi_id):
    """
    Öğretim üyesinin bölümlerini güncelle.
    
    Birden fazla bölüm seçilebilir.
    """
    try:
        ogretim_uyesi = OgretimUyesi.query.get(ogretim_uyesi_id)
        if not ogretim_uyesi:
            flash('Öğretim üyesi bulunamadı!', 'danger')
            return redirect(url_for('admin.ogretim_uyeleri'))
        
        # Seçilen bölüm ID'lerini al
        bolum_ids = request.form.getlist('bolum_ids')
        
        if not bolum_ids:
            flash('En az bir bölüm seçmelisiniz!', 'warning')
            return redirect(url_for('admin.ogretim_uyeleri'))
        
        # Bölümleri bul
        yeni_bolumler = Bolum.query.filter(Bolum.id.in_([int(b) for b in bolum_ids])).all()
        
        if not yeni_bolumler:
            flash('Geçerli bölüm bulunamadı!', 'danger')
            return redirect(url_for('admin.ogretim_uyeleri'))
        
        # Mevcut bölümleri temizle
        for bolum in list(ogretim_uyesi.bolumler):
            ogretim_uyesi.bolumler.remove(bolum)
        
        # Yeni bölümleri ekle
        for bolum in yeni_bolumler:
            ogretim_uyesi.bolumler.append(bolum)
        
        # Ana bölümü ilk seçilen bölüm yap
        ogretim_uyesi.bolum_id = yeni_bolumler[0].id
        ogretim_uyesi.fakulte_id = yeni_bolumler[0].fakulte_id
        
        db.session.commit()
        
        bolum_adlari = ', '.join([b.ad for b in yeni_bolumler])
        flash(f'{ogretim_uyesi.tam_ad} için bölümler güncellendi: {bolum_adlari}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Bölümler güncellenirken hata oluştu: {str(e)}', 'danger')
    
    return redirect(url_for('admin.ogretim_uyeleri'))


# ============================================
# SİLME İŞLEMLERİ
# ============================================

@admin_bp.route('/kullanici/sil/<int:kullanici_id>', methods=['POST'])
@login_required
@admin_required
def kullanici_sil(kullanici_id):
    """
    Kullanıcı silme işlemi.

    Admin kullanıcısı silinemez.
    Eğer kullanıcı bir öğretim üyesi veya öğrenci ise, onları da sil.
    """
    try:
        kullanici = User.query.get(kullanici_id)
        if not kullanici:
            flash('Kullanıcı bulunamadı!', 'danger')
            return redirect(url_for('admin.kullanicilar'))

        # Admin kullanıcısı silinemez
        if kullanici.kullanici_adi == 'admin':
            flash('Admin kullanıcısı silinemez!', 'warning')
            return redirect(url_for('admin.kullanicilar'))

        kullanici_adi = kullanici.kullanici_adi
        
        # Eğer kullanıcı bir öğretim üyesi ise, öğretim üyesi kaydını da sil
        if kullanici.ogretim_uyesi_id:
            ogretim_uyesi = OgretimUyesi.query.get(kullanici.ogretim_uyesi_id)
            if ogretim_uyesi:
                # Öğretim üyesinin dersi var mı kontrol et
                ders_sayisi = Ders.query.filter_by(ogretim_uyesi_id=ogretim_uyesi.id).count()
                if ders_sayisi > 0:
                    flash(f'Bu kullanıcının {ders_sayisi} dersi var! Önce dersleri başka bir öğretim üyesine atayın veya silin.', 'warning')
                    return redirect(url_for('admin.kullanicilar'))
                
                # Dersi yoksa öğretim üyesini de sil
                db.session.delete(ogretim_uyesi)
        
        # Eğer kullanıcı bir öğrenci ise, öğrenci kaydını da sil
        if kullanici.ogrenci_id:
            from models.ogrenci import Ogrenci
            ogrenci = Ogrenci.query.get(kullanici.ogrenci_id)
            if ogrenci:
                db.session.delete(ogrenci)
        
        # Kullanıcıyı sil
        db.session.delete(kullanici)
        db.session.commit()

        flash(f'"{kullanici_adi}" kullanıcısı başarıyla silindi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Kullanıcı silinirken hata oluştu: {str(e)}', 'danger')

    return redirect(url_for('admin.kullanicilar'))


@admin_bp.route('/fakulte/sil/<int:fakulte_id>', methods=['POST'])
@login_required
@admin_required
def fakulte_sil(fakulte_id):
    """
    Fakülte silme işlemi.

    Cascade delete sayesinde bağlı bölümler de silinir.
    """
    try:
        fakulte = Fakulte.query.get(fakulte_id)
        if not fakulte:
            flash('Fakülte bulunamadı!', 'danger')
            return redirect(url_for('admin.fakulteler'))

        fakulte_ad = fakulte.ad
        db.session.delete(fakulte)
        db.session.commit()

        flash(f'"{fakulte_ad}" fakültesi ve tüm bölümleri başarıyla silindi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fakülte silinirken hata oluştu: {str(e)}', 'danger')

    return redirect(url_for('admin.fakulteler'))


@admin_bp.route('/bolum/sil/<int:bolum_id>', methods=['POST'])
@login_required
@admin_required
def bolum_sil(bolum_id):
    """
    Bölüm silme işlemi.

    Cascade delete sayesinde bağlı dersler de silinir.
    """
    try:
        bolum = Bolum.query.get(bolum_id)
        if not bolum:
            flash('Bölüm bulunamadı!', 'danger')
            return redirect(url_for('admin.fakulteler'))

        bolum_ad = bolum.ad
        db.session.delete(bolum)
        db.session.commit()

        flash(f'"{bolum_ad}" bölümü başarıyla silindi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Bölüm silinirken hata oluştu: {str(e)}', 'danger')

    return redirect(url_for('admin.fakulteler'))


@admin_bp.route('/ogretim_uyesi/sil/<int:ogretim_uyesi_id>', methods=['POST'])
@login_required
@admin_required
def ogretim_uyesi_sil(ogretim_uyesi_id):
    """
    Öğretim üyesi silme işlemi.
    
    İlişkili kullanıcı hesabını ve öğretim üyesini siler.
    """
    try:
        ogretim_uyesi = OgretimUyesi.query.get(ogretim_uyesi_id)
        if not ogretim_uyesi:
            flash('Öğretim üyesi bulunamadı!', 'danger')
            return redirect(url_for('admin.ogretim_uyeleri'))
        
        ogretim_uyesi_ad = ogretim_uyesi.tam_ad
        
        # Bu öğretim üyesinin verdiği dersleri kontrol et
        dersler = Ders.query.filter_by(ogretim_uyesi_id=ogretim_uyesi_id).count()
        if dersler > 0:
            flash(f'Bu öğretim üyesinin {dersler} dersi var! Önce dersleri başka bir öğretim üyesine atayın.', 'warning')
            return redirect(url_for('admin.ogretim_uyeleri'))
        
        # İlişkili kullanıcı hesabı varsa onu da sil
        user = User.query.filter_by(ogretim_uyesi_id=ogretim_uyesi_id).first()
        if user:
            db.session.delete(user)
        
        # Öğretim üyesini sil
        db.session.delete(ogretim_uyesi)
        db.session.commit()
        
        flash(f'"{ogretim_uyesi_ad}" öğretim üyesi başarıyla silindi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Öğretim üyesi silinirken hata oluştu: {str(e)}', 'danger')
    
    return redirect(url_for('admin.ogretim_uyeleri'))


# ============================================
# VERİTABANI GÖRÜNTÜLEME
# ============================================

@admin_bp.route('/veritabani')
@login_required
@admin_required
def veritabani():
    """
    Veritabanı görüntüleme sayfası.
    
    Tüm tabloları ve içeriklerini görüntüler.
    Sadece admin kullanıcılar erişebilir.
    """
    # Tüm modelleri ve verilerini hazırla
    tablolar = {}
    
    # Kullanıcılar tablosu
    tablolar['Kullanıcılar'] = {
        'model': User,
        'kolonlar': ['id', 'kullanici_adi', 'email', 'rol', 'ogretim_uyesi_id', 'ogrenci_id', 'olusturulma_tarihi'],
        'veriler': User.query.all()
    }
    
    # Fakülteler tablosu
    tablolar['Fakülteler'] = {
        'model': Fakulte,
        'kolonlar': ['id', 'ad', 'kod', 'aciklama'],
        'veriler': Fakulte.query.all()
    }
    
    # Bölümler tablosu
    tablolar['Bölümler'] = {
        'model': Bolum,
        'kolonlar': ['id', 'ad', 'kod', 'fakulte_id', 'aciklama'],
        'veriler': Bolum.query.all()
    }
    
    # Öğretim Üyeleri tablosu
    tablolar['Öğretim Üyeleri'] = {
        'model': OgretimUyesi,
        'kolonlar': ['id', 'ad', 'soyad', 'email', 'unvan', 'fakulte_id', 'bolum_id'],
        'veriler': OgretimUyesi.query.all()
    }
    
    # Dersler tablosu
    tablolar['Dersler'] = {
        'model': Ders,
        'kolonlar': ['id', 'kod', 'ad', 'bolum_id', 'ogretim_uyesi_id', 'donem', 'kredi', 'sinif', 'aktif'],
        'veriler': Ders.query.all()
    }
    
    # Derslikler tablosu
    tablolar['Derslikler'] = {
        'model': Derslik,
        'kolonlar': ['id', 'ad', 'bina', 'kapasite', 'sinav_icin_uygun', 'aktif'],
        'veriler': Derslik.query.all()
    }
    
    # Öğrenciler tablosu
    tablolar['Öğrenciler'] = {
        'model': Ogrenci,
        'kolonlar': ['id', 'ogrenci_no', 'ad', 'soyad', 'email', 'bolum_id', 'sinif', 'aktif'],
        'veriler': Ogrenci.query.all()
    }
    
    # Öğrenci-Ders tablosu
    tablolar['Öğrenci-Ders Kayıtları'] = {
        'model': OgrenciDers,
        'kolonlar': ['id', 'ogrenci_id', 'ders_id', 'kayit_tarihi'],
        'veriler': OgrenciDers.query.all()
    }
    
    # Sınavlar tablosu
    tablolar['Sınavlar'] = {
        'model': Sinav,
        'kolonlar': ['id', 'ders_id', 'derslik_id', 'tarih', 'baslangic_saati', 'bitis_saati', 'sinav_turu', 'durum'],
        'veriler': Sinav.query.all()
    }
    
    # Özel Durumlar tablosu
    tablolar['Özel Durumlar'] = {
        'model': OzelDurum,
        'kolonlar': ['id', 'ders_id', 'derslik_id', 'ogretim_uyesi_id', 'gun', 'baslangic_saati', 'bitis_saati', 'aciklama', 'tip'],
        'veriler': OzelDurum.query.all()
    }
    
    return render_template('admin/veritabani.html', tablolar=tablolar)

