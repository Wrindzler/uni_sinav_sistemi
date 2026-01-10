"""
SINAV PLANLAMA ALGORİTMASI
==========================
Kısıt tabanlı sınav planlama algoritması (Constraint-Based Scheduling).

Algoritma Özeti:
----------------
Bu algoritma, üniversitenin tüm derslerine ait sınavları, belirtilen tüm
kısıtlamalara uygun şekilde dersliklere ve zaman dilimlerine yerleştirir.

Algoritma Türü:
- Hybrid Greedy + Backtracking
- En zor problemleri (büyük sınıflar) önce çözer
- Başarısız olursa geri adım atar (backtrack)

Temel Kısıtlamalar (Constraints):
----------------------------------
1. TEKLIK KISITLAMI (Uniqueness Constraint)
   - Bir ders için birden fazla sınav saati atanamaz
   - Her ders maksimum 1 sınav alır

2. DERSLIK KAPASITE KISITLAMI (Room Capacity Constraint)
   - Bir derslikte aynı anda birden fazla sınav yapılamaz
   - Sınav öğrenci sayısı derslik kapasitesini aşamaz

3. ÖĞRENCİ ÇAKIŞMA KISITLAMI (Student Conflict Constraint)
   - Bir öğrencinin aynı saatte iki sınavı olamaz
   - Öğrenci dersleri karşılaştırılarak kontrol edilir

4. HOCA MÜSAİTLİK KISITLAMI (Instructor Availability Constraint)
   - Hoca sadece müsait olduğu günlerde sınava girebilir
   - Özel durum tablosundan kontrol edilir

5. SAAT ARALIGI KISITLAMI (Time Gap Constraint)
   - İki sınav arası minimum aralık olmalı
   - Hocanın derslere yetişmesi için zaman gerekir

6. ÇALIŞMA GÜNÜ KISITLAMI (Working Days Constraint)
   - Sınavlar sadece belirlenen çalışma günlerinde yapılır
   - Hafta sonu sınav yapılmaz (genellikle)

7. HOCA ÇAKIŞMA KISITLAMI (Instructor Conflict Constraint) - YENİ
   - Bir hocanın aynı saatte iki FARKLI İSİMLİ dersi için sınavı olamaz
   - İSTİSNA: Aynı isimli dersler (örn: ALGORİTMA TASARIMI VE ANALİZİ)
     farklı bölümlerde olsa bile aynı saatte planlanabilir
   - Bu sayede aynı ders kodlu farklı bölüm dersleri birlikte sınava girebilir

Başarısızlık Senaryoları:
------------------------
- Tüm derslikler dolu: "Uygun derslik bulunamadı"
- Hoca müsait değil: "Hoca bu tarih aralığında müsait değil"
- Öğrenci çakışması: "Öğrenci başka sınavı var"
- Zaman aralığı yok: "İki sınav arası zaman yok"
- Hoca çakışması: "Hocanın bu saatte başka (farklı isimli) dersi var"

Algoritma: Greedy + Backtracking hibrit yaklaşımı
"""

