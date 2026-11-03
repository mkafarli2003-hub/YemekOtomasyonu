import sqlite3


def veritabani_olustur():
  conn = sqlite3.connect("yemek_otomasyonu.db")
  cursor = conn.cursor()

  # 1. Çalışanlar Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS Calisan (
            calisan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            departman TEXT,
            email TEXT NOT NULL UNIQUE,
            sifre_hash TEXT NOT NULL,
            rol TEXT DEFAULT 'Calisan',
            telefon TEXT
        )
    """)

  # 2. Etkinlik Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS Etkinlik (
            etkinlik_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            tarih TEXT NOT NULL,
            restoran_adi TEXT NOT NULL,
            kisi_basi_ucret REAL NOT NULL,
            son_katilim_tarihi TEXT NOT NULL,
            durum TEXT DEFAULT 'Aktif'
        )
    """)

  # 3. Katılım Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS Katilim (
            katilim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            calisan_id INTEGER NOT NULL,
            etkinlik_id INTEGER NOT NULL,
            katilim_durumu TEXT NOT NULL,
            toplam_kisi_sayisi INTEGER NOT NULL DEFAULT 1,
            odeme_durumu TEXT DEFAULT 'Beklemede',
            kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (calisan_id) REFERENCES Calisan (calisan_id),
            FOREIGN KEY (etkinlik_id) REFERENCES Etkinlik (etkinlik_id),
            UNIQUE(calisan_id, etkinlik_id)
        )
    """)

  # 4. Refakatçi Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS Refakatci (
            refakatci_id INTEGER PRIMARY KEY AUTOINCREMENT,
            katilim_id INTEGER NOT NULL,
            ad TEXT,
            tur TEXT NOT NULL,
            yas INTEGER,
            FOREIGN KEY (katilim_id) REFERENCES Katilim (katilim_id) ON DELETE CASCADE
        )
    """)

  # 5. Ödeme Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS Odeme (
            odeme_id INTEGER PRIMARY KEY AUTOINCREMENT,
            katilim_id INTEGER NOT NULL UNIQUE,
            tutar REAL NOT NULL,
            odeme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            yontem TEXT,
            durum TEXT DEFAULT 'Beklemede',
            FOREIGN KEY (katilim_id) REFERENCES Katilim (katilim_id)
        )
    """)

  # 6. Masa Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS Masa (
            masa_id INTEGER PRIMARY KEY AUTOINCREMENT,
            etkinlik_id INTEGER NOT NULL,
            masa_no INTEGER NOT NULL,
            kapasite INTEGER NOT NULL DEFAULT 8,
            konum TEXT,
            FOREIGN KEY (etkinlik_id) REFERENCES Etkinlik (etkinlik_id),
            UNIQUE(etkinlik_id, masa_no)
        )
    """)

  # 7. Oturma Planı Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS Oturma_Plani (
            oturma_id INTEGER PRIMARY KEY AUTOINCREMENT,
            masa_id INTEGER NOT NULL,
            katilim_id INTEGER NOT NULL,
            kisi_tipi TEXT,
            FOREIGN KEY (masa_id) REFERENCES Masa (masa_id),
            FOREIGN KEY (katilim_id) REFERENCES Katilim (katilim_id)
        )
    """)

  # 8. Rapor Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS Rapor (
            rapor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            etkinlik_id INTEGER NOT NULL,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            toplam_kisi INTEGER,
            toplam_tutar REAL,
            dosya_yolu TEXT,
            FOREIGN KEY (etkinlik_id) REFERENCES Etkinlik (etkinlik_id)
        )
    """)

  conn.commit()
  conn.close()
  print("Veritabanı ve projenin tüm tabloları başarıyla oluşturuldu!")


if __name__ == "__main__":
  veritabani_olustur()