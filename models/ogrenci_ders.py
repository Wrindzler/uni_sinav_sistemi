"""
ÖĞRENCİ-DERS İLİŞKİ MODELİ
===========================
Öğrencilerin derslere kayıtlarını temsil eder.

Bu model, bir öğrencinin hangi derslere kayıtlı olduğunu tutar.
Bu bilgi, çakışma kontrolü için kritiktir.
"""

from models.database import db


class OgrenciDers(db.Model):
    """
    Öğrenci-Ders ilişki tablosu.
    
    Bir öğrencinin hangi derslere kayıtlı olduğunu saklar.
    Bu bilgi, bir öğrencinin aynı saatte iki sınavının olmaması
    için kullanılır.
    """
    
    __tablename__ = 'ogrenci_dersler'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Kayıt ID')
    
    # İlişkiler
    # Hangi öğrenci
    ogrenci_id = db.Column(db.Integer, db.ForeignKey('ogrenciler.id'),
                          nullable=False, comment='Öğrenci ID')
    
    # Hangi ders
    ders_id = db.Column(db.Integer, db.ForeignKey('dersler.id'),
                       nullable=False, comment='Ders ID')
    
    # Tekrar kayıtları önlemek için unique constraint
    __table_args__ = (
        db.UniqueConstraint('ogrenci_id', 'ders_id', name='unique_ogrenci_ders'),
    )
    
    def __repr__(self):
        """
        Öğrenci-Ders ilişkisinin string temsili.
        
        Returns:
            str: Öğrenci ve ders bilgisi
        """
        return f'<OgrenciDers {self.ogrenci.ogrenci_no} - {self.ders.ad}>'

