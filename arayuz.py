import sqlite3
from tkinter import *
from tkinter import messagebox
from tkinter import ttk


# Veritabanı ve Tabloları Hazırlama
def veritabani_kur():
  conn = sqlite3.connect("yemek_otomasyonu.db")
  cursor = conn.cursor()

  # Eski tabloları temizleyip güncel ve ilişkisel yapıyı kuruyoruz
  cursor.execute("DROP TABLE IF EXISTS Odeme")
  cursor.execute("DROP TABLE IF EXISTS Refakatci")
  cursor.execute("DROP TABLE IF EXISTS Katilim")
  cursor.execute("DROP TABLE IF EXISTS Etkinlik")
  cursor.execute("DROP TABLE IF EXISTS Calisan")

  # 1. Calisan Tablosu
  cursor.execute(
      """
        CREATE TABLE Calisan (
            calisan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT,
            soyad TEXT,
            departman TEXT,
            email TEXT UNIQUE,
            sifre_hash TEXT
        )
    """
  )

  # 2. Etkinlik Tablosu
  cursor.execute(
      """
        CREATE TABLE Etkinlik (
            etkinlik_id INTEGER PRIMARY KEY AUTOINCREMENT,
            etkinlik_adi TEXT,
            tarih TEXT,
            mekan TEXT,
            kisi_basi_ucret REAL
        )
    """
  )

  # 3. Katilim Tablosu (Çalışan ve Etkinlik Arasındaki Çoka-Çok İlişki)
  cursor.execute(
      """
        CREATE TABLE Katilim (
            katilim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            calisan_id INTEGER,
            etkinlik_id INTEGER,
            katilim_durumu TEXT,
            toplam_kisi_sayisi INTEGER,
            odeme_durumu TEXT,
            UNIQUE(calisan_id, etkinlik_id)
        )
    """
  )

  # 4. Refakatci Tablosu
  cursor.execute(
      """
        CREATE TABLE Refakatci (
            refakatci_id INTEGER PRIMARY KEY AUTOINCREMENT,
            katilim_id INTEGER,
            ad TEXT,
            tur TEXT,
            yas INTEGER
        )
    """
  )

  # 5. Odeme Tablosu
  cursor.execute(
      """
        CREATE TABLE Odeme (
            odeme_id INTEGER PRIMARY KEY AUTOINCREMENT,
            katilim_id INTEGER UNIQUE,
            tutar REAL,
            yontem TEXT,
            durum TEXT
        )
    """
  )

  # Varsayılan Aktif Etkinliği Ekle
  cursor.execute(
      """
        INSERT INTO Etkinlik (etkinlik_adi, tarih, mekan, kisi_basi_ucret)
        VALUES ('BT Departmanı Yıl Sonu Yemeği', '2026-12-31', 'Grand Amasya Otel', 500.0)
    """
  )

  conn.commit()
  conn.close()


# Uygulama Başlangıcında Veritabanını Kur
veritabani_kur()

# --- ANA PENCERE ---
pencere = Tk()
pencere.title("Yemek Gecesi Otomasyon Sistemi - Bitirme Projesi")
pencere.geometry("550x700")


