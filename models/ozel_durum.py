"""
ÖZEL DURUM MODELİ
=================
Dersler ve öğretim üyeleri için özel durumları temsil eder.

Özel durumlar:
- Hocanın belirli günlerde müsait olması
- Ders için sınav olmaması
- Özel sınav süresi
"""

from models.database import db
from datetime import date


class OzelDurum(db.Model):
    """
    Özel durum tablosu.
    
    Dersler ve öğretim üyeleri için özel kısıtlamaları saklar.
    Bu kısıtlamalar planlama algoritması tarafından dikkate alınır.
    """
    
    __tablename__ = 'ozel_durumlar'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Özel durum ID')
    
    # Durum türü
    # 'hoca_musaitlik': Hoca sadece belirli günlerde müsait
    # 'ders_sinav_yok': Bu ders için sınav yapılmayacak
    # 'ozel_sure': Özel sınav süresi
    durum_turu = db.Column(db.String(50), nullable=False,
                          comment='Özel durum türü')
    
    # İlişkiler
    # Bu özel durum hangi derse ait? (opsiyonel)
    ders_id = db.Column(db.Integer, db.ForeignKey('dersler.id'),
                       nullable=True, comment='Ders ID (eğer ders için ise)')
    
    # Bu özel durum hangi öğretim üyesine ait? (opsiyonel)
    ogretim_uyesi_id = db.Column(db.Integer, db.ForeignKey('ogretim_uyeleri.id'),
                                nullable=True, comment='Öğretim üyesi ID (eğer hoca için ise)')
    
    # Müsaitlik günleri (virgülle ayrılmış: "Pazartesi,Salı,Çarşamba")
    musait_gunler = db.Column(db.String(200), nullable=True,
                             comment='Müsait günler (virgülle ayrılmış)')
    
    # Müsaitlik tarih aralığı
    baslangic_tarihi = db.Column(db.Date, nullable=True,
                                 comment='Müsaitlik başlangıç tarihi')
    bitis_tarihi = db.Column(db.Date, nullable=True,
                            comment='Müsaitlik bitiş tarihi')
    
    # Özel sınav süresi (dakika)
    ozel_sinav_suresi = db.Column(db.Integer, nullable=True,
                                  comment='Özel sınav süresi (dakika)')
    
    # Özel sınıf ataması
    ozel_sinif_adi = db.Column(db.String(100), nullable=True,
                               comment='Özel sınıf adı (elle girilir)')
    ozel_sinif_kapasitesi = db.Column(db.Integer, nullable=True,
                                      comment='Özel sınıf kapasitesi')
    
    # Açıklama
    aciklama = db.Column(db.Text, nullable=True, comment='Özel durum açıklaması')
    
    # Aktiflik durumu
    aktif = db.Column(db.Boolean, default=True, nullable=False,
                     comment='Bu özel durum aktif mi?')
    
    def musait_gunler_listesi(self):
        """
        Müsait günleri liste olarak döndür.
        
        Returns:
            list: Müsait günler listesi
        """
        if not self.musait_gunler:
            return []
        return [gun.strip() for gun in self.musait_gunler.split(',')]
    
    def __repr__(self):
        """
        Özel durum nesnesinin string temsili.
        
        Returns:
            str: Durum türü ve açıklama
        """
        return f'<OzelDurum {self.durum_turu}>'

