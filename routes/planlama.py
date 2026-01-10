"""
SINAV PLANLAMA ROUTE'LARI
=========================
Otomatik sınav planlama işlemleri.

Sadece admin kullanıcılar planlama yapabilir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from datetime import datetime, date
from models.database import db
from models.sinav import Sinav
from algorithms.planlama_algoritmasi import SinavPlanlayici
from utils.decorators import admin_required

# Blueprint oluştur
planlama_bp = Blueprint('planlama', __name__, url_prefix='/planlama')


@planlama_bp.route('/')
@login_required
@admin_required
def index():
    """
    Planlama ana sayfası.
    
    Planlama formunu ve sonuçları gösterir.
    """
    # Son planlama sonuçlarını göster (opsiyonel)
    return render_template('planlama/index.html')


@planlama_bp.route('/baslat', methods=['POST'])
@login_required
@admin_required
def baslat():
    """
    Sınav planlamasını başlat.
    
    POST isteği ile planlama parametrelerini alır ve
    planlama algoritmasını çalıştırır.
    """
    # Form verilerini al
    baslangic_tarihi_str = request.form.get('baslangic_tarihi')
    bitis_tarihi_str = request.form.get('bitis_tarihi')
    
    if not baslangic_tarihi_str or not bitis_tarihi_str:
        flash('Lütfen başlangıç ve bitiş tarihlerini girin!', 'error')
        return redirect(url_for('planlama.index'))
    
    # Tarihleri parse et
    baslangic_tarihi = datetime.strptime(baslangic_tarihi_str, '%Y-%m-%d').date()
    bitis_tarihi = datetime.strptime(bitis_tarihi_str, '%Y-%m-%d').date()
    
    # Tarih kontrolü
    if baslangic_tarihi > bitis_tarihi:
        flash('Başlangıç tarihi bitiş tarihinden sonra olamaz!', 'error')
        return redirect(url_for('planlama.index'))
    
    # Mevcut planlanmış sınavları temizle (opsiyonel)
    # Kullanıcıya sorulabilir veya yeni planlama yapılırken eski planlar silinir
    mevcut_sinavlar = Sinav.query.filter_by(durum='planlandi').all()
    if mevcut_sinavlar:
        # Kullanıcıya uyarı gösterilebilir
        # Şimdilik eski planları silelim
        for sinav in mevcut_sinavlar:
            db.session.delete(sinav)
        db.session.commit()
    
    # Planlayıcıyı oluştur
    planlayici = SinavPlanlayici()
    
    # Planlamayı başlat
    sonuc = planlayici.planla(baslangic_tarihi, bitis_tarihi)
    
    # Sonuçları göster
    if sonuc['basarili']:
        flash(f'Planlama başarıyla tamamlandı! {sonuc["istatistikler"]["planlanan"]} ders planlandı.', 'success')
    else:
        flash(f'Planlama tamamlandı ancak {len(sonuc["hatalar"])} ders planlanamadı.', 'warning')
    
    # Sonuçları template'e gönder
    return render_template('planlama/sonuc.html', sonuc=sonuc)


@planlama_bp.route('/api/durum')
@login_required
@admin_required
def durum():
    """
    Planlama durumu API.
    
    Mevcut planlanmış sınavların istatistiklerini döndürür.
    """
    toplam_sinav = Sinav.query.filter_by(durum='planlandi').count()
    
    # Tarih aralığı
    sinavlar = Sinav.query.filter_by(durum='planlandi').all()
    if sinavlar:
        tarihler = [s.tarih for s in sinavlar]
        ilk_tarih = min(tarihler)
        son_tarih = max(tarihler)
    else:
        ilk_tarih = None
        son_tarih = None
    
    return jsonify({
        'toplam_sinav': toplam_sinav,
        'ilk_tarih': ilk_tarih.isoformat() if ilk_tarih else None,
        'son_tarih': son_tarih.isoformat() if son_tarih else None
    })

