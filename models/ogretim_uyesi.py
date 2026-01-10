"""
ÖĞRETİM ÜYESİ MODELİ
====================
Üniversitedeki öğretim üyelerini temsil eder.

Her öğretim üyesi birden fazla ders verebilir.
Her öğretim üyesi birden fazla bölümde görev alabilir.
"""

from models.database import db


# Öğretim üyesi - Bölüm ara tablosu (Many-to-Many ilişki)
ogretim_uyesi_bolum = db.Table('ogretim_uyesi_bolum',
    db.Column('ogretim_uyesi_id', db.Integer, db.ForeignKey('ogretim_uyeleri.id'), primary_key=True),
    db.Column('bolum_id', db.Integer, db.ForeignKey('bolumler.id'), primary_key=True)
)


class OgretimUyesi(db.Model):
    """
    Öğretim üyesi tablosu.
    
    Üniversitedeki tüm öğretim üyelerini saklar.
    """
    
    __tablename__ = 'ogretim_uyeleri'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Öğretim üyesi ID')
    
    # Öğretim üyesi bilgileri
    ad = db.Column(db.String(100), nullable=False, comment='Ad')
    soyad = db.Column(db.String(100), nullable=False, comment='Soyad')
    email = db.Column(db.String(120), unique=True, nullable=True,
                     comment='E-posta adresi')

    # Fakülte ve Bölüm bilgileri (geriye uyumluluk için korunuyor - ana bölüm)
    fakulte_id = db.Column(db.Integer, db.ForeignKey('fakulteler.id'),
                          nullable=True, comment='Öğretim üyesinin ana fakültesi')
    bolum_id = db.Column(db.Integer, db.ForeignKey('bolumler.id'),
                        nullable=True, comment='Öğretim üyesinin ana bölümü')
    
    # İlişkiler
    # Bir öğretim üyesi birden fazla ders verebilir
    dersler = db.relationship('Ders', backref='ogretim_uyesi', lazy=True)

    # Bir öğretim üyesinin özel durumları olabilir (müsaitlik günleri)
    ozel_durumlar = db.relationship('OzelDurum', backref='ogretim_uyesi', lazy=True,
                                   cascade='all, delete-orphan')

    # Fakülte ve bölüm ilişkileri (ana bölüm)
    fakulte = db.relationship('Fakulte', backref='ogretim_uyeleri', lazy=True)
    bolum = db.relationship('Bolum', backref='ogretim_uyeleri', lazy=True)
    
    # Çoklu bölüm ilişkisi (Many-to-Many)
    bolumler = db.relationship('Bolum', secondary=ogretim_uyesi_bolum,
                               backref=db.backref('bolum_ogretim_uyeleri', lazy='dynamic'),
                               lazy='dynamic')
    
    @property
    def tam_ad(self):
        """
        Öğretim üyesinin tam adını döndür.
        
        Returns:
            str: Ad + Soyad
        """
        return f'{self.ad} {self.soyad}'
    
    def __repr__(self):
        """
        Öğretim üyesi nesnesinin string temsili.
        
        Returns:
            str: Öğretim üyesinin tam adı
        """
        return f'<OgretimUyesi {self.tam_ad}>'

