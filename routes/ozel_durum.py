"""
ÖZEL DURUM YÖNETİMİ ROUTE'LARI
===============================
Özel durum ekleme, silme, güncelleme işlemleri.

Bölüm yetkilileri kendi bölümlerine ait dersler için özel durum ekleyebilir.
Admin tüm özel durumları yönetebilir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.database import db
from models.ozel_durum import OzelDurum
from models.ders import Ders
from models.ogretim_uyesi import OgretimUyesi
from utils.decorators import bolum_yetkilisi_required

# Blueprint oluştur
ozel_durum_bp = Blueprint('ozel_durum', __name__, url_prefix='/ozel_durum')


@ozel_durum_bp.route('/')
@login_required
@bolum_yetkilisi_required
def liste():
    """
    Özel durum listesi sayfası.
    
    Kullanıcının yetkili olduğu bölümlere ait özel durumları gösterir.
    """
    # Admin ise tüm özel durumlar, bölüm yetkilisi ise sadece kendi bölümünün dersleri için
    # Sadece aktif özel durumları göster
    if current_user.is_admin():
        ozel_durumlar = OzelDurum.query.filter_by(aktif=True).all()
    else:
        # Bölüm yetkilisi ise sadece kendi bölümünün dersleri ve öğretim üyeleri için özel durumlar
        from models.bolum_yetkilisi import BolumYetkilisi
        bolum_yetkilisi = BolumYetkilisi.query.get(current_user.bolum_yetkilisi_id)
        if bolum_yetkilisi:
            # Kendi bölümünün derslerini al
            bolum_dersleri = Ders.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id).all()
            ders_ids = [d.id for d in bolum_dersleri] if bolum_dersleri else []
            
            # Kendi bölümünün öğretim üyelerini al
            bolum_ogretim_uyeleri = OgretimUyesi.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id).all()
            ogretim_uyesi_ids = [o.id for o in bolum_ogretim_uyeleri] if bolum_ogretim_uyeleri else []
            
            # Hem ders hem öğretim üyesi için özel durumları getir
            from sqlalchemy import or_
            
            filtre_kosullari = []
            if ders_ids:
                filtre_kosullari.append(OzelDurum.ders_id.in_(ders_ids))
            if ogretim_uyesi_ids:
                filtre_kosullari.append(OzelDurum.ogretim_uyesi_id.in_(ogretim_uyesi_ids))
            
            if filtre_kosullari:
                ozel_durumlar = OzelDurum.query.filter(
                    OzelDurum.aktif == True,
                    or_(*filtre_kosullari)
                ).all()
            else:
                ozel_durumlar = []
        else:
            ozel_durumlar = []
    
    return render_template('ozel_durum/liste.html', ozel_durumlar=ozel_durumlar)


@ozel_durum_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@bolum_yetkilisi_required
def ekle():
    """
    Yeni özel durum ekleme sayfası.
    
    GET: Özel durum ekleme formunu gösterir
    POST: Yeni özel durum oluşturur
    """
    if request.method == 'POST':
        # Form verilerini al
        durum_turu = request.form.get('durum_turu')
        ders_id = request.form.get('ders_id')
        ogretim_uyesi_id = request.form.get('ogretim_uyesi_id')
        musait_gunler = request.form.get('musait_gunler')
        baslangic_tarihi = request.form.get('baslangic_tarihi')
        bitis_tarihi = request.form.get('bitis_tarihi')
        ozel_sinav_suresi = request.form.get('ozel_sinav_suresi')
        ozel_sinif_adi = request.form.get('ozel_sinif_adi')
        ozel_sinif_kapasitesi = request.form.get('ozel_sinif_kapasitesi')
        aciklama = request.form.get('aciklama')
        
        # Özel sınıf için validasyon
        if durum_turu == 'ozel_sinif':
            if not ders_id:
                flash('Özel sınıf için ders seçimi zorunludur!', 'danger')
                if current_user.is_admin():
                    dersler = Ders.query.filter_by(aktif=True).all()
                    ogretim_uyeleri = OgretimUyesi.query.all()
                else:
                    from models.bolum_yetkilisi import BolumYetkilisi
                    bolum_yetkilisi = BolumYetkilisi.query.get(current_user.bolum_yetkilisi_id)
                    if bolum_yetkilisi:
                        dersler = Ders.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id, aktif=True).all()
                        ogretim_uyeleri = OgretimUyesi.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id).all()
                    else:
                        dersler = []
                        ogretim_uyeleri = []
                return render_template('ozel_durum/ekle.html', dersler=dersler, ogretim_uyeleri=ogretim_uyeleri)
            
            if not ozel_sinif_adi or not ozel_sinif_kapasitesi:
                flash('Özel sınıf için sınıf adı ve kapasitesi zorunludur!', 'danger')
                if current_user.is_admin():
                    dersler = Ders.query.filter_by(aktif=True).all()
                    ogretim_uyeleri = OgretimUyesi.query.all()
                else:
                    from models.bolum_yetkilisi import BolumYetkilisi
                    bolum_yetkilisi = BolumYetkilisi.query.get(current_user.bolum_yetkilisi_id)
                    if bolum_yetkilisi:
                        dersler = Ders.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id, aktif=True).all()
                        ogretim_uyeleri = OgretimUyesi.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id).all()
                    else:
                        dersler = []
                        ogretim_uyeleri = []
                return render_template('ozel_durum/ekle.html', dersler=dersler, ogretim_uyeleri=ogretim_uyeleri)
        
        # Tarihleri parse et
        from datetime import datetime
        baslangic_tarihi_obj = None
        bitis_tarihi_obj = None
        if baslangic_tarihi:
            baslangic_tarihi_obj = datetime.strptime(baslangic_tarihi, '%Y-%m-%d').date()
        if bitis_tarihi:
            bitis_tarihi_obj = datetime.strptime(bitis_tarihi, '%Y-%m-%d').date()
        
        # KONTROL: Aynı ders için aynı türde aktif özel durum var mı?
        if ders_id:
            ders_id_int = int(ders_id)
            mevcut_ozel_durum = OzelDurum.query.filter_by(
                durum_turu=durum_turu,
                ders_id=ders_id_int,
                aktif=True
            ).first()
            
            if mevcut_ozel_durum:
                ders = Ders.query.get(ders_id_int)
                ders_adi = ders.ad if ders else f"Ders ID: {ders_id_int}"
                flash(f'"{ders_adi}" dersi için "{durum_turu}" türünde zaten aktif bir özel durum var! Lütfen önce mevcut özel durumu silin veya pasif yapın.', 'danger')
                # Form için gerekli verileri tekrar al
                if current_user.is_admin():
                    dersler = Ders.query.filter_by(aktif=True).all()
                    ogretim_uyeleri = OgretimUyesi.query.all()
                else:
                    from models.bolum_yetkilisi import BolumYetkilisi
                    bolum_yetkilisi = BolumYetkilisi.query.get(current_user.bolum_yetkilisi_id)
                    if bolum_yetkilisi:
                        dersler = Ders.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id, aktif=True).all()
                        ogretim_uyeleri = OgretimUyesi.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id).all()
                    else:
                        dersler = []
                        ogretim_uyeleri = []
                return render_template('ozel_durum/ekle.html', dersler=dersler, ogretim_uyeleri=ogretim_uyeleri)
        
        # KONTROL: Aynı öğretim üyesi için aynı türde aktif özel durum var mı?
        if ogretim_uyesi_id:
            ogretim_uyesi_id_int = int(ogretim_uyesi_id)
            mevcut_ozel_durum = OzelDurum.query.filter_by(
                durum_turu=durum_turu,
                ogretim_uyesi_id=ogretim_uyesi_id_int,
                aktif=True
            ).first()
            
            if mevcut_ozel_durum:
                ogretim_uyesi = OgretimUyesi.query.get(ogretim_uyesi_id_int)
                hoca_adi = f"{ogretim_uyesi.ad} {ogretim_uyesi.soyad}" if ogretim_uyesi else f"Öğretim Üyesi ID: {ogretim_uyesi_id_int}"
                flash(f'"{hoca_adi}" için "{durum_turu}" türünde zaten aktif bir özel durum var! Lütfen önce mevcut özel durumu silin veya pasif yapın.', 'danger')
                # Form için gerekli verileri tekrar al
                if current_user.is_admin():
                    dersler = Ders.query.filter_by(aktif=True).all()
                    ogretim_uyeleri = OgretimUyesi.query.all()
                else:
                    from models.bolum_yetkilisi import BolumYetkilisi
                    bolum_yetkilisi = BolumYetkilisi.query.get(current_user.bolum_yetkilisi_id)
                    if bolum_yetkilisi:
                        dersler = Ders.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id, aktif=True).all()
                        ogretim_uyeleri = OgretimUyesi.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id).all()
                    else:
                        dersler = []
                        ogretim_uyeleri = []
                return render_template('ozel_durum/ekle.html', dersler=dersler, ogretim_uyeleri=ogretim_uyeleri)
        
        # Yeni özel durum oluştur
        ozel_durum = OzelDurum(
            durum_turu=durum_turu,
            ders_id=int(ders_id) if ders_id else None,
            ogretim_uyesi_id=int(ogretim_uyesi_id) if ogretim_uyesi_id else None,
            musait_gunler=musait_gunler,
            baslangic_tarihi=baslangic_tarihi_obj,
            bitis_tarihi=bitis_tarihi_obj,
            ozel_sinav_suresi=int(ozel_sinav_suresi) if ozel_sinav_suresi else None,
            ozel_sinif_adi=ozel_sinif_adi if ozel_sinif_adi else None,
            ozel_sinif_kapasitesi=int(ozel_sinif_kapasitesi) if ozel_sinif_kapasitesi else None,
            aciklama=aciklama
        )
        
        db.session.add(ozel_durum)
        db.session.commit()
        
        flash('Özel durum başarıyla eklendi!', 'success')
        return redirect(url_for('ozel_durum.liste'))
    
    # Form için gerekli veriler
    if current_user.is_admin():
        dersler = Ders.query.filter_by(aktif=True).all()
        ogretim_uyeleri = OgretimUyesi.query.all()
    else:
        # Bölüm yetkilisinin bölümüne ait dersler
        from models.bolum_yetkilisi import BolumYetkilisi
        bolum_yetkilisi = BolumYetkilisi.query.get(current_user.bolum_yetkilisi_id)
        if bolum_yetkilisi:
            dersler = Ders.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id, aktif=True).all()
            ogretim_uyeleri = OgretimUyesi.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id).all()
        else:
            dersler = []
            ogretim_uyeleri = []
    
    return render_template('ozel_durum/ekle.html', dersler=dersler, ogretim_uyeleri=ogretim_uyeleri)


@ozel_durum_bp.route('/<int:ozel_durum_id>/sil', methods=['POST'])
@login_required
@bolum_yetkilisi_required
def sil(ozel_durum_id):
    """
    Özel durum silme işlemi.
    
    Args:
        ozel_durum_id: Silinecek özel durum ID'si
    """
    ozel_durum = OzelDurum.query.get_or_404(ozel_durum_id)
    
    # Yetki kontrolü
    if not current_user.is_admin():
        if ozel_durum.ders_id:
            ders = Ders.query.get(ozel_durum.ders_id)
            from models.bolum_yetkilisi import BolumYetkilisi
            bolum_yetkilisi = BolumYetkilisi.query.get(current_user.bolum_yetkilisi_id)
            if not bolum_yetkilisi or (ders and ders.bolum_id != bolum_yetkilisi.bolum_id):
                flash('Bu özel durumu silme yetkiniz yok!', 'error')
                return redirect(url_for('ozel_durum.liste'))
    
    try:
        # Eğer özel sınıf türündeyse, ilgili dersliği de sil
        if ozel_durum.durum_turu == 'ozel_sinif' and ozel_durum.ozel_sinif_adi:
            from models.derslik import Derslik
            from models.sinav import Sinav
            
            # Bu özel sınıf adıyla oluşturulmuş derslik var mı?
            ozel_derslik = Derslik.query.filter_by(ad=ozel_durum.ozel_sinif_adi).first()
            
            if ozel_derslik:
                # Bu derslik özel durum nedeniyle mi oluşturulmuş?
                # (aciklama alanında "Özel durum ile eklendi" yazıyorsa)
                if ozel_derslik.aciklama and 'Özel durum ile eklendi' in ozel_derslik.aciklama:
                    # Bu dersliğe atanmış sınavları da sil
                    Sinav.query.filter_by(derslik_id=ozel_derslik.id).delete()
                    
                    # Dersliği sil
                    derslik_adi = ozel_derslik.ad
                    db.session.delete(ozel_derslik)
                    flash(f'"{derslik_adi}" dersliği ve ilgili sınavlar silindi.', 'info')
        
        # Özel durumu gerçekten sil (hard delete)
        db.session.delete(ozel_durum)
        db.session.commit()
        
        flash('Özel durum başarıyla silindi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Özel durum silinirken hata oluştu: {str(e)}', 'danger')
    
    return redirect(url_for('ozel_durum.liste'))

