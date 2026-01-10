"""
SINAV MODELİ
============
Planlanmış sınavları temsil eder.

Her sınav bir derse, bir dersliğe ve bir zamana atanır.
"""

from models.database import db
from datetime import datetime, date, time


class Sinav(db.Model):
    """
    Sınav tablosu.
    
    Otomatik planlama sonucunda oluşturulan sınavları saklar.
    Her sınav bir ders, bir derslik ve bir zaman dilimine atanır.
    """
    
    __tablename__ = 'sinavlar'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Sınav ID')
    
    # İlişkiler
    # Her sınav bir derse aittir
    ders_id = db.Column(db.Integer, db.ForeignKey('dersler.id'),
                       nullable=False, index=True, comment='Sınav yapılacak ders ID')

    # Her sınav bir derslikte yapılır
    derslik_id = db.Column(db.Integer, db.ForeignKey('derslikler.id'),
                          nullable=False, index=True, comment='Sınav yapılacak derslik ID')

    # Sınav zamanı
    tarih = db.Column(db.Date, nullable=False, index=True, comment='Sınav tarihi')
    baslangic_saati = db.Column(db.Time, nullable=False, comment='Sınav başlangıç saati')
    bitis_saati = db.Column(db.Time, nullable=False, comment='Sınav bitiş saati')

    # Durum bilgisi
    durum = db.Column(db.String(50), default='planlandi', nullable=False,
                     index=True, comment='Sınav durumu (planlandi, iptal, tamamlandi)')
    
    # Notlar
    notlar = db.Column(db.Text, nullable=True, comment='Sınav hakkında notlar')
    
    # Bu dersliğe atanan öğrenci sayısı (bölünmüş sınavlar için)
    atanan_ogrenci_sayisi = db.Column(db.Integer, nullable=True, 
                                      comment='Bu dersliğe atanan öğrenci sayısı')
    
    # Zaman damgaları
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow,
                                comment='Sınav planlama tarihi')
    planlama_tarihi = db.Column(db.DateTime, nullable=True,
                                comment='Sınav planlama tarihi (otomatik planlama için)')
    
    def __repr__(self):
        """
        Sınav nesnesinin string temsili.
        
        Returns:
            str: Ders adı, tarih ve saat
        """
        return f'<Sinav {self.ders.ad} - {self.tarih} {self.baslangic_saati}>'

