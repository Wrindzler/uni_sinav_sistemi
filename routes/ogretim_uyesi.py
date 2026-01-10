"""
ÖĞRETİM ÜYESİ ROUTE'LARI
========================
Öğretim üyelerinin listelenmesi ve yönetimi.
Öğretim üyesi paneli ve ders yükleme işlemleri.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.database import db
from models.ogretim_uyesi import OgretimUyesi
from models.bolum_yetkilisi import BolumYetkilisi
from models.ders import Ders
from models.bolum import Bolum
from utils.decorators import admin_required, bolum_yetkilisi_required, hoca_required

# Blueprint oluştur
ogretim_uyesi_bp = Blueprint('ogretim_uyesi', __name__, url_prefix='/ogretim-uyesi')


@ogretim_uyesi_bp.route('/')
@login_required
@bolum_yetkilisi_required
def liste():
    """
    Öğretim üyesi listesi sayfası.

    Admin tüm öğretim üyelerini, bölüm yetkilisi sadece kendi bölümündekileri görür.
    """
    if current_user.is_admin():
        # Admin tüm öğretim üyelerini görür
        ogretim_uyeleri = OgretimUyesi.query.all()
    elif current_user.is_bolum_yetkilisi():
        # Bölüm yetkilisinin bölüm ID'sini al
        bolum_yetkilisi = BolumYetkilisi.query.get(current_user.bolum_yetkilisi_id)
        if bolum_yetkilisi:
            # Sadece kendi bölümündeki öğretim üyelerini göster
            ogretim_uyeleri = OgretimUyesi.query.filter_by(bolum_id=bolum_yetkilisi.bolum_id).all()
        else:
            ogretim_uyeleri = []
    else:
        ogretim_uyeleri = []

    return render_template('ogretim_uyesi/liste.html', ogretim_uyeleri=ogretim_uyeleri)


@ogretim_uyesi_bp.route('/sil/<int:ogretim_uyesi_id>', methods=['POST'])
@login_required
@bolum_yetkilisi_required
def sil(ogretim_uyesi_id):
    """
    Öğretim üyesi silme işlemi.
    
    Args:
        ogretim_uyesi_id: Silinecek öğretim üyesi ID'si
    """
    try:
        from models.user import User
        from models.ders import Ders
        
        ogretim_uyesi = OgretimUyesi.query.get(ogretim_uyesi_id)
        if not ogretim_uyesi:
            flash('Öğretim üyesi bulunamadı!', 'danger')
            return redirect(url_for('ogretim_uyesi.liste'))
        
        # Yetki kontrolü
        if current_user.is_bolum_yetkilisi():
            bolum_yetkilisi = BolumYetkilisi.query.get(current_user.bolum_yetkilisi_id)
            if bolum_yetkilisi and ogretim_uyesi.bolum_id != bolum_yetkilisi.bolum_id:
                flash('Bu öğretim üyesini silme yetkiniz yok!', 'danger')
                return redirect(url_for('ogretim_uyesi.liste'))
        
        ogretim_uyesi_ad = ogretim_uyesi.tam_ad
        
        # Bu öğretim üyesinin verdiği dersleri kontrol et
        dersler = Ders.query.filter_by(ogretim_uyesi_id=ogretim_uyesi_id).count()
        if dersler > 0:
            flash(f'Bu öğretim üyesinin {dersler} dersi var! Önce dersleri başka bir öğretim üyesine atayın.', 'warning')
            return redirect(url_for('ogretim_uyesi.liste'))
        
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
    
    return redirect(url_for('ogretim_uyesi.liste'))


@ogretim_uyesi_bp.route('/panel')
@login_required
@hoca_required
def panel():
    """
    Öğretim üyesi paneli.
    
    Öğretim üyesinin kendi derslerini ve öğrenci sayılarını gösterir.
    """
    # Öğretim üyesini bul
    if not current_user.ogretim_uyesi_id:
        flash('Öğretim üyesi bilgisi bulunamadı!', 'error')
        return redirect(url_for('sinav.program'))
    
    ogretim_uyesi = OgretimUyesi.query.get(current_user.ogretim_uyesi_id)
    if not ogretim_uyesi:
        flash('Öğretim üyesi bilgisi bulunamadı!', 'error')
        return redirect(url_for('sinav.program'))
    
    # Öğretim üyesinin dersleri
    dersler = Ders.query.filter_by(ogretim_uyesi_id=ogretim_uyesi.id, aktif=True).all()
    
    # Tüm bölümleri al
    tum_bolumler = Bolum.query.all()
    
    # Öğretim üyesinin atandığı bölümler
    atanmis_bolumler = list(ogretim_uyesi.bolumler.all())
    # Ana bölüm atanmış bölümler listesinde değilse ekle
    if ogretim_uyesi.bolum and ogretim_uyesi.bolum not in atanmis_bolumler:
        atanmis_bolumler.append(ogretim_uyesi.bolum)
    
    return render_template('ogretim_uyesi/panel.html', 
                          ogretim_uyesi=ogretim_uyesi,
                          dersler=dersler,
                          tum_bolumler=tum_bolumler,
                          atanmis_bolumler=atanmis_bolumler)


@ogretim_uyesi_bp.route('/bolum-guncelle', methods=['POST'])
@login_required
@hoca_required
def bolum_guncelle():
    """
    Öğretim üyesinin bölümlerini güncelle.
    
    Birden fazla bölüm seçilebilir.
    """
    # Öğretim üyesini bul
    if not current_user.ogretim_uyesi_id:
        flash('Öğretim üyesi bilgisi bulunamadı!', 'error')
        return redirect(url_for('ogretim_uyesi.panel'))
    
    ogretim_uyesi = OgretimUyesi.query.get(current_user.ogretim_uyesi_id)
    if not ogretim_uyesi:
        flash('Öğretim üyesi bilgisi bulunamadı!', 'error')
        return redirect(url_for('ogretim_uyesi.panel'))
    
    try:
        # Seçilen bölüm ID'lerini al
        bolum_ids = request.form.getlist('bolum_ids')
        
        if not bolum_ids:
            flash('En az bir bölüm seçmelisiniz!', 'warning')
            return redirect(url_for('ogretim_uyesi.panel'))
        
        # Bölümleri bul
        yeni_bolumler = Bolum.query.filter(Bolum.id.in_([int(b) for b in bolum_ids])).all()
        
        if not yeni_bolumler:
            flash('Geçerli bölüm bulunamadı!', 'error')
            return redirect(url_for('ogretim_uyesi.panel'))
        
        # Mevcut bölümleri temizle ve yenilerini ekle
        # Önce mevcut many-to-many ilişkisini temizle
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
        flash(f'Bölümleriniz güncellendi: {bolum_adlari}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Bölümler güncellenirken hata oluştu: {str(e)}', 'error')
    
    return redirect(url_for('ogretim_uyesi.panel'))


@ogretim_uyesi_bp.route('/ders-bolum-guncelle/<int:ders_id>', methods=['POST'])
@login_required
@hoca_required
def ders_bolum_guncelle(ders_id):
    """
    Bir dersin bölümlerini güncelle.
    
    Öğretim üyesi, dersini birden fazla bölüme atayabilir (seçmeli dersler için).
    
    Args:
        ders_id: Güncellenecek dersin ID'si
    """
    from models.ders import ders_bolumler
    
    # Öğretim üyesini bul
    if not current_user.ogretim_uyesi_id:
        flash('Öğretim üyesi bilgisi bulunamadı!', 'error')
        return redirect(url_for('ogretim_uyesi.panel'))
    
    ogretim_uyesi = OgretimUyesi.query.get(current_user.ogretim_uyesi_id)
    if not ogretim_uyesi:
        flash('Öğretim üyesi bilgisi bulunamadı!', 'error')
        return redirect(url_for('ogretim_uyesi.panel'))
    
    # Dersi bul
    ders = Ders.query.get(ders_id)
    if not ders:
        flash('Ders bulunamadı!', 'error')
        return redirect(url_for('ogretim_uyesi.panel'))
    
    # Dersin bu öğretim üyesine ait olduğunu kontrol et
    if ders.ogretim_uyesi_id != ogretim_uyesi.id:
        flash('Bu ders size ait değil!', 'error')
        return redirect(url_for('ogretim_uyesi.panel'))
    
    try:
        # Seçilen bölüm ID'lerini al
        bolum_ids = request.form.getlist('bolum_ids')
        
        if not bolum_ids:
            flash('En az bir bölüm seçmelisiniz!', 'warning')
            return redirect(url_for('ogretim_uyesi.panel'))
        
        # Bölümleri bul
        yeni_bolumler = Bolum.query.filter(Bolum.id.in_([int(b) for b in bolum_ids])).all()
        
        if not yeni_bolumler:
            flash('Geçerli bölüm bulunamadı!', 'error')
            return redirect(url_for('ogretim_uyesi.panel'))
        
        # İlk seçilen bölümü ana bölüm yap
        ders.bolum_id = yeni_bolumler[0].id
        
        # Mevcut ek bölümleri temizle
        for bolum in list(ders.ek_bolumler):
            ders.ek_bolumler.remove(bolum)
        
        # Ek bölümleri ekle (ana bölüm hariç)
        for bolum in yeni_bolumler[1:]:
            ders.ek_bolumler.append(bolum)
        
        db.session.commit()
        
        bolum_adlari = ', '.join([b.ad for b in yeni_bolumler])
        flash(f'"{ders.ad}" dersi şu bölümlere atandı: {bolum_adlari}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Bölümler güncellenirken hata oluştu: {str(e)}', 'error')
    
    return redirect(url_for('ogretim_uyesi.panel'))


@ogretim_uyesi_bp.route('/ders-yukle', methods=['GET', 'POST'])
@login_required
@hoca_required
def ders_yukle():
    """
    Öğretim üyesi için Excel'den ders ve öğrenci yükleme.
    
    Dosya adından ders kodunu çıkarır ve öğretim üyesine otomatik atar.
    """
    from models.ogrenci import Ogrenci
    from models.ogrenci_ders import OgrenciDers
    from werkzeug.utils import secure_filename
    import os
    import re
    from config import Config
    
    # Öğretim üyesini bul
    if not current_user.ogretim_uyesi_id:
        flash('Öğretim üyesi bilgisi bulunamadı!', 'error')
        return redirect(url_for('ogretim_uyesi.panel'))
    
    ogretim_uyesi = OgretimUyesi.query.get(current_user.ogretim_uyesi_id)
    if not ogretim_uyesi:
        flash('Öğretim üyesi bilgisi bulunamadı!', 'error')
        return redirect(url_for('ogretim_uyesi.panel'))
    
    # Öğretim üyesinin atandığı bölümler
    atanmis_bolumler = list(ogretim_uyesi.bolumler.all())
    # Ana bölüm atanmış bölümler listesinde değilse ekle
    if ogretim_uyesi.bolum and ogretim_uyesi.bolum not in atanmis_bolumler:
        atanmis_bolumler.insert(0, ogretim_uyesi.bolum)
    
    if request.method == 'POST':
        # Dosya kontrolü
        if 'dosya' not in request.files:
            flash('Dosya seçilmedi!', 'error')
            return redirect(url_for('ogretim_uyesi.ders_yukle'))
        
        dosya = request.files['dosya']
        
        if dosya.filename == '':
            flash('Dosya seçilmedi!', 'error')
            return redirect(url_for('ogretim_uyesi.ders_yukle'))
        
        # Dosya uzantısı kontrolü
        if not ('.' in dosya.filename and dosya.filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']):
            flash('Geçersiz dosya formatı! Sadece XLSX veya XLS dosyaları yüklenebilir.', 'error')
            return redirect(url_for('ogretim_uyesi.ders_yukle'))
        
        # Seçilen bölüm ID'sini al
        secilen_bolum_id = request.form.get('bolum_id')
        if not secilen_bolum_id:
            flash('Bölüm seçilmedi!', 'error')
            return redirect(url_for('ogretim_uyesi.ders_yukle'))
        
        # Seçilen bölümün geçerli olduğunu kontrol et
        secilen_bolum = Bolum.query.get(int(secilen_bolum_id))
        if not secilen_bolum:
            flash('Geçersiz bölüm seçildi!', 'error')
            return redirect(url_for('ogretim_uyesi.ders_yukle'))
        
        # Dosya adından ders kodunu çıkar
        original_filename = dosya.filename
        ders_kodu_match = re.search(r'\[([^\]]+)\]', original_filename)
        if not ders_kodu_match:
            flash('Dosya adında ders kodu bulunamadı! Dosya adı SınıfListesi[DERSKODU].xls formatında olmalı.', 'error')
            return redirect(url_for('ogretim_uyesi.ders_yukle'))
        
        ders_kodu = ders_kodu_match.group(1).strip()
        
        # Uploads klasörünü oluştur (yoksa)
        uploads_dir = Config.UPLOAD_FOLDER
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        
        # Dosyayı kaydet
        filename = secure_filename(dosya.filename)
        dosya_yolu = os.path.join(uploads_dir, filename)
        dosya.save(dosya_yolu)
        
        # Dosyayı işle
        try:
            sonuc = _ogretim_uyesi_ders_yukle(dosya_yolu, filename, ders_kodu, ogretim_uyesi, int(secilen_bolum_id))
            
            # Dosyayı sil
            try:
                os.remove(dosya_yolu)
            except PermissionError:
                pass
            
            flash(f'Ders "{sonuc["ders_adi"]}" ({sonuc["bolum_adi"]}) oluşturuldu/güncellendi. {sonuc["eklenen"]} öğrenci eklendi, {sonuc["mevcut"]} öğrenci zaten kayıtlıydı.', 'success')
            return redirect(url_for('ogretim_uyesi.panel'))
        except Exception as e:
            try:
                if os.path.exists(dosya_yolu):
                    os.remove(dosya_yolu)
            except PermissionError:
                pass
            flash(f'Dosya işlenirken hata oluştu: {str(e)}', 'error')
            return redirect(url_for('ogretim_uyesi.ders_yukle'))
    
    return render_template('ogretim_uyesi/ders_yukle.html', 
                          ogretim_uyesi=ogretim_uyesi,
                          atanmis_bolumler=atanmis_bolumler)


def _ders_kodundan_bolum_bul(ders_kodu):
    """
    Ders kodunun önekine göre bölümü otomatik tespit et.
    
    Args:
        ders_kodu: Ders kodu (örn: YZM119, BLM111, SEC908)
        
    Returns:
        Bolum: Bulunan bölüm nesnesi veya None
    """
    ders_kodu_upper = ders_kodu.upper().strip()
    
    # Ders kodu önekine göre bölüm eşleştirme
    bolum_onekleri = {
        'YZM': 'Yazılım Mühendisliği',
        'BLM': 'Bilgisayar Mühendisliği',
    }
    
    for onek, bolum_adi in bolum_onekleri.items():
        if ders_kodu_upper.startswith(onek):
            # Bölümü veritabanında ara (büyük/küçük harf duyarsız)
            bolum = Bolum.query.filter(Bolum.ad.ilike(f'%{bolum_adi}%')).first()
            if bolum:
                return bolum
    
    # Eşleşme bulunamadı
    return None


def _ogretim_uyesi_ders_yukle(dosya_yolu, filename, ders_kodu, ogretim_uyesi, bolum_id=None):
    """
    Öğretim üyesi için Excel'den ders ve öğrencileri yükle.
    
    Args:
        dosya_yolu: Excel dosyasının yolu
        filename: Dosya adı
        ders_kodu: Ders kodu
        ogretim_uyesi: Öğretim üyesi nesnesi
        bolum_id: Dersin atanacağı bölüm ID'si (opsiyonel, yoksa ders koduna göre veya öğretim üyesinin bölümü kullanılır)
        
    Returns:
        dict: {'ders_adi': str, 'eklenen': int, 'mevcut': int, 'hata': int, 'bolum_adi': str}
    """
    from models.ogrenci import Ogrenci
    from models.ogrenci_ders import OgrenciDers
    import xlrd
    
    eklenen = 0
    mevcut = 0
    hata = 0
    
    # Önce ders koduna göre bölümü otomatik tespit et
    otomatik_bolum = _ders_kodundan_bolum_bul(ders_kodu)
    
    if otomatik_bolum:
        # Ders koduna göre bölüm bulundu, onu kullan
        bolum_id = otomatik_bolum.id
        bolum_adi = otomatik_bolum.ad
    elif bolum_id:
        # Manuel seçilen bölümü kullan
        secilen_bolum = Bolum.query.get(bolum_id)
        bolum_adi = secilen_bolum.ad if secilen_bolum else "Bilinmiyor"
    else:
        # Öğretim üyesinin bölümünü kullan
        bolum_id = ogretim_uyesi.bolum_id
        bolum_adi = ogretim_uyesi.bolum.ad if ogretim_uyesi.bolum else "Bilinmiyor"
    
    if not bolum_id:
        raise Exception('Bölüm belirtilmedi ve öğretim üyesinin bölümü tanımlı değil!')
    
    # Excel dosyasını oku
    wb = xlrd.open_workbook(dosya_yolu)
    ws = wb.sheet_by_index(0)
    
    # Excel'den ders adını bul (ilk 10 satır, tüm sütunlarda)
    ders_adi = ders_kodu  # Varsayılan olarak ders kodu
    ders_kodu_upper = ders_kodu.upper().strip()
    
    # İlk 10 satırda ara
    ders_adi_bulundu = False
    for i in range(min(10, ws.nrows)):
        if ders_adi_bulundu:
            break
        for j in range(ws.ncols):
            try:
                cell_val = str(ws.cell_value(i, j))
                
                # Hücre içinde newline ile ayrılmış satırlar olabilir
                satirlar = cell_val.split('\n')
                
                for satir in satirlar:
                    satir = satir.strip()
                    satir_upper = satir.upper()
                    
                    # Ders kodunu içeren satırı bul (örn: "BLM111 BİLGİSAYAR MÜHENDİSLİĞİNE GİRİŞ")
                    if satir_upper.startswith(ders_kodu_upper):
                        # Ders kodundan sonraki kısmı al
                        kalan = satir[len(ders_kodu):].strip()
                        if kalan:
                            ders_adi = kalan
                            ders_adi_bulundu = True
                            break
                
                if ders_adi_bulundu:
                    break
            except:
                continue
    
    # Başlık satırını ve sütun indekslerini bul
    baslik_satiri = -1
    ogrenci_no_col = -1
    ad_soyad_col = -1
    
    for i in range(min(20, ws.nrows)):
        for j in range(ws.ncols):
            cell_val = str(ws.cell_value(i, j)).lower().strip()
            if 'renci no' in cell_val or cell_val == '#':
                if cell_val == '#':
                    baslik_satiri = i
                else:
                    baslik_satiri = i
                    ogrenci_no_col = j
            if 'soyad' in cell_val:
                ad_soyad_col = j
        if baslik_satiri >= 0 and ogrenci_no_col < 0:
            ogrenci_no_col = 4
            ad_soyad_col = 5
        if baslik_satiri >= 0:
            break
    
    if baslik_satiri < 0:
        baslik_satiri = 4
        ogrenci_no_col = 4
        ad_soyad_col = 5
    
    baslangic = baslik_satiri + 1
    
    # Dersi bul veya oluştur
    ders = Ders.query.filter_by(kod=ders_kodu).first()
    if not ders:
        ders = Ders(
            kod=ders_kodu,
            ad=ders_adi,
            bolum_id=bolum_id,
            ogretim_uyesi_id=ogretim_uyesi.id,
            ogrenci_sayisi=0,
            sinav_suresi=60,
            sinav_turu='yazili',
            aktif=True
        )
        db.session.add(ders)
        db.session.flush()
    else:
        # Ders varsa öğretim üyesini ve ders adını güncelle
        ders.ogretim_uyesi_id = ogretim_uyesi.id
        if ders_adi != ders_kodu:
            ders.ad = ders_adi
    
    # Öğrencileri oku ve ekle
    for satir in range(baslangic, ws.nrows):
        # Öğrenci numarasını al
        ogrenci_no_raw = ws.cell_value(satir, ogrenci_no_col)
        if isinstance(ogrenci_no_raw, float):
            ogrenci_no = str(int(ogrenci_no_raw)).strip()
        else:
            ogrenci_no = str(ogrenci_no_raw).strip() if ogrenci_no_raw else None
        
        # Boş veya geçersiz öğrenci numarası atla
        if not ogrenci_no or ogrenci_no == '0' or ogrenci_no == '':
            continue
        
        # Ad Soyadı al ve ayır
        ad_soyad = str(ws.cell_value(satir, ad_soyad_col)).strip() if ws.cell_value(satir, ad_soyad_col) else None
        
        if not ad_soyad:
            hata += 1
            continue
        
        # Ad Soyadı ayır (son kelime soyad, kalanlar ad)
        parcalar = ad_soyad.split()
        if len(parcalar) >= 2:
            soyad = parcalar[-1]
            ad = ' '.join(parcalar[:-1])
        else:
            ad = ad_soyad
            soyad = ''
        
        if not ad:
            hata += 1
            continue
        
        # Öğrenci var mı kontrol et
        ogrenci = Ogrenci.query.filter_by(ogrenci_no=ogrenci_no).first()
        
        if not ogrenci:
            # Yeni öğrenci oluştur
            ogrenci = Ogrenci(
                ogrenci_no=ogrenci_no,
                ad=ad,
                soyad=soyad,
                email=None,
                bolum_id=bolum_id
            )
            db.session.add(ogrenci)
            db.session.flush()
        
        # Öğrenciyi derse kaydet (zaten kayıtlı değilse)
        if not OgrenciDers.query.filter_by(ogrenci_id=ogrenci.id, ders_id=ders.id).first():
            ogrenci_ders = OgrenciDers(
                ogrenci_id=ogrenci.id,
                ders_id=ders.id
            )
            db.session.add(ogrenci_ders)
            eklenen += 1
        else:
            mevcut += 1
    
    # Dersin öğrenci sayısını güncelle
    ders.ogrenci_sayisi = OgrenciDers.query.filter_by(ders_id=ders.id).count()
    
    db.session.commit()
    
    return {
        'ders_adi': ders.kod,
        'eklenen': eklenen,
        'mevcut': mevcut,
        'hata': hata,
        'bolum_adi': bolum_adi
    }