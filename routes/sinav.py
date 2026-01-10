"""
SINAV GÖRÜNTÜLEME ROUTE'LARI
============================
Sınav programını görüntüleme işlemleri.

Tüm kullanıcılar sınav programını görüntüleyebilir.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from models.sinav import Sinav
from models.ders import Ders
from models.derslik import Derslik
from models.ogretim_uyesi import OgretimUyesi
from models.bolum import Bolum
from models.fakulte import Fakulte
from datetime import date, datetime
from utils.helpers import tarih_formatla, saat_formatla, gun_adi_tr

# Blueprint oluştur
sinav_bp = Blueprint('sinav', __name__, url_prefix='/sinav')


@sinav_bp.route('/program')
@login_required
def program():
    """
    Sınav programı görüntüleme sayfası.
    
    Tüm planlanmış sınavları gösterir.
    Filtreleme seçenekleri: fakülte, bölüm, tarih
    """
    # Filtreleme parametreleri
    fakulte_id = request.args.get('fakulte_id', type=int)
    bolum_id = request.args.get('bolum_id', type=int)
    baslangic_tarihi = request.args.get('baslangic_tarihi')
    bitis_tarihi = request.args.get('bitis_tarihi')
    
    # Sorgu oluştur
    sorgu = Sinav.query.filter_by(durum='planlandi')
    
    # Filtreleme
    if bolum_id:
        # Bölüme göre filtrele
        ders_ids = [d.id for d in Ders.query.filter_by(bolum_id=bolum_id).all()]
        if ders_ids:
            sorgu = sorgu.filter(Sinav.ders_id.in_(ders_ids))
        else:
            # Bölüme ait ders yoksa, boş sonuç dön
            sorgu = sorgu.filter(Sinav.id == -1)
    elif fakulte_id:
        # Fakülteye göre filtrele
        bolum_ids = [b.id for b in Bolum.query.filter_by(fakulte_id=fakulte_id).all()]
        if bolum_ids:
            ders_ids = [d.id for d in Ders.query.filter(Ders.bolum_id.in_(bolum_ids)).all()]
            if ders_ids:
                sorgu = sorgu.filter(Sinav.ders_id.in_(ders_ids))
            else:
                sorgu = sorgu.filter(Sinav.id == -1)
        else:
            sorgu = sorgu.filter(Sinav.id == -1)
    
    if baslangic_tarihi:
        sorgu = sorgu.filter(Sinav.tarih >= datetime.strptime(baslangic_tarihi, '%Y-%m-%d').date())
    
    if bitis_tarihi:
        sorgu = sorgu.filter(Sinav.tarih <= datetime.strptime(bitis_tarihi, '%Y-%m-%d').date())

    # N+1 query problemini önlemek için joinedload kullan
    # Sınavları tarihe göre sırala
    sinavlar = sorgu.options(
        joinedload(Sinav.ders).joinedload(Ders.ogretim_uyesi),
        joinedload(Sinav.ders).joinedload(Ders.bolum),
        joinedload(Sinav.derslik)
    ).order_by(Sinav.tarih, Sinav.baslangic_saati).all()
    
    # Filtreleme için gerekli veriler
    fakulteler = Fakulte.query.all()
    bolumler = Bolum.query.all()
    
    return render_template('sinav/program.html', 
                         sinavlar=sinavlar,
                         fakulteler=fakulteler,
                         bolumler=bolumler,
                         tarih_formatla=tarih_formatla,
                         saat_formatla=saat_formatla,
                         gun_adi_tr=gun_adi_tr)


@sinav_bp.route('/api/program')
@login_required
def program_api():
    """
    Sınav programı JSON API.
    
    AJAX istekleri için JSON formatında sınav programı döndürür.
    """
    # Filtreleme parametreleri
    fakulte_id = request.args.get('fakulte_id', type=int)
    bolum_id = request.args.get('bolum_id', type=int)
    baslangic_tarihi = request.args.get('baslangic_tarihi')
    bitis_tarihi = request.args.get('bitis_tarihi')
    
    # Sorgu oluştur
    sorgu = Sinav.query.filter_by(durum='planlandi')
    
    # Filtreleme (yukarıdaki ile aynı)
    if bolum_id:
        ders_ids = [d.id for d in Ders.query.filter_by(bolum_id=bolum_id).all()]
        sorgu = sorgu.filter(Sinav.ders_id.in_(ders_ids))
    elif fakulte_id:
        bolum_ids = [b.id for b in Bolum.query.filter_by(fakulte_id=fakulte_id).all()]
        ders_ids = [d.id for d in Ders.query.filter(Ders.bolum_id.in_(bolum_ids)).all()]
        sorgu = sorgu.filter(Sinav.ders_id.in_(ders_ids))
    
    if baslangic_tarihi:
        sorgu = sorgu.filter(Sinav.tarih >= datetime.strptime(baslangic_tarihi, '%Y-%m-%d').date())
    
    if bitis_tarihi:
        sorgu = sorgu.filter(Sinav.tarih <= datetime.strptime(bitis_tarihi, '%Y-%m-%d').date())

    # N+1 query problemini önlemek için joinedload kullan
    sinavlar = sorgu.options(
        joinedload(Sinav.ders).joinedload(Ders.ogretim_uyesi),
        joinedload(Sinav.derslik)
    ).order_by(Sinav.tarih, Sinav.baslangic_saati).all()

    # JSON formatına çevir
    sinav_listesi = []
    for sinav in sinavlar:
        sinav_listesi.append({
            'id': sinav.id,
            'ders_adi': sinav.ders.ad,
            'ders_kodu': sinav.ders.kod,
            'ogretim_uyesi': sinav.ders.ogretim_uyesi.tam_ad,
            'derslik_adi': sinav.derslik.ad,
            'tarih': sinav.tarih.isoformat(),
            'baslangic_saati': sinav.baslangic_saati.strftime('%H:%M'),
            'bitis_saati': sinav.bitis_saati.strftime('%H:%M'),
            'ogrenci_sayisi': sinav.ders.ogrenci_sayisi
        })
    
    return jsonify(sinav_listesi)


@sinav_bp.route('/benim-sinavlarim')
@login_required
def benim_sinavlarim():
    """
    Hoca veya öğrenci için kişisel sınav programı.
    
    - Hoca ise: Verdiği derslerin sınavlarını gösterir
    - Öğrenci ise: Kayıtlı olduğu derslerin sınavlarını gösterir
    """
    from models.ogrenci_ders import OgrenciDers
    from models.ogretim_uyesi import OgretimUyesi
    
    sinavlar = []
    kullanici_tipi = None
    
    if current_user.is_hoca():
        # Hoca ise: Verdiği derslerin sınavlarını getir
        kullanici_tipi = 'hoca'
        
        # Hocanın öğretim üyesi kaydını bul
        ogretim_uyesi = OgretimUyesi.query.get(current_user.ogretim_uyesi_id)
        
        if ogretim_uyesi:
            # Hocanın verdiği dersleri bul
            ders_ids = [d.id for d in Ders.query.filter_by(ogretim_uyesi_id=ogretim_uyesi.id, aktif=True).all()]
            
            # Bu derslerin sınavlarını getir
            sinavlar = Sinav.query.filter(
                Sinav.ders_id.in_(ders_ids),
                Sinav.durum == 'planlandi'
            ).options(
                joinedload(Sinav.ders).joinedload(Ders.ogretim_uyesi),
                joinedload(Sinav.derslik)
            ).order_by(Sinav.tarih, Sinav.baslangic_saati).all()
    
    elif current_user.is_ogrenci():
        # Öğrenci ise: Kayıtlı olduğu derslerin sınavlarını getir
        kullanici_tipi = 'ogrenci'
        
        from models.ogrenci import Ogrenci
        
        # Öğrencinin kaydını bul
        ogrenci = Ogrenci.query.get(current_user.ogrenci_id)
        
        if ogrenci:
            # Öğrencinin kayıtlı olduğu dersleri bul
            ogrenci_ders_kayitlari = OgrenciDers.query.filter_by(ogrenci_id=ogrenci.id).all()
            ders_ids = [od.ders_id for od in ogrenci_ders_kayitlari]
            
            # Bu derslerin sınavlarını getir
            sinavlar = Sinav.query.filter(
                Sinav.ders_id.in_(ders_ids),
                Sinav.durum == 'planlandi'
            ).options(
                joinedload(Sinav.ders).joinedload(Ders.ogretim_uyesi),
                joinedload(Sinav.derslik)
            ).order_by(Sinav.tarih, Sinav.baslangic_saati).all()
    
    else:
        # Admin veya bölüm yetkilisi ise genel programa yönlendir
        from flask import redirect, url_for
        return redirect(url_for('sinav.program'))
    
    return render_template('sinav/benim_sinavlarim.html',
                         sinavlar=sinavlar,
                         kullanici_tipi=kullanici_tipi,
                         tarih_formatla=tarih_formatla,
                         saat_formatla=saat_formatla,
                         gun_adi_tr=gun_adi_tr)