from datetime import datetime, date, time, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from models.database import db
from models.ders import Ders
from models.derslik import Derslik
from models.sinav import Sinav
from models.ogrenci_ders import OgrenciDers
from models.ozel_durum import OzelDurum
from config import Config
import logging

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sinav_planlama.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class SinavPlanlayici:
    """
    Sınav planlama sınıfı.
    
    Tüm dersleri, kısıtlamalara uygun şekilde
    dersliklere ve zaman dilimlerine yerleştirir.
    
    Planlama Stratejisi:
    --------------------
    1. Greedy Yaklaşım: Dersler öğrenci sayısına göre sıralanır (büyükten küçüğe)
       - Büyük sınıflar için az derslik seçeneği vardır
       - Bu yüzden büyük sınıfları önce planlamak tercih edilir
       - Daha sonra küçük sınıflar kalan seçenekleri kullanabilir
    
    2. Backtracking: Başarısız olursa geri çekilir
       - Bir zaman dilimi başarısız olursa sonraki zaman denenir
       - Hala başarısız olursa sonraki derslik denenir
       - Tüm kombinasyonlar deneninceye kadar devam eder
    
    3. Sırası İle Kontroller:
       - Kapasite kontrolü (öğrenci sayısı ≤ derslik kapasitesi)
       - Zaman kontrolü (çalışma günü, saat aralığı)
       - Müsaitlik kontrolü (hoca müsait mi?)
       - Çakışma kontrolü (öğrenci başka sınavı var mı?)
       - Aralık kontrolü (önceki sınavdan sonra yeterli zaman var mı?)
    
    Kullanım Örneği:
    ----------------
    >>> from datetime import date
    >>> planlayici = SinavPlanlayici()
    >>> sonuc = planlayici.planla(
    ...     date(2024, 1, 15),
    ...     date(2024, 2, 15)
    ... )
    >>> print(f"Planlanmış: {sonuc['istatistikler']['planlanan']}")
    Planlanmış: 45
    """
    
    def __init__(self):
        """
        Planlayıcıyı başlat ve yapılandırma yükle.
        
        Config sınıfından sınav planlama ayarlarını alır:
        - Başlama ve bitiş saatleri
        - Sınavlar arası aralık
        - Çalışma günleri
        
        Öznitelikler:
        -----------
        baslangic_saati: Sınavların başlayabileceği en erken saat (int, 0-23)
        bitis_saati: Sınavların başlayabileceği en geç saat (int, 0-23)
        sinav_araligi: İki sınav arası minimum dakika (int)
        calisma_gunleri: Çalışma günleri listesi (list)
        """
        self.baslangic_saati = Config.SINAV_BASLANGIC_SAATI
        self.bitis_saati = Config.SINAV_BITIS_SAATI
        self.sinav_araligi = Config.SINAV_ARALIGI
        self.calisma_gunleri = Config.CALISMA_GUNLERI
        
        # YENİ: Bir öğrencinin günlük sınav limitleri (kademeli)
        # İdeal: günde 1 sınav, zor durumda: günde 2, en zor: günde 3
        self.gunluk_sinav_limitleri = [1, 2, 3]  # Kademeli artış
        self.gunluk_max_sinav = 1  # Başlangıç değeri (dinamik olarak değişecek)
    
    def planla(self, baslangic_tarihi: date, bitis_tarihi: date) -> Dict:
        """
        Ana planlama fonksiyonu.
        
        Belirtilen tarih aralığında tüm dersler için sınav planı oluşturur.
        
        Args:
            baslangic_tarihi: Planlama başlangıç tarihi
            bitis_tarihi: Planlama bitiş tarihi
            
        Returns:
            dict: Planlama sonucu
                - basarili: bool - Planlama başarılı mı?
                - sinavlar: list - Oluşturulan sınavlar
                - hatalar: list - Planlanamayan dersler ve nedenleri
                - istatistikler: dict - Planlama istatistikleri
        """
        logger.info("=" * 70)
        logger.info(f"🚀 SINAV PLANLAMA BAŞLATILDI")
        logger.info(f"📅 Tarih Aralığı: {baslangic_tarihi} - {bitis_tarihi}")
        logger.info("=" * 70)
        
        # Mevcut sınavları temizle (yeni planlama için)
        # Not: Gerçek uygulamada bu opsiyonel olabilir
        
        # Tüm aktif dersleri al (öğrenci sayısı 0'dan büyük olanlar)
        # ÖNEMLİ: Hiçbir öğrenci almayan dersler için sınav planlanmaz
        dersler = Ders.query.filter_by(aktif=True).filter(Ders.ogrenci_sayisi > 0).all()
        logger.info(f"📚 Toplam aktif ders sayısı (öğrencisi olan): {len(dersler)}")
        
        # Öğrenci sayısı 0 olan dersleri logla
        ogrencisiz_dersler = Ders.query.filter_by(aktif=True).filter(Ders.ogrenci_sayisi == 0).all()
        if ogrencisiz_dersler:
            logger.info(f"⏭️  Öğrencisi olmayan {len(ogrencisiz_dersler)} ders planlamadan hariç tutuldu:")
            for ders in ogrencisiz_dersler:
                logger.info(f"   - {ders.ad} (Öğrenci sayısı: 0)")
        
        # Tüm uygun derslikleri al
        derslikler = Derslik.query.filter_by(sinav_icin_uygun=True).all()
        logger.info(f"🏢 Toplam uygun derslik sayısı: {len(derslikler)}")
        
        if not derslikler:
            return {
                'basarili': False,
                'sinavlar': [],
                'hatalar': ['Hiç uygun derslik bulunamadı!'],
                'istatistikler': {}
            }
        
        # Planlama sonuçları
        planlanan_sinavlar = []
        planlanamayan_dersler = []
        
        # YENİ: Aynı isimli dersleri grupla (farklı bölümlerin aynı dersleri)
        # Örnek: "ALGORİTMA TASARIMI VE ANALİZİ" hem BLM331 hem YZM332 olabilir
        ders_gruplari = defaultdict(list)
        for ders in dersler:
            # Ders adını normalize et (büyük/küçük harf farkını kaldır)
            ders_adi_normalized = ders.ad.strip().upper()
            ders_gruplari[ders_adi_normalized].append(ders)
        
        # Aynı isimli dersleri logla
        for ders_adi, grup in ders_gruplari.items():
            if len(grup) > 1:
                kodlar = [d.kod for d in grup]
                logger.info(f"🔗 Aynı isimli dersler bulundu: {grup[0].ad} -> {kodlar}")
        
        # Grupları toplam öğrenci sayısına göre sırala (büyükten küçüğe)
        gruplar_sirali = sorted(
            ders_gruplari.values(),
            key=lambda grup: sum(d.ogrenci_sayisi for d in grup),
            reverse=True
        )
        
        # ============================================
        # KADEMELİ PLANLAMA: Sınavları günlere yay
        # ============================================
        # 1. Geçiş: Günde 1 sınav (ideal - maksimum yayılma)
        # 2. Geçiş: Günde 2 sınav (orta)
        # 3. Geçiş: Günde 3 sınav (zor durum)
        
        bekleyen_gruplar = list(gruplar_sirali)  # Planlanacak gruplar
        
        for limit in self.gunluk_sinav_limitleri:
            if not bekleyen_gruplar:
                break  # Tüm dersler planlandı
            
            self.gunluk_max_sinav = limit
            logger.info(f"")
            logger.info(f"{'='*50}")
            logger.info(f"📆 KADEME {limit}: Günde maksimum {limit} sınav ile planlama")
            logger.info(f"{'='*50}")
            
            hala_bekleyen = []
            
            for grup in bekleyen_gruplar:
                # Grup içindeki dersleri kontrol et
                planlanacak_dersler = []
                
                for ders in grup:
                    # Bu ders için zaten planlanmış sınav var mı?
                    mevcut_sinav = Sinav.query.filter_by(
                        ders_id=ders.id,
                        durum='planlandi'
                    ).first()
                    
                    if mevcut_sinav:
                        if mevcut_sinav not in planlanan_sinavlar:
                            planlanan_sinavlar.append(mevcut_sinav)
                        continue
                    
                    # Sınav yapılmayacak mı?
                    if self._ders_sinav_yapilmayacak_mi(ders):
                        logger.info(f"⏭️  {ders.ad} ({ders.kod}) - Sınav yapılmayacak olarak işaretli")
                        if not any(p['ders'].id == ders.id for p in planlanamayan_dersler):
                            planlanamayan_dersler.append({
                                'ders': ders,
                                'neden': 'Bu ders için sınav yapılmayacak olarak işaretlenmiş'
                            })
                        continue
                    
                    planlanacak_dersler.append(ders)
                
                if not planlanacak_dersler:
                    continue
                
                # Eğer birden fazla aynı isimli ders varsa, birlikte planla
                if len(planlanacak_dersler) > 1:
                    toplam_ogrenci = sum(d.ogrenci_sayisi for d in planlanacak_dersler)
                    kodlar = [d.kod for d in planlanacak_dersler]
                    logger.info(f"🔍 GRUP PLANLAMA: {planlanacak_dersler[0].ad} ({', '.join(kodlar)}) - Toplam: {toplam_ogrenci} öğrenci")
                    
                    sinavlar = self._grup_ders_planla(planlanacak_dersler, derslikler, baslangic_tarihi, bitis_tarihi)
                    
                    if sinavlar:
                        for sinav in sinavlar:
                            logger.info(f"✅ BAŞARILI (limit={limit}): {sinav.ders.ad} ({sinav.ders.kod}) - {sinav.tarih} {sinav.baslangic_saati} @ {sinav.derslik.ad}")
                            planlanan_sinavlar.append(sinav)
                    else:
                        # Bu kademede planlanamadı, sonraki kademeye bırak
                        logger.info(f"⏳ BEKLEMEDE: {planlanacak_dersler[0].ad} - limit={limit} ile planlanamadı, sonraki kademeye bırakıldı")
                        hala_bekleyen.append(grup)
                else:
                    # Tek ders, normal planlama
                    ders = planlanacak_dersler[0]
                    logger.info(f"🔍 Planlama deneniyor: {ders.ad} ({ders.kod}) (Öğrenci: {ders.ogrenci_sayisi})")
                    sinav = self._ders_planla(ders, derslikler, baslangic_tarihi, bitis_tarihi)
                    
                    if sinav:
                        logger.info(f"✅ BAŞARILI (limit={limit}): {ders.ad} - {sinav.tarih} {sinav.baslangic_saati}")
                        planlanan_sinavlar.append(sinav)
                    else:
                        # Bu kademede planlanamadı, sonraki kademeye bırak
                        logger.info(f"⏳ BEKLEMEDE: {ders.ad} - limit={limit} ile planlanamadı, sonraki kademeye bırakıldı")
                        hala_bekleyen.append(grup)
            
            bekleyen_gruplar = hala_bekleyen
            logger.info(f"📊 Kademe {limit} tamamlandı. Bekleyen: {len(bekleyen_gruplar)} grup")
        
        # Son kademeden sonra hala planlanamayan dersler
        for grup in bekleyen_gruplar:
            for ders in grup:
                # Zaten planlandı mı kontrol et
                mevcut_sinav = Sinav.query.filter_by(ders_id=ders.id, durum='planlandi').first()
                if mevcut_sinav:
                    continue
                if self._ders_sinav_yapilmayacak_mi(ders):
                    continue
                    
                hata_mesaji = self._detayli_hata_mesaji_olustur(ders)
                logger.warning(f"❌ BAŞARISIZ: {ders.ad} ({ders.kod}) - {hata_mesaji}")
                if not any(p['ders'].id == ders.id for p in planlanamayan_dersler):
                    planlanamayan_dersler.append({
                        'ders': ders,
                        'neden': hata_mesaji
                    })
        
        # İstatistikler
        toplam_ders = len(dersler)
        planlanan = len(planlanan_sinavlar)
        planlanamayan = len(planlanamayan_dersler)
        
        istatistikler = {
            'toplam_ders': toplam_ders,
            'planlanan': planlanan,
            'planlanamayan': planlanamayan,
            'basarı_orani': (planlanan / toplam_ders * 100) if toplam_ders > 0 else 0
        }
        
        # Sonuç logları
        logger.info("=" * 70)
        logger.info("📊 PLANLAMA SONUÇLARI")
        logger.info(f"✅ Planlanan Sınavlar: {planlanan}/{toplam_ders}")
        logger.info(f"❌ Planlanamayan Sınavlar: {planlanamayan}/{toplam_ders}")
        logger.info(f"📈 Başarı Oranı: {istatistikler['basarı_orani']:.1f}%")
        logger.info("=" * 70)
        
        if planlanamayan_dersler:
            logger.warning("⚠️  PLANLANAMAYAN DERSLER:")
            for item in planlanamayan_dersler:
                logger.warning(f"  - {item['ders'].ad}: {item['neden']}")
        
        return {
            'basarili': len(planlanamayan_dersler) == 0,
            'sinavlar': planlanan_sinavlar,
            'hatalar': planlanamayan_dersler,
            'istatistikler': istatistikler
        }
    
    def _grup_ders_planla(self, dersler: List[Ders], derslikler: List[Derslik],
                          baslangic_tarihi: date, bitis_tarihi: date) -> Optional[List[Sinav]]:
        """
        Aynı isimli birden fazla dersin sınavını AYNI ANDA planla.
        
        Bu fonksiyon farklı bölümlerin aynı isimli derslerini (örn: ALGORİTMA TASARIMI)
        aynı tarih ve saatte, farklı dersliklerde planlar.
        
        Args:
            dersler: Aynı isimli dersler listesi
            derslikler: Mevcut derslikler listesi
            baslangic_tarihi: Planlama başlangıç tarihi
            bitis_tarihi: Planlama bitiş tarihi
            
        Returns:
            List[Sinav]: Oluşturulan sınav nesneleri listesi veya None
        """
        # En uzun sınav süresini al (tüm dersler için aynı süre kullanılacak)
        sinav_suresi = max(self._ders_sinav_suresi_al(ders) for ders in dersler)
        
        # Tüm öğretim üyelerinin müsait günlerini birleştir (kesişim)
        tum_musait_gunler = None
        for ders in dersler:
            musait = self._hoca_musait_gunler_al(ders.ogretim_uyesi)
            if musait:
                if tum_musait_gunler is None:
                    tum_musait_gunler = set(musait)
                else:
                    tum_musait_gunler = tum_musait_gunler.intersection(set(musait))
        
        musait_gunler = list(tum_musait_gunler) if tum_musait_gunler else []
        
        # Zaman dilimlerini oluştur
        zaman_dilimleri = self._zaman_dilimleri_olustur(
            baslangic_tarihi, bitis_tarihi, sinav_suresi, musait_gunler
        )
        
        # Her zaman dilimi için dene
        for tarih, baslangic_saati, bitis_saati in zaman_dilimleri:
            # YENİ: Önce tüm dersler için günlük limit kontrolü yap
            limit_asiliyor = False
            for ders in dersler:
                if self._ogrenci_gunluk_limit_asildi_mi(ders, tarih):
                    limit_asiliyor = True
                    break
            
            if limit_asiliyor:
                continue  # Bu tarihte limit aşılacak, sonraki tarihe geç
            
            # YENİ: Hoca çakışması kontrolü - hocanın farklı isimli dersleri için
            # Not: Aynı isimli dersler zaten bu grupta, onlar için çakışma kontrol edilmez
            hoca_cakismasi = False
            for ders in dersler:
                if self._hoca_cakismasi_var_mi(ders, tarih, baslangic_saati, bitis_saati):
                    hoca_cakismasi = True
                    break
            
            if hoca_cakismasi:
                continue  # Hocanın bu saatte farklı isimli dersi var, sonraki zaman dilimine geç
            
            # Bu zaman diliminde tüm dersler için uygun derslik bul
            atamalar = []  # [(ders, derslik, ogrenci_sayisi), ...]
            kullanilan_derslik_idleri = set()
            referans_derslikler = []  # Yakınlık için referans derslikler
            basarili = True
            
            # Dersleri öğrenci sayısına göre sırala (büyük sınıflar önce)
            dersler_sirali = sorted(dersler, key=lambda d: d.ogrenci_sayisi, reverse=True)
            
            for ders in dersler_sirali:
                # Bu ders için uygun derslik(ler) bul
                # YENİ: Referans derslikler gönderilerek yakınlık önceliği sağlanıyor
                ders_atamalari = self._ders_icin_derslik_bul(
                    ders, derslikler, tarih, baslangic_saati, bitis_saati, 
                    kullanilan_derslik_idleri, referans_derslikler
                )
                
                if not ders_atamalari:
                    basarili = False
                    break
                
                # Bulunan derslikleri işaretle ve referans listesine ekle
                for derslik, ogrenci_sayisi in ders_atamalari:
                    kullanilan_derslik_idleri.add(derslik.id)
                    atamalar.append((ders, derslik, ogrenci_sayisi))
                    referans_derslikler.append(derslik)  # Sonraki dersler için referans
            
            if basarili and atamalar:
                # Tüm dersler için uygun derslik bulundu, sınavları oluştur
                olusturulan_sinavlar = []
                
                # Yakınlık bilgisini logla
                derslik_adlari = list(set([d.ad for _, d, _ in atamalar]))
                logger.info(f"  📍 Grup derslikleri (yakınlık): {derslik_adlari}")
                
                for ders, derslik, ogrenci_sayisi in atamalar:
                    sinav = Sinav(
                        ders_id=ders.id,
                        derslik_id=derslik.id,
                        tarih=tarih,
                        baslangic_saati=baslangic_saati,
                        bitis_saati=bitis_saati,
                        durum='planlandi',
                        planlama_tarihi=datetime.now(),
                        atanan_ogrenci_sayisi=ogrenci_sayisi,
                        notlar=f'Aynı isimli derslerle eş zamanlı sınav (yakın derslikler)'
                    )
                    db.session.add(sinav)
                    olusturulan_sinavlar.append(sinav)
                
                db.session.commit()
                return olusturulan_sinavlar
        
        # Uygun zaman/derslik bulunamadı
        return None
    
    def _ders_icin_derslik_bul(self, ders: Ders, derslikler: List[Derslik],
                               tarih: date, baslangic_saati: time, bitis_saati: time,
                               kullanilan_derslik_idleri: set,
                               referans_derslikler: List[Derslik] = None) -> Optional[List[Tuple[Derslik, int]]]:
        """
        Bir ders için uygun derslik(ler) bul.
        
        Tek derslik yeterliyse tek derslik, değilse birden fazla derslik döner.
        YENİ: Referans derslikler verilmişse, onlara yakın derslikler önceliklendirilir.
        
        Args:
            ders: Planlanacak ders
            derslikler: Mevcut derslikler
            tarih: Sınav tarihi
            baslangic_saati: Başlangıç saati
            bitis_saati: Bitiş saati
            kullanilan_derslik_idleri: Zaten kullanılan derslik ID'leri
            referans_derslikler: Yakınlık için referans alınacak derslikler (aynı isimli diğer derslerin derslikleri)
            
        Returns:
            List[Tuple[Derslik, int]]: (derslik, atanan_ogrenci_sayisi) listesi veya None
        """
        ogrenci_sayisi = ders.ogrenci_sayisi
        
        # Derslikleri sırala
        derslikler_sirali = self._derslikleri_akillica_sirala(derslikler, ogrenci_sayisi)
        
        # YENİ: Referans derslikler varsa, onlara yakın olanları öne al
        if referans_derslikler:
            derslikler_sirali = self._referans_yakinligina_gore_sirala(
                derslikler_sirali, referans_derslikler, kullanilan_derslik_idleri
            )
        
        # Önce tek derslik dene
        for derslik in derslikler_sirali:
            if derslik.id in kullanilan_derslik_idleri:
                continue
            if derslik.kapasite < ogrenci_sayisi:
                continue
            if self._derslik_dolu_mu(derslik, tarih, baslangic_saati, bitis_saati):
                continue
            if self._ogrenci_cakismasi_var_mi(ders, derslik, tarih, baslangic_saati, bitis_saati):
                continue
            
            # Tek derslik yeterli
            return [(derslik, ogrenci_sayisi)]
        
        # Tek derslik yetmedi, birden fazla derslik dene
        secilen = []
        toplam_kapasite = 0
        kalan_ogrenci = ogrenci_sayisi
        
        # İlk uygun dersliği bul (referans yakınlığına göre sıralı listeden)
        birincil_derslik = None
        for derslik in derslikler_sirali:
            if derslik.id in kullanilan_derslik_idleri:
                continue
            if self._derslik_dolu_mu(derslik, tarih, baslangic_saati, bitis_saati):
                continue
            if self._ogrenci_cakismasi_var_mi(ders, derslik, tarih, baslangic_saati, bitis_saati):
                continue
            birincil_derslik = derslik
            break
        
        if not birincil_derslik:
            return None
        
        atanacak = min(kalan_ogrenci, birincil_derslik.kapasite)
        secilen.append((birincil_derslik, atanacak))
        toplam_kapasite += birincil_derslik.kapasite
        kalan_ogrenci -= atanacak
        secilen_idler = {birincil_derslik.id}
        
        if toplam_kapasite >= ogrenci_sayisi:
            return secilen
        
        # Yakın derslikleri ekle
        yakin_derslikler = self._yakinlik_sirasina_gore_sirala(
            birincil_derslik, derslikler_sirali, secilen_idler | kullanilan_derslik_idleri
        )
        
        for derslik in yakin_derslikler:
            if derslik.id in kullanilan_derslik_idleri or derslik.id in secilen_idler:
                continue
            if self._derslik_dolu_mu(derslik, tarih, baslangic_saati, bitis_saati):
                continue
            if self._ogrenci_cakismasi_var_mi(ders, derslik, tarih, baslangic_saati, bitis_saati):
                continue
            
            atanacak = min(kalan_ogrenci, derslik.kapasite)
            secilen.append((derslik, atanacak))
            toplam_kapasite += derslik.kapasite
            kalan_ogrenci -= atanacak
            secilen_idler.add(derslik.id)
            
            if toplam_kapasite >= ogrenci_sayisi:
                return secilen
        
        # Yakın derslikler yetmediyse diğerlerini dene
        for derslik in derslikler_sirali:
            if derslik.id in kullanilan_derslik_idleri or derslik.id in secilen_idler:
                continue
            if self._derslik_dolu_mu(derslik, tarih, baslangic_saati, bitis_saati):
                continue
            if self._ogrenci_cakismasi_var_mi(ders, derslik, tarih, baslangic_saati, bitis_saati):
                continue
            
            atanacak = min(kalan_ogrenci, derslik.kapasite)
            secilen.append((derslik, atanacak))
            toplam_kapasite += derslik.kapasite
            kalan_ogrenci -= atanacak
            secilen_idler.add(derslik.id)
            
            if toplam_kapasite >= ogrenci_sayisi:
                return secilen
        
        # Yeterli kapasite bulunamadı
        return None
    
    def _referans_yakinligina_gore_sirala(self, derslikler: List[Derslik], 
                                          referans_derslikler: List[Derslik],
                                          kullanilan_idler: set) -> List[Derslik]:
        """
        Derslikleri referans dersliklere yakınlığına göre sırala.
        
        Bu fonksiyon aynı isimli derslerin sınavlarının birbirine yakın 
        dersliklerde yapılmasını sağlar.
        
        Args:
            derslikler: Sıralanacak derslikler
            referans_derslikler: Yakınlık için referans derslikler
            kullanilan_idler: Zaten kullanılan derslik ID'leri
            
        Returns:
            List[Derslik]: Yakınlık sırasına göre sıralanmış derslikler
        """
        if not referans_derslikler:
            return derslikler
        
        # Tüm referans dersliklerin yakınlıklarını birleştir
        yakin_derslik_adlari = set()
        for ref_derslik in referans_derslikler:
            if ref_derslik.yakinliklar:
                yakin_derslik_adlari.update(ref_derslik.yakinliklar)
        
        if not yakin_derslik_adlari:
            return derslikler
        
        # Öncelik sırası: 1) Referansa yakın, 2) Diğerleri
        yakin_olanlar = []
        diger_olanlar = []
        
        for derslik in derslikler:
            if derslik.id in kullanilan_idler:
                continue
            if derslik.ad in yakin_derslik_adlari:
                yakin_olanlar.append(derslik)
            else:
                diger_olanlar.append(derslik)
        
        # Log mesajı
        if yakin_olanlar:
            yakin_adlar = [d.ad for d in yakin_olanlar[:5]]
            ref_adlar = [d.ad for d in referans_derslikler]
            logger.debug(f"  🔗 Referans derslikler: {ref_adlar} -> Yakın derslikler: {yakin_adlar}")
        
        return yakin_olanlar + diger_olanlar
    
    def _ders_planla(self, ders: Ders, derslikler: List[Derslik],
                     baslangic_tarihi: date, bitis_tarihi: date) -> Optional[Sinav]:
        """
        Tek bir ders için sınav planla.
        
        Args:
            ders: Planlanacak ders
            derslikler: Mevcut derslikler listesi
            baslangic_tarihi: Planlama başlangıç tarihi
            bitis_tarihi: Planlama bitiş tarihi
            
        Returns:
            Sinav: Oluşturulan sınav nesnesi veya None
        """
        # Hata mesajlarını saklamak için liste
        self.son_hata_mesajlari = []
        
        # YENİ: Özel sınıf kontrolü
        ozel_sinif = self._ders_ozel_sinif_al(ders)
        if ozel_sinif:
            sinif_adi, sinif_kapasitesi = ozel_sinif
            logger.info(f"  🏫 Özel sınıf tanımlı: {sinif_adi} ({sinif_kapasitesi} kişi)")
            return self._ozel_sinif_ile_planla(ders, sinif_adi, sinif_kapasitesi, baslangic_tarihi, bitis_tarihi)
        
        # Dersin sınav süresini al
        sinav_suresi = self._ders_sinav_suresi_al(ders)
        
        # Öğretim üyesinin müsait günlerini al
        musait_gunler = self._hoca_musait_gunler_al(ders.ogretim_uyesi)
        
        # Tüm olası zaman dilimlerini oluştur
        zaman_dilimleri = self._zaman_dilimleri_olustur(
            baslangic_tarihi, bitis_tarihi, sinav_suresi, musait_gunler
        )
        
        # Derslikleri akıllı sıralama: Önce kullanım sıklığına göre, sonra kapasiteye göre
        # En az kullanılan derslikleri önceliklendir (daha dengeli dağılım için)
        derslikler_sirali = self._derslikleri_akillica_sirala(derslikler, ders.ogrenci_sayisi)
        
        # Her zaman dilimi için dene
        for tarih, baslangic_saati, bitis_saati in zaman_dilimleri:
            # Önce tek derslik ile dene
            derslik = self._uygun_derslik_bul(
                ders, derslikler_sirali, tarih, baslangic_saati, bitis_saati
            )
            
            if derslik:
                # Tek derslik yeterli, sınav oluştur
                sinav = Sinav(
                    ders_id=ders.id,
                    derslik_id=derslik.id,
                    tarih=tarih,
                    baslangic_saati=baslangic_saati,
                    bitis_saati=bitis_saati,
                    durum='planlandi',
                    planlama_tarihi=datetime.now(),
                    atanan_ogrenci_sayisi=ders.ogrenci_sayisi  # Tek derslik = tüm öğrenciler
                )
                
                # Veritabanına kaydet
                db.session.add(sinav)
                db.session.commit()
                
                return sinav
            
            # Tek derslik yeterli değilse, birden fazla derslik birleştir
            uygun_derslikler = self._uygun_derslikler_bul_birlestir(
                ders, derslikler_sirali, tarih, baslangic_saati, bitis_saati
            )
            
            if uygun_derslikler:
                # Birden fazla derslik kullanılacak
                # Her derslik için ayrı sınav kaydı oluştur
                # (Aynı ders, aynı zaman, farklı derslikler)
                derslik_adlari = [d.ad for d in uygun_derslikler]
                ilk_sinav = None
                
                # Öğrenci sayısını dersliklere dağıt
                kalan_ogrenci = ders.ogrenci_sayisi
                
                for derslik in uygun_derslikler:
                    # Bu dersliğe atanacak öğrenci sayısını hesapla
                    atanacak = min(kalan_ogrenci, derslik.kapasite)
                    kalan_ogrenci -= atanacak
                    
                    sinav = Sinav(
                        ders_id=ders.id,
                        derslik_id=derslik.id,
                        tarih=tarih,
                        baslangic_saati=baslangic_saati,
                        bitis_saati=bitis_saati,
                        durum='planlandi',
                        planlama_tarihi=datetime.now(),
                        notlar=f'Birleştirilmiş derslik: {", ".join(derslik_adlari)}',
                        atanan_ogrenci_sayisi=atanacak
                    )
                    
                    db.session.add(sinav)
                    if not ilk_sinav:
                        ilk_sinav = sinav
                
                db.session.commit()
                
                return ilk_sinav  # İlk sınavı döndür (referans için)
        
        # Uygun zaman/derslik bulunamadı
        return None
    
    def _uygun_derslik_bul(self, ders: Ders, derslikler: List[Derslik],
                           tarih: date, baslangic_saati: time, bitis_saati: time) -> Optional[Derslik]:
        """
        Belirli bir zaman dilimi için uygun derslik bul.
        
        Kısıtlamalar:
        - Derslik kapasitesi yeterli olmalı
        - Derslik o saatte boş olmalı
        - Öğrenci çakışması olmamalı
        - Öğrenci günlük sınav limiti aşılmamalı
        - Hoca çakışması olmamalı (farklı isimli dersler için)
        
        Args:
            ders: Planlanacak ders
            derslikler: Derslikler listesi
            tarih: Sınav tarihi
            baslangic_saati: Başlangıç saati
            bitis_saati: Bitiş saati
            
        Returns:
            Derslik: Uygun derslik veya None
        """
        # YENİ: Önce günlük sınav limiti kontrolü yap
        if self._ogrenci_gunluk_limit_asildi_mi(ders, tarih):
            return None  # Bu tarihte limit aşılacak, başka gün dene
        
        # YENİ: Hoca çakışması kontrolü - farklı isimli dersler için
        if self._hoca_cakismasi_var_mi(ders, tarih, baslangic_saati, bitis_saati):
            return None  # Hocanın bu saatte başka (farklı isimli) dersi var
        
        # Dersin öğrenci sayısı
        ogrenci_sayisi = ders.ogrenci_sayisi
        
        # Her derslik için kontrol et
        for derslik in derslikler:
            # Kapasite kontrolü
            if derslik.kapasite < ogrenci_sayisi:
                continue  # Bu derslik yeterli değil
            
            # Derslik çakışma kontrolü
            if self._derslik_dolu_mu(derslik, tarih, baslangic_saati, bitis_saati):
                continue  # Bu derslik o saatte dolu
            
            # Öğrenci çakışma kontrolü
            if self._ogrenci_cakismasi_var_mi(ders, derslik, tarih, baslangic_saati, bitis_saati):
                continue  # Öğrenci çakışması var
            
            # Bu derslik uygun!
            return derslik
        
        # Uygun derslik bulunamadı
        return None
    
    def _uygun_derslikler_bul_birlestir(self, ders: Ders, derslikler: List[Derslik],
                                        tarih: date, baslangic_saati: time, bitis_saati: time) -> Optional[List[Derslik]]:
        """
        Kapasite yetersizse birden fazla dersliği birleştirerek uygun derslik kombinasyonu bul.
        
        Bu fonksiyon, tek bir derslik yeterli olmadığında birden fazla dersliği
        birleştirerek kullanır. Aynı zamanda ve aynı tarihte birden fazla derslikte
        aynı dersin sınavı yapılabilir.
        
        YENİ: Derslik yakınlık bilgisi kullanılır - önce birincil dersliğin yakınlarına bakılır.
        
        Args:
            ders: Planlanacak ders
            derslikler: Derslikler listesi (akıllı sıralama ile)
            tarih: Sınav tarihi
            baslangic_saati: Başlangıç saati
            bitis_saati: Bitiş saati
            
        Returns:
            List[Derslik]: Uygun derslik kombinasyonu veya None
        """
        # YENİ: Önce günlük sınav limiti kontrolü yap
        if self._ogrenci_gunluk_limit_asildi_mi(ders, tarih):
            return None  # Bu tarihte limit aşılacak, başka gün dene
        
        # YENİ: Hoca çakışması kontrolü - farklı isimli dersler için
        if self._hoca_cakismasi_var_mi(ders, tarih, baslangic_saati, bitis_saati):
            return None  # Hocanın bu saatte başka (farklı isimli) dersi var
        
        # Dersin öğrenci sayısı
        ogrenci_sayisi = ders.ogrenci_sayisi
        
        # Derslikleri akıllı sıralama ile sırala (kullanım sıklığına göre)
        derslikler_sirali = self._derslikleri_akillica_sirala(derslikler, ogrenci_sayisi)
        
        # İlk uygun (birincil) dersliği bul
        birincil_derslik = None
        for derslik in derslikler_sirali:
            if self._derslik_dolu_mu(derslik, tarih, baslangic_saati, bitis_saati):
                continue
            if self._ogrenci_cakismasi_var_mi(ders, derslik, tarih, baslangic_saati, bitis_saati):
                continue
            birincil_derslik = derslik
            break
        
        if not birincil_derslik:
            return None  # Hiç uygun derslik yok
        
        # Uygun derslik kombinasyonu bul - yakınlık öncelikli
        secilen_derslikler = [birincil_derslik]
        toplam_kapasite = birincil_derslik.kapasite
        kullanilan_derslik_idleri = {birincil_derslik.id}
        
        # Yeterli kapasiteye ulaştıysak hemen dön
        if toplam_kapasite >= ogrenci_sayisi:
            return secilen_derslikler
        
        # Birincil dersliğin yakınlıklarına bak (sırasıyla)
        yakin_derslikler_sirali = self._yakinlik_sirasina_gore_sirala(
            birincil_derslik, derslikler_sirali, kullanilan_derslik_idleri
        )
        
        # Önce yakın dersliklerden ekle
        for derslik in yakin_derslikler_sirali:
            if derslik.id in kullanilan_derslik_idleri:
                continue
            
            if self._derslik_dolu_mu(derslik, tarih, baslangic_saati, bitis_saati):
                continue
            
            if self._ogrenci_cakismasi_var_mi(ders, derslik, tarih, baslangic_saati, bitis_saati):
                continue
            
            secilen_derslikler.append(derslik)
            toplam_kapasite += derslik.kapasite
            kullanilan_derslik_idleri.add(derslik.id)
            
            logger.info(f"  📍 Yakın derslik eklendi: {derslik.ad} (Birincil: {birincil_derslik.ad})")
            
            if toplam_kapasite >= ogrenci_sayisi:
                return secilen_derslikler
        
        # Yakın derslikler yetmediyse, diğer derslikleri de kontrol et
        for derslik in derslikler_sirali:
            if derslik.id in kullanilan_derslik_idleri:
                continue
            
            if self._derslik_dolu_mu(derslik, tarih, baslangic_saati, bitis_saati):
                continue
            
            if self._ogrenci_cakismasi_var_mi(ders, derslik, tarih, baslangic_saati, bitis_saati):
                continue
            
            secilen_derslikler.append(derslik)
            toplam_kapasite += derslik.kapasite
            kullanilan_derslik_idleri.add(derslik.id)
            
            logger.warning(f"  ⚠️ Yakın olmayan derslik eklendi: {derslik.ad} (Birincil: {birincil_derslik.ad})")
            
            if toplam_kapasite >= ogrenci_sayisi:
                return secilen_derslikler
        
        # Yeterli kapasiteye ulaşılamadı
        return None
    
    def _yakinlik_sirasina_gore_sirala(self, birincil_derslik: Derslik, 
                                        tum_derslikler: List[Derslik],
                                        kullanilan_idler: set) -> List[Derslik]:
        """
        Birincil dersliğin yakınlık listesine göre derslikleri sırala.
        
        Yakınlık listesindeki sıra önemlidir - en yakın olan önce gelir.
        
        Args:
            birincil_derslik: Ana derslik
            tum_derslikler: Tüm derslikler listesi
            kullanilan_idler: Zaten kullanılan derslik ID'leri
            
        Returns:
            List[Derslik]: Yakınlık sırasına göre sıralanmış derslikler
        """
        sonuc = []
        
        # Birincil dersliğin yakınlıkları varsa
        if birincil_derslik.yakinliklar:
            yakinlik_listesi = birincil_derslik.yakinliklar
            logger.info(f"  🏢 {birincil_derslik.ad} için yakınlıklar: {yakinlik_listesi}")
            
            # Yakınlık listesindeki sıraya göre ekle
            for yakin_ad in yakinlik_listesi:
                for derslik in tum_derslikler:
                    if derslik.ad == yakin_ad and derslik.id not in kullanilan_idler:
                        sonuc.append(derslik)
                        break
        else:
            logger.info(f"  ℹ️ {birincil_derslik.ad} için yakınlık tanımlanmamış")
        
        return sonuc
    
    def _derslik_dolu_mu(self, derslik: Derslik, tarih: date,
                        baslangic_saati: time, bitis_saati: time) -> bool:
        """
        Bir dersliğin belirli bir zaman diliminde dolu olup olmadığını kontrol et.
        
        Args:
            derslik: Kontrol edilecek derslik
            tarih: Tarih
            baslangic_saati: Başlangıç saati
            bitis_saati: Bitiş saati
            
        Returns:
            bool: Dolu ise True
        """
        # Bu derslikte bu zaman diliminde başka sınav var mı?
        cakisan_sinavlar = Sinav.query.filter(
            Sinav.derslik_id == derslik.id,
            Sinav.tarih == tarih,
            Sinav.durum == 'planlandi'
        ).all()
        
        # Zaman çakışması kontrolü
        for sinav in cakisan_sinavlar:
            if self._zaman_cakisiyor_mu(
                baslangic_saati, bitis_saati,
                sinav.baslangic_saati, sinav.bitis_saati
            ):
                return True  # Çakışma var
        
        return False  # Derslik boş
    
    def _hoca_cakismasi_var_mi(self, ders: Ders, tarih: date, 
                               baslangic_saati: time, bitis_saati: time) -> bool:
        """
        Bir hocanın aynı zaman diliminde başka bir sınavı olup olmadığını kontrol et.
        
        ÖNEMLI: Eğer dersler birebir aynı isimdeyse (farklı bölümlerin aynı dersi),
        bu durumda çakışma sayılmaz çünkü aynı ders birlikte planlanabilir.
        
        Args:
            ders: Kontrol edilecek ders
            tarih: Sınav tarihi
            baslangic_saati: Başlangıç saati
            bitis_saati: Bitiş saati
            
        Returns:
            bool: Çakışma varsa True
        """
        # Dersin öğretim üyesini al
        ogretim_uyesi = ders.ogretim_uyesi
        if not ogretim_uyesi:
            return False  # Öğretim üyesi yoksa kontrol yapılmaz
        
        # Bu hocanın diğer derslerini bul
        hocanin_dersleri = Ders.query.filter(
            Ders.ogretim_uyesi_id == ogretim_uyesi.id,
            Ders.id != ders.id,
            Ders.aktif == True
        ).all()
        
        if not hocanin_dersleri:
            return False  # Hocanın başka dersi yok
        
        # Mevcut dersin adını normalize et
        mevcut_ders_adi = ders.ad.strip().upper()
        
        # Bu derslerin aynı zaman diliminde sınavı var mı kontrol et
        for diger_ders in hocanin_dersleri:
            # Ders isimleri aynıysa çakışma sayılmaz
            # (Aynı isimli dersler birlikte planlanabilir)
            diger_ders_adi = diger_ders.ad.strip().upper()
            if diger_ders_adi == mevcut_ders_adi:
                continue  # Aynı isimli ders, çakışma değil
            
            # Bu diğer dersin sınavı var mı?
            diger_sinav = Sinav.query.filter(
                Sinav.ders_id == diger_ders.id,
                Sinav.tarih == tarih,
                Sinav.durum == 'planlandi'
            ).first()
            
            if diger_sinav:
                # Zaman çakışması var mı?
                if self._zaman_cakisiyor_mu(
                    baslangic_saati, bitis_saati,
                    diger_sinav.baslangic_saati, diger_sinav.bitis_saati
                ):
                    logger.debug(f"  ⚠️ Hoca çakışması: {ogretim_uyesi.ad} - {ders.ad} ile {diger_ders.ad} aynı saatte")
                    return True  # Çakışma var
        
        return False  # Çakışma yok
    
    def _ogrenci_cakismasi_var_mi(self, ders: Ders, derslik: Derslik,
                                  tarih: date, baslangic_saati: time, bitis_saati: time) -> bool:
        """
        Bir dersin öğrencilerinin başka bir sınavla çakışıp çakışmadığını kontrol et.
        
        ÖNEMLİ: Farklı dersliklerde aynı saatte farklı derslerin sınavları OLABİLİR.
        Sadece aynı öğrencinin aynı saatte iki sınavı olmamalı.
        
        İyileştirilmiş Versiyon:
        - Eğer öğrenci listesi varsa: Öğrenci bazlı kontrol (kesin kontrol)
        - Eğer öğrenci listesi yoksa: Çakışma kontrolü yapılmaz (farklı dersliklerde olabilir)
        
        Args:
            ders: Kontrol edilecek ders
            derslik: Derslik (şu an kullanılmıyor, gelecekte kullanılabilir)
            tarih: Sınav tarihi
            baslangic_saati: Başlangıç saati
            bitis_saati: Bitiş saati
            
        Returns:
            bool: Çakışma varsa True
        """
        # Bu derse kayıtlı öğrencileri al
        ogrenci_dersler = OgrenciDers.query.filter_by(ders_id=ders.id).all()
        
        if ogrenci_dersler:
            # DURUM 1: Öğrenci listesi VAR - Öğrenci bazlı kontrol yap
            # Bu öğrencilerin diğer derslerini al
            ogrenci_ids = [od.ogrenci_id for od in ogrenci_dersler]
            
            # Bu öğrencilerin diğer derslerine kayıtlı oldukları dersleri bul
            diger_dersler = db.session.query(OgrenciDers.ders_id).filter(
                OgrenciDers.ogrenci_id.in_(ogrenci_ids),
                OgrenciDers.ders_id != ders.id
            ).distinct().all()
            
            diger_ders_ids = [d[0] for d in diger_dersler]
            
            if not diger_ders_ids:
                return False  # Başka ders yok, çakışma yok
            
            # Bu diğer derslerin aynı zamanda sınavı var mı?
            # ÖNEMLİ: Farklı dersliklerde olsa bile, aynı öğrenci aynı saatte iki sınav olamaz
            cakisan_sinavlar = Sinav.query.filter(
                Sinav.ders_id.in_(diger_ders_ids),
                Sinav.tarih == tarih,
                Sinav.durum == 'planlandi'
            ).all()
            
            # Zaman çakışması kontrolü
            for sinav in cakisan_sinavlar:
                if self._zaman_cakisiyor_mu(
                    baslangic_saati, bitis_saati,
                    sinav.baslangic_saati, sinav.bitis_saati
                ):
                    return True  # Çakışma var (aynı öğrenci aynı saatte iki sınav)
            
            return False  # Çakışma yok
        
        else:
            # DURUM 2: Öğrenci listesi YOK
            # Öğrenci bilgisi olmadığı için kesin çakışma kontrolü yapılamaz
            # Farklı dersliklerde aynı saatte farklı derslerin sınavları olabilir
            # Sadece aynı derslikte çakışma kontrolü yapılır (bu _derslik_dolu_mu ile yapılıyor)
            return False  # Öğrenci listesi yoksa çakışma kontrolü yapılmaz
    
    def _ogrenci_gunluk_limit_asildi_mi(self, ders: Ders, tarih: date) -> bool:
        """
        Bir dersin öğrencilerinin günlük sınav limitini aşıp aşmadığını kontrol et.
        
        Bir öğrenci bir günde en fazla self.gunluk_max_sinav (varsayılan: 3) sınava girebilir.
        Bu limit aşılırsa, ders başka güne planlanmalı.
        
        Args:
            ders: Kontrol edilecek ders
            tarih: Kontrol edilecek tarih
            
        Returns:
            bool: Limit aşılacaksa True
        """
        # Bu derse kayıtlı öğrencileri al
        ogrenci_dersler = OgrenciDers.query.filter_by(ders_id=ders.id).all()
        
        if not ogrenci_dersler:
            return False  # Öğrenci listesi yoksa kontrol yapılmaz
        
        ogrenci_ids = [od.ogrenci_id for od in ogrenci_dersler]
        
        # Bu öğrencilerin diğer derslerini bul
        diger_ders_kayitlari = db.session.query(
            OgrenciDers.ogrenci_id, 
            OgrenciDers.ders_id
        ).filter(
            OgrenciDers.ogrenci_id.in_(ogrenci_ids),
            OgrenciDers.ders_id != ders.id
        ).all()
        
        if not diger_ders_kayitlari:
            return False  # Başka ders yok
        
        # Öğrenci -> dersleri eşleştir
        ogrenci_dersleri = defaultdict(set)
        for ogrenci_id, ders_id in diger_ders_kayitlari:
            ogrenci_dersleri[ogrenci_id].add(ders_id)
        
        # Bu tarihteki planlanmış sınavları bul
        gunun_sinavlari = Sinav.query.filter(
            Sinav.tarih == tarih,
            Sinav.durum == 'planlandi'
        ).all()
        
        # Hangi derslerin o gün sınavı var
        gundeki_ders_ids = set(sinav.ders_id for sinav in gunun_sinavlari)
        
        # Her öğrenci için o günkü sınav sayısını hesapla
        for ogrenci_id in ogrenci_ids:
            ogrenci_diger_dersleri = ogrenci_dersleri.get(ogrenci_id, set())
            
            # Bu öğrencinin o gün kaç sınavı var?
            ogrencinin_gundeki_sinavlari = ogrenci_diger_dersleri.intersection(gundeki_ders_ids)
            mevcut_sinav_sayisi = len(ogrencinin_gundeki_sinavlari)
            
            # Bu dersi de eklersek limit aşılacak mı?
            # +1 çünkü şu an planlamaya çalıştığımız dersi de sayıyoruz
            if mevcut_sinav_sayisi + 1 > self.gunluk_max_sinav:
                logger.debug(f"  ⚠️ Günlük limit aşılacak: Öğrenci {ogrenci_id} için {tarih} tarihinde {mevcut_sinav_sayisi + 1} sınav olacak (limit: {self.gunluk_max_sinav})")
                return True  # En az bir öğrenci için limit aşılacak
        
        return False  # Limit aşılmayacak
    
    def _zaman_cakisiyor_mu(self, bas1: time, bit1: time, bas2: time, bit2: time) -> bool:
        """
        İki zaman diliminin çakışıp çakışmadığını kontrol et.
        
        Args:
            bas1, bit1: İlk zaman dilimi
            bas2, bit2: İkinci zaman dilimi
            
        Returns:
            bool: Çakışma varsa True
        """
        # Zamanları datetime'a çevir (aynı gün için)
        dt_bas1 = datetime.combine(date.today(), bas1)
        dt_bit1 = datetime.combine(date.today(), bit1)
        dt_bas2 = datetime.combine(date.today(), bas2)
        dt_bit2 = datetime.combine(date.today(), bit2)
        
        # Çakışma kontrolü: İki zaman dilimi kesişiyor mu?
        return not (dt_bit1 <= dt_bas2 or dt_bit2 <= dt_bas1)
    
    def _zaman_dilimleri_olustur(self, baslangic_tarihi: date, bitis_tarihi: date,
                                 sinav_suresi: int, musait_gunler: List[str]) -> List[Tuple[date, time, time]]:
        """
        Belirtilen tarih aralığı için tüm olası zaman dilimlerini oluştur.
        
        Args:
            baslangic_tarihi: Başlangıç tarihi
            bitis_tarihi: Bitiş tarihi
            sinav_suresi: Sınav süresi (dakika)
            musait_gunler: Müsait günler listesi (boşsa tüm günler)
            
        Returns:
            list: (tarih, başlangıç_saati, bitiş_saati) tuple'ları listesi
        """
        zaman_dilimleri = []
        mevcut_tarih = baslangic_tarihi
        
        # Tarih aralığını tara
        while mevcut_tarih <= bitis_tarihi:
            # Haftanın gününü al
            gun_adi = self._tarih_gun_adi(mevcut_tarih)
            
            # Çalışma günü kontrolü: Pazar ve Cumartesi hariç tutulur
            if self.calisma_gunleri and gun_adi not in self.calisma_gunleri:
                mevcut_tarih += timedelta(days=1)
                continue
            
            # Müsait gün kontrolü (hoca özel durumu varsa)
            if musait_gunler and gun_adi not in musait_gunler:
                mevcut_tarih += timedelta(days=1)
                continue
            
            # Bu gün için olası saatleri oluştur
            saat_int = self.baslangic_saati
            
            while saat_int < self.bitis_saati:
                # Başlangıç ve bitiş saatini hesapla
                saat = time(saat_int, 0)
                baslangic_dt = datetime.combine(mevcut_tarih, saat)
                bitis_dt = baslangic_dt + timedelta(minutes=sinav_suresi)
                bitis_saati = bitis_dt.time()
                
                # Bitiş saati sınırları aşmamalı
                if bitis_saati > time(self.bitis_saati, 0):
                    break
                
                zaman_dilimleri.append((mevcut_tarih, saat, bitis_saati))
                
                # Sonraki zaman dilimi için saat aralığı ekle
                saat_dt = datetime.combine(mevcut_tarih, saat)
                saat_dt += timedelta(minutes=sinav_suresi + self.sinav_araligi)
                saat_int = saat_dt.hour
                if saat_dt.minute > 0:
                    saat_int += 1
            
            mevcut_tarih += timedelta(days=1)
        
        return zaman_dilimleri
    
    def _tarih_gun_adi(self, tarih: date) -> str:
        """
        Bir tarihin haftanın hangi günü olduğunu Türkçe olarak döndür.
        
        Args:
            tarih: Tarih
            
        Returns:
            str: Gün adı (Pazartesi, Salı, vb.)
        """
        gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        return gunler[tarih.weekday()]
    
    def _ders_sinav_suresi_al(self, ders: Ders) -> int:
        """
        Bir dersin sınav süresini al.
        
        Özel durum varsa onu kullan, yoksa dersin normal süresini kullan.
        
        Args:
            ders: Ders
            
        Returns:
            int: Sınav süresi (dakika)
        """
        # Özel durum kontrolü
        ozel_durum = OzelDurum.query.filter_by(
            ders_id=ders.id,
            durum_turu='ozel_sure',
            aktif=True
        ).first()
        
        if ozel_durum and ozel_durum.ozel_sinav_suresi:
            return ozel_durum.ozel_sinav_suresi
        
        # Normal süre
        return ders.sinav_suresi
    
    def _hoca_musait_gunler_al(self, ogretim_uyesi) -> List[str]:
        """
        Bir öğretim üyesinin müsait günlerini al.
        
        Args:
            ogretim_uyesi: Öğretim üyesi
            
        Returns:
            list: Müsait günler listesi (boşsa tüm günler müsait)
        """
        # Özel durum kontrolü
        ozel_durum = OzelDurum.query.filter_by(
            ogretim_uyesi_id=ogretim_uyesi.id,
            durum_turu='hoca_musaitlik',
            aktif=True
        ).first()
        
        if ozel_durum:
            return ozel_durum.musait_gunler_listesi()
        
        # Özel durum yoksa tüm günler müsait
        return []
    
    def _ders_sinav_yapilmayacak_mi(self, ders: Ders) -> bool:
        """
        Bir ders için sınav yapılmayacak mı kontrol et.
        
        Args:
            ders: Ders
            
        Returns:
            bool: Sınav yapılmayacaksa True
        """
        ozel_durum = OzelDurum.query.filter_by(
            ders_id=ders.id,
            durum_turu='ders_sinav_yok',
            aktif=True
        ).first()
        
        return ozel_durum is not None
    
    def _ozel_sinif_ile_planla(self, ders: Ders, sinif_adi: str, sinif_kapasitesi: int,
                               baslangic_tarihi: date, bitis_tarihi: date) -> Optional[Sinav]:
        """
        Özel sınıf tanımlı ders için sınav planla.
        
        Eğer sınıf sistemde varsa o dersliği kullanır.
        Yoksa özel sınıf bilgisiyle sınav oluşturur.
        
        Args:
            ders: Planlanacak ders
            sinif_adi: Özel sınıf adı
            sinif_kapasitesi: Özel sınıf kapasitesi
            baslangic_tarihi: Planlama başlangıç tarihi
            bitis_tarihi: Planlama bitiş tarihi
            
        Returns:
            Sinav: Oluşturulan sınav nesnesi veya None
        """
        # Dersin sınav süresini al
        sinav_suresi = self._ders_sinav_suresi_al(ders)
        
        # Öğretim üyesinin müsait günlerini al
        musait_gunler = self._hoca_musait_gunler_al(ders.ogretim_uyesi)
        
        # Zaman dilimlerini oluştur
        zaman_dilimleri = self._zaman_dilimleri_olustur(
            baslangic_tarihi, bitis_tarihi, sinav_suresi, musait_gunler
        )
        
        # Sistemde bu isimde derslik var mı kontrol et
        ozel_derslik = Derslik.query.filter_by(ad=sinif_adi).first()
        
        if ozel_derslik:
            # Derslik sistemde var, normal planlama yap ama sadece bu dersliği kullan
            logger.info(f"  ✓ Özel sınıf sistemde bulundu: {sinif_adi}")
            
            for tarih, baslangic_saati, bitis_saati in zaman_dilimleri:
                # Günlük limit kontrolü
                if self._ogrenci_gunluk_limit_asildi_mi(ders, tarih):
                    continue
                
                # Hoca çakışması kontrolü - farklı isimli dersler için
                if self._hoca_cakismasi_var_mi(ders, tarih, baslangic_saati, bitis_saati):
                    continue
                
                # Derslik dolu mu?
                if self._derslik_dolu_mu(ozel_derslik, tarih, baslangic_saati, bitis_saati):
                    continue
                
                # Öğrenci çakışması var mı?
                if self._ogrenci_cakismasi_var_mi(ders, ozel_derslik, tarih, baslangic_saati, bitis_saati):
                    continue
                
                # Sınav oluştur
                sinav = Sinav(
                    ders_id=ders.id,
                    derslik_id=ozel_derslik.id,
                    tarih=tarih,
                    baslangic_saati=baslangic_saati,
                    bitis_saati=bitis_saati,
                    durum='planlandi',
                    planlama_tarihi=datetime.now(),
                    atanan_ogrenci_sayisi=ders.ogrenci_sayisi,
                    notlar=f'Özel sınıf ataması: {sinif_adi}'
                )
                
                db.session.add(sinav)
                db.session.commit()
                
                return sinav
        else:
            # Derslik sistemde yok, yeni derslik oluştur
            logger.info(f"  + Özel sınıf sisteme ekleniyor: {sinif_adi} ({sinif_kapasitesi} kişi)")
            
            yeni_derslik = Derslik(
                ad=sinif_adi,
                kapasite=sinif_kapasitesi,
                sinav_icin_uygun=True,
                aciklama=f'Özel durum ile eklendi - {ders.ad} dersi için'
            )
            db.session.add(yeni_derslik)
            db.session.commit()
            
            # Şimdi planlama yap
            for tarih, baslangic_saati, bitis_saati in zaman_dilimleri:
                # Günlük limit kontrolü
                if self._ogrenci_gunluk_limit_asildi_mi(ders, tarih):
                    continue
                
                # Hoca çakışması kontrolü - farklı isimli dersler için
                if self._hoca_cakismasi_var_mi(ders, tarih, baslangic_saati, bitis_saati):
                    continue
                
                # Öğrenci çakışması var mı?
                if self._ogrenci_cakismasi_var_mi(ders, yeni_derslik, tarih, baslangic_saati, bitis_saati):
                    continue
                
                # Sınav oluştur
                sinav = Sinav(
                    ders_id=ders.id,
                    derslik_id=yeni_derslik.id,
                    tarih=tarih,
                    baslangic_saati=baslangic_saati,
                    bitis_saati=bitis_saati,
                    durum='planlandi',
                    planlama_tarihi=datetime.now(),
                    atanan_ogrenci_sayisi=ders.ogrenci_sayisi,
                    notlar=f'Özel sınıf ataması: {sinif_adi}'
                )
                
                db.session.add(sinav)
                db.session.commit()
                
                return sinav
        
        # Uygun zaman bulunamadı
        return None
    
    def _ders_ozel_sinif_al(self, ders: Ders) -> Optional[Tuple[str, int]]:
        """
        Bir ders için özel sınıf tanımlı mı kontrol et.
        
        Args:
            ders: Ders
            
        Returns:
            Tuple[str, int]: (sınıf_adı, kapasite) veya None
        """
        ozel_durum = OzelDurum.query.filter_by(
            ders_id=ders.id,
            durum_turu='ozel_sinif',
            aktif=True
        ).first()
        
        if ozel_durum and ozel_durum.ozel_sinif_adi and ozel_durum.ozel_sinif_kapasitesi:
            return (ozel_durum.ozel_sinif_adi, ozel_durum.ozel_sinif_kapasitesi)
        
        return None
    
    def _derslikleri_akillica_sirala(self, derslikler: List[Derslik], ogrenci_sayisi: int) -> List[Derslik]:
        """
        Derslikleri akıllı bir şekilde sırala.
        
        YENİ Sıralama kriterleri (öncelik sırasıyla):
        1. TEK SINIF ÖNCELİĞİ: Kapasitesi yeterli olanlar önce (minimum sınıf bölünmesi)
        2. Kapasite optimizasyonu: Yeterli kapasiteli derslikler arasında en küçük kapasite (israf minimize)
        3. Kullanım sıklığı: Az kullanılan derslikler önce (dengeli dağılım)
        4. Yetersiz kapasiteli derslikler en sona (birden fazla sınıf gerektirecekler)
        
        Örnek: 61 öğrenci için
        - AMFİA (100 kişi) -> kapasitesi yeterli, TEK SINIF = ÖNCELİKLİ
        - E101 (48 kişi) -> kapasitesi yetersiz, 2 SINIF GEREKİR = EN SONA
        
        Args:
            derslikler: Sıralanacak derslikler listesi
            ogrenci_sayisi: Dersin öğrenci sayısı
            
        Returns:
            List[Derslik]: Sıralanmış derslikler listesi
        """
        # Her derslik için kullanım sayısını hesapla
        derslik_kullanim_sayilari = {}
        for derslik in derslikler:
            # Bu derslik için planlanmış sınav sayısı
            kullanim_sayisi = Sinav.query.filter_by(
                derslik_id=derslik.id,
                durum='planlandi'
            ).count()
            derslik_kullanim_sayilari[derslik.id] = kullanim_sayisi
        
        def siralama_kriteri(derslik: Derslik) -> Tuple[int, int, int, int]:
            """
            Sıralama kriteri fonksiyonu.
            
            Returns:
                Tuple: (kapasite_yeterli_mi, kapasite, kullanim_sayisi, -kapasite)
                - kapasite_yeterli_mi: 0 = yeterli (önce), 1 = yetersiz (sonra)
                - kapasite: Yeterli olanlar arasında en küçük kapasiteli önce (israf minimize)
                - kullanim_sayisi: Az kullanılan önce
                - -kapasite: Aynı durumda büyük kapasiteli önce
            """
            kullanim = derslik_kullanim_sayilari.get(derslik.id, 0)
            
            # EN ÖNEMLİ: Kapasitesi yeterli mi? (Tek sınıfla çözülebilir mi?)
            if derslik.kapasite >= ogrenci_sayisi:
                # Kapasitesi YETERLİ - TEK SINIF İLE ÇÖZÜLEBİLİR
                # Bu derslikler öncelikli! (kapasite_yeterli = 0)
                # Aralarında en küçük kapasiteli olan tercih edilir (israf minimize)
                return (0, derslik.kapasite, kullanim, -derslik.kapasite)
            else:
                # Kapasitesi YETERSİZ - BİRDEN FAZLA SINIF GEREKİR
                # Bu derslikler en sona! (kapasite_yeterli = 1)
                return (1, 0, kullanim, -derslik.kapasite)
        
        # Sırala: Önce tek sınıfla çözülebilecekler, sonra diğerleri
        derslikler_sirali = sorted(derslikler, key=siralama_kriteri)
        
        # Log: İlk birkaç dersliği göster
        yeterli_kapasiteli = [d for d in derslikler_sirali if d.kapasite >= ogrenci_sayisi]
        if yeterli_kapasiteli:
            logger.debug(f"📊 {ogrenci_sayisi} öğrenci için tek sınıf seçenekleri: {[d.ad + f'({d.kapasite})' for d in yeterli_kapasiteli[:3]]}")
        else:
            logger.debug(f"📊 {ogrenci_sayisi} öğrenci için tek sınıf yeterli değil, birden fazla sınıf kullanılacak")
        
        return derslikler_sirali
    
    def _detayli_hata_mesaji_olustur(self, ders: Ders) -> str:
        """
        Planlanamayan ders için detaylı hata mesajı oluştur.
        
        Args:
            ders: Planlanamayan ders
            
        Returns:
            str: Detaylı hata mesajı
        """
        mesajlar = []
        
        # Kapasite kontrolü
        toplam_derslik_kapasitesi = sum(d.kapasite for d in Derslik.query.filter_by(sinav_icin_uygun=True).all())
        if ders.ogrenci_sayisi > toplam_derslik_kapasitesi:
            mesajlar.append(f"⚠️ Öğrenci sayısı ({ders.ogrenci_sayisi}) toplam derslik kapasitesini ({toplam_derslik_kapasitesi}) aşıyor")
        
        # Hoca müsaitlik kontrolü
        ogretim_uyesi = ders.ogretim_uyesi
        musait_gunler = self._hoca_musait_gunler_al(ogretim_uyesi)
        if musait_gunler:
            mesajlar.append(f"ℹ️ Hoca sadece şu günlerde müsait: {', '.join(musait_gunler)}")
        
        # Genel mesaj
        if not mesajlar:
            mesajlar.append("❌ Uygun zaman/derslik bulunamadı - Tüm zaman dilimleri dolu veya uygun değil")
        
        return " | ".join(mesajlar)