# Kayıt Ol Fonksiyonu
def calisan_kaydet():
  ad = entry_ad.get().strip()
  soyad = entry_soyad.get().strip()
  departman = entry_dep.get().strip()
  email = entry_email.get().strip()

  if not ad or not soyad or not email:
    messagebox.showerror(
        "Hata", "Lütfen Ad, Soyad ve E-posta alanlarını doldurun!"
    )
    return

  try:
    conn = sqlite3.connect("yemek_otomasyonu.db")
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO Calisan (ad, soyad, departman, email, sifre_hash)
            VALUES (?, ?, ?, ?, '123456')
        """,
        (ad, soyad, departman, email),
    )
    conn.commit()
    conn.close()
    messagebox.showinfo("Başarılı", f"Çalışan {ad} {soyad} sisteme kaydedildi!")
    entry_ad.delete(0, END)
    entry_soyad.delete(0, END)
    entry_dep.delete(0, END)
    entry_email.delete(0, END)
  except sqlite3.IntegrityError:
    messagebox.showerror(
        "Hata", "Bu e-posta adresi ile zaten bir kayıt mevcut!"
    )
  except Exception as e:
    messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


# Katılım Bildir Fonksiyonu
def katilim_bildir():
  email = entry_katilim_email.get().strip()
  durum = katilim_durumu.get()
  ref_var_mi = ref_durumu.get()
  ref_ad = entry_ref_ad.get().strip()

  if not email:
    messagebox.showerror("Hata", "Lütfen e-posta adresinizi girin!")
    return

  conn = sqlite3.connect("yemek_otomasyonu.db")
  cursor = conn.cursor()

  cursor.execute(
      "SELECT calisan_id, ad, soyad FROM Calisan WHERE email = ?", (email,)
  )
  calisan = cursor.fetchone()

  if not calisan:
    messagebox.showerror(
        "Hata", "Bu e-posta ile kayıtlı çalışan bulunamadı! Önce kayıt olun."
    )
    conn.close()
    return

  calisan_id = calisan[0]
  calisan_ad_soyad = f"{calisan[1]} {calisan[2]}"

  cursor.execute("SELECT etkinlik_id, kisi_basi_ucret FROM Etkinlik LIMIT 1")
  etkinlik = cursor.fetchone()
  etkinlik_id = etkinlik[0]
  ucret = etkinlik[1]

  toplam_kisi = 2 if ref_var_mi == "Evet" else 1
  toplam_tutar = ucret * toplam_kisi

  # Katılım Kaydı
  cursor.execute(
      """
        INSERT INTO Katilim (calisan_id, etkinlik_id, katilim_durumu, toplam_kisi_sayisi, odeme_durumu)
        VALUES (?, ?, ?, ?, 'Beklemede')
        ON CONFLICT(calisan_id, etkinlik_id) 
        DO UPDATE SET katilim_durumu=excluded.katilim_durumu, toplam_kisi_sayisi=excluded.toplam_kisi_sayisi
    """,
      (calisan_id, etkinlik_id, durum, toplam_kisi),
  )

  cursor.execute(
      "SELECT katilim_id FROM Katilim WHERE calisan_id = ? AND etkinlik_id = ?",
      (calisan_id, etkinlik_id),
  )
  katilim_id_val = cursor.fetchone()[0]

  # Eski refakatçi kaydını temizle ve yenisini ekle
  cursor.execute(
      "DELETE FROM Refakatci WHERE katilim_id = ?", (katilim_id_val,)
  )
  if ref_var_mi == "Evet" and ref_ad:
    cursor.execute(
        """
            INSERT INTO Refakatci (katilim_id, ad, tur, yas)
            VALUES (?, ?, 'Misafir', 25)
        """,
        (katilim_id_val, ref_ad),
    )

  # Ödeme Tablosu Güncelleme
  cursor.execute(
      """
        INSERT INTO Odeme (katilim_id, tutar, yontem, durum)
        VALUES (?, ?, 'Nakit/Elden', 'Beklemede')
        ON CONFLICT(katilim_id) DO UPDATE SET tutar=excluded.tutar
    """,
      (katilim_id_val, toplam_tutar),
  )

  conn.commit()
  conn.close()

  messagebox.showinfo(
      "Başarılı",
      f"Sayın {calisan_ad_soyad},\nKatılımınız kaydedildi!\nToplam Tutar:"
      f" {toplam_tutar} TL",
  )


# --- YÖNETİCİ RAPORLAMA PANELİ (TABLO GÖRÜNÜMÜ) ---
def yonetici_paneli_ac():
  yonetici_penceresi = Toplevel(pencere)
  yonetici_penceresi.title("Yönetici Raporlama ve Katılımcı Listesi")
  yonetici_penceresi.geometry("750x450")

  Label(
      yonetici_penceresi,
      text="Yemek Etkinliği Katılımcı ve Bütçe Raporu",
      font=("Arial", 12, "bold"),
  ).pack(pady=10)

  # Tablo (Treeview) Yapısı
  columns = (
      "Ad Soyad",
      "Departman",
      "Durum",
      "Kişi Sayısı",
      "Refakatçi",
      "Toplam Tutar",
  )
  tree = ttk.Treeview(yonetici_penceresi, columns=columns, show="headings")

  for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=110, anchor="center")

  tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

  # Veritabanından verileri çekip tabloya doldurma
  try:
    conn = sqlite3.connect("yemek_otomasyonu.db")
    cursor = conn.cursor()

    query = """
            SELECT 
                c.ad || ' ' || c.soyad,
                c.departman,
                k.katilim_durumu,
                k.toplam_kisi_sayisi,
                COALESCE(r.ad, 'Yok'),
                o.tutar
            FROM Katilim k
            JOIN Calisan c ON k.calisan_id = c.calisan_id
            LEFT JOIN Refakatci r ON k.katilim_id = r.katilim_id
            LEFT JOIN Odeme o ON k.katilim_id = o.katilim_id
        """
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
      tree.insert("", END, values=row)

    conn.close()
  except Exception as e:
    messagebox.showerror("Hata", f"Veriler yüklenirken hata oluştu: {e}")


# --- ARAYÜZ BİLEŞENLERİ ---
Label(
    pencere,
    text="Yemek Gecesi Otomasyon Sistemi",
    font=("Arial", 14, "bold"),
    fg="darkblue",
).pack(pady=10)

# 1. BÖLÜM: ÇALIŞAN KAYIT
frame_kayit = LabelFrame(
    pencere, text=" 1. Çalışan Kayıt Formu ", font=("Arial", 10, "bold")
)
frame_kayit.pack(fill="x", padx=15, pady=5)

Label(frame_kayit, text="Ad:").pack(anchor="w", padx=10)
entry_ad = Entry(frame_kayit, width=40)
entry_ad.pack(padx=10, pady=2)

Label(frame_kayit, text="Soyad:").pack(anchor="w", padx=10)
entry_soyad = Entry(frame_kayit, width=40)
entry_soyad.pack(padx=10, pady=2)

Label(frame_kayit, text="Departman:").pack(anchor="w", padx=10)
entry_dep = Entry(frame_kayit, width=40)
entry_dep.pack(padx=10, pady=2)

Label(frame_kayit, text="E-posta:").pack(anchor="w", padx=10)
entry_email = Entry(frame_kayit, width=40)
entry_email.pack(padx=10, pady=2)

Button(
    frame_kayit,
    text="Kaydı Tamamla",
    command=calisan_kaydet,
    bg="green",
    fg="white",
    font=("Arial", 9, "bold"),
).pack(pady=8)

# 2. BÖLÜM: KATILIM VE REFAKATÇİ
frame_katilim = LabelFrame(
    pencere, text=" 2. Yemek Katılım ve Refakatçi Bildirimi ", font=("Arial", 10, "bold")
)
frame_katilim.pack(fill="x", padx=15, pady=5)

Label(frame_katilim, text="Kayıtlı E-posta Adresiniz:").pack(anchor="w", padx=10)
entry_katilim_email = Entry(frame_katilim, width=40)
entry_katilim_email.pack(padx=10, pady=2)

katilim_durumu = StringVar(value="Katılacak")
Checkbutton(
    frame_katilim,
    text="Yemeğe Katılacağım",
    variable=katilim_durumu,
    onvalue="Katılacak",
    offvalue="Katılmayacak",
).pack(anchor="w", padx=10)

ref_durumu = StringVar(value="Hayır")
Checkbutton(
    frame_katilim,
    text="Yanımda Refakatçi Getireceğim (+1 Kişi)",
    variable=ref_durumu,
    onvalue="Evet",
    offvalue="Hayır",
).pack(anchor="w", padx=10)

Label(frame_katilim, text="Refakatçi Adı Soyadı:").pack(anchor="w", padx=10)
entry_ref_ad = Entry(frame_katilim, width=40)
entry_ref_ad.pack(padx=10, pady=2)

Button(
    frame_katilim,
    text="Katılımı Onayla ve Hesapla",
    command=katilim_bildir,
    bg="blue",
    fg="white",
    font=("Arial", 9, "bold"),
).pack(pady=8)

# 3. BÖLÜM: YÖNETİCİ PANELİ BUTONU
frame_yonetici = LabelFrame(
    pencere, text=" 3. Yönetim ve Raporlama ", font=("Arial", 10, "bold")
)
frame_yonetici.pack(fill="x", padx=15, pady=5)

Button(
    frame_yonetici,
    text="📊 Yönetici Paneli Raporunu Görüntüle",
    command=yonetici_paneli_ac,
    bg="purple",
    fg="white",
    font=("Arial", 10, "bold"),
).pack(fill="x", padx=10, pady=10)

pencere.mainloop()