"""
DERS MODELİ
===========
Üniversitedeki dersleri temsil eder.

Her ders bir veya birden fazla bölüme ait olabilir ve bir öğretim üyesi tarafından verilir.
"""

from models.database import db


# Ders-Bölüm çoktan-çoka ilişki tablosu
# Bir ders birden fazla bölüme ait olabilir (örn: seçmeli dersler)
ders_bolumler = db.Table('ders_bolumler',
    db.Column('ders_id', db.Integer, db.ForeignKey('dersler.id'), primary_key=True),
    db.Column('bolum_id', db.Integer, db.ForeignKey('bolumler.id'), primary_key=True)
)


class Ders(db.Model):
    """
    Ders tablosu.
    
    Üniversitedeki tüm dersleri saklar.
    Her ders için sınav bilgileri de burada tutulur.
    """
    
    __tablename__ = 'dersler'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Ders ID')
    
    # Ders bilgileri
    ad = db.Column(db.String(200), nullable=False, comment='Ders adı')
    kod = db.Column(db.String(20), nullable=True, comment='Ders kodu')
    aciklama = db.Column(db.Text, nullable=True, comment='Ders açıklaması')
    
    # İlişkiler
    # Her ders bir bölüme aittir
    bolum_id = db.Column(db.Integer, db.ForeignKey('bolumler.id'),
                        nullable=False, index=True, comment='Bağlı olduğu bölüm ID')

    # Her ders bir öğretim üyesi tarafından verilir
    ogretim_uyesi_id = db.Column(db.Integer, db.ForeignKey('ogretim_uyeleri.id'),
                                 nullable=False, index=True, comment='Dersi veren öğretim üyesi ID')
    
    # Öğrenci bilgileri
    ogrenci_sayisi = db.Column(db.Integer, nullable=False, default=0,
                              comment='Derse kayıtlı öğrenci sayısı')
    
    # Sınav bilgileri
    sinav_suresi = db.Column(db.Integer, nullable=False, default=60,
                            comment='Sınav süresi (dakika) - 30, 60, 90, 120')
    sinav_turu = db.Column(db.String(50), nullable=False, default='yazili',
                          comment='Sınav türü (yazılı, uygulama, proje vb.)')
    
    # Aktiflik durumu
    aktif = db.Column(db.Boolean, default=True, nullable=False,
                     comment='Ders aktif mi?')
    
    # İlişkiler
    # Bir dersin birden fazla sınavı olabilir (farklı dönemler için)
    sinavlar = db.relationship('Sinav', backref='ders', lazy=True,
                              cascade='all, delete-orphan')
    
    # Bir derse birden fazla öğrenci kayıtlı olabilir
    ogrenciler = db.relationship('OgrenciDers', backref='ders', lazy=True,
                                cascade='all, delete-orphan')
    
    # Bir dersin özel durumları olabilir
    ozel_durumlar = db.relationship('OzelDurum', backref='ders', lazy=True,
                                   cascade='all, delete-orphan')
    
    # Bir ders birden fazla bölüme ait olabilir (seçmeli dersler için)
    # bolum_id ana bölümü temsil eder, ek bölümler bu ilişki ile tanımlanır
    ek_bolumler = db.relationship('Bolum', secondary=ders_bolumler, lazy='dynamic',
                                  backref=db.backref('ortak_dersler', lazy='dynamic'))
    
    @property
    def tum_bolumler(self):
        """
        Dersin bağlı olduğu tüm bölümleri döndür (ana bölüm + ek bölümler).
        
        Returns:
            list: Bölüm listesi
        """
        bolumler = []
        if self.bolum:
            bolumler.append(self.bolum)
        for bolum in self.ek_bolumler:
            if bolum not in bolumler:
                bolumler.append(bolum)
        return bolumler
    
    @property
    def bolum_adlari(self):
        """
        Dersin bağlı olduğu tüm bölümlerin adlarını virgülle ayrılmış olarak döndür.
        
        Returns:
            str: Bölüm adları
        """
        return ', '.join([b.ad for b in self.tum_bolumler])
    
    def __repr__(self):
        """
        Ders nesnesinin string temsili.
        
        Returns:
            str: Ders adı ve kodu
        """
        return f'<Ders {self.ad} ({self.kod})>'

