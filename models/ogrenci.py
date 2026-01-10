"""
ÖĞRENCİ MODELİ
==============
Üniversitedeki öğrencileri temsil eder.

Her öğrenci birden fazla derse kayıtlı olabilir.
"""

from models.database import db


class Ogrenci(db.Model):
    """
    Öğrenci tablosu.

    Üniversitedeki tüm öğrencileri saklar.
    Öğrenciler derslere kayıt olabilir.
    """

    __tablename__ = 'ogrenciler'

    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Öğrenci ID')

    # Öğrenci bilgileri
    ogrenci_no = db.Column(db.String(20), unique=True, nullable=False,
                          comment='Öğrenci numarası (benzersiz)')
    ad = db.Column(db.String(100), nullable=False, comment='Ad')
    soyad = db.Column(db.String(100), nullable=False, comment='Soyad')
    email = db.Column(db.String(120), unique=True, nullable=True,
                     comment='E-posta adresi')

    # Fakülte ve Bölüm bilgileri
    fakulte_id = db.Column(db.Integer, db.ForeignKey('fakulteler.id'),
                           nullable=True, index=True, comment='Öğrencinin fakültesi')
    bolum_id = db.Column(db.Integer, db.ForeignKey('bolumler.id'),
                         nullable=True, index=True, comment='Öğrencinin bölümü')

    # İlişkiler
    # Bir öğrenci birden fazla derse kayıtlı olabilir
    dersler = db.relationship('OgrenciDers', backref='ogrenci', lazy=True,
                             cascade='all, delete-orphan')

    # Fakülte ve bölüm ilişkileri
    fakulte = db.relationship('Fakulte', backref='ogrenciler', lazy=True)
    bolum = db.relationship('Bolum', backref='ogrenciler', lazy=True)
    
    @property
    def tam_ad(self):
        """
        Öğrencinin tam adını döndür.
        
        Returns:
            str: Ad + Soyad
        """
        return f'{self.ad} {self.soyad}'
    
    def __repr__(self):
        """
        Öğrenci nesnesinin string temsili.
        
        Returns:
            str: Öğrenci numarası ve adı
        """
        return f'<Ogrenci {self.ogrenci_no} - {self.tam_ad}>'

