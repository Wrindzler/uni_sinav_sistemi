"""
DERSLİK YÖNETİMİ ROUTE'LARI
===========================
Derslik ekleme, silme, güncelleme işlemleri.

Sadece admin kullanıcılar derslik yönetimi yapabilir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models.database import db
from models.derslik import Derslik
from utils.decorators import admin_required

# Blueprint oluştur
derslik_bp = Blueprint('derslik', __name__, url_prefix='/derslik')


@derslik_bp.route('/')
@login_required
@admin_required
def liste():
    """
    Derslik listesi sayfası.
    
    Tüm derslikleri listeler.
    """
    derslikler = Derslik.query.all()
    return render_template('derslik/liste.html', derslikler=derslikler)


@derslik_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@admin_required
def ekle():
    """
    Yeni derslik ekleme sayfası.
    
    GET: Derslik ekleme formunu gösterir
    POST: Yeni derslik oluşturur
    """
    # Mevcut tüm derslikleri al (yakınlık seçimi için)
    tum_derslikler = Derslik.query.order_by(Derslik.ad).all()
    
    if request.method == 'POST':
        # Form verilerini al
        ad = request.form.get('ad')
        try:
            kapasite = int(request.form.get('kapasite', 30))
            if kapasite <= 0:
                flash('Kapasite pozitif bir sayı olmalıdır!', 'danger')
                return render_template('derslik/ekle.html', tum_derslikler=tum_derslikler)
        except (ValueError, TypeError):
            flash('Kapasite geçerli bir sayı olmalıdır!', 'danger')
            return render_template('derslik/ekle.html', tum_derslikler=tum_derslikler)

        sinav_icin_uygun = request.form.get('sinav_icin_uygun') == 'on'
        bina = request.form.get('bina')
        kat = request.form.get('kat')
        aciklama = request.form.get('aciklama')
        
        # Yakın derslikleri al (çoklu seçim)
        yakin_derslik_ids = request.form.getlist('yakinliklar')
        yakin_derslik_adlari = []
        for derslik_id in yakin_derslik_ids:
            d = Derslik.query.get(int(derslik_id))
            if d:
                yakin_derslik_adlari.append(d.ad)

        # Yeni derslik oluştur
        derslik = Derslik(
            ad=ad,
            kapasite=kapasite,
            sinav_icin_uygun=sinav_icin_uygun,
            bina=bina,
            kat=kat,
            aciklama=aciklama,
            yakinliklar=yakin_derslik_adlari
        )

        db.session.add(derslik)
        db.session.commit()

        flash('Derslik başarıyla eklendi!', 'success')
        return redirect(url_for('derslik.liste'))
    
    return render_template('derslik/ekle.html', tum_derslikler=tum_derslikler)


@derslik_bp.route('/<int:derslik_id>/duzenle', methods=['GET', 'POST'])
@login_required
@admin_required
def duzenle(derslik_id):
    """
    Derslik düzenleme sayfası.
    
    Args:
        derslik_id: Düzenlenecek derslik ID'si
    """
    derslik = Derslik.query.get_or_404(derslik_id)
    
    # Mevcut tüm derslikleri al (yakınlık seçimi için) - kendisi hariç
    tum_derslikler = Derslik.query.filter(Derslik.id != derslik_id).order_by(Derslik.ad).all()
    
    # Mevcut yakınlıkların ID'lerini bul
    mevcut_yakinlik_idleri = []
    if derslik.yakinliklar:
        for yakin_ad in derslik.yakinliklar:
            yakin_derslik = Derslik.query.filter_by(ad=yakin_ad).first()
            if yakin_derslik:
                mevcut_yakinlik_idleri.append(yakin_derslik.id)
    
    if request.method == 'POST':
        # Form verilerini güncelle
        derslik.ad = request.form.get('ad')
        try:
            kapasite = int(request.form.get('kapasite', 30))
            if kapasite <= 0:
                flash('Kapasite pozitif bir sayı olmalıdır!', 'danger')
                return render_template('derslik/duzenle.html', derslik=derslik, 
                                      tum_derslikler=tum_derslikler, 
                                      mevcut_yakinlik_idleri=mevcut_yakinlik_idleri)
            derslik.kapasite = kapasite
        except (ValueError, TypeError):
            flash('Kapasite geçerli bir sayı olmalıdır!', 'danger')
            return render_template('derslik/duzenle.html', derslik=derslik,
                                  tum_derslikler=tum_derslikler,
                                  mevcut_yakinlik_idleri=mevcut_yakinlik_idleri)

        derslik.sinav_icin_uygun = request.form.get('sinav_icin_uygun') == 'on'
        derslik.bina = request.form.get('bina')
        derslik.kat = request.form.get('kat')
        derslik.aciklama = request.form.get('aciklama')
        
        # Yakın derslikleri al (çoklu seçim)
        yakin_derslik_ids = request.form.getlist('yakinliklar')
        yakin_derslik_adlari = []
        for did in yakin_derslik_ids:
            d = Derslik.query.get(int(did))
            if d:
                yakin_derslik_adlari.append(d.ad)
        
        derslik.yakinliklar = yakin_derslik_adlari

        db.session.commit()

        flash('Derslik başarıyla güncellendi!', 'success')
        return redirect(url_for('derslik.liste'))
    
    return render_template('derslik/duzenle.html', derslik=derslik,
                          tum_derslikler=tum_derslikler,
                          mevcut_yakinlik_idleri=mevcut_yakinlik_idleri)


@derslik_bp.route('/<int:derslik_id>/sil', methods=['POST'])
@login_required
@admin_required
def sil(derslik_id):
    """
    Derslik silme işlemi.

    Dersliği ve ilişkili tüm sınavları siler (CASCADE delete).

    Args:
        derslik_id: Silinecek derslik ID'si
    """
    from models.sinav import Sinav

    derslik = Derslik.query.get_or_404(derslik_id)

    try:
        # Bu derslikte yapılan sınavları kontrol et
        sinavlar = Sinav.query.filter_by(derslik_id=derslik_id).all()
        sinav_sayisi = len(sinavlar)

        # Önce bu dersliğe ait tüm sınavları sil
        for sinav in sinavlar:
            db.session.delete(sinav)

        # Sonra dersliği sil
        db.session.delete(derslik)
        db.session.commit()

        if sinav_sayisi > 0:
            flash(f'Derslik ve ilişkili {sinav_sayisi} sınav başarıyla silindi!', 'success')
        else:
            flash('Derslik başarıyla silindi!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Derslik silinirken bir hata oluştu: {str(e)}', 'danger')

    return redirect(url_for('derslik.liste'))
