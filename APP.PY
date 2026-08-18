import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import json as flask_json
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "Gemi Setiti"

# Konfigurasi Database SQLite
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'data_gudang.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================================================
# MODEL DATABASE / STRUKTUR TABEL MURNI KANTOR GUDANG
# ==================================================

class BahanBaku(db.Model):
    __tablename__ = 'bahan_baku'
    id_bahan = db.Column(db.String(20), primary_key=True)
    nama_bahan = db.Column(db.String(100), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    satuan = db.Column(db.String(20), nullable=False)
    saldo_awal = db.Column(db.Float, default=0.0)
    stok_akhir = db.Column(db.Float, default=0.0)
    takaran_standar = db.Column(db.Float, default=0.0)
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

class BarangJadi(db.Model):
    __tablename__ = 'barang_jadi'
    id_barang_jadi = db.Column(db.String(20), primary_key=True)
    nama_barang = db.Column(db.String(100), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    tipe_film = db.Column(db.String(100))
    satuan = db.Column(db.String(20), nullable=False)
    saldo_awal = db.Column(db.Float, default=0.0)
    stok_akhir = db.Column(db.Float, default=0.0)
    rumus_produksi = db.Column(db.Text)
    keterangan = db.Column(db.Text)

class BarangJadiSaldoPanjang(db.Model):
    __tablename__ = 'barang_jadi_saldo_panjang'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_barang_jadi = db.Column(db.String(20), db.ForeignKey('barang_jadi.id_barang_jadi'), nullable=False)
    panjang = db.Column(db.String(20), nullable=False)
    saldo_awal = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    barang_jadi = db.relationship('BarangJadi', backref=db.backref('saldo_per_panjang', lazy=True, cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('id_barang_jadi', 'panjang', name='uq_barang_panjang'),)

class Supplier(db.Model):
    __tablename__ = 'supplier'
    id_supplier = db.Column(db.String(20), primary_key=True)
    nama_supplier = db.Column(db.String(100), nullable=False)
    kode_singkat = db.Column(db.String(10), nullable=False, unique=True)
    telepon = db.Column(db.String(20))
    alamat = db.Column(db.Text)

# ==================================================
# MODEL BARU: PELANGGAN & PESANAN BARANG JADI
# ==================================================
class Pelanggan(db.Model):
    __tablename__ = 'pelanggan'
    id_pelanggan = db.Column(db.String(20), primary_key=True)
    nama_pelanggan = db.Column(db.String(100), nullable=False)
    kode_singkat = db.Column(db.String(10), nullable=False, unique=True)
    telepon = db.Column(db.String(20))
    alamat = db.Column(db.Text)
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

class PesananBarangJadi(db.Model):
    __tablename__ = 'pesanan_barang_jadi'
    id_pesanan = db.Column(db.Integer, primary_key=True, autoincrement=True)
    no_pesanan = db.Column(db.String(30), nullable=False, unique=True)
    tanggal_pesan = db.Column(db.Date, nullable=False)
    tanggal_kirim_rencana = db.Column(db.Date, nullable=True)
    id_pelanggan = db.Column(db.String(20), db.ForeignKey('pelanggan.id_pelanggan'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='DRAFT')  # DRAFT, DIPROSES, SIAP KIRIM, DIKIRIM, SELESAI, BATAL
    total_item = db.Column(db.Integer, default=0)
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    pelanggan = db.relationship('Pelanggan', backref=db.backref('daftar_pesanan', lazy=True))

class PesananBarangJadiDetail(db.Model):
    __tablename__ = 'pesanan_barang_jadi_detail'
    id_detail = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_pesanan = db.Column(db.Integer, db.ForeignKey('pesanan_barang_jadi.id_pesanan'), nullable=False)
    id_barang_jadi = db.Column(db.String(20), db.ForeignKey('barang_jadi.id_barang_jadi'), nullable=False)
    panjang_produk = db.Column(db.Float, nullable=False, default=4.0)
    jumlah_pesan = db.Column(db.Float, nullable=False, default=0)
    jumlah_terkirim = db.Column(db.Float, nullable=False, default=0)
    keterangan_item = db.Column(db.Text)
    pesanan = db.relationship('PesananBarangJadi', backref=db.backref('items_pesanan', lazy=True, cascade='all, delete-orphan'))
    barang_jadi = db.relationship('BarangJadi', backref=db.backref('riwayat_pesanan_detail', lazy=True))

# ==================================================
# MODEL BARU: PENGIRIMAN / SURAT JALAN (PARTIAL BISA)
# ==================================================
class PengirimanPelanggan(db.Model):
    __tablename__ = 'pengiriman_pelanggan'
    id_pengiriman = db.Column(db.Integer, primary_key=True, autoincrement=True)
    no_pengiriman = db.Column(db.String(30), nullable=False, unique=True)  # SJ-YYYYMM-0001
    tanggal_kirim = db.Column(db.Date, nullable=False, default=date.today)
    id_pesanan = db.Column(db.Integer, db.ForeignKey('pesanan_barang_jadi.id_pesanan'), nullable=True)
    id_pelanggan = db.Column(db.String(20), db.ForeignKey('pelanggan.id_pelanggan'), nullable=False)
    alamat_kirim = db.Column(db.Text)
    sopir = db.Column(db.String(100))
    no_polisi = db.Column(db.String(20))
    ekspedisi = db.Column(db.String(100))
    keterangan = db.Column(db.Text)
    status_kirim = db.Column(db.String(30), default='TERKIRIM')  # DRAFT, DALAM PERJALANAN, TERKIRIM, BATAL
    total_qty = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    pesanan = db.relationship('PesananBarangJadi', backref=db.backref('daftar_pengiriman', lazy=True))
    pelanggan = db.relationship('Pelanggan', backref=db.backref('daftar_pengiriman', lazy=True))

class PengirimanPelangganDetail(db.Model):
    __tablename__ = 'pengiriman_pelanggan_detail'
    id_detail_kirim = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_pengiriman = db.Column(db.Integer, db.ForeignKey('pengiriman_pelanggan.id_pengiriman'), nullable=False)
    id_detail_pesanan = db.Column(db.Integer, db.ForeignKey('pesanan_barang_jadi_detail.id_detail'), nullable=True)
    id_barang_jadi = db.Column(db.String(20), db.ForeignKey('barang_jadi.id_barang_jadi'), nullable=False)
    panjang_produk = db.Column(db.Float, default=4.0)
    jumlah_kirim = db.Column(db.Float, nullable=False, default=0)
    keterangan_item = db.Column(db.Text)
    pengiriman = db.relationship('PengirimanPelanggan', backref=db.backref('items_kirim', lazy=True, cascade='all, delete-orphan'))
    barang_jadi = db.relationship('BarangJadi', backref=db.backref('riwayat_kirim_detail', lazy=True))
    detail_pesanan = db.relationship('PesananBarangJadiDetail', backref=db.backref('riwayat_kirim_per_detail', lazy=True))

# ==================================================
# MODEL RELASI TAMBAHAN JEMBATAN LOGISTIK GUDANG
# ==================================================

class KedatanganBahan(db.Model):
    __tablename__ = 'kedatangan_bahan'
    id_kedatangan = db.Column(db.Integer, primary_key=True, autoincrement=True)
    no_nota = db.Column(db.String(50), nullable=False, unique=True)
    tanggal = db.Column(db.Date, nullable=False)
    id_supplier = db.Column(db.String(20), db.ForeignKey('supplier.id_supplier'), nullable=False)
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    supplier = db.relationship('Supplier', backref=db.backref('daftar_nota_masuk', lazy=True))

class KedatanganBahanDetail(db.Model):
    __tablename__ = 'kedatangan_bahan_detail'
    id_detail = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_kedatangan = db.Column(db.Integer, db.ForeignKey('kedatangan_bahan.id_kedatangan'), nullable=False)
    id_bahan = db.Column(db.String(20), db.ForeignKey('bahan_baku.id_bahan'), nullable=False)
    jumlah_masuk = db.Column(db.Float, nullable=False)
    nota = db.relationship('KedatanganBahan', backref=db.backref('items_nota', lazy=True, cascade='all, delete-orphan'))
    bahan = db.relationship('BahanBaku', backref=db.backref('riwayat_kedatangan_item', lazy=True))

class StokFilmRol(db.Model):
    __tablename__ = 'stok_film_rol'
    id_rol_internal = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_kode_telusur = db.Column(db.String(50), unique=True, nullable=False)
    id_bahan = db.Column(db.String(20), db.ForeignKey('bahan_baku.id_bahan'), nullable=False)
    id_kedatangan = db.Column(db.Integer, db.ForeignKey('kedatangan_bahan.id_kedatangan'), nullable=False)
    nomor_urut_film = db.Column(db.Integer, nullable=False)
    panjang_awal = db.Column(db.Float, nullable=False)
    panjang_sisa = db.Column(db.Float, nullable=False)
    status_rol = db.Column(db.String(20), default='TERSEDIA')
    tanggal_datang = db.Column(db.Date, nullable=False)
    operator_terakhir = db.Column(db.String(100), nullable=True)
    tanggal_pakai_terakhir = db.Column(db.Date, nullable=True)
    bahan = db.relationship('BahanBaku', backref=db.backref('daftar_gulungan_rol', lazy=True))
    kedatangan = db.relationship('KedatanganBahan', backref=db.backref('daftar_rol_masuk', lazy=True))
# ==============================================================================
# MODEL BACKEND: TABEL DEDIKASI PEREKAM 3 KASUS PENYESUAIAN STOK (APP.PY)
# ==============================================================================
class PenyesuaianStok(db.Model):
    __tablename__ = 'penyesuaian_stok'
    id_penyesuaian = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tanggal = db.Column(db.Date, nullable=False)
    
    # Berisi penanda jenis: 'SISA_PROD', 'KOREKSI_RETUR', atau 'PERBAIKAN'
    kategori = db.Column(db.String(30), nullable=False)
    
    # Berisi penanda saklar: 'MASUK' atau 'KELUAR'
    jenis_saklar = db.Column(db.String(10), nullable=False)
    
    id_bahan = db.Column(db.String(20), db.ForeignKey('bahan_baku.id_bahan'), nullable=False)
    
    # Nilai murni yang diketik admin (Selalu Angka Positif di database)
    jumlah_input = db.Column(db.Float, nullable=False, default=0.0)
    
    # Nilai akhir hasil perhitungan JavaScript (Otomatis Minus jika KELUAR)
    jumlah_efektif = db.Column(db.Float, nullable=False, default=0.0)
    
    alasan_keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relasi balik ke tabel master bahan baku
    bahan = db.relationship('BahanBaku', backref=db.backref('daftar_penyesuaian_stok', lazy=True, cascade='all, delete-orphan'))

# ==============================================================================
# MODEL BARU: PENYESUAIAN STOK BARANG JADI (TANPA UBAH ALUR LAMA)
# ==============================================================================
class PenyesuaianBarangJadi(db.Model):
    __tablename__ = 'penyesuaian_barang_jadi'
    id_penyesuaian = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tanggal = db.Column(db.Date, nullable=False)
    kategori = db.Column(db.String(30), nullable=False)
    jenis_saklar = db.Column(db.String(10), nullable=False)
    id_barang_jadi = db.Column(db.String(20), db.ForeignKey('barang_jadi.id_barang_jadi'), nullable=False)
    
    # >>> TAMBAHKAN INI <<<
    panjang_produk = db.Column(db.Float, nullable=False, default=4.0, server_default='4.0')
    
    jumlah_input = db.Column(db.Float, nullable=False, default=0.0)
    jumlah_efektif = db.Column(db.Float, nullable=False, default=0.0)
    alasan_keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    barang_jadi = db.relationship('BarangJadi', backref=db.backref('daftar_penyesuaian_barang_jadi', lazy=True, cascade='all, delete-orphan'))


# ==========================================================
# MODEL DATABASE: TRANSAKSI PRODUKSI HARIAN PABRIK GEMI SETITI
# ==========================================================
class ProduksiHarian(db.Model):
    __tablename__ = 'produksi_harian'
    id_produksi = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tanggal = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(10), nullable=False) # Shift 1, 2, atau 3
    id_barang_jadi = db.Column(db.String(20), db.ForeignKey('barang_jadi.id_barang_jadi'), nullable=False)
    tipe_adonan = db.Column(db.String(50), nullable=False) # PLAFON COKLAT, LIS PUTIH, TRIAL, dll
    jumlah_batch = db.Column(db.Integer, nullable=False, default=1) # Berapa kali aduk mixer
        # ==========================================================
    # POTONGAN 1: UPDATE KOLOM AUDIT LIMBAH PRODUKSI (APP.PY)
    # ==========================================================
    jumlah_produk_jadi = db.Column(db.Integer, nullable=False) # Hasil Baik (Lbr)
    
    # Kolom baru hasil bedah lapangan: Pencatatan limbah scrap aktual
        # ==========================================================
    # UPDATE FISIK: TAMBAH LORONG PEREKAM KODE ROL FILM (APP.PY)
    # ==========================================================
    jumlah_produk_rusak_film = db.Column(db.Integer, nullable=False, default=0) 
    jumlah_produk_rusak_tanpa_film = db.Column(db.Integer, nullable=False, default=0) 
    
    # KUNCI BARU: Lorong pencatat nomor rol film gudang hulu
    kode_telusur_film = db.Column(db.String(50), nullable=True)
    
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relasi FIX MASTER HILANG FINAL
    barang_jadi = db.relationship('BarangJadi', backref=db.backref('riwayat_produksi', lazy=True))
    @property
    def produk(self):
        return self.barang_jadi

class ProduksiBahanPotong(db.Model):
    __tablename__ = 'produksi_bahan_potong'
    id_potong = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_produksi = db.Column(db.Integer, db.ForeignKey('produksi_harian.id_produksi'), nullable=False)
    id_bahan = db.Column(db.String(20), db.ForeignKey('bahan_baku.id_bahan'), nullable=False)
    jumlah_terpakai = db.Column(db.Float, nullable=False) # Volume Kg/Meter yang dipotong otomatis
    
    # Relasi Balik
    produksi = db.relationship('ProduksiHarian', backref=db.backref('rincian_bahan_terpakai', lazy=True, cascade='all, delete-orphan'))
    bahan = db.relationship('BahanBaku', backref=db.backref('riwayat_pakai_produksi', lazy=True))

# ==================================================
# HALAMAN UTAMA / DASHBOARD RESMI
# ==================================================

@app.route('/master/bahan-baku')
def daftar_bahan_baku():
    semua_bahan = BahanBaku.query.order_by(BahanBaku.id_bahan.asc()).all()
    return render_template('bahan_baku.html', bahan_list=semua_bahan)

@app.route('/master/bahan-baku/tambah', methods=['POST'])
def tambah_bahan_baku():
    nama = request.form.get('nama', '').upper().strip()
    kategori = request.form.get('kategori', '').upper().strip()  
    satuan = request.form.get('satuan', '').upper().strip()
    saldo_awal_raw = request.form.get('saldo_awal', '0').strip()
    takaran = request.form.get('takaran', '0').strip()
    keterangan = request.form.get('keterangan', '').upper().strip()

    if not nama or not kategori or not satuan:
        flash("Nama, Kategori, dan Satuan wajib diisi!", "warning")
        return redirect(url_for('daftar_bahan_baku'))

    try:
        val_saldo_awal = float(saldo_awal_raw) if saldo_awal_raw else 0.0
        val_takaran = float(takaran) if takaran else 0.0
    except ValueError:
        flash("Saldo awal dan takaran harus berupa angka!", "danger")
        return redirect(url_for('daftar_bahan_baku'))

    if kategori == "BAHAN BAKU": prefix = "BB-"
    elif kategori == "BAHAN FILM": prefix = "BF-"
    elif kategori == "BAHAN PENOLONG": prefix = "BP-"
    else:
        flash("Kategori tidak valid!", "danger")
        return redirect(url_for('daftar_bahan_baku'))

    terakhir = BahanBaku.query.filter(BahanBaku.id_bahan.like(f"{prefix}%")).order_by(BahanBaku.id_bahan.desc()).first()
    
    nomor = 1
    if terakhir:
        try:
            nomor = int(terakhir.id_bahan.split('-')[-1]) + 1
        except (ValueError, IndexError):
            nomor = 1
            
    id_bhn = f"{prefix}{nomor:03d}"

    baru = BahanBaku(
        id_bahan=id_bhn, nama_bahan=nama, kategori=kategori, satuan=satuan,
        saldo_awal=val_saldo_awal, stok_akhir=val_saldo_awal, takaran_standar=val_takaran, keterangan=keterangan
    )
    db.session.add(baru)
    db.session.commit()
    flash(f"Bahan {nama} berhasil ditambahkan | Kode: {id_bhn}", "success")
    return redirect(url_for('daftar_bahan_baku'))

@app.route('/master/bahan-baku/edit/<string:id>', methods=['GET', 'POST'])
def edit_bahan_baku(id):
    data = db.session.get(BahanBaku, id)
    if not data:
        flash("Data tidak ditemukan!", "danger")
        return redirect(url_for('daftar_bahan_baku'))
        
    if request.method == 'POST':
        nama = request.form.get('nama', '').upper().strip()
        satuan = request.form.get('satuan', '').upper().strip()
        takaran = request.form.get('takaran', '0').strip()
        keterangan = request.form.get('keterangan', '').upper().strip()
        saldo_awal_raw = request.form.get('saldo_awal', '').strip()

        if not nama or not satuan:
            flash("Nama dan Satuan wajib diisi!", "warning")
            return redirect(url_for('edit_bahan_baku', id=id))

        try:
            val_saldo_awal_baru = float(saldo_awal_raw) if saldo_awal_raw else data.saldo_awal
            val_takaran = float(takaran) if takaran else 0.0
        except ValueError:
            flash("Saldo awal dan takaran standar harus berupa angka!", "danger")
            return redirect(url_for('edit_bahan_baku', id=id))

        selisih = val_saldo_awal_baru - data.saldo_awal
        data.stok_akhir = round(data.stok_akhir + selisih, 2)
        data.nama_bahan = nama
        data.satuan = satuan
        data.takaran_standar = val_takaran
        data.keterangan = keterangan
        data.saldo_awal = val_saldo_awal_baru
        db.session.commit()
        flash("Data bahan baku berhasil diperbarui!", "success")
        return redirect(url_for('daftar_bahan_baku'))
    return render_template('edit_bahan_baku.html', data=data)

@app.route('/master/bahan-baku/hapus/<string:id>', methods=['POST'])
def hapus_bahan_baku(id):
    data = db.session.get(BahanBaku, id)
    if not data:
        flash("Data tidak ditemukan!", "danger")
        return redirect(url_for('daftar_bahan_baku'))
        
    if KedatanganBahanDetail.query.filter_by(id_bahan=id).first() or StokFilmRol.query.filter_by(id_bahan=id).first():
        flash("Tidak bisa dihapus! Data bahan ini sudah terpakai di riwayat transaksi logistik gudang.", "danger")
        return redirect(url_for('daftar_bahan_baku'))
    db.session.delete(data)
    db.session.commit()
    flash("Data bahan baku berhasil dihapus dari sistem!", "success")
    return redirect(url_for('daftar_bahan_baku'))
@app.route('/')
def dashboard():
    # Menghitung total ringkasan data langsung dari database
    total_bahan = BahanBaku.query.count()
    total_barang = BarangJadi.query.count()
    total_supplier = Supplier.query.count()
    total_pelanggan = Pelanggan.query.count()
    total_pesanan = PesananBarangJadi.query.count()
    pesanan_pending = PesananBarangJadi.query.filter(PesananBarangJadi.status.in_(['DRAFT','DIPROSES','SIAP KIRIM'])).count()
    try:
        total_pengiriman = PengirimanPelanggan.query.count()
        pengiriman_pending = PengirimanPelanggan.query.filter(PengirimanPelanggan.status_kirim.in_(['DRAFT','DALAM PERJALANAN'])).count()
    except:
        total_pengiriman = 0
        pengiriman_pending = 0
    
    # Mengambil sampel 5 bahan baku dengan stok paling tipis/sedikit untuk peringatan
    stok_menipis = BahanBaku.query.order_by(BahanBaku.stok_akhir.asc()).limit(5).all()
    
    return render_template(
        'dashboard.html', 
        total_bahan=total_bahan, 
        total_barang=total_barang, 
        total_supplier=total_supplier,
        total_pelanggan=total_pelanggan,
        total_pesanan=total_pesanan,
        pesanan_pending=pesanan_pending,
        total_pengiriman=total_pengiriman,
        pengiriman_pending=pengiriman_pending,
        stok_menipis=stok_menipis
    )


@app.route('/master/barang-jadi')
def daftar_barang_jadi():
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS barang_jadi_saldo_panjang (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_barang_jadi VARCHAR(20) NOT NULL,
                panjang VARCHAR(20) NOT NULL,
                saldo_awal FLOAT DEFAULT 0.0,
                created_at DATETIME,
                FOREIGN KEY(id_barang_jadi) REFERENCES barang_jadi(id_barang_jadi),
                UNIQUE(id_barang_jadi, panjang)
            )"""))
            conn.commit()
    except Exception as e:
        print(f"Auto create: {e}")
    semua_barang = BarangJadi.query.order_by(BarangJadi.id_barang_jadi.asc()).all()
    return render_template('barang_jadi.html', daftar=semua_barang)

@app.route('/debug/per-panjang')
def debug_per_panjang():
    from sqlalchemy import text
    try:
        with db.engine.connect() as conn:
            rows = conn.execute(text("SELECT id_barang_jadi, panjang, saldo_awal FROM barang_jadi_saldo_panjang ORDER BY id_barang_jadi, panjang")).fetchall()
            bj = conn.execute(text("SELECT id_barang_jadi, nama_barang, saldo_awal, stok_akhir FROM barang_jadi")).fetchall()
            html = "<h2>DEBUG PER PANJANG</h2><h3>barang_jadi</h3><pre>"
            for r in bj:
                html += str(r) + "\n"
            html += "</pre><h3>barang_jadi_saldo_panjang</h3><pre>"
            for r in rows:
                html += str(r) + "\n"
            html += "</pre><p><a href='/master/barang-jadi'>Kembali</a></p>"
            return html
    except Exception as e:
        return f"ERROR: {e}" 

@app.route('/master/barang-jadi/tambah', methods=['POST'])
def tambah_barang_jadi():
    # AUTO CREATE TABLE
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS barang_jadi_saldo_panjang (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_barang_jadi VARCHAR(20) NOT NULL,
                panjang VARCHAR(20) NOT NULL,
                saldo_awal FLOAT DEFAULT 0.0,
                created_at DATETIME,
                FOREIGN KEY(id_barang_jadi) REFERENCES barang_jadi(id_barang_jadi),
                UNIQUE(id_barang_jadi, panjang)
            )"""))
            conn.commit()
    except Exception as e:
        print(f"Auto create: {e}")

    nama = request.form.get('nama', '').upper().strip()
    kategori = request.form.get('kategori', '').upper().strip()
    tipe_film = request.form.get('tipe_film', '').upper().strip()
    satuan = request.form.get('satuan', '').upper().strip()
    rumus = request.form.get('rumus', '').upper().strip()
    keterangan = request.form.get('keterangan', '').upper().strip()

    def _p(k):
        try:
            return float(request.form.get(k, '0') or 0)
        except:
            return 0.0
    s3 = _p('saldo_3')
    s4 = _p('saldo_4')
    s5 = _p('saldo_5')
    s6 = _p('saldo_6')
    sR = _p('saldo_request')
    legacy_raw = request.form.get('saldo_awal', '0').strip()
    try:
        legacy = float(legacy_raw) if legacy_raw else 0.0
    except:
        legacy = 0.0
    if s3+s4+s5+s6+sR == 0 and legacy>0:
        s4 = legacy
    total = s3+s4+s5+s6+sR

    if not nama or not kategori or not satuan:
        flash("Nama, Kategori, dan Satuan wajib diisi!", "warning")
        return redirect(url_for('daftar_barang_jadi'))

    prefix = "P-" if kategori == "PLAFON" else "L-"
    terakhir = BarangJadi.query.filter(BarangJadi.id_barang_jadi.like(f"{prefix}%")).order_by(BarangJadi.id_barang_jadi.desc()).first()
    nomor = 1
    if terakhir:
        try:
            nomor = int(terakhir.id_barang_jadi.split('-')[-1]) + 1
        except:
            nomor = 1
    id_produk = f"{prefix}{nomor:03d}"

    baru = BarangJadi(
        id_barang_jadi=id_produk, nama_barang=nama, kategori=kategori,
        tipe_film=tipe_film, satuan=satuan, saldo_awal=total,
        stok_akhir=total, rumus_produksi=rumus, keterangan=keterangan
    )
    db.session.add(baru)
    db.session.flush()
    for pk, val in [('3', s3), ('4', s4), ('5', s5), ('6', s6), ('REQUEST', sR)]:
        if val>0:
            db.session.add(BarangJadiSaldoPanjang(id_barang_jadi=id_produk, panjang=pk, saldo_awal=val))
    db.session.commit()
    flash(f"OK {id_produk} | 3M:{s3} 4M:{s4} 5M:{s5} 6M:{s6} REQ:{sR} TOTAL:{total}", "success")
    return redirect(url_for('daftar_barang_jadi'))

    try:
        val_saldo_awal = float(saldo_awal_raw) if saldo_awal_raw else 0.0
    except ValueError:
        flash("Saldo awal harus berupa angka!", "danger")
        return redirect(url_for('daftar_barang_jadi'))

    prefix = "P-" if kategori == "PLAFON" else "L-"
    terakhir = BarangJadi.query.filter(BarangJadi.id_barang_jadi.like(f"{prefix}%"))\
                               .order_by(BarangJadi.id_barang_jadi.desc()).first()
    
    nomor = 1
    if terakhir:
        try:
            nomor = int(terakhir.id_barang_jadi.split('-')[-1]) + 1
        except (ValueError, IndexError):
            nomor = 1
            
    id_produk = f"{prefix}{nomor:03d}"

    baru = BarangJadi(
        id_barang_jadi=id_produk, nama_barang=nama, kategori=kategori,
        tipe_film=tipe_film, satuan=satuan, saldo_awal=val_saldo_awal,
        stok_akhir=val_saldo_awal, rumus_produksi=rumus, keterangan=keterangan
    )
    db.session.add(baru)
    db.session.commit()
    flash(f"Produk {nama} berhasil ditambahkan | Kode: {id_produk}", "success")
    return redirect(url_for('daftar_barang_jadi'))

@app.route('/master/barang-jadi/edit/<string:id>', methods=['GET', 'POST'])
def edit_barang_jadi(id):
    data = db.session.get(BarangJadi, id)
    if not data:
        flash("Data tidak ditemukan!", "danger")
        return redirect(url_for('daftar_barang_jadi'))
    if request.method == 'POST':
        nama = request.form.get('nama', '').upper().strip()
        tipe_film = request.form.get('tipe_film', '').upper().strip()
        satuan = request.form.get('satuan', '').upper().strip()
        rumus = request.form.get('rumus', '').upper().strip()
        keterangan = request.form.get('keterangan', '').upper().strip()
        def _p(k, d=0):
            try:
                v = request.form.get(k, '').strip()
                return float(v) if v!='' else d
            except:
                return d
        existing = {sp.panjang: float(sp.saldo_awal or 0) for sp in (data.saldo_per_panjang or [])}
        s3 = _p('saldo_3', existing.get('3',0))
        s4 = _p('saldo_4', existing.get('4',0))
        s5 = _p('saldo_5', existing.get('5',0))
        s6 = _p('saldo_6', existing.get('6',0))
        sR = _p('saldo_request', existing.get('REQUEST',0))
        total_baru = s3+s4+s5+s6+sR
        if not nama or not satuan:
            flash("Nama dan Satuan wajib diisi!", "warning")
            return redirect(url_for('edit_barang_jadi', id=id))
        selisih = total_baru - float(data.saldo_awal or 0)
        data.stok_akhir = round(float(data.stok_akhir or 0) + selisih, 2)
        data.saldo_awal = total_baru
        data.nama_barang = nama
        data.tipe_film = tipe_film
        data.satuan = satuan
        data.rumus_produksi = rumus
        data.keterangan = keterangan
        for pk, val in [('3', s3), ('4', s4), ('5', s5), ('6', s6), ('REQUEST', sR)]:
            sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=id, panjang=pk).first()
            if sp:
                sp.saldo_awal = val
            else:
                if val>0:
                    db.session.add(BarangJadiSaldoPanjang(id_barang_jadi=id, panjang=pk, saldo_awal=val))
        db.session.commit()
        flash(f"Update OK | 3M:{s3} 4M:{s4} 5M:{s5} 6M:{s6} REQ:{sR} TOTAL:{total_baru}", "success")
        return redirect(url_for('daftar_barang_jadi'))
    return render_template('edit_barang_jadi.html', data=data)

@app.route('/master/barang-jadi/hapus/<string:id>', methods=['POST'])
def hapus_barang_jadi(id):
    data = db.session.get(BarangJadi, id)
    if not data:
        flash("Data tidak ditemukan!", "danger")
        return redirect(url_for('daftar_barang_jadi'))
        
    if ProduksiHarian.query.filter_by(id_barang_jadi=id).first():
        flash("Tidak bisa dihapus! Data produk ini sudah terpakai di riwayat transaksi produksi harian.", "danger")
        return redirect(url_for('daftar_barang_jadi'))
    db.session.delete(data)
    db.session.commit()
    flash("Data barang jadi berhasil dihapus dari sistem!", "success")
    return redirect(url_for('daftar_barang_jadi'))

# ==================================================
# MASTER SUPPLIER (SUP-)
# ==================================================
@app.route('/master/supplier')
def daftar_supplier():
    semua_supplier = Supplier.query.order_by(Supplier.id_supplier.asc()).all()
    return render_template('supplier.html', supplier_list=semua_supplier)

@app.route('/master/supplier/tambah', methods=['POST'])
def tambah_supplier():
    nama = request.form.get('nama', '').upper().strip()
    kode = request.form.get('kode', '').upper().strip()
    telepon = request.form.get('telepon', '').strip()
    alamat = request.form.get('alamat', '').upper().strip()

    if not nama or not kode:
        flash("Nama dan Kode Singkat Supplier wajib diisi!", "warning")
        return redirect(url_for('daftar_supplier'))

    if Supplier.query.filter_by(kode_singkat=kode).first():
        flash("Kode singkat sudah digunakan! Gunakan kode lain.", "danger")
        return redirect(url_for('daftar_supplier'))

    terakhir = Supplier.query.order_by(Supplier.id_supplier.desc()).first()
    
    nomor = 1
    if terakhir:
        try:
            nomor = int(terakhir.id_supplier.split('-')[-1]) + 1
        except (ValueError, IndexError):
            nomor = 1
            
    id_sup = f"SUP-{nomor:03d}"

    baru = Supplier(id_supplier=id_sup, nama_supplier=nama, kode_singkat=kode, telepon=telepon, alamat=alamat)
    db.session.add(baru)
    db.session.commit()
    flash(f"Supplier {nama} berhasil ditambahkan | Kode: {id_sup}", "success")
    return redirect(url_for('daftar_supplier'))

@app.route('/master/supplier/edit/<string:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    data = db.session.get(Supplier, id)
    if not data:
        flash("Data tidak ditemukan!", "danger")
        return redirect(url_for('daftar_supplier'))
        
    if request.method == 'POST':
        nama = request.form.get('nama', '').upper().strip()
        kode = request.form.get('kode', '').upper().strip()
        telepon = request.form.get('telepon', '').strip()
        alamat = request.form.get('alamat', '').upper().strip()

        if not nama or not kode:
            flash("Nama dan Kode Singkat wajib diisi!", "warning")
            return redirect(url_for('edit_supplier', id=id))

        if Supplier.query.filter(Supplier.kode_singkat == kode, Supplier.id_supplier != id).first():
            flash("Kode singkat sudah dipakai supplier lain!", "danger")
            return redirect(url_for('edit_supplier', id=id))

        data.nama_supplier = nama
        data.kode_singkat = kode
        data.telepon = telepon
        data.alamat = alamat
        db.session.commit()
        flash("Data supplier berhasil diperbarui!", "success")
        return redirect(url_for('daftar_supplier'))
    return render_template('edit_supplier.html', data=data)
    
@app.route('/master/supplier/hapus/<string:id>', methods=['POST'])
def hapus_supplier(id):
    data = db.session.get(Supplier, id)
    if not data:
        flash("Data tidak ditemukan!", "danger")
        return redirect(url_for('daftar_supplier'))
        
    # PROTEKSI: Cek apakah supplier ini punya riwayat nota masuk gudang
    if KedatanganBahan.query.filter_by(id_supplier=id).first():
        flash("Tidak bisa dihapus! Data supplier ini sudah terikat dengan nota transaksi kedatangan barang.", "danger")
        return redirect(url_for('daftar_supplier'))
        
    db.session.delete(data)
    db.session.commit()
    flash("Data supplier berhasil dihapus!", "success")
    return redirect(url_for('daftar_supplier'))

# ==================================================
# MODUL BARU: MASTER PELANGGAN (CUSTOMER)
# ==================================================
@app.route('/master/pelanggan')
def daftar_pelanggan():
    semua_pelanggan = Pelanggan.query.order_by(Pelanggan.id_pelanggan.asc()).all()
    return render_template('pelanggan.html', pelanggan_list=semua_pelanggan)

@app.route('/master/pelanggan/tambah', methods=['POST'])
def tambah_pelanggan():
    nama = request.form.get('nama', '').upper().strip()
    kode = request.form.get('kode', '').upper().strip()
    telepon = request.form.get('telepon', '').strip()
    alamat = request.form.get('alamat', '').upper().strip()
    keterangan = request.form.get('keterangan', '').upper().strip()

    if not nama or not kode:
        flash("Nama dan Kode Singkat Pelanggan wajib diisi!", "warning")
        return redirect(url_for('daftar_pelanggan'))

    if Pelanggan.query.filter_by(kode_singkat=kode).first():
        flash("Kode singkat sudah digunakan! Gunakan kode lain.", "danger")
        return redirect(url_for('daftar_pelanggan'))

    terakhir = Pelanggan.query.order_by(Pelanggan.id_pelanggan.desc()).first()
    nomor = 1
    if terakhir:
        try:
            nomor = int(terakhir.id_pelanggan.split('-')[-1]) + 1
        except (ValueError, IndexError):
            nomor = 1
    id_plg = f"CUST-{nomor:03d}"

    baru = Pelanggan(id_pelanggan=id_plg, nama_pelanggan=nama, kode_singkat=kode, telepon=telepon, alamat=alamat, keterangan=keterangan)
    db.session.add(baru)
    db.session.commit()
    flash(f"Pelanggan {nama} berhasil ditambahkan | Kode: {id_plg}", "success")
    return redirect(url_for('daftar_pelanggan'))

@app.route('/master/pelanggan/edit/<string:id>', methods=['GET', 'POST'])
def edit_pelanggan(id):
    data = db.session.get(Pelanggan, id)
    if not data:
        flash("Data tidak ditemukan!", "danger")
        return redirect(url_for('daftar_pelanggan'))
        
    if request.method == 'POST':
        nama = request.form.get('nama', '').upper().strip()
        kode = request.form.get('kode', '').upper().strip()
        telepon = request.form.get('telepon', '').strip()
        alamat = request.form.get('alamat', '').upper().strip()
        keterangan = request.form.get('keterangan', '').upper().strip()

        if not nama or not kode:
            flash("Nama dan Kode Singkat wajib diisi!", "warning")
            return redirect(url_for('edit_pelanggan', id=id))

        if Pelanggan.query.filter(Pelanggan.kode_singkat == kode, Pelanggan.id_pelanggan != id).first():
            flash("Kode singkat sudah dipakai pelanggan lain!", "danger")
            return redirect(url_for('edit_pelanggan', id=id))

        data.nama_pelanggan = nama
        data.kode_singkat = kode
        data.telepon = telepon
        data.alamat = alamat
        data.keterangan = keterangan
        db.session.commit()
        flash("Data pelanggan berhasil diperbarui!", "success")
        return redirect(url_for('daftar_pelanggan'))
    return render_template('edit_pelanggan.html', data=data)

@app.route('/master/pelanggan/hapus/<string:id>', methods=['POST'])
def hapus_pelanggan(id):
    data = db.session.get(Pelanggan, id)
    if not data:
        flash("Data tidak ditemukan!", "danger")
        return redirect(url_for('daftar_pelanggan'))
        
    if PesananBarangJadi.query.filter_by(id_pelanggan=id).first():
        flash("Tidak bisa dihapus! Pelanggan ini sudah punya riwayat pesanan.", "danger")
        return redirect(url_for('daftar_pelanggan'))
        
    db.session.delete(data)
    db.session.commit()
    flash("Data pelanggan berhasil dihapus!", "success")
    return redirect(url_for('daftar_pelanggan'))

# ==================================================
# MODUL INTI: TRANSAKSI KEDATANGAN BAHAN BAKU & FILM
# ==================================================
@app.route('/transaksi/kedatangan-bahan', methods=['GET', 'POST'])
def transaksi_kedatangan_bahan():
    if request.method == 'POST':
        # 1. Tangkap Informasi Dokumen Induk Nota
        tanggal_raw = request.form.get('tanggal')
        id_supplier = request.form.get('id_supplier')
        no_dokumen = request.form.get('no_dokumen', '').upper().strip()
        keterangan = request.form.get('keterangan', '').upper().strip()

        if not tanggal_raw or not id_supplier or not no_dokumen:
            flash("Gagal Simpan! Tanggal, Supplier, dan No Dokumen Surat Jalan wajib diisi.", "danger")
            return redirect(url_for('transaksi_kedatangan_bahan'))

        # Proteksi Cek Duplikasi Nomor Surat Jalan / Nota
        if KedatanganBahan.query.filter_by(no_nota=no_dokumen).first():
            flash(f"Gagal! Nomor Surat Jalan {no_dokumen} sudah terdaftar sebelumnya di sistem hulu.", "danger")
            return redirect(url_for('transaksi_kedatangan_bahan'))

        try:
            tanggal_fiskal = datetime.strptime(tanggal_raw, '%Y-%m-%d').date()
            
            # 2. Rekam Dokumen Induk Baru ke Database
            nota_baru = KedatanganBahan(
                no_nota=no_dokumen, tanggal=tanggal_fiskal,
                id_supplier=id_supplier, keterangan=keterangan
            )
            db.session.add(nota_baru)
            db.session.flush() # Mendapatkan id_kedatangan otomatis sebelum commit final
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error Sistem Validasi: {str(e)}", "danger")
            return redirect(url_for('transaksi_kedatangan_bahan'))

        # Blok Penanganan Item Array Multi-Barang Dinamis (Berlanjut ke Bagian 2)
        # 3. PROSES MULTI-BARANG DINAMIS & KODE URUT TELUSUR ROL (FIXED QTY)
        try:
            # Tangkap array kategori dan id bahan yang dikirim oleh form HTML
            kategori_list = request.form.getlist('kategori[]')
            bahan_id_list = request.form.getlist('bahan_id[]')
            # FIX: Filter empty string karena input film yang disabled tidak ikut, tapi jaga-jaga browser lama
            jumlah_list_raw = request.form.getlist('jumlah[]')
            jumlah_list = [x for x in jumlah_list_raw if x is not None and str(x).strip() != ""]

            # Ambil data singkatan kode supplier untuk penomoran telusur rol film
            supplier_info = db.session.get(Supplier, id_supplier)
            kode_sup = supplier_info.kode_singkat if supplier_info else "SUP"

            indeks_baku = 0 # Penanda urutan untuk mengambil index jumlah[] bahan non-film
            
            for i in range(len(kategori_list)):
                kat = kategori_list[i].upper().strip()
                id_bhn = bahan_id_list[i]
                
                # Ambil objek master bahan baku untuk diupdate stok akhirnya
                master_bahan = db.session.get(BahanBaku, id_bhn)
                if not master_bahan:
                    continue

                                # ==========================================================
                # JALUR A: KHUSUS PEMPROSESAN MULTI-BATCH BAHAN FILM PVC
                # ==========================================================
                if kat == "BAHAN FILM":
                    # FIXED: Coba ambil dengan index i (setelah re-index JS), fallback ke film_counter jika terhapus
                    qty_rol_array = request.form.getlist(f'qty_rol_batch_{i}[]')
                    panjang_rol_array = request.form.getlist(f'panjang_rol_batch_{i}[]')
                    # Fallback: jika tidak ketemu karena hapus baris, coba cari key film yang masih ada sesuai urutan
                    if not qty_rol_array:
                        # Cari semua keys qty_rol_batch_* di form
                        all_keys = [k for k in request.form.keys() if k.startswith('qty_rol_batch_')]
                        # Urutkan dan ambil sesuai urutan kemunculan film
                        # Hitung berapa film sebelumnya
                        film_idx = sum(1 for x in kategori_list[:i] if x == "BAHAN FILM")
                        if film_idx < len(all_keys):
                            fallback_key = sorted(all_keys)[film_idx]
                            qty_rol_array = request.form.getlist(fallback_key)
                            panjang_key = fallback_key.replace('qty_rol_batch_', 'panjang_rol_batch_')
                            panjang_rol_array = request.form.getlist(panjang_key)
                    
                    total_panjang_masuk = 0.0
                    
                    # Kamus Kode Sandi Bulan Internal Pabrik
                    sandi_bulan = {
                        1:'S', 2:'E', 3:'N', 4:'Y', 5:'U', 6:'M', 
                        7:'D', 8:'I', 9:'W', 10:'J', 11:'H', 12:'X'
                    }
                    huruf_bulan = sandi_bulan.get(tanggal_fiskal.month, 'Z')
                    
                    # Format penanggalan harian hulu (Contoh: tanggal 11 dan tahun 26)
                    teks_tgl = f"{tanggal_fiskal.day:02d}"
                    teks_thn = f"{tanggal_fiskal.year % 100:02d}"
                    
                    # Loop 1: Berjalan menyusuri setiap baris ukuran batch yang diinput user
                    for b in range(len(qty_rol_array)):
                        jml_rol = int(qty_rol_array[b])
                        panjang_meter = float(panjang_rol_array[b])
                        
                        # Loop 2: Mengurai jumlah gulungan rol satu per satu untuk dicetak kodenya
                        for r in range(jml_rol):
                            # Hitung nomor urut yang HANYA COCOK dengan TANGGAL & ID BAHAN ini saja (Reset Harian)
                            rol_hari_ini = StokFilmRol.query.filter_by(
                                id_bahan=id_bhn, 
                                tanggal_datang=tanggal_fiskal
                            ).count()
                            
                            nomor_urut_baru = rol_hari_ini + 1
                            
                            # FORMULASI KODE TELUSUR MANUNGGAL RAMAH MATA SILINDER
                            kode_telusur_unik = f"{kode_sup}-{teks_tgl}{huruf_bulan}{teks_thn}-{id_bhn}-{nomor_urut_baru:03d}"
                            
                            # Daftarkan gulungan baru ke rak penyimpanan database
                            rol_baru = StokFilmRol(
                                id_kode_telusur=kode_telusur_unik, id_bahan=id_bhn,
                                id_kedatangan=nota_baru.id_kedatangan, nomor_urut_film=nomor_urut_baru,
                                panjang_awal=panjang_meter, panjang_sisa=panjang_meter,
                                status_rol='TERSEDIA', tanggal_datang=tanggal_fiskal
                            )
                            db.session.add(rol_baru)
                            total_panjang_masuk += panjang_meter                   
                    
                    # Rekam ke detail nota dengan total akumulasi panjang meter film harian
                    detail_item = KedatanganBahanDetail(
                        id_kedatangan=nota_baru.id_kedatangan, id_bahan=id_bhn,
                        jumlah_masuk=total_panjang_masuk
                    )
                    db.session.add(detail_item)
                    
                    # AKUNTANSI UPDATE STOK: Naikkan stok meter film di master database
                    master_bahan.stok_akhir = round(master_bahan.stok_akhir + total_panjang_masuk, 2)

                # JALUR B: KHUSUS PEMPROSESAN MATERIAL CURAH (BAHAN BAKU & PENOLONG)
                else:
                    qty_masuk = float(jumlah_list[indeks_baku])
                    indeks_baku += 1 # Majukan index penanda untuk baris bahan baku berikutnya
                    
                    detail_item = KedatanganBahanDetail(
                        id_kedatangan=nota_baru.id_kedatangan, id_bahan=id_bhn,
                        jumlah_masuk=qty_masuk
                    )
                    db.session.add(detail_item)
                    
                    # AKUNTANSI UPDATE STOK: Naikkan stok volume/kg material curah di master database
                    master_bahan.stok_akhir = round(master_bahan.stok_akhir + qty_masuk, 2)

            db.session.commit()
            flash(f"Sukses! Surat Jalan {no_dokumen} berhasil dibukukan. Stok hulu diperbarui otomatis.", "success")
            return redirect(url_for('transaksi_kedatangan_bahan'))

        except Exception as e:
            db.session.rollback()
            flash(f"Gagal memproses baris material. Terjadi kesalahan audit: {str(e)}", "danger")
            return redirect(url_for('transaksi_kedatangan_bahan'))

    # JALUR C: MERENDER HALAMAN JIKA DI-GET OLEH BROWSER (MENAMPILKAN DATA)
    semua_bahan = BahanBaku.query.order_by(BahanBaku.id_bahan.asc()).all()
    semua_supplier = Supplier.query.order_by(Supplier.id_supplier.asc()).all()
    semua_nota = KedatanganBahan.query.order_by(KedatanganBahan.tanggal.desc(), KedatanganBahan.id_kedatangan.desc()).all()
    tanggal_sekarang = datetime.now().strftime('%Y-%m-%d')

    return render_template(
        'kedatangan_bahan.html',
        bahan_list=semua_bahan,
        supplier_list=semua_supplier,
        semua_nota=semua_nota,
        tanggal_hari_ini=tanggal_sekarang
    )
    
    
# ==================================================
# API ENDPOINT: PENYUPLAI RINCIAN DOKUMEN KEDATANGAN
# ==================================================
@app.route('/api/get-detail-kedatangan/<int:id_kedatangan>')
def api_get_detail_kedatangan(id_kedatangan):
    # 1. Ambil data induk dokumen nota kedatangan
    nota = db.session.get(KedatanganBahan, id_kedatangan)
    if not nota:
        return jsonify({'error': 'Data Dokumen Surat Jalan tidak ditemukan'}), 404

    # 2. Susun data header dokumen induk
    respons_data = {
        'no_nota': nota.no_nota,
        'tanggal': nota.tanggal.strftime('%d-%m-%Y') if nota.tanggal else '-',
        'supplier': nota.supplier.nama_supplier if nota.supplier else '-',
        'keterangan': nota.keterangan or '-',
        'items': [],
        'rols': []
    }

    # Blok Pengumpulan Data Item Rincian & Kode Telusur Rol (Berlanjut ke Potongan 2)
    # 3. KUMPULKAN RINCIAN MATERIAL NON-FILM (CURAH / PENOLONG)
    rincian_barang = KedatanganBahanDetail.query.filter_by(id_kedatangan=id_kedatangan).all()
    for item in rincian_barang:
        respons_data['items'].append({
            'kategori': item.bahan.kategori if item.bahan else '-',
            'id_bahan': item.id_bahan,
            'nama_bahan': item.bahan.nama_bahan if item.bahan else '-',
            'jumlah_masuk': item.jumlah_masuk if item.bahan and item.bahan.kategori != "BAHAN FILM" else 0,
            'satuan': item.bahan.satuan if item.bahan else '-'
        })

    # 4. KUMPULKAN DAFTAR KODE URUT TELUSUR GULUNGAN ROL FILM
    gulungan_film = StokFilmRol.query.filter_by(id_kedatangan=id_kedatangan).order_by(StokFilmRol.id_rol_internal.asc()).all()
    for rol in gulungan_film:
        respons_data['rols'].append({
            'kode_telusur': rol.id_kode_telusur,
            'nama_bahan': rol.bahan.nama_bahan if rol.bahan else '-',
            'panjang': rol.panjang_awal
        })

    return jsonify(respons_data)
    
# ==========================================================
# MODUL INTI: KARTU KENDALI TELUSUR FILM AKTIF (AUDIT SHEET)
# ==========================================================
@app.route('/transaksi/kartu-kendali-film')
def kartu_kendali_film():

    # Tarik semua daftar gulungan rol film yang statusnya masih TERSEDIA di rak gudang hulu
    daftar_rol_aktif = StokFilmRol.query.filter_by(status_rol='TERSEDIA')\
        .order_by(StokFilmRol.tanggal_datang.desc(), StokFilmRol.id_rol_internal.desc()).all()
    
    # Render ke dalam file template HTML baru
    return render_template(
        'kartu_kendali_film.html',
        rol_list=daftar_rol_aktif
    )
  
# ==============================================================================
# ROUTE PRODUKSI HARIAN FULL SINKRON BP KARTON GEMI SETITI (BAGIAN 1)
# ==============================================================================
@app.route('/transaksi/produksi-harian', methods=['GET', 'POST'])
def transaksi_produksi_harian():
    # 1. MATRIKS RESEP ADONAN BERDASARKAN KODE ID RESMI GUDANG
    KAMUS_RESEP_TETAP = {
        'PLAFON COKLAT': {'BB-001': 50.0, 'BB-002': 100.0, 'BB-003': 2.5, 'BB-004': 3.0, 'BB-005': 0.8, 'BB-006': 1.0, 'BB-007': 5.0, 'BB-008': 0.1, 'BB-009': 0.28},
        'PLAFON PUTIH': {'BB-001': 53.0, 'BB-002': 100.0, 'BB-003': 3.0, 'BB-004': 3.3, 'BB-005': 0.6, 'BB-006': 1.0, 'BB-007': 0.04, 'BB-008': 0.025, 'BB-009': 0.8, 'BB-012': 10.0},
        'LIS COKLAT': {'BB-001': 50.0, 'BB-002': 100.0, 'BB-003': 4.0, 'BB-004': 3.5, 'BB-005': 0.8, 'BB-007': 0.015, 'BB-008': 0.08, 'BB-009': 1.0, 'BB-010': 0.1, 'BB-011': 0.28},
        'LIS PUTIH': {'BB-001': 50.0, 'BB-002': 100.0, 'BB-003': 4.0, 'BB-004': 3.5, 'BB-006': 1.5, 'BB-005': 0.8, 'BB-007': 0.03, 'BB-008': 0.015, 'BB-009': 1.0}
    }
    
    if request.method == 'POST':
        tanggal_raw = request.form.get('tanggal')
        shift = request.form.get('shift', '').upper().strip()
        array_no_mesin = request.form.getlist('no_mesin[]')
        array_id_barang = request.form.getlist('id_barang_jadi[]')
        array_panjang = request.form.getlist('panjang_ukuran[]')
        array_baik = request.form.getlist('jumlah_produk_jadi[]')
        array_rusak_film = request.form.getlist('jumlah_produk_rusak_film[]')
        array_rusak_tanpa_film = request.form.getlist('jumlah_produk_rusak_tanpa_film[]')
        array_batch = request.form.getlist('jumlah_batch[]')
        array_adonan = request.form.getlist('tipe_adonan[]')
        array_telusur = request.form.getlist('kode_telusur_film[]')
        array_remarks = request.form.getlist('keterangan_baris[]')
        
        try:
            tanggal_fiskal = datetime.strptime(tanggal_raw, '%Y-%m-%d').date()
            # ==============================================================================
            # FIX FINAL: 1 MESIN 10 TIPE CUMA 3 MASAKAN - GROUPING BATCH PER MESIN + ADONAN
            # + FIX MASTER HILANG: konversi ID/nama robust
            # ==============================================================================
            rows_valid = []
            for i in range(len(array_no_mesin)):
                id_barang_input = (array_id_barang[i] or "").strip().upper()
                if not id_barang_input: 
                    continue
                id_barang_jadi = id_barang_input
                master_cari = db.session.get(BarangJadi, id_barang_jadi)
                if not master_cari:
                    master_cari = BarangJadi.query.filter(BarangJadi.nama_barang == id_barang_input).first()
                    if master_cari:
                        id_barang_jadi = master_cari.id_barang_jadi
                    else:
                        master_cari = BarangJadi.query.filter(BarangJadi.nama_barang.ilike(f"%{id_barang_input}%")).first()
                        if master_cari:
                            id_barang_jadi = master_cari.id_barang_jadi
                        else:
                            # coba cari by ID LIKE (untuk Y-03 C dll)
                            master_cari = BarangJadi.query.filter(BarangJadi.id_barang_jadi.ilike(f"%{id_barang_input}%")).first()
                            if master_cari:
                                id_barang_jadi = master_cari.id_barang_jadi
                            else:
                                continue
                rows_valid.append({
                    'idx': i,
                    'id_barang_jadi': id_barang_jadi,
                    'qty_baik': int(array_baik[i] or 0),
                    'qty_rusak_film': int(array_rusak_film[i] or 0),
                    'qty_rusak_tanpa_film': int(array_rusak_tanpa_film[i] or 0),
                    'jml_batch': int(array_batch[i] or 0),
                    'tipe_adonan': array_adonan[i].upper().strip(),
                    'no_mesin_aktif': array_no_mesin[i].upper().strip(),
                    'remarks_qc': array_remarks[i].upper().strip(),
                    'panjang_produk_kustom': float(array_panjang[i] or 4.0),
                    'kode_telusur_input': array_telusur[i].upper().strip(),
                })

            created = []
            for r in rows_valid:
                teks_audit_keterangan = f"{r['no_mesin_aktif']} | QC: {r['remarks_qc']} | LEN: {int(r['panjang_produk_kustom'])}"
                film_terpakai = float((r['qty_baik'] + r['qty_rusak_film']) * r['panjang_produk_kustom'])
                prod_baru = ProduksiHarian(
                    tanggal=tanggal_fiskal, shift=shift, id_barang_jadi=r['id_barang_jadi'], tipe_adonan=r['tipe_adonan'],
                    jumlah_batch=r['jml_batch'], jumlah_produk_jadi=r['qty_baik'], jumlah_produk_rusak_film=r['qty_rusak_film'],
                    jumlah_produk_rusak_tanpa_film=r['qty_rusak_tanpa_film'], kode_telusur_film=r['kode_telusur_input'], keterangan=teks_audit_keterangan
                )
                db.session.add(prod_baru)
                db.session.flush()
                r['prod_baru'] = prod_baru
                r['film_terpakai'] = film_terpakai
                created.append(r)

            # GROUPING BB MIXER PER MESIN+ADONAN
            from collections import defaultdict
            grouped = defaultdict(lambda: {'total_batch':0, 'first_prod':None, 'tipe_adonan':None})
            for r in created:
                key = f"{r['no_mesin_aktif']}|{r['tipe_adonan']}"
                grouped[key]['total_batch'] += int(r['jml_batch'] or 0)
                grouped[key]['tipe_adonan'] = r['tipe_adonan']
                if grouped[key]['first_prod'] is None:
                    grouped[key]['first_prod'] = r['prod_baru']

            for key, info in grouped.items():
                total_batch = info['total_batch']
                if total_batch <=0:
                    continue
                tipe_adonan = info['tipe_adonan']
                first_prod = info['first_prod']
                if tipe_adonan in KAMUS_RESEP_TETAP:
                    for id_bhn, takaran in KAMUS_RESEP_TETAP[tipe_adonan].items():
                        total_kg = round(takaran * total_batch, 2)
                        master_bahan = db.session.get(BahanBaku, id_bhn)
                        if master_bahan:
                            master_bahan.stok_akhir = round(master_bahan.stok_akhir - total_kg, 2)
                        db.session.add(ProduksiBahanPotong(id_produksi=first_prod.id_produksi, id_bahan=id_bhn, jumlah_terpakai=total_kg))

            # LANJUT PER BARIS UNTUK FILM, KARTON, NAT, LEM
            for r in created:
                prod_baru = r['prod_baru']
                id_barang_jadi = r['id_barang_jadi']
                qty_baik = r['qty_baik']
                qty_rusak_film = r['qty_rusak_film']
                qty_rusak_tanpa_film = r['qty_rusak_tanpa_film']
                tipe_adonan = r['tipe_adonan']
                panjang_produk_kustom = r['panjang_produk_kustom']
                kode_telusur_input = r['kode_telusur_input']
                film_terpakai = r['film_terpakai']
                master_barang_jadi = db.session.get(BarangJadi, id_barang_jadi)
                LIS_PAKAI_FILM = ["X2E","X2H","X2J","X2K","X2G","X2I","X2P","X2O","X2C","X2D","X2F","X2M"]
                if master_barang_jadi:
                    nama_cek_film = (master_barang_jadi.nama_barang or "").upper().strip()
                    is_lis_prod = "LIS" in nama_cek_film or id_barang_jadi.startswith("L-")
                    if is_lis_prod:
                        if not any(kode in nama_cek_film for kode in LIS_PAKAI_FILM):
                            film_terpakai = 0.0


                # B. KONDISI POTONG METERAN ROL FILM - FILTER LIS POLOSAN FINAL (X2A/X2B/X4B=0M)
                if film_terpakai > 0:
                    if kode_telusur_input:
                        rol_film = StokFilmRol.query.filter_by(id_kode_telusur=kode_telusur_input).first()
                        if rol_film:
                            rol_film.panjang_sisa = round(rol_film.panjang_sisa - film_terpakai, 2)
                            if rol_film.panjang_sisa <= 0:
                                rol_film.panjang_sisa = 0
                                rol_film.status_rol = 'HABIS'
                            m_film_master = db.session.get(BahanBaku, rol_film.id_bahan)
                            if m_film_master:
                                m_film_master.stok_akhir = round(m_film_master.stok_akhir - film_terpakai, 2)
                            db.session.add(ProduksiBahanPotong(id_produksi=prod_baru.id_produksi, id_bahan=rol_film.id_bahan, jumlah_terpakai=film_terpakai))
                    else:
                        if master_barang_jadi and master_barang_jadi.tipe_film and master_barang_jadi.tipe_film.strip().upper() not in ('0', 'POLOSAN', '-', ''):
                            kunci_film = master_barang_jadi.tipe_film.strip().upper()
                            m_film = BahanBaku.query.filter((BahanBaku.id_bahan == kunci_film) | (BahanBaku.nama_bahan == kunci_film)).first()
                            if m_film:
                                m_film.stok_akhir = round(m_film.stok_akhir - film_terpakai, 2)
                                db.session.add(ProduksiBahanPotong(id_produksi=prod_baru.id_produksi, id_bahan=m_film.id_bahan, jumlah_terpakai=film_terpakai))

                # C. KONDISI NAIKKAN STOK AKHIR MATERIAL SKU BARANG JADI (HASIL BAIK)
                if master_barang_jadi:
                    master_barang_jadi.stok_akhir = int(master_barang_jadi.stok_akhir + qty_baik)
                    
                    # D. INJEKSI AUTOMATION: KALKULATOR BP KARTON + NAT + LEM NAT/HOT/LAMINATE - FINAL Y-12..Y-17 + Y-12 P..Y-17 P NO C
                    krt_15, krt_20, krt_sb, krt_lis_x2, krt_lis_x4, krt_lis_x5x6, krt_nat_silver, krt_nat_gold, krt_lem_nat, krt_lem_hot, krt_lem_lam = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                    sku_nama = master_barang_jadi.nama_barang.upper().strip() if master_barang_jadi.nama_barang else ""
                    id_sku_upper = id_barang_jadi.upper().strip()
                    
                    PLAFON_NAT_SILVER = ["Y-03","Y-05","Y-45","Y-47"]
                    PLAFON_NAT_GOLD = ["Y-13","Y-15","Y-17","Y-37","Y-41"]
                    LEM_NAT_PLAFON = ["Y-03","Y-05","Y-13 P","Y-15 P","Y-17 P"]
                    LEM_NAT_LIS = ["X2E","X2H","X2J","X2K","X2G","X2I","X2P","X2O","X2C","X2D","X2F","X2M"]
                    LEM_HOT_LIST = ["Y-01","Y-02","Y-03","Y-04","Y-05","Y-06","Y-07","Y-08","Y-09","Y-10","Y-11","Y-12","Y-13","Y-14","Y-15","Y-16","Y-17","Y-32","Y-33","Y-34","Y-35","Y-36","Y-37","Y-38","Y-39","Y-40","Y-41","Y-42","Y-43","Y-44","Y-45","Y-46","Y-47","Y-48","Y-12 P","Y-13 P","Y-14 P","Y-15 P","Y-16 P","Y-17 P"]
                    LEM_LAM_LIST = ["Y-18","Y-19","Y-20","Y-21","Y-22","Y-23","Y-24","Y-25","Y-26","Y-27","Y-28","Y-29","Y-30","Y-31"]
                    
                    if "PLAFON" in sku_nama or sku_nama.startswith("P-") or id_barang_jadi.startswith("P-"):
                        pak_utuh = qty_baik // 15
                        sisa_eceran = qty_baik % 15
                        total_pak = pak_utuh + (1 if sisa_eceran >= 5 else 0)
                        if total_pak > 0:
                            if panjang_produk_kustom <= 3.0:
                                krt_15 = float(total_pak * 2)
                            elif panjang_produk_kustom <= 4.0:
                                krt_20 = float(total_pak * 2)
                            elif panjang_produk_kustom <= 5.0:
                                krt_15 = float(total_pak * 2)
                                krt_sb = float(total_pak * 1)
                            else:
                                krt_20 = float(total_pak * 2)
                                krt_sb = float(total_pak * 1)
                        total_batang = qty_baik + qty_rusak_film + qty_rusak_tanpa_film
                        cek = sku_nama + " " + id_sku_upper
                        meter_total = float(total_batang * panjang_produk_kustom)
                        is_c_code = " C" in cek
                        if not is_c_code:
                            if any(k in cek for k in PLAFON_NAT_SILVER):
                                krt_nat_silver = meter_total
                            if any(k in cek for k in PLAFON_NAT_GOLD):
                                krt_nat_gold = meter_total
                            if any(k in cek for k in LEM_NAT_PLAFON):
                                krt_lem_nat += meter_total * 0.0002
                            if any(k in cek for k in LEM_HOT_LIST):
                                krt_lem_hot += meter_total * 0.0038
                            if any(k in cek for k in LEM_LAM_LIST):
                                krt_lem_lam += meter_total * 0.01

                    elif "LIS" in sku_nama or sku_nama.startswith("L-") or id_barang_jadi.startswith("L-"):
                        nama_asli_produk = sku_nama
                        if master_barang_jadi and master_barang_jadi.nama_barang:
                            nama_asli_produk = master_barang_jadi.nama_barang.upper().strip()
                        seri_24 = ["X2A","X2B","X2E","X2H","X2J","X2K","X2G","X2I","X2P","X2O","X2C","X2D","X2F","X2M","X7A","X7B", "X2", "X7"]
                        kapasitas = 24 if any(s in nama_asli_produk for s in seri_24) else 48
                        pak_utuh = qty_baik // kapasitas
                        sisa_eceran = qty_baik % kapasitas
                        total_pak = pak_utuh + (1 if sisa_eceran >= 5 else 0)
                        if total_pak > 0:
                            vol = float(total_pak * 2)
                            if "X4" in nama_asli_produk:
                                krt_lis_x4 = vol
                            elif "X5" in nama_asli_produk or "X6" in nama_asli_produk:
                                krt_lis_x5x6 = vol
                            else:
                                krt_lis_x2 = vol
                        total_batang_lis = qty_baik + qty_rusak_film + qty_rusak_tanpa_film
                        meter_lis = float(total_batang_lis * panjang_produk_kustom)
                        if any(k in nama_asli_produk for k in LEM_NAT_LIS):
                            krt_lem_nat += meter_lis * 0.001

                    # Eksekusi pengurangan - MAP KE ID SCREENSHOT BP-011,012,013
                    peta_potong = {'BP-001': krt_15, 'BP-002': krt_20, 'BP-003': krt_sb, 'BP-005': krt_lis_x4, 'BP-006': krt_lis_x5x6, 'BP-014': krt_lis_x2, 'BP-010': krt_nat_silver, 'BP-009': krt_nat_gold, 'BP-011': krt_lem_nat, 'BP-012': krt_lem_hot, 'BP-013': krt_lem_lam}
                    for id_krt, vol_pakai in peta_potong.items():
                        if vol_pakai > 0:
                            item_master = db.session.get(BahanBaku, id_krt)
                            if item_master:
                                item_master.stok_akhir = round(item_master.stok_akhir - vol_pakai, 2)
                            # Catat histori pemakaian ke tabel log jembatan produksi
                            db.session.add(ProduksiBahanPotong(id_produksi=prod_baru.id_produksi, id_bahan=id_krt, jumlah_terpakai=vol_pakai))
# ==============================================================================
# ROUTE PRODUKSI HARIAN FULL SINKRON BP KARTON GEMI SETITI (BAGIAN 3)
# ==============================================================================
            db.session.commit()
            flash(f"Sukses! Jurnal Laporan Produksi {shift} berhasil dibukukan hulu.", "success")
            return redirect(url_for('transaksi_produksi_harian'))
        except Exception as e:
            db.session.rollback()
            flash(f"Gagal memproses jurnal produksi massal: {str(e)}", "danger")
            return redirect(url_for('transaksi_produksi_harian'))

    # ==============================================================================
    # 2. JALUR GET - DATA HISTORIS DENGAN REKONSTRUKSI SUSUT BERANTAI
    # ==============================================================================
    produk_mentah = BarangJadi.query.order_by(BarangJadi.id_barang_jadi.asc()).all()
    semua_produk = []
    for prd in produk_mentah:
        if prd.tipe_film: prd.tipe_film = prd.tipe_film.upper().strip()
        semua_produk.append(prd)
        
    semua_bahan = BahanBaku.query.order_by(BahanBaku.id_bahan.asc()).all()
    tgl_dari_raw = request.args.get('tgl_dari', '')
    tgl_sampai_raw = request.args.get('tgl_sampai', '')
    
    query_prod = ProduksiHarian.query
    if tgl_dari_raw:
        tgl_dari = datetime.strptime(tgl_dari_raw, '%Y-%m-%d').date()
        query_prod = query_prod.filter(ProduksiHarian.tanggal >= tgl_dari)
    if tgl_sampai_raw:
        tgl_sampai = datetime.strptime(tgl_sampai_raw, '%Y-%m-%d').date()
        query_prod = query_prod.filter(ProduksiHarian.tanggal <= tgl_sampai)
        
    riwayat_prod_mentah = query_prod.order_by(ProduksiHarian.tanggal.desc(), ProduksiHarian.id_produksi.desc()).all()
    riwayat_prod = []
    kamus_susut_mundur = {}
    # BUILD KAMUS MASTER UNTUK FIX MASTER HILANG
    kamus_master_id = {m.id_barang_jadi.upper(): m for m in semua_produk}
    kamus_master_nama = { (m.nama_barang or '').upper(): m for m in semua_produk}
    
    for p in reversed(riwayat_prod_mentah):
        # FIX MASTER HILANG: coba attach manual jika relationship kosong
        if not p.barang_jadi:
            id_cari = (p.id_barang_jadi or '').upper().strip()
            master_fix = kamus_master_id.get(id_cari)
            if not master_fix:
                # coba cari contains
                for mid, mobj in kamus_master_id.items():
                    if id_cari in mid or mid in id_cari:
                        master_fix = mobj
                        break
            if not master_fix:
                master_fix = kamus_master_nama.get(id_cari)
            if master_fix:
                # attach secara paksa ke property (bypass relationship)
                p.barang_jadi = master_fix

        p.panjang_awal_gudang = 0
        p.panjang_sisa_gudang = 0
        if p.kode_telusur_film and p.kode_telusur_film.strip() != "-":
            no_seri_rol = p.kode_telusur_film.strip()
            rol = StokFilmRol.query.filter_by(id_kode_telusur=no_seri_rol).first()
            if rol:
                qty_b = p.jumlah_produk_jadi or 0
                qty_r = p.jumlah_produk_rusak_film or 0
                panjang_m = 4.0
                if p.keterangan and "LEN:" in p.keterangan:
                    try: panjang_m = float(p.keterangan.split("LEN:")[-1].strip())
                    except (ValueError, IndexError): panjang_m = 4.0
                meter_terpakai_shift_ini = int((qty_b + qty_r) * panjang_m)
                if no_seri_rol not in list(kamus_susut_mundur.keys()):
                    p.panjang_awal_gudang = int(rol.panjang_awal)
                else:
                    p.panjang_awal_gudang = int(kamus_susut_mundur[no_seri_rol])
                p.panjang_sisa_gudang = int(p.panjang_awal_gudang - meter_terpakai_shift_ini)
                kamus_susut_mundur[no_seri_rol] = p.panjang_sisa_gudang
        riwayat_prod.append(p)
        
    riwayat_prod.reverse()
    return render_template('produksi_harian.html', semua_produk=semua_produk, bahan_list=semua_bahan, produksi_list=riwayat_prod, tanggal_hari_ini=datetime.now().strftime('%Y-%m-%d'), tgl_dari_val=tgl_dari_raw, tgl_sampai_val=tgl_sampai_raw)

# ==========================================================
# API ENDPOINT: PENYUPLAI RADAR ROL FILM SANGAT CERDAS
# ==========================================================
@app.route('/api/get-rol-tersedia/<string:id_bahan>')
def api_get_rol_tersedia(id_bahan):
    # 1. Bersihkan kata kunci dari spasi tersembunyi
    kata_kunci = id_bahan.strip()
    
    # 2. Lakukan pelacakan berantai (Cari ID Bahan murninya di tabel master berdasarkan nama seperti 'NP-29')
    master_bahan = BahanBaku.query.filter(
        (BahanBaku.id_bahan == kata_kunci) | 
        (BahanBaku.nama_bahan == kata_kunci)
    ).first()
    
    # Ambil ID Bahan murni hasil pencarian (misal 'BF-001'), jika tidak ketemu pakai kata kunci awal
    id_bahan_murni = master_bahan.id_bahan if master_bahan else kata_kunci
    
    # 3. Tarik seluruh daftar gulungan rol film dari rak gudang yang statusnya TERSEDIA
    rols_gudang = StokFilmRol.query.filter_by(
        id_bahan=id_bahan_murni, 
        status_rol='TERSEDIA'
    ).order_by(StokFilmRol.id_rol_internal.asc()).all()
    
    respons = {'rols': []}
    for r in rols_gudang:
        respons['rols'].append({
            'kode_telusur': r.id_kode_telusur,
            'panjang_sisa': r.panjang_sisa
        })
    return jsonify(respons)

# ==============================================================================
# FIX FINAL POST SINKRON: ENGINE TANGKAP ALASAN KORIDOR ADAPTIF GUDANG (APP.PY)
# ==============================================================================
# ==============================================================================
# LOCK FINAL PART 1: ENGINE SIMPAN ADJUSTMENT KEDAP INVALID ARGUMENT (APP.PY)
# ==============================================================================
@app.route('/transaksi/penyesuaian-stok/simpan', methods=['POST'])
def simpan_penyesuaian_stok():
    try:
        id_edit = request.form.get('id_penyesuaian_edit', '').strip()
        tanggal_raw = request.form.get('tanggal_transaksi')
        kategori = request.form.get('kategori_cases', request.form.get('kategori_kasus', '')).upper().strip()
        jenis_saklar = request.form.get('jenis_saklar', 'MASUK').upper().strip()
        id_bahan = request.form.get('id_bahan', '').strip()
        qty_murni = float(request.form.get('jumlah_volume', 0))
        alasan = request.form.get('alasan_koreksi', '').upper().strip()
        
        if not alasan:
            alasan = "ADJUSTMENT SYSTEM"
            
        tanggal_fiskal = datetime.strptime(tanggal_raw, '%Y-%m-%d').date()

        # FORMULASI AKUNTANSI: Jumlah efektif dipaksa minus (-) jika arahnya KELUAR
        qty_efektif = qty_murni if jenis_saklar == 'MASUK' else -abs(qty_murni)

        if not id_edit:
            # MENGUNCI HANYA ATRIBUT KOLOM YANG SAH SESUAI KELAS MODEL DATABASE ANDA
            mutasi_baru = PenyesuaianStok(
                tanggal=tanggal_fiskal,
                kategori=kategori,
                jenis_saklar=jenis_saklar,
                id_bahan=id_bahan,
                jumlah_input=qty_murni,
                jumlah_efektif=qty_efektif,
                alasan_keterangan=alasan
            )
            db.session.add(mutasi_baru)
            
            # SAKLAR LOGISTIK: Update mutasi langsung ke kolom master stok_akhir BahanBaku
            master_bhn = db.session.get(BahanBaku, id_bahan)
            if master_bhn:
                if jenis_saklar == 'MASUK':
                    master_bhn.stok_akhir = round(master_bhn.stok_akhir + qty_murni, 2)
                else:
                    master_bhn.stok_akhir = round(master_bhn.stok_akhir - qty_murni, 2)
        else:
            # FIXED: MODE EDIT - REVERSAL STOK LAMA + APPLY BARU
            log_lama = db.session.get(PenyesuaianStok, int(id_edit))
            if not log_lama:
                flash("Data adjustment yang akan diedit tidak ditemukan!", "danger")
                return redirect(url_for('monitoring_kartu_stok'))
            
            # 1. Reversal stok lama
            old_bahan_id = log_lama.id_bahan
            old_qty = float(log_lama.jumlah_input or 0)
            old_saklar = log_lama.jenis_saklar
            master_old = db.session.get(BahanBaku, old_bahan_id)
            if master_old and old_qty > 0:
                if old_saklar == 'MASUK':
                    master_old.stok_akhir = round(master_old.stok_akhir - old_qty, 2)
                else:
                    master_old.stok_akhir = round(master_old.stok_akhir + old_qty, 2)
            
            # 2. Update field log
            log_lama.tanggal = tanggal_fiskal
            log_lama.kategori = kategori
            log_lama.jenis_saklar = jenis_saklar
            log_lama.id_bahan = id_bahan
            log_lama.jumlah_input = qty_murni
            log_lama.jumlah_efektif = qty_efektif
            log_lama.alasan_keterangan = alasan
            
            # 3. Apply stok baru
            master_new = db.session.get(BahanBaku, id_bahan)
            if master_new:
                if jenis_saklar == 'MASUK':
                    master_new.stok_akhir = round(master_new.stok_akhir + qty_murni, 2)
                else:
                    master_new.stok_akhir = round(master_new.stok_akhir - qty_murni, 2)
                    
        db.session.commit()
        flash(f"Sukses! Data penyesuaian stok {kategori} berhasil dibukukan hulu.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Gagal mengeksekusi adjustment persediaan. Eror: {str(e)}", "danger")
        
    return redirect(url_for('monitoring_kartu_stok'))

# ==============================================================================
# POTONGAN 3: REVISI ENGINE UTAMA KARTU STOK SINKRON DATA POPUP (APP.PY)
# ==============================================================================
@app.route('/monitoring/kartu-stok')
def monitoring_kartu_stok():
    tgl_dari_raw = request.args.get('tgl_dari', datetime.now().strftime('%Y-%m-01'))
    tgl_sampai_raw = request.args.get('tgl_sampai', datetime.now().strftime('%Y-%m-%d'))
    
    daftar_mutasi_kartu = []
    try:
        tgl_dari = datetime.strptime(tgl_dari_raw, '%Y-%m-%d').date()
        tgl_sampai = datetime.strptime(tgl_sampai_raw, '%Y-%m-%d').date()
        semua_bahan = BahanBaku.query.order_by(BahanBaku.id_bahan.asc()).all()

        # ==============================================================================
        # MASTER FIX: INTEGRASI LOGIKAL KEDAP EROR (POST-GET SINKRONISASI)
        # ==============================================================================
        for b in semua_bahan:
            # --- BLOK 1: HITUNG TOTAL MUTASI MASA LALU (SAMPAI H-1 TGL_DARI) ---
            past_in_supplier = db.session.query(db.func.sum(KedatanganBahanDetail.jumlah_masuk)).join(KedatanganBahan).filter(
                KedatanganBahanDetail.id_bahan == b.id_bahan, KedatanganBahan.tanggal < tgl_dari
            ).scalar() or 0.0
            
            past_in_sisa_prod = db.session.query(db.func.sum(PenyesuaianStok.jumlah_input)).filter(
                PenyesuaianStok.id_bahan == b.id_bahan, PenyesuaianStok.kategori == 'SISA_PROD', PenyesuaianStok.tanggal < tgl_dari
            ).scalar() or 0.0
            
            past_koreksi = db.session.query(db.func.sum(PenyesuaianStok.jumlah_efektif)).filter(
                PenyesuaianStok.id_bahan == b.id_bahan, PenyesuaianStok.kategori == 'KOREKSI_RETUR', PenyesuaianStok.tanggal < tgl_dari
            ).scalar() or 0.0

            past_out_mesin = db.session.query(db.func.sum(ProduksiBahanPotong.jumlah_terpakai)).join(ProduksiHarian).filter(
                ProduksiBahanPotong.id_bahan == b.id_bahan, ProduksiHarian.tanggal < tgl_dari
            ).scalar() or 0.0
            
            past_out_perbaikan = db.session.query(db.func.sum(PenyesuaianStok.jumlah_input)).filter(
                PenyesuaianStok.id_bahan == b.id_bahan, PenyesuaianStok.kategori == 'PERBAIKAN', PenyesuaianStok.tanggal < tgl_dari
            ).scalar() or 0.0

            saldo_awal_dinamis = float(b.saldo_awal or 0.0) + past_in_supplier + past_in_sisa_prod + past_koreksi - past_out_mesin - past_out_perbaikan

            # --- BLOK 2: HITUNG MUTASI AKTUAL DI DALAM RENTANG FILTER TANGGAL ---
            in_supplier = 0.0
            try:
                detail_masuk = KedatanganBahanDetail.query.filter_by(id_bahan=b.id_bahan).all()
                for item in detail_masuk:
                    if item.id_kedatangan:
                        nota_induk = KedatanganBahan.query.filter_by(id_kedatangan=item.id_kedatangan).first()
                        if nota_induk and nota_induk.tanggal and tgl_dari <= nota_induk.tanggal <= tgl_sampai:
                            in_supplier += float(item.jumlah_masuk or 0)
            except Exception: 
                in_supplier = 0.0

            in_sisa_prod = db.session.query(db.func.sum(PenyesuaianStok.jumlah_input)).filter(
                PenyesuaianStok.id_bahan == b.id_bahan, PenyesuaianStok.kategori == 'SISA_PROD',
                PenyesuaianStok.tanggal >= tgl_dari, PenyesuaianStok.tanggal <= tgl_sampai
            ).scalar() or 0.0

            koreksi_stok = db.session.query(db.func.sum(PenyesuaianStok.jumlah_efektif)).filter(
                PenyesuaianStok.id_bahan == b.id_bahan, PenyesuaianStok.kategori == 'KOREKSI_RETUR',
                PenyesuaianStok.tanggal >= tgl_dari, PenyesuaianStok.tanggal <= tgl_sampai
            ).scalar() or 0.0

            out_pakai_mesin = db.session.query(db.func.sum(ProduksiBahanPotong.jumlah_terpakai)).join(
                ProduksiHarian, ProduksiBahanPotong.id_produksi == ProduksiHarian.id_produksi
            ).filter(
                ProduksiBahanPotong.id_bahan == b.id_bahan,
                ProduksiHarian.tanggal >= tgl_dari,
                ProduksiHarian.tanggal <= tgl_sampai
            ).scalar() or 0.0
            
            out_perbaikan = db.session.query(db.func.sum(PenyesuaianStok.jumlah_input)).filter(
                PenyesuaianStok.id_bahan == b.id_bahan, PenyesuaianStok.kategori == 'PERBAIKAN',
                PenyesuaianStok.tanggal >= tgl_dari, PenyesuaianStok.tanggal <= tgl_sampai
            ).scalar() or 0.0

            # --- BLOK 3: FORMULASI STOK AKHIR PERIODE PILIHAN ---
            stok_akhir_periode = saldo_awal_dinamis + in_supplier + in_sisa_prod - out_pakai_mesin - out_perbaikan + koreksi_stok

            daftar_mutasi_kartu.append({
                'id_bahan': b.id_bahan, 'nama_bahan': b.nama_bahan, 'satuan': b.satuan if b.satuan else 'KG',
                'saldo_awal': round(saldo_awal_dinamis, 2), 'in_supplier': round(in_supplier, 2),
                'in_sisa_prod': round(in_sisa_prod, 2), 'koreksi': round(koreksi_stok, 2),
                'out_pakai_mesin': round(out_pakai_mesin, 2), 'out_perbaikan': round(out_perbaikan, 2),
                'stok_akhir': round(stok_akhir_periode, 2)
            })

        riwayat_koreksi_list = PenyesuaianStok.query.filter(
            PenyesuaianStok.tanggal >= tgl_dari, PenyesuaianStok.tanggal <= tgl_sampai
        ).order_by(PenyesuaianStok.tanggal.desc(), PenyesuaianStok.id_penyesuaian.desc()).all()

    except Exception as e:
        db.session.rollback()
        riwayat_koreksi_list = []
        flash(f"Gagal memproses kalkulasi kartu stok: {str(e)}", "danger")

    try:
        return render_template(
            'monitoring/kartu_stok.html', 
            kartu_list=daftar_mutasi_kartu,
            bahan_list=BahanBaku.query.order_by(BahanBaku.id_bahan.asc()).all(),
            tgl_dari_val=tgl_dari_raw, 
            tgl_sampai_val=tgl_sampai_raw
        )
    except Exception:
        return render_template(
            'kartu_stok.html', 
            kartu_list=daftar_mutasi_kartu,
            bahan_list=BahanBaku.query.order_by(BahanBaku.id_bahan.asc()).all(),
            tgl_dari_val=tgl_dari_raw, 
            tgl_sampai_val=tgl_sampai_raw
        )

# =============================================================================
# SUBFOLDER BARU: LOG BAHAN BAKU TERPISAH - BIAR KARTU STOK BB LEGA
# =============================================================================
@app.route('/monitoring/log-bahan-baku')
def monitoring_log_bahan_baku():
    tgl_dari_raw = request.args.get('tgl_dari', datetime.now().strftime('%Y-%m-01'))
    tgl_sampai_raw = request.args.get('tgl_sampai', datetime.now().strftime('%Y-%m-%d'))
    riwayat_koreksi_list = []
    try:
        tgl_dari = datetime.strptime(tgl_dari_raw, '%Y-%m-%d').date()
        tgl_sampai = datetime.strptime(tgl_sampai_raw, '%Y-%m-%d').date()
        riwayat_koreksi_list = PenyesuaianStok.query.filter(
            PenyesuaianStok.tanggal >= tgl_dari,
            PenyesuaianStok.tanggal <= tgl_sampai
        ).order_by(PenyesuaianStok.tanggal.desc(), PenyesuaianStok.id_penyesuaian.desc()).all()
    except Exception as e:
        db.session.rollback()
        riwayat_koreksi_list = []
        flash(f"Gagal memproses log bahan baku: {str(e)}", "danger")

    try:
        return render_template(
            'monitoring/log_bahan_baku.html',
            log_koreksi_list=riwayat_koreksi_list,
            bahan_list=BahanBaku.query.order_by(BahanBaku.id_bahan.asc()).all(),
            tgl_dari_val=tgl_dari_raw,
            tgl_sampai_val=tgl_sampai_raw
        )
    except Exception:
        return render_template(
            'log_bahan_baku.html',
            log_koreksi_list=riwayat_koreksi_list,
            bahan_list=BahanBaku.query.order_by(BahanBaku.id_bahan.asc()).all(),
            tgl_dari_val=tgl_dari_raw,
            tgl_sampai_val=tgl_sampai_raw
        )

# ==========================================================
# SAKLAR BACKEND: FUNGSI HAPUS GULUNGAN ROL FILM TUNGGAL FROM POP-UP
# ==========================================================
@app.route('/transaksi/kedatangan-bahan/hapus-rol/<string:kode_telusur>', methods=['POST'])
def hapus_rol_tunggal(kode_telusur):
    try:
        # 1. Cari data rol film di rak gudang berdasarkan kode telusur uniknya
        rol = StokFilmRol.query.filter_by(id_kode_telusur=kode_telusur).first()
        if not rol:
            flash("Data rol film tidak ditemukan atau sudah dihapus!", "danger")
            return redirect(url_for('transaksi_kedatangan_bahan'))
        
        # 2. Ambil objek master bahan baku terkait untuk dikurangi stok akhirnya (Akuntansi Koreksi)
        master_bahan = db.session.get(BahanBaku, rol.id_bahan)
        if master_bahan:
            # Kurangi stok akhir master bahan baku sebesar panjang awal rol yang dihapus
            master_bahan.stok_akhir = round(master_bahan.stok_akhir - rol.panjang_awal, 2)
            if master_bahan.stok_akhir < 0:
                master_bahan.stok_akhir = 0.0

        # 3. Eksekusi hapus fisik data gulungan rol dari database
        db.session.delete(rol)
        db.session.commit()
        
        flash(f"Sukses Audit! Gulungan rol film {kode_telusur} berhasil dihapus dan stok hulu disesuaikan.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal menghapus gulungan rol film. Eror audit: {str(e)}", "danger")
        
    return redirect(url_for('transaksi_kedatangan_bahan'))
# ==========================================================
# SAKLAR BACKEND: FUNGSI KOREKSI KUANTITAS MATERIAL CURAH (KG)
# ==========================================================
@app.route('/transaksi/kedatangan-bahan/edit-curah/<int:id_kedatangan>/<string:id_bahan>', methods=['POST'])
def edit_curah_tunggal(id_kedatangan, id_bahan):
    try:
        volume_baru = float(request.form.get('volume_baru', 0))
        detail = KedatanganBahanDetail.query.filter_by(id_kedatangan=id_kedatangan, id_bahan=id_bahan).first()
        if not detail:
            flash("Data rincian material tidak ditemukan!", "danger")
            return redirect(url_for('transaksi_kedatangan_bahan'))
        
        selisih_volume = volume_baru - detail.jumlah_masuk
        master_bahan = db.session.get(BahanBaku, id_bahan)
        if master_bahan:
            master_bahan.stok_akhir = round(master_bahan.stok_akhir + selisih_volume, 2)
            if master_bahan.stok_akhir < 0: 
                master_bahan.stok_akhir = 0.0

        detail.jumlah_masuk = volume_baru
        db.session.commit()
        flash(f"Sukses Koreksi! Volume material {id_bahan} disesuaikan menjadi {volume_baru}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal memproses koreksi material. Eror: {str(e)}", "danger")
    return redirect(url_for('transaksi_kedatangan_bahan'))

# ==========================================================
# SAKLAR BACKEND: FUNGSI HAPUS ITEM MATERIAL CURAH DARI NOTA
# ==========================================================
@app.route('/transaksi/kedatangan-bahan/hapus-curah/<int:id_kedatangan>/<string:id_bahan>', methods=['POST'])
def hapus_curah_tunggal(id_kedatangan, id_bahan):
    try:
        detail = KedatanganBahanDetail.query.filter_by(id_kedatangan=id_kedatangan, id_bahan=id_bahan).first()
        if not detail:
            flash("Data material sudah tidak ada!", "danger")
            return redirect(url_for('transaksi_kedatangan_bahan'))
        
        master_bahan = db.session.get(BahanBaku, id_bahan)
        if master_bahan:
            master_bahan.stok_akhir = round(master_bahan.stok_akhir - detail.jumlah_masuk, 2)
            if master_bahan.stok_akhir < 0: 
                master_bahan.stok_akhir = 0.0

        db.session.delete(detail)
        db.session.commit()
        flash(f"Sukses Audit! Material {id_bahan} berhasil dihapus dari daftar nota kedatangan.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal menghapus material dari nota. Eror: {str(e)}", "danger")
    return redirect(url_for('transaksi_kedatangan_bahan'))
# ==========================================================
# SAKLAR BACKEND: FUNGSI KOREKSI UKURAN PANJANG ROL FILM TUNGGAL
# ==========================================================
@app.route('/transaksi/kedatangan-bahan/edit-rol/<string:kode_telusur>', methods=['POST'])
def edit_rol_tunggal(kode_telusur):
    try:
        # 1. Tangkap angka panjang baru dari form HTML virtual
        panjang_baru = float(request.form.get('panjang_baru', 0))
        
        # 2. Cari data gulungan film lama di database berdasarkan kode telusur
        rol = StokFilmRol.query.filter_by(id_kode_telusur=kode_telusur).first()
        if not rol:
            flash("Data rol film tidak ditemukan!", "danger")
            return redirect(url_for('transaksi_kedatangan_bahan'))
        
        # 3. Hitung selisih perubahan ukuran untuk mengoreksi stok akhir master bahan
        selisih_meter = panjang_baru - rol.panjang_awal
        
        master_bahan = db.session.get(BahanBaku, rol.id_bahan)
        if master_bahan:
            # Sesuaikan neraca stok gudang hulu berdasarkan selisih (bisa plus atau minus)
            master_bahan.stok_akhir = round(master_bahan.stok_akhir + selisih_meter, 2)
            if master_bahan.stok_akhir < 0: 
                master_bahan.stok_akhir = 0.0

        # 4. Update data panjang fisik gulungan di database (FIXED - SISA DIKALIBRASI PAKAI SELISIH)
        rol.panjang_awal = panjang_baru
        rol.panjang_sisa = round(rol.panjang_sisa + selisih_meter, 2) # Sisa ikut terkoreksi, tidak reset full
        if rol.panjang_sisa < 0:
            rol.panjang_sisa = 0.0
        if rol.panjang_sisa > 0:
            rol.status_rol = 'TERSEDIA'
        db.session.commit()
        
        flash(f"Sukses Koreksi! Ukuran rol {kode_telusur} diperbarui menjadi {panjang_baru} Meter.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal memproses koreksi rol film. Eror audit: {str(e)}", "danger")
        
    return redirect(url_for('transaksi_kedatangan_bahan'))
@app.route('/transaksi/produksi-harian/hapus/<int:id_prod>', methods=['POST'])
def hapus_produksi_harian(id_prod):
    prod = db.session.get(ProduksiHarian, id_prod)
    if not prod:
        flash("Data jurnal produksi tidak ditemukan!", "danger")
        return redirect(url_for('transaksi_produksi_harian'))
        
    try:
        # 1. KAMUS RESEP TETAP UNTUK REVERSAL MATERIAL CURAH (FIXED - SINKRON DENGAN KAMUS PRODUKSI)
        RESEP = {
            'PLAFON COKLAT': {'BB-001': 50.0, 'BB-002': 100.0, 'BB-003': 2.5, 'BB-004': 3.0, 'BB-005': 0.8, 'BB-006': 1.0, 'BB-007': 5.0, 'BB-008': 0.1, 'BB-009': 0.28},
            'PLAFON PUTIH': {'BB-001': 53.0, 'BB-002': 100.0, 'BB-003': 3.0, 'BB-004': 3.3, 'BB-005': 0.6, 'BB-006': 1.0, 'BB-007': 0.04, 'BB-008': 0.025, 'BB-009': 0.8, 'BB-012': 10.0},
            'LIS COKLAT': {'BB-001': 50.0, 'BB-002': 100.0, 'BB-003': 4.0, 'BB-004': 3.5, 'BB-005': 0.8, 'BB-007': 0.015, 'BB-008': 0.08, 'BB-009': 1.0, 'BB-010': 0.1, 'BB-011': 0.28},
            'LIS PUTIH': {'BB-001': 50.0, 'BB-002': 100.0, 'BB-003': 4.0, 'BB-004': 3.5, 'BB-006': 1.5, 'BB-005': 0.8, 'BB-007': 0.03, 'BB-008': 0.015, 'BB-009': 1.0}
        }
        
        # 2. REVERSAL STOK GUDANG ROL FILM (KEMBALIKAN METERAN SISA)
        qty_baik = prod.jumlah_produk_jadi or 0
        qty_rusak = prod.jumlah_produk_rusak_film or 0
        panjang_m = 4.0
        
        if prod.id_barang_jadi:
            master_brg = db.session.get(BarangJadi, prod.id_barang_jadi)
            if master_brg:
                # Potong kembali stok produk jadi yang batal diproduksi hulu
                master_brg.stok_akhir = int(master_brg.stok_akhir - qty_baik)
              
               # ==============================================================================
        # FIX KALIBRASI HAPUS ACAK: REKONSTRUKSI ULANG SISA ROL AKTIF GUDANG (APP.PY)
        # ==============================================================================
        if prod.kode_telusur_film and prod.kode_telusur_film.strip() != "-":
            no_seri_rol = prod.kode_telusur_film.strip()
            rol = StokFilmRol.query.filter_by(id_kode_telusur=no_seri_rol).first()
            
            if rol:
                # 1. Tarik semua baris jurnal produksi LAIN yang masih aktif memakai rol ini
                sisa_jurnal_aktif = ProduksiHarian.query.filter(
                    ProduksiHarian.kode_telusur_film == no_seri_rol,
                    ProduksiHarian.id_produksi != prod.id_produksi
                ).all()
                
                # 2. Hitung total komulatif pemakaian dari baris-baris yang tersisa
                total_meter_terpakai_sisa_jurnal = 0
                for pj in sisa_jurnal_aktif:
                    qb = pj.jumlah_produk_jadi or 0
                    qr = pj.jumlah_produk_rusak_film or 0
                    
                    # Deteksi ukuran panjang kustom dari teks keterangan
                    p_len = 4.0
                    if pj.keterangan and "LEN:" in pj.keterangan:
                        try:
                            p_len = float(pj.keterangan.split("LEN:")[-1].strip())
                        except (ValueError, IndexError):
                            p_len = 4.0
                            
                    total_meter_terpakai_sisa_jurnal += int((qb + qr) * p_len)
                
                # 3. Kunci Nilai Fisik Gudang: Sisa Riil Gudang = Panjang Awal Pabrik - Total Sisa Pemakaian Jurnal
                rol.panjang_sisa = round(rol.panjang_awal - total_meter_terpakai_sisa_jurnal, 2)
                
                # Proteksi anti-minus batas bawah gudang
                if rol.panjang_sisa < 0:
                    rol.panjang_sisa = 0.0
                    
                # Buka kembali gembok status gulungan aktif hulu
                rol.status_rol = 'TERSEDIA'


        # 3. REVERSAL MATERIAL CURAH (TAMBAHKAN KEMBALI STOK MIXER BERDASARKAN BATCH)
        if prod.tipe_adonan in RESEP:
            resep_terpilih = RESEP[prod.tipe_adonan]
            for id_bhn, takaran in resep_terpilih.items():
                total_kg_kembali = round(takaran * (prod.jumlah_batch or 1), 2)
                master_bahan = db.session.get(BahanBaku, id_bhn)
                if master_bahan:
                    master_bahan.stok_akhir = round(master_bahan.stok_akhir + total_kg_kembali, 2)
                    
        # 4. EKSEKUSI PENGHAPUSAN MULTI-TABEL SECARA BERSIH
        ProduksiBahanPotong.query.filter_by(id_produksi=prod.id_produksi).delete()
        db.session.delete(prod)
        db.session.commit()
        
        flash("Sukses Reversal! Jurnal produksi berhasil dihapus dan seluruh stok dikembalikan.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal menghapus data hulu. Eror audit: {str(e)}", "danger")
        
    return redirect(url_for('transaksi_produksi_harian'))

# ==============================================================================
# LOCK FINAL PART 2: ROUTE HAPUS REVERSAL KEDAP EROR SCHEMA DATABASE (APP.PY)
# ==============================================================================
@app.route('/transaksi/penyesuaian-stok/hapus/<int:id_koreksi>', methods=['POST'])
def hapus_penyesuaian_stok(id_koreksi):
    log = db.session.get(PenyesuaianStok, id_koreksi)
    if not log:
        flash("Data log historis adjustment tidak ditemukan!", "danger")
        return redirect(url_for('monitoring_kartu_stok'))
        
    try:
        id_bahan = log.id_bahan
        qty_murni = float(log.jumlah_input or 0.0)
        jenis_saklar = log.jenis_saklar
        
        # SAKLAR BALIK LOGISTIK: Kembalikan saldo fisik ke master BahanBaku
        master_bhn = db.session.get(BahanBaku, id_bahan)
        if master_bhn and qty_murni > 0:
            if jenis_saklar == 'MASUK':
                # Jika dulu barang masuk (+), maka saat dibatalkan stok dikurangi (-)
                master_bhn.stok_akhir = round(master_bhn.stok_akhir - qty_murni, 2)
            else:
                # Jika dulu barang keluar (-), maka saat dibatalkan stok ditambah (+)
                master_bhn.stok_akhir = round(master_bhn.stok_akhir + qty_murni, 2)
                
        db.session.delete(log)
        db.session.commit()
        flash("Sukses Reversal! Log adjustment berhasil dihapus dan neraca gudang telah dikalibrasi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Gagal membatalkan transaksi adjustment. Eror: {str(e)}", "danger")
        
    return redirect(url_for('monitoring_kartu_stok'))

# ==============================================================================

# ==============================================================================
# MODUL BARU: KARTU STOK BARANG JADI - TANPA UBAH ALUR LAMA (APP.PY)
# ==============================================================================

# ==============================================================================
# MODUL BARU: KARTU STOK BARANG JADI PER PANJANG - LIS=4M+REQUEST, PLAFON=3,4,5,6+REQUEST
# ==============================================================================

# =============================================================================
# MODUL BARU: KARTU STOK BARANG JADI PER PANJANG - FIX TOTAL (ANTI NGUMPUL 4M)
# LIS=4M+REQUEST, PLAFON=3,4,5,6+REQUEST - SALDO DARI barang_jadi_saldo_panjang
# =============================================================================
@app.route('/monitoring/kartu-stok-barang-jadi')
def monitoring_kartu_stok_barang_jadi():
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            tbl = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='penyesuaian_barang_jadi'")).fetchone()
            if tbl:
                res = conn.execute(text("PRAGMA table_info(penyesuaian_barang_jadi)"))
                cols = [row[1] for row in res]
                if 'panjang_produk' not in cols:
                    conn.execute(text("ALTER TABLE penyesuaian_barang_jadi ADD COLUMN panjang_produk FLOAT DEFAULT 4.0"))
                    conn.commit()
                if 'jumlah_efektif' not in cols:
                    conn.execute(text("ALTER TABLE penyesuaian_barang_jadi ADD COLUMN jumlah_efektif FLOAT DEFAULT 0.0"))
                    conn.commit()
    except Exception as e:
        print(f"Auto migrate warning: {e}")

    tgl_dari_raw = request.args.get('tgl_dari', datetime.now().strftime('%Y-%m-01'))
    tgl_sampai_raw = request.args.get('tgl_sampai', datetime.now().strftime('%Y-%m-%d'))
    filter_panjang_raw = request.args.get('panjang', 'ALL')

    daftar_mutasi_kartu = []
    riwayat_koreksi_list = []
    try:
        tgl_dari = datetime.strptime(tgl_dari_raw, '%Y-%m-%d').date()
        tgl_sampai = datetime.strptime(tgl_sampai_raw, '%Y-%m-%d').date()
        semua_barang = BarangJadi.query.order_by(BarangJadi.id_barang_jadi.asc()).all()

        def parse_len(prod):
            try:
                if prod.keterangan and "LEN:" in prod.keterangan:
                    # Ambil angka setelah LEN:
                    part = prod.keterangan.split("LEN:")[-1].strip().split()[0]
                    return float(part)
            except:
                pass
            return 4.0

        def get_std_panjang(barang):
            kat = (barang.kategori or "").upper()
            nama = (barang.nama_barang or "").upper()
            if "LIS" in kat or "LIS" in nama:
                return [4.0]
            else:
                return [3.0, 4.0, 5.0, 6.0]

        def build_saldo_map(barang):
            """Ambil saldo per panjang dari tabel barang_jadi_saldo_panjang"""
            mp = {}
            try:
                for sp in (barang.saldo_per_panjang or []):
                    k = str(sp.panjang).strip().upper()
                    v = float(sp.saldo_awal or 0)
                    # normalisasi 3.0 -> 3 , 4.0 -> 4
                    try:
                        fv = float(k)
                        if fv.is_integer():
                            k = str(int(fv))
                        else:
                            # keep float as is, e.g. 2.5
                            k = str(fv).rstrip('0').rstrip('.') if '.' in str(fv) else str(fv)
                            # untuk pencocokan nanti kita simpan juga versi float string
                    except:
                        pass
                    # k bisa '3','4','5','6','REQUEST' atau custom seperti '2.5'
                    mp[k] = mp.get(k, 0) + v
            except Exception as e:
                print(f"saldo map error {barang.id_barang_jadi}: {e}")
            return mp

        def get_saldo_for_panjang(saldo_map, panjang_float):
            """Ambil saldo untuk panjang numeric tertentu"""
            # coba key integer
            try:
                if float(panjang_float).is_integer():
                    key_int = str(int(float(panjang_float)))
                    if key_int in saldo_map:
                        return saldo_map.get(key_int, 0.0)
                key_f = str(float(panjang_float))
                # normalisasi 3.0 -> 3 sudah, tapi cek juga 3.5 tetap 3.5
                # coba beberapa format
                if key_f in saldo_map:
                    return saldo_map[key_f]
                # coba tanpa trailing .0
                key_f2 = str(panjang_float).rstrip('0').rstrip('.') if '.' in str(panjang_float) else str(panjang_float)
                if key_f2 in saldo_map:
                    return saldo_map.get(key_f2, 0.0)
            except:
                pass
            return 0.0

        for b in semua_barang:
            all_prod = ProduksiHarian.query.filter_by(id_barang_jadi=b.id_barang_jadi).all()
            try:
                all_adj = PenyesuaianBarangJadi.query.filter_by(id_barang_jadi=b.id_barang_jadi).all()
            except Exception:
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    try:
                        conn.execute(text("ALTER TABLE penyesuaian_barang_jadi ADD COLUMN panjang_produk FLOAT DEFAULT 4.0"))
                        conn.commit()
                    except:
                        pass
                    try:
                        conn.execute(text("ALTER TABLE penyesuaian_barang_jadi ADD COLUMN jumlah_efektif FLOAT DEFAULT 0.0"))
                        conn.commit()
                    except:
                        pass
                all_adj = PenyesuaianBarangJadi.query.filter_by(id_barang_jadi=b.id_barang_jadi).all()

            saldo_map = build_saldo_map(b)
            std_panjang = get_std_panjang(b)

            # Kumpulkan panjang custom dari transaksi
            custom_panjang = set()
            for p in all_prod:
                pl = round(parse_len(p),2)
                if pl not in std_panjang:
                    custom_panjang.add(pl)
            for a in all_adj:
                try:
                    pl = round(float(getattr(a,'panjang_produk',4.0) or 4.0),2)
                except:
                    pl = 4.0
                if pl not in std_panjang:
                    custom_panjang.add(pl)

            panjang_set = set(std_panjang) | custom_panjang

            # === LOOP PER PANJANG STANDARD + CUSTOM NUMERIK ===
            for panjang in sorted(panjang_set):
                # filter
                if filter_panjang_raw != 'ALL':
                    if filter_panjang_raw == 'REQUEST':
                        if panjang in std_panjang:
                            continue
                    else:
                        try:
                            if float(filter_panjang_raw) != float(panjang):
                                continue
                        except:
                            pass

                # saldo awal master per panjang - FIX UTAMA: dari saldo_per_panjang, bukan b.saldo_awal
                if panjang in std_panjang:
                    saldo_master_alokasi = get_saldo_for_panjang(saldo_map, panjang)
                else:
                    # custom numeric: coba cari exact, kalau tidak ada = 0 (jangan ambil REQUEST)
                    saldo_master_alokasi = get_saldo_for_panjang(saldo_map, panjang)

                past_prod = 0.0
                for p in all_prod:
                    if p.tanggal < tgl_dari and round(parse_len(p),2) == round(panjang,2):
                        past_prod += float(p.jumlah_produk_jadi or 0)

                past_eff = 0.0
                for a in all_adj:
                    try:
                        a_panjang = float(getattr(a,'panjang_produk',4.0) or 4.0)
                    except:
                        a_panjang = 4.0
                    if a.tanggal < tgl_dari and round(a_panjang,2) == round(panjang,2):
                        past_eff += float(getattr(a,'jumlah_efektif',0) or 0)

                saldo_awal_dinamis = saldo_master_alokasi + past_prod + past_eff

                in_prod = 0.0
                for p in all_prod:
                    if tgl_dari <= p.tanggal <= tgl_sampai and round(parse_len(p),2) == round(panjang,2):
                        in_prod += float(p.jumlah_produk_jadi or 0)

                adj_periode = []
                for a in all_adj:
                    try:
                        a_panjang = float(getattr(a,'panjang_produk',4.0) or 4.0)
                    except:
                        a_panjang = 4.0
                    if tgl_dari <= a.tanggal <= tgl_sampai and round(a_panjang,2) == round(panjang,2):
                        adj_periode.append(a)

                in_retur = sum(float(a.jumlah_input) for a in adj_periode if a.kategori == 'RETUR' and a.jenis_saklar == 'MASUK')
                out_jual = sum(float(a.jumlah_input) for a in adj_periode if a.kategori == 'PENJUALAN')
                out_rusak = sum(float(a.jumlah_input) for a in adj_periode if a.kategori == 'RUSAK')
                koreksi_eff = sum(float(getattr(a,'jumlah_efektif',0) or 0) for a in adj_periode if a.kategori == 'KOREKSI')
                total_eff = sum(float(getattr(a,'jumlah_efektif',0) or 0) for a in adj_periode)

                stok_akhir = saldo_awal_dinamis + in_prod + total_eff

                daftar_mutasi_kartu.append({
                    'id_barang_jadi': b.id_barang_jadi,
                    'nama_barang': b.nama_barang,
                    'kategori': b.kategori,
                    'satuan': b.satuan if b.satuan else 'LBR',
                    'panjang': round(panjang,2),
                    'panjang_label': f"{int(panjang) if float(panjang).is_integer() else panjang}M" if panjang in std_panjang else f"{panjang}M (REQUEST)",
                    'is_request': panjang not in std_panjang,
                    'is_lis': "LIS" in (b.kategori or "").upper() or "LIS" in (b.nama_barang or "").upper(),
                    'saldo_awal': round(saldo_awal_dinamis,2),
                    'in_produksi': round(in_prod,2),
                    'in_retur': round(in_retur,2),
                    'out_jual': round(out_jual,2),
                    'out_rusak': round(out_rusak,2),
                    'koreksi': round(koreksi_eff,2),
                    'total_efektif': round(total_eff,2),
                    'stok_akhir': round(stok_akhir,2),
                    'stok_meter': round(stok_akhir * panjang,2),
                    'stok_real': b.stok_akhir
                })

            # === TAMBAHAN: BARIS KHUSUS REQUEST JIKA ADA SALDO REQUEST DI MASTER ===
            req_saldo_raw = saldo_map.get('REQUEST', 0)
            if req_saldo_raw > 0:
                # Hanya tampilkan jika filter mengizinkan
                if filter_panjang_raw in ('ALL', 'REQUEST'):
                    # Hitung mutasi untuk REQUEST: semua custom sebelum periode + periode
                    past_prod_req = 0.0
                    past_eff_req = 0.0
                    in_prod_req = 0.0
                    adj_req = []
                    for p in all_prod:
                        pl = round(parse_len(p),2)
                        if pl not in std_panjang:
                            if p.tanggal < tgl_dari:
                                past_prod_req += float(p.jumlah_produk_jadi or 0)
                            if tgl_dari <= p.tanggal <= tgl_sampai:
                                in_prod_req += float(p.jumlah_produk_jadi or 0)
                    for a in all_adj:
                        try:
                            ap = round(float(getattr(a,'panjang_produk',4.0) or 4.0),2)
                        except:
                            ap = 4.0
                        if ap not in std_panjang:
                            # untuk REQUEST row, kita TIDAK hitung yang sudah ada di custom_panjang agar tidak double
                            # tapi karena REQUEST adalah bucket terpisah, kita hitung hanya adj yang panjangnya tidak ada di custom? 
                            # Sederhananya: REQUEST row hanya untuk saldo REQUEST murni, tanpa produksi custom
                            # Jadi past dan in_prod_req = 0 untuk REQUEST murni
                            pass
                    # Untuk REQUEST murni, saldo awal = req_saldo + past yang benar-benar REQUEST (kita anggap 0)
                    # Ambil adj yang panjangnya tidak numeric? sebenarnya adj REQUEST tidak ada karena panjang_produk float
                    # Jadi REQUEST row = saldo REQUEST saja + koreksi yang panjangnya REQUEST (tidak ada)
                    # Kita buat simple: saldo_awal_req = req_saldo + past untuk custom yang belum teralokasi? 
                    # Agar tidak double, kita set past=0, in_prod=0
                    saldo_awal_req = req_saldo_raw
                    # Cari adj periode yang kategorinya terkait REQUEST dan panjang custom? kita kosongkan agar tidak double
                    # Tapi tetap hitung adj yang panjangnya di luar std dan belum ada di custom? sudah 0
                    total_eff_req = 0.0
                    # Jika ada adj dengan panjang 0 atau yang sengaja diinput sebagai REQUEST (misal 0), masukkan
                    for a in all_adj:
                        try:
                            ap = float(getattr(a,'panjang_produk',4.0) or 4.0)
                        except:
                            ap = 4.0
                        # Jika adj panjangnya = 0 (tidak valid) kita anggap REQUEST
                        if ap == 0:
                            if a.tanggal < tgl_dari:
                                past_eff_req += float(getattr(a,'jumlah_efektif',0) or 0)
                            if tgl_dari <= a.tanggal <= tgl_sampai:
                                adj_req.append(a)
                    saldo_awal_req += past_eff_req
                    in_retur_req = sum(float(a.jumlah_input) for a in adj_req if a.kategori == 'RETUR' and a.jenis_saklar == 'MASUK')
                    out_jual_req = sum(float(a.jumlah_input) for a in adj_req if a.kategori == 'PENJUALAN')
                    out_rusak_req = sum(float(a.jumlah_input) for a in adj_req if a.kategori == 'RUSAK')
                    koreksi_req = sum(float(getattr(a,'jumlah_efektif',0) or 0) for a in adj_req if a.kategori == 'KOREKSI')
                    total_eff_req = sum(float(getattr(a,'jumlah_efektif',0) or 0) for a in adj_req)
                    stok_akhir_req = saldo_awal_req + total_eff_req

                    # Cek apakah sudah ada baris REQUEST custom yang sama (hindari duplikat)
                    already_exists = any(r['id_barang_jadi']==b.id_barang_jadi and r.get('is_request') and r.get('panjang_label','').startswith('REQUEST') and r['panjang']==0 for r in daftar_mutasi_kartu)
                    if not already_exists:
                        daftar_mutasi_kartu.append({
                            'id_barang_jadi': b.id_barang_jadi,
                            'nama_barang': b.nama_barang,
                            'kategori': b.kategori,
                            'satuan': b.satuan if b.satuan else 'LBR',
                            'panjang': 0,
                            'panjang_label': "REQUEST",
                            'is_request': True,
                            'is_lis': "LIS" in (b.kategori or "").upper() or "LIS" in (b.nama_barang or "").upper(),
                            'saldo_awal': round(saldo_awal_req,2),
                            'in_produksi': round(in_prod_req,2),
                            'in_retur': round(in_retur_req,2),
                            'out_jual': round(out_jual_req,2),
                            'out_rusak': round(out_rusak_req,2),
                            'koreksi': round(koreksi_req,2),
                            'total_efektif': round(total_eff_req,2),
                            'stok_akhir': round(stok_akhir_req,2),
                            'stok_meter': 0,
                            'stok_real': b.stok_akhir
                        })

        daftar_mutasi_kartu.sort(key=lambda x: (x['id_barang_jadi'], x['panjang']))

        try:
            riwayat_koreksi_list = PenyesuaianBarangJadi.query.filter(
                PenyesuaianBarangJadi.tanggal >= tgl_dari,
                PenyesuaianBarangJadi.tanggal <= tgl_sampai
            ).order_by(PenyesuaianBarangJadi.tanggal.desc(), PenyesuaianBarangJadi.id_penyesuaian.desc()).all()
        except Exception as e:
            riwayat_koreksi_list = []
            flash(f"Info: {str(e)}", "warning")

        if filter_panjang_raw != 'ALL':
            if filter_panjang_raw == 'REQUEST':
                filtered = []
                for r in riwayat_koreksi_list:
                    try:
                        pl = round(float(getattr(r,'panjang_produk',4.0) or 4.0),2)
                    except:
                        pl = 4.0
                    try:
                        b_master = next((x for x in semua_barang if x.id_barang_jadi == r.id_barang_jadi), None)
                        std = [4.0] if b_master and ("LIS" in (b_master.kategori or "").upper() or "LIS" in (b_master.nama_barang or "").upper()) else [3.0,4.0,5.0,6.0]
                        if pl not in std:
                            filtered.append(r)
                    except:
                        if pl not in [3.0,4.0,5.0,6.0]:
                            filtered.append(r)
                # juga tampilkan log dengan panjang 0 = REQUEST
                for r in riwayat_koreksi_list:
                    try:
                        if float(getattr(r,'panjang_produk',4.0) or 4.0) == 0:
                            if r not in filtered:
                                filtered.append(r)
                    except:
                        pass
                riwayat_koreksi_list = filtered
            else:
                try:
                    fp = float(filter_panjang_raw)
                    riwayat_koreksi_list = [r for r in riwayat_koreksi_list if round(float(getattr(r,'panjang_produk',4.0) or 4.0),2) == round(fp,2)]
                except:
                    pass

        # === FILTER FINAL: REQUEST 0 HILANG, STANDAR TETAP TAMPIL ===
        kartu_list_tampil = []
        for r in daftar_mutasi_kartu:
            if r.get('is_request'):
                # untuk REQUEST label murni (panjang 0) tetap tampilkan jika saldo >0
                if r.get('panjang') == 0:
                    if r.get('saldo_awal',0) == 0 and r.get('stok_akhir',0) == 0:
                        continue
                else:
                    total_mutasi = r.get('in_produksi',0) + r.get('in_retur',0) + r.get('out_jual',0) + r.get('out_rusak',0) + abs(r.get('koreksi',0))
                    if r.get('saldo_awal',0) == 0 and total_mutasi == 0 and r.get('stok_akhir',0) == 0:
                        continue
            kartu_list_tampil.append(r)
        daftar_mutasi_kartu = kartu_list_tampil

    except Exception as e:
        db.session.rollback()
        flash(f"Gagal kalkulasi: {str(e)}", "danger")
        import traceback; traceback.print_exc()

    try:
        return render_template(
            'monitoring/kartu_stok_barang_jadi.html',
            kartu_list=daftar_mutasi_kartu,
            log_koreksi_list=riwayat_koreksi_list,
            barang_list=BarangJadi.query.order_by(BarangJadi.id_barang_jadi.asc()).all(),
            tgl_dari_val=tgl_dari_raw,
            tgl_sampai_val=tgl_sampai_raw,
            panjang_filter_val=filter_panjang_raw
        )
    except Exception:
        try:
            return render_template(
                'kartu_stok_barang_jadi.html',
                kartu_list=daftar_mutasi_kartu,
                log_koreksi_list=riwayat_koreksi_list,
                barang_list=BarangJadi.query.order_by(BarangJadi.id_barang_jadi.asc()).all(),
                tgl_dari_val=tgl_dari_raw,
                tgl_sampai_val=tgl_sampai_raw,
                panjang_filter_val=filter_panjang_raw
            )
        except Exception as e:
            return f"Template kartu_stok_barang_jadi tidak ditemukan: {e} - Data: {len(daftar_mutasi_kartu)} baris", 500


@app.route('/monitoring/log-barang-jadi')
def monitoring_log_barang_jadi():
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            tbl = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='penyesuaian_barang_jadi'")).fetchone()
            if tbl:
                res = conn.execute(text("PRAGMA table_info(penyesuaian_barang_jadi)"))
                cols = [row[1] for row in res]
                if 'panjang_produk' not in cols:
                    conn.execute(text("ALTER TABLE penyesuaian_barang_jadi ADD COLUMN panjang_produk FLOAT DEFAULT 4.0"))
                    conn.commit()
                if 'jumlah_efektif' not in cols:
                    conn.execute(text("ALTER TABLE penyesuaian_barang_jadi ADD COLUMN jumlah_efektif FLOAT DEFAULT 0.0"))
                    conn.commit()
    except Exception as e:
        print(f"Auto migrate log warning: {e}")
    tgl_dari_raw = request.args.get('tgl_dari', datetime.now().strftime('%Y-%m-01'))
    tgl_sampai_raw = request.args.get('tgl_sampai', datetime.now().strftime('%Y-%m-%d'))
    filter_panjang_raw = request.args.get('panjang', 'ALL')
    riwayat_koreksi_list = []
    try:
        tgl_dari = datetime.strptime(tgl_dari_raw, '%Y-%m-%d').date()
        tgl_sampai = datetime.strptime(tgl_sampai_raw, '%Y-%m-%d').date()
        riwayat_koreksi_list = PenyesuaianBarangJadi.query.filter(PenyesuaianBarangJadi.tanggal >= tgl_dari, PenyesuaianBarangJadi.tanggal <= tgl_sampai).order_by(PenyesuaianBarangJadi.tanggal.desc(), PenyesuaianBarangJadi.id_penyesuaian.desc()).all()
        if filter_panjang_raw != 'ALL':
            if filter_panjang_raw == 'REQUEST':
                filtered = []
                for r in riwayat_koreksi_list:
                    try:
                        pl = round(float(getattr(r,'panjang_produk',4.0) or 4.0),2)
                    except:
                        pl = 4.0
                    try:
                        b_master = BarangJadi.query.filter_by(id_barang_jadi=r.id_barang_jadi).first()
                        std = [4.0] if b_master and ("LIS" in (b_master.kategori or "").upper() or "LIS" in (b_master.nama_barang or "").upper()) else [3.0,4.0,5.0,6.0]
                        if pl not in std:
                            filtered.append(r)
                    except:
                        if pl not in [3.0,4.0,5.0,6.0]:
                            filtered.append(r)
                riwayat_koreksi_list = filtered
            else:
                try:
                    fp = float(filter_panjang_raw)
                    riwayat_koreksi_list = [r for r in riwayat_koreksi_list if round(float(getattr(r,'panjang_produk',4.0) or 4.0),2) == round(fp,2)]
                except:
                    pass
    except Exception as e:
        db.session.rollback()
        riwayat_koreksi_list = []
    try:
        return render_template('monitoring/log_barang_jadi.html', log_koreksi_list=riwayat_koreksi_list, barang_list=BarangJadi.query.order_by(BarangJadi.id_barang_jadi.asc()).all(), tgl_dari_val=tgl_dari_raw, tgl_sampai_val=tgl_sampai_raw, panjang_filter_val=filter_panjang_raw)
    except Exception:
        return render_template('log_barang_jadi.html', log_koreksi_list=riwayat_koreksi_list, barang_list=BarangJadi.query.order_by(BarangJadi.id_barang_jadi.asc()).all(), tgl_dari_val=tgl_dari_raw, tgl_sampai_val=tgl_sampai_raw, panjang_filter_val=filter_panjang_raw)


@app.route('/transaksi/penyesuaian-barang-jadi/simpan', methods=['POST'])
def simpan_penyesuaian_barang_jadi():
    try:
        id_edit = request.form.get('id_penyesuaian_edit', '').strip()
        tanggal_raw = request.form.get('tanggal_transaksi')
        kategori = request.form.get('kategori_cases', request.form.get('kategori_kasus', '')).upper().strip()
        jenis_saklar = request.form.get('jenis_saklar', 'KELUAR').upper().strip()
        id_barang_jadi = request.form.get('id_barang_jadi', '').strip()
        qty_murni = float(request.form.get('jumlah_volume', 0))
        panjang_raw = request.form.get('panjang_produk', '4').strip()
        try:
            panjang_produk = float(panjang_raw)
        except:
            panjang_produk = 4.0
        alasan = request.form.get('alasan_koreksi', '').upper().strip() or "ADJUSTMENT BARANG JADI"
        tanggal_fiskal = datetime.strptime(tanggal_raw, '%Y-%m-%d').date()
        qty_efektif = qty_murni if jenis_saklar == 'MASUK' else -abs(qty_murni)
        if not id_edit:
            mutasi_baru = PenyesuaianBarangJadi(
                tanggal=tanggal_fiskal,
                kategori=kategori,
                jenis_saklar=jenis_saklar,
                id_barang_jadi=id_barang_jadi,
                panjang_produk=panjang_produk,
                jumlah_input=qty_murni,
                jumlah_efektif=qty_efektif,
                alasan_keterangan=alasan
            )
            db.session.add(mutasi_baru)
            master = db.session.get(BarangJadi, id_barang_jadi)
            if master:
                if jenis_saklar == 'MASUK':
                    master.stok_akhir = int(master.stok_akhir + qty_murni)
                else:
                    master.stok_akhir = int(master.stok_akhir - qty_murni)
        else:
            log_lama = db.session.get(PenyesuaianBarangJadi, int(id_edit))
            if not log_lama:
                flash("Data adjustment tidak ditemukan!", "danger")
                return redirect(url_for('monitoring_kartu_stok_barang_jadi'))
            old_qty = float(log_lama.jumlah_input or 0)
            old_saklar = log_lama.jenis_saklar
            master_old = db.session.get(BarangJadi, log_lama.id_barang_jadi)
            if master_old and old_qty > 0:
                if old_saklar == 'MASUK':
                    master_old.stok_akhir = int(master_old.stok_akhir - old_qty)
                else:
                    master_old.stok_akhir = int(master_old.stok_akhir + old_qty)
            log_lama.tanggal = tanggal_fiskal
            log_lama.kategori = kategori
            log_lama.jenis_saklar = jenis_saklar
            log_lama.id_barang_jadi = id_barang_jadi
            log_lama.panjang_produk = panjang_produk
            log_lama.jumlah_input = qty_murni
            log_lama.jumlah_efektif = qty_efektif
            log_lama.alasan_keterangan = alasan
            master_new = db.session.get(BarangJadi, id_barang_jadi)
            if master_new:
                if jenis_saklar == 'MASUK':
                    master_new.stok_akhir = int(master_new.stok_akhir + qty_murni)
                else:
                    master_new.stok_akhir = int(master_new.stok_akhir - qty_murni)
        db.session.commit()
        flash(f"Sukses! {kategori} {panjang_produk}M berhasil.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal simpan: {str(e)}", "danger")
    return redirect(url_for('monitoring_kartu_stok_barang_jadi'))

@app.route('/transaksi/penyesuaian-barang-jadi/hapus/<int:id_koreksi>', methods=['POST'])
def hapus_penyesuaian_barang_jadi(id_koreksi):
    log = db.session.get(PenyesuaianBarangJadi, id_koreksi)
    if not log:
        flash("Log tidak ditemukan!", "danger")
        return redirect(url_for('monitoring_kartu_stok_barang_jadi'))
    try:
        qty = float(log.jumlah_input or 0)
        saklar = log.jenis_saklar
        master = db.session.get(BarangJadi, log.id_barang_jadi)
        if master and qty > 0:
            if saklar == 'MASUK':
                master.stok_akhir = int(master.stok_akhir - qty)
            else:
                master.stok_akhir = int(master.stok_akhir + qty)
        db.session.delete(log)
        db.session.commit()
        flash("Log dihapus & stok dikalibrasi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal hapus: {str(e)}", "danger")
    return redirect(url_for('monitoring_kartu_stok_barang_jadi'))


@app.route('/api/get-kartu-barang-jadi/<string:id_barang>')
def api_get_kartu_barang_jadi(id_barang):
    tgl_dari_raw = request.args.get('tgl_dari', datetime.now().strftime('%Y-%m-01'))
    tgl_sampai_raw = request.args.get('tgl_sampai', datetime.now().strftime('%Y-%m-%d'))
    panjang_filter = request.args.get('panjang', 'ALL')
    try:
        tgl_dari = datetime.strptime(tgl_dari_raw, '%Y-%m-%d').date()
        tgl_sampai = datetime.strptime(tgl_sampai_raw, '%Y-%m-%d').date()
        master = db.session.get(BarangJadi, id_barang)
        if not master:
            return jsonify({'error': 'Barang jadi tidak ditemukan'}), 404

        # Build saldo map dari barang_jadi_saldo_panjang - FIX
        saldo_map = {}
        for sp in (master.saldo_per_panjang or []):
            k = str(sp.panjang).strip().upper()
            try:
                fv = float(k)
                if fv.is_integer():
                    k = str(int(fv))
            except:
                pass
            saldo_map[k] = saldo_map.get(k,0) + float(sp.saldo_awal or 0)

        def parse_len(prod):
            try:
                if prod.keterangan and "LEN:" in prod.keterangan:
                    part = prod.keterangan.split("LEN:")[-1].strip().split()[0]
                    return float(part)
            except:
                pass
            return 4.0

        def match_panjang(p_len):
            if panjang_filter == 'ALL':
                return True
            if panjang_filter == 'REQUEST':
                kat = (master.kategori or "").upper()
                nama = (master.nama_barang or "").upper()
                std = [4.0] if "LIS" in kat or "LIS" in nama else [3.0,4.0,5.0,6.0]
                return round(p_len,2) not in std
            try:
                return round(p_len,2) == round(float(panjang_filter),2)
            except:
                # jika filter REQUEST label (panjang 0)
                if str(panjang_filter).upper() == 'REQUEST' and p_len == 0:
                    return True
                return True

        def get_saldo_awal_for_filter():
            if panjang_filter == 'ALL':
                # sum semua saldo per panjang
                total = 0.0
                for k,v in saldo_map.items():
                    if k == 'REQUEST':
                        total += v
                    else:
                        try:
                            float(k)
                            total += v
                        except:
                            pass
                return total
            elif panjang_filter == 'REQUEST':
                # saldo REQUEST + saldo custom numeric yang ada di map tapi bukan std?
                # Untuk detail popup REQUEST, kita tampilkan saldo REQUEST saja + semua custom
                total = saldo_map.get('REQUEST',0)
                # tambah saldo custom yang tidak termasuk std (jika ada key 2.5 dll)
                kat = (master.kategori or "").upper()
                nama = (master.nama_barang or "").upper()
                std = [4.0] if "LIS" in kat or "LIS" in nama else [3.0,4.0,5.0,6.0]
                for k,v in saldo_map.items():
                    if k == 'REQUEST':
                        continue
                    try:
                        fv = float(k)
                        if round(fv,2) not in std:
                            total += v
                    except:
                        pass
                return total
            else:
                try:
                    fp = float(panjang_filter)
                    key = str(int(fp)) if fp.is_integer() else str(fp)
                    if key in saldo_map:
                        return saldo_map.get(key,0)
                    # coba key float
                    return saldo_map.get(str(fp),0)
                except:
                    return 0.0

        all_prod_before = ProduksiHarian.query.filter(
            ProduksiHarian.id_barang_jadi == id_barang,
            ProduksiHarian.tanggal < tgl_dari
        ).all()
        past_prod_filtered = sum(float(p.jumlah_produk_jadi or 0) for p in all_prod_before if match_panjang(parse_len(p)))
        all_adj_before = PenyesuaianBarangJadi.query.filter(
            PenyesuaianBarangJadi.id_barang_jadi == id_barang,
            PenyesuaianBarangJadi.tanggal < tgl_dari
        ).all()
        past_eff_filtered = sum(float(getattr(a,'jumlah_efektif',0) or 0) for a in all_adj_before if match_panjang(float(getattr(a,'panjang_produk',4.0) or 4.0)))

        saldo_master = get_saldo_awal_for_filter()
        saldo_awal = saldo_master + past_prod_filtered + past_eff_filtered

        prod_list = ProduksiHarian.query.filter(
            ProduksiHarian.id_barang_jadi == id_barang,
            ProduksiHarian.tanggal >= tgl_dari,
            ProduksiHarian.tanggal <= tgl_sampai
        ).order_by(ProduksiHarian.tanggal.asc()).all()
        prod_list = [p for p in prod_list if match_panjang(parse_len(p))]
        adj_list = PenyesuaianBarangJadi.query.filter(
            PenyesuaianBarangJadi.id_barang_jadi == id_barang,
            PenyesuaianBarangJadi.tanggal >= tgl_dari,
            PenyesuaianBarangJadi.tanggal <= tgl_sampai
        ).order_by(PenyesuaianBarangJadi.tanggal.asc()).all()
        adj_list = [a for a in adj_list if match_panjang(float(getattr(a,'panjang_produk',4.0) or 4.0))]
        timeline = []
        for p in prod_list:
            timeline.append({
                'tanggal': p.tanggal,
                'tipe': 'PRODUKSI',
                'panjang': parse_len(p),
                'keterangan': f"{p.shift} | {p.keterangan or ''}",
                'masuk': float(p.jumlah_produk_jadi or 0),
                'keluar': 0.0
            })
        for a in adj_list:
            timeline.append({
                'tanggal': a.tanggal,
                'tipe': a.kategori,
                'panjang': float(getattr(a,'panjang_produk',4.0) or 4.0),
                'keterangan': a.alasan_keterangan or '',
                'masuk': float(a.jumlah_input) if a.jenis_saklar == 'MASUK' else 0.0,
                'keluar': float(a.jumlah_input) if a.jenis_saklar == 'KELUAR' else 0.0,
                'efektif': float(getattr(a,'jumlah_efektif',0) or 0)
            })
        timeline = sorted(timeline, key=lambda x: x['tanggal'])
        mutasi = []
        running = saldo_awal
        for t in timeline:
            if 'efektif' in t:
                running += float(t['efektif'])
            else:
                running += float(t['masuk'])
            t['saldo'] = round(running, 2)
            t['tanggal_str'] = t['tanggal'].strftime('%d-%m-%Y')
            mutasi.append(t)
        return jsonify({
            'id_barang': master.id_barang_jadi,
            'nama': master.nama_barang,
            'panjang_filter': panjang_filter,
            'saldo_awal': round(saldo_awal,2),
            'stok_akhir_periode': round(running,2),
            'stok_real': master.stok_akhir,
            'mutasi': mutasi
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================================================
# MODUL BARU: TRANSAKSI PESANAN BARANG JADI OLEH PELANGGAN
# ==================================================

# ==================================================
# HELPER PESANAN PER PANJANG (LIS 4+REQ, PLAFON 3,4,5,6+REQ)
# ==================================================
def _build_saldo_map_barang(barang):
    mp = {}
    try:
        for sp in (barang.saldo_per_panjang or []):
            k = str(sp.panjang).strip().upper()
            v = float(sp.saldo_awal or 0)
            try:
                fv = float(k)
                if fv.is_integer():
                    k = str(int(fv))
            except:
                pass
            mp[k] = mp.get(k, 0) + v
    except Exception as e:
        print(f"saldo map error {getattr(barang,'id_barang_jadi','?')}: {e}")
    return mp

def _get_std_panjang_for_barang(barang):
    kat = (barang.kategori or "").upper()
    nama = (barang.nama_barang or "").upper()
    if "LIS" in kat or "LIS" in nama:
        return [4.0]
    else:
        return [3.0, 4.0, 5.0, 6.0]

def _parse_len_produksi(prod):
    try:
        if prod.keterangan and "LEN:" in prod.keterangan:
            part = prod.keterangan.split("LEN:")[-1].strip().split()[0]
            return float(part)
    except:
        pass
    return 4.0

def hitung_stok_per_panjang(barang):
    saldo_map = _build_saldo_map_barang(barang)
    std = _get_std_panjang_for_barang(barang)
    all_prod = ProduksiHarian.query.filter_by(id_barang_jadi=barang.id_barang_jadi).all()
    try:
        all_adj = PenyesuaianBarangJadi.query.filter_by(id_barang_jadi=barang.id_barang_jadi).all()
    except:
        all_adj = []
    custom = set()
    for p in all_prod:
        pl = round(_parse_len_produksi(p),2)
        if pl not in std:
            custom.add(pl)
    for a in all_adj:
        try:
            pl = round(float(getattr(a,'panjang_produk',4.0) or 4.0),2)
        except:
            pl = 4.0
        if pl not in std and pl != 0:
            custom.add(pl)
    result = {}
    for panjang in std:
        key = str(int(panjang)) if float(panjang).is_integer() else str(panjang)
        saldo_awal = saldo_map.get(key, 0)
        prod_sum = sum(float(p.jumlah_produk_jadi or 0) for p in all_prod if round(_parse_len_produksi(p),2) == round(panjang,2))
        eff_sum = sum(float(getattr(a,'jumlah_efektif',0) or 0) for a in all_adj if round(float(getattr(a,'panjang_produk',4.0) or 4.0),2) == round(panjang,2))
        result[key] = round(saldo_awal + prod_sum + eff_sum,2)
    for panjang in sorted(custom):
        key = str(panjang)
        key_int = str(int(panjang)) if float(panjang).is_integer() else key
        saldo_awal = saldo_map.get(key, saldo_map.get(key_int, 0))
        prod_sum = sum(float(p.jumlah_produk_jadi or 0) for p in all_prod if round(_parse_len_produksi(p),2) == round(panjang,2))
        eff_sum = sum(float(getattr(a,'jumlah_efektif',0) or 0) for a in all_adj if round(float(getattr(a,'panjang_produk',4.0) or 4.0),2) == round(panjang,2))
        result[str(panjang)] = round(saldo_awal + prod_sum + eff_sum,2)
    req = saldo_map.get('REQUEST',0)
    if req>0:
        result['REQUEST'] = round(req,2)
    result['_total'] = round(sum(v for k,v in result.items() if k!='_total'),2)
    result['_saldo_map'] = saldo_map
    result['_std'] = std
    return result

@app.route('/api/get-stok-barang-jadi-per-panjang/<string:id_barang>')
def api_get_stok_per_panjang(id_barang):
    try:
        barang = db.session.get(BarangJadi, id_barang)
        if not barang:
            return jsonify({'error':'Barang tidak ditemukan'}),404
        stok_dict = hitung_stok_per_panjang(barang)
        options = []
        for p in stok_dict.get('_std', []):
            key = str(int(p)) if float(p).is_integer() else str(p)
            stok = stok_dict.get(key, 0)
            options.append({'panjang': p, 'key': key, 'label': f"{key}M", 'stok': stok, 'is_request': False})
        for k,v in stok_dict.items():
            if k in ('_total','_saldo_map','_std','REQUEST'):
                continue
            try:
                fv = float(k)
                if fv not in stok_dict.get('_std', []):
                    options.append({'panjang': fv, 'key': k, 'label': f"{k}M (REQUEST)", 'stok': v, 'is_request': True})
            except:
                pass
        if 'REQUEST' in stok_dict:
            options.append({'panjang': 0, 'key': 'REQUEST', 'label': 'REQUEST CUSTOM', 'stok': stok_dict.get('REQUEST',0), 'is_request': True})
        return jsonify({
            'id_barang_jadi': barang.id_barang_jadi,
            'nama_barang': barang.nama_barang,
            'kategori': barang.kategori,
            'total_stok': barang.stok_akhir,
            'per_panjang': stok_dict,
            'options': options
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}),500



@app.route('/transaksi/pesanan-barang-jadi', methods=['GET'])
def transaksi_pesanan_barang_jadi():
    semua_pesanan = PesananBarangJadi.query.order_by(PesananBarangJadi.tanggal_pesan.desc()).all()
    semua_pelanggan = Pelanggan.query.order_by(Pelanggan.nama_pelanggan.asc()).all()
    semua_barang = BarangJadi.query.order_by(BarangJadi.nama_barang.asc()).all()
    tanggal_hari_ini = date.today().isoformat()
    last = PesananBarangJadi.query.order_by(PesananBarangJadi.id_pesanan.desc()).first()
    next_no = 1
    if last:
        try:
            next_no = int(last.no_pesanan.split('-')[-1]) + 1
        except:
            next_no = last.id_pesanan + 1
    preview_no = f"PO-{datetime.now().strftime('%Y%m')}-{next_no:04d}"
    barang_stok_map = {}
    for b in semua_barang:
        try:
            sd = hitung_stok_per_panjang(b)
            barang_stok_map[b.id_barang_jadi] = sd
        except Exception as e:
            barang_stok_map[b.id_barang_jadi] = {'_total': b.stok_akhir, '_std': _get_std_panjang_for_barang(b), '_saldo_map': {}}
    return render_template('pesanan_barang_jadi.html',
                           pesanan_list=semua_pesanan,
                           pelanggan_list=semua_pelanggan,
                           barang_list=semua_barang,
                           barang_stok_map=barang_stok_map,
                           tanggal_hari_ini=tanggal_hari_ini,
                           preview_no=preview_no)


@app.route('/transaksi/pesanan-barang-jadi/tambah', methods=['POST'])
def tambah_pesanan_barang_jadi():
    try:
        tanggal_raw = request.form.get('tanggal_pesan')
        tgl_kirim_raw = request.form.get('tanggal_kirim_rencana')
        id_pelanggan = request.form.get('id_pelanggan')
        keterangan = request.form.get('keterangan','').upper().strip()
        status = request.form.get('status','DRAFT').upper()

        if not tanggal_raw or not id_pelanggan:
            flash("Tanggal dan Pelanggan wajib diisi!", "warning")
            return redirect(url_for('transaksi_pesanan_barang_jadi'))

        tanggal_pesan = datetime.strptime(tanggal_raw, '%Y-%m-%d').date()
        tgl_kirim = None
        if tgl_kirim_raw:
            tgl_kirim = datetime.strptime(tgl_kirim_raw, '%Y-%m-%d').date()

        # Generate No Pesanan otomatis
        last = PesananBarangJadi.query.order_by(PesananBarangJadi.id_pesanan.desc()).first()
        next_no = 1
        if last:
            try:
                next_no = int(last.no_pesanan.split('-')[-1]) + 1
            except:
                next_no = last.id_pesanan + 1
        no_pesanan = f"PO-{datetime.now().strftime('%Y%m')}-{next_no:04d}"

        pesanan = PesananBarangJadi(
            no_pesanan=no_pesanan,
            tanggal_pesan=tanggal_pesan,
            tanggal_kirim_rencana=tgl_kirim,
            id_pelanggan=id_pelanggan,
            status=status,
            keterangan=keterangan
        )
        db.session.add(pesanan)
        db.session.flush()  # dapat id_pesanan

        # Ambil items dinamis
        ids_barang = request.form.getlist('id_barang_jadi[]')
        panjangs = request.form.getlist('panjang[]')
        jumlahs = request.form.getlist('jumlah[]')
        ket_items = request.form.getlist('keterangan_item[]')

        total_item = 0
        for i in range(len(ids_barang)):
            id_bj = ids_barang[i].strip()
            if not id_bj:
                continue
            try:
                pj = float(panjangs[i]) if i < len(panjangs) and panjangs[i] else 4.0
            except:
                pj = 4.0
            try:
                jml = float(jumlahs[i]) if i < len(jumlahs) and jumlahs[i] else 0
            except:
                jml = 0
            if jml <= 0:
                continue
            ket = ket_items[i].upper().strip() if i < len(ket_items) else ""
            detail = PesananBarangJadiDetail(
                id_pesanan=pesanan.id_pesanan,
                id_barang_jadi=id_bj,
                panjang_produk=pj,
                jumlah_pesan=jml,
                keterangan_item=ket
            )
            db.session.add(detail)
            total_item += 1

        if total_item == 0:
            db.session.rollback()
            flash("Minimal 1 item barang jadi harus diisi!", "warning")
            return redirect(url_for('transaksi_pesanan_barang_jadi'))

        pesanan.total_item = total_item
        db.session.commit()
        flash(f"Pesanan {no_pesanan} berhasil disimpan ({total_item} item).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal simpan pesanan: {str(e)}", "danger")
    return redirect(url_for('transaksi_pesanan_barang_jadi'))

@app.route('/transaksi/pesanan-barang-jadi/detail/<int:id_pesanan>')
def detail_pesanan_barang_jadi(id_pesanan):
    pesanan = db.session.get(PesananBarangJadi, id_pesanan)
    if not pesanan:
        flash("Pesanan tidak ditemukan!", "danger")
        return redirect(url_for('transaksi_pesanan_barang_jadi'))
    stok_per_item = {}
    for det in pesanan.items_pesanan:
        try:
            barang = db.session.get(BarangJadi, det.id_barang_jadi)
            if barang:
                sd = hitung_stok_per_panjang(barang)
                key = str(int(det.panjang_produk)) if float(det.panjang_produk).is_integer() else str(det.panjang_produk)
                stok_panjang = sd.get(key, sd.get(str(det.panjang_produk), 0))
                if key == '99' or str(det.panjang_produk) == '99':
                    stok_panjang = sd.get('REQUEST', 0)
                stok_per_item[det.id_detail] = {'stok_panjang': stok_panjang, 'map': sd}
            else:
                stok_per_item[det.id_detail] = {'stok_panjang': 0, 'map': {}}
        except Exception as e:
            stok_per_item[det.id_detail] = {'stok_panjang': 0, 'map': {}}
    return render_template('pesanan_detail.html', pesanan=pesanan, stok_per_item=stok_per_item)


@app.route('/transaksi/pesanan-barang-jadi/hapus/<int:id_pesanan>', methods=['POST'])
def hapus_pesanan_barang_jadi(id_pesanan):
    pesanan = db.session.get(PesananBarangJadi, id_pesanan)
    if not pesanan:
        flash("Pesanan tidak ditemukan!", "danger")
        return redirect(url_for('transaksi_pesanan_barang_jadi'))
    try:
        # Jika status sudah DIKIRIM/SELESAI, kembalikan stok
        if pesanan.status in ['DIKIRIM','SELESAI']:
            for det in pesanan.items_pesanan:
                master = db.session.get(BarangJadi, det.id_barang_jadi)
                if master:
                    master.stok_akhir = float(master.stok_akhir or 0) + float(det.jumlah_pesan or 0)
        db.session.delete(pesanan)
        db.session.commit()
        flash(f"Pesanan {pesanan.no_pesanan} berhasil dihapus.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal hapus: {str(e)}", "danger")
    return redirect(url_for('transaksi_pesanan_barang_jadi'))

@app.route('/transaksi/pesanan-barang-jadi/update-status/<int:id_pesanan>', methods=['POST'])
def update_status_pesanan(id_pesanan):
    pesanan = db.session.get(PesananBarangJadi, id_pesanan)
    if not pesanan:
        flash("Pesanan tidak ditemukan!", "danger")
        return redirect(url_for('transaksi_pesanan_barang_jadi'))
    new_status = request.form.get('status','').upper().strip()
    if new_status not in ['DRAFT','DIPROSES','SIAP KIRIM','DIKIRIM','SELESAI','BATAL']:
        flash("Status tidak valid!", "warning")
        return redirect(url_for('detail_pesanan_barang_jadi', id_pesanan=id_pesanan))

    try:
        old_status = pesanan.status
        # CEK: jika PO sudah punya SJ TERKIRIM, jangan potong stok lagi via status PO (hindari double)
        # Stok sekarang dipotong via SJ, bukan via PO
        has_sj_terkirim = False
        try:
            has_sj_terkirim = any(k.status_kirim == 'TERKIRIM' for k in (pesanan.daftar_pengiriman or []))
        except Exception:
            has_sj_terkirim = False

        will_deduct_statuses = ['DIKIRIM','SELESAI']
        was_deducted = old_status in will_deduct_statuses
        will_be_deducted = new_status in will_deduct_statuses

        # Jika sudah ada SJ TERKIRIM, skip potong stok via PO
        if has_sj_terkirim:
            # hanya update status tanpa utak-atik stok
            pesanan.status = new_status
            db.session.commit()
            flash(f"Status pesanan {pesanan.no_pesanan} diubah menjadi {new_status} (stok sudah via SJ, tidak double).", "success")
            return redirect(url_for('detail_pesanan_barang_jadi', id_pesanan=id_pesanan))

        if not was_deducted and will_be_deducted:
            # cek stok cukup
            for det in pesanan.items_pesanan:
                master = db.session.get(BarangJadi, det.id_barang_jadi)
                if not master:
                    continue
                if float(master.stok_akhir or 0) < float(det.jumlah_pesan or 0):
                    flash(f"Stok {master.nama_barang} tidak cukup! Sisa {master.stok_akhir}, butuh {det.jumlah_pesan}", "danger")
                    return redirect(url_for('detail_pesanan_barang_jadi', id_pesanan=id_pesanan))
            # potong stok
            for det in pesanan.items_pesanan:
                master = db.session.get(BarangJadi, det.id_barang_jadi)
                if master:
                    master.stok_akhir = float(master.stok_akhir or 0) - float(det.jumlah_pesan or 0)
                    # Buat log penyesuaian keluar otomatis
                    log = PenyesuaianBarangJadi(
                        tanggal=date.today(),
                        kategori='PESANAN',
                        jenis_saklar='KELUAR',
                        id_barang_jadi=det.id_barang_jadi,
                        panjang_produk=float(det.panjang_produk or 4.0),
                        jumlah_input=float(det.jumlah_pesan or 0),
                        jumlah_efektif= -float(det.jumlah_pesan or 0),
                        alasan_keterangan=f"PESANAN {pesanan.no_pesanan} - {pesanan.pelanggan.nama_pelanggan if pesanan.pelanggan else ''}"
                    )
                    db.session.add(log)

        elif was_deducted and not will_be_deducted and new_status in ['BATAL','DRAFT','DIPROSES']:
            # kembalikan stok
            for det in pesanan.items_pesanan:
                master = db.session.get(BarangJadi, det.id_barang_jadi)
                if master:
                    master.stok_akhir = float(master.stok_akhir or 0) + float(det.jumlah_pesan or 0)
                    log = PenyesuaianBarangJadi(
                        tanggal=date.today(),
                        kategori='BATAL PESAN',
                        jenis_saklar='MASUK',
                        id_barang_jadi=det.id_barang_jadi,
                        panjang_produk=float(det.panjang_produk or 4.0),
                        jumlah_input=float(det.jumlah_pesan or 0),
                        jumlah_efektif= float(det.jumlah_pesan or 0),
                        alasan_keterangan=f"RETUR BATAL {pesanan.no_pesanan}"
                    )
                    db.session.add(log)

        pesanan.status = new_status
        db.session.commit()
        flash(f"Status pesanan {pesanan.no_pesanan} diubah menjadi {new_status}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal update status: {str(e)}", "danger")
    return redirect(url_for('detail_pesanan_barang_jadi', id_pesanan=id_pesanan))
@app.route('/transaksi/pengiriman', methods=['GET'])
@app.route('/transaksi/pengiriman-pelanggan', methods=['GET'])
def transaksi_pengiriman():
    try:
        # Ambil semua pesanan yang masih ada sisa (belum lunas kirim) - support partial
        all_pesanan = PesananBarangJadi.query.filter(PesananBarangJadi.status.in_(['DRAFT','DIPROSES', 'SIAP KIRIM', 'DIKIRIM'])).order_by(PesananBarangJadi.tanggal_pesan.desc()).all()
        pesanan_sisa_list = []
        for p in all_pesanan:
            sisa_total = sum(max(0.0, float(d.jumlah_pesan or 0) - float(d.jumlah_terkirim or 0)) for d in p.items_pesanan)
            if sisa_total > 0.001:
                pesanan_sisa_list.append(p)
        # Jika tidak ada yang sisa tapi masih ada DIPROSES/SIAP KIRIM, tampilkan juga
        if not pesanan_sisa_list:
            pesanan_sisa_list = PesananBarangJadi.query.filter(PesananBarangJadi.status.in_(['DIPROSES', 'SIAP KIRIM'])).all()
    except Exception:
        pesanan_sisa_list = PesananBarangJadi.query.filter(PesananBarangJadi.status.in_(['DIPROSES', 'SIAP KIRIM'])).all()
    
    try:
        pengiriman_list = PengirimanPelanggan.query.order_by(PengirimanPelanggan.tanggal_kirim.desc(), PengirimanPelanggan.id_pengiriman.desc()).all()
    except Exception:
        pengiriman_list = []
    
    tanggal_hari_ini = date.today().isoformat()
    # Generate preview No SJ auto increment per bulan
    try:
        prefix = f"SJ-{datetime.now().strftime('%Y%m')}-"
        last = PengirimanPelanggan.query.filter(PengirimanPelanggan.no_pengiriman.like(f"{prefix}%")).order_by(PengirimanPelanggan.no_pengiriman.desc()).first()
        next_no = 1
        if last:
            try:
                next_no = int(last.no_pengiriman.split('-')[-1]) + 1
            except:
                next_no = last.id_pengiriman + 1
        preview_no = f"{prefix}{next_no:04d}"
    except Exception:
        preview_no = f"SJ-{datetime.now().strftime('%Y%m')}-0001"
    
    # Support dua lokasi template (root dan subfolder)
    try:
        return render_template('buat_surat_jalan.html',
                               pesanan_sisa_list=pesanan_sisa_list,
                               pengiriman_list=pengiriman_list,
                               tanggal_hari_ini=tanggal_hari_ini,
                               preview_no=preview_no)
    except Exception:
        return render_template('pengiriman/buat_surat_jalan.html',
                               pesanan_sisa_list=pesanan_sisa_list,
                               pengiriman_list=pengiriman_list,
                               tanggal_hari_ini=tanggal_hari_ini,
                               preview_no=preview_no)

@app.route('/api/get-pesanan-detail-lengkap/<int:id_pesanan>', methods=['GET'])
def api_get_pesanan_detail(id_pesanan):
    pesanan = db.session.get(PesananBarangJadi, id_pesanan)
    if not pesanan:
        return jsonify({'error': 'Pesanan tidak ditemukan'}), 404
        
    items_data = []
    for det in pesanan.items_pesanan:
        sisa = float(det.jumlah_pesan or 0) - float(det.jumlah_terkirim or 0)
        items_data.append({
            'id_detail_pesanan': det.id_detail,
            'id_barang_jadi': det.id_barang_jadi,
            'nama': det.barang_jadi.nama_barang if det.barang_jadi else "Produk",
            'panjang': det.panjang_produk,
            'ket': det.keterangan_item or "",
            'jumlah_pesan': det.jumlah_pesan,
            'jumlah_terkirim': det.jumlah_terkirim,
            'sisa': sisa if sisa > 0 else 0
        })
    
    riwayat = []
    try:
        for k in pesanan.daftar_pengiriman:
            riwayat.append({
                'no_sj': k.no_pengiriman,
                'tgl': k.tanggal_kirim.strftime('%d-%m-%Y') if k.tanggal_kirim else '-',
                'status': k.status_kirim
            })
    except Exception:
        riwayat = []
        
    return jsonify({
        'nama_pelanggan': pesanan.pelanggan.nama_pelanggan if pesanan.pelanggan else "Umum",
        'kode_pelanggan': pesanan.pelanggan.kode_singkat if pesanan.pelanggan else "",
        'id_pelanggan': pesanan.id_pelanggan,
        'alamat': pesanan.pelanggan.alamat if pesanan.pelanggan else "",
        'status_pesanan': pesanan.status,
        'riwayat_kirim': riwayat,
        'items': items_data
    })

@app.route('/transaksi/pengiriman/tambah', methods=['POST'])
@app.route('/transaksi/pengiriman-pelanggan/tambah', methods=['POST'])
def tambah_pengiriman_pelanggan():
    try:
        id_pesanan = request.form.get('id_pesanan')
        no_sj_input = request.form.get('no_sj','').strip().upper()
        tanggal_raw = request.form.get('tanggal') or request.form.get('tanggal_kirim')
        alamat_kirim = request.form.get('alamat_kirim','').upper().strip()
        sopir = request.form.get('sopir','').upper().strip()
        no_polisi = request.form.get('no_polisi','').upper().strip()
        ekspedisi = request.form.get('ekspedisi','').upper().strip()
        keterangan = request.form.get('keterangan','').upper().strip()

        id_detail_list = request.form.getlist('id_detail_pesanan[]') or request.form.getlist('id_detail_pesanan')
        jumlah_kirim_list = request.form.getlist('jumlah_kirim[]') or request.form.getlist('jumlah_kirim')

        pesanan = db.session.get(PesananBarangJadi, int(id_pesanan) if str(id_pesanan).isdigit() else 0)
        if not pesanan:
            try:
                pesanan = db.session.get(PesananBarangJadi, int(id_pesanan))
            except:
                pesanan = None
        if not pesanan:
            flash("Pesanan tidak ditemukan!", "danger")
            return redirect(url_for('transaksi_pengiriman'))

        # Validasi tanggal
        try:
            tgl_kirim = datetime.strptime(tanggal_raw, '%Y-%m-%d').date() if tanggal_raw else date.today()
        except:
            tgl_kirim = date.today()

        # Generate No SJ jika kosong
        if not no_sj_input:
            prefix = f"SJ-{datetime.now().strftime('%Y%m')}-"
            last = PengirimanPelanggan.query.filter(PengirimanPelanggan.no_pengiriman.like(f"{prefix}%")).order_by(PengirimanPelanggan.no_pengiriman.desc()).first()
            next_no = 1
            if last:
                try:
                    next_no = int(last.no_pengiriman.split('-')[-1]) + 1
                except:
                    next_no = last.id_pengiriman + 1
            no_sj_input = f"{prefix}{next_no:04d}"
        else:
            # Cek duplikat
            if PengirimanPelanggan.query.filter_by(no_pengiriman=no_sj_input).first():
                prefix = f"SJ-{datetime.now().strftime('%Y%m')}-"
                last = PengirimanPelanggan.query.filter(PengirimanPelanggan.no_pengiriman.like(f"{prefix}%")).order_by(PengirimanPelanggan.no_pengiriman.desc()).first()
                next_no = (last.id_pengiriman + 1) if last else 1
                if last:
                    try:
                        next_no = int(last.no_pengiriman.split('-')[-1]) + 1
                    except:
                        pass
                no_sj_input = f"{prefix}{next_no:04d}"

        # Hitung total qty
        total_qty = 0.0
        pairs = []
        for i in range(len(id_detail_list)):
            try:
                id_det = int(id_detail_list[i])
                qty = float(jumlah_kirim_list[i]) if i < len(jumlah_kirim_list) and jumlah_kirim_list[i] != '' else 0.0
            except:
                continue
            if qty <= 0:
                continue
            det = db.session.get(PesananBarangJadiDetail, id_det)
            if not det or det.id_pesanan != pesanan.id_pesanan:
                continue
            sisa = float(det.jumlah_pesan or 0) - float(det.jumlah_terkirim or 0)
            if qty > sisa + 0.001:
                flash(f"Qty kirim melebihi sisa! {det.id_barang_jadi} sisa {sisa}, diminta {qty}", "danger")
                return redirect(url_for('transaksi_pengiriman'))
            # Cek stok per panjang
            try:
                barang = db.session.get(BarangJadi, det.id_barang_jadi)
                if barang:
                    sd = hitung_stok_per_panjang(barang)
                    key = str(int(det.panjang_produk)) if float(det.panjang_produk).is_integer() else str(det.panjang_produk)
                    if key == '99':
                        key = 'REQUEST'
                    stok_panjang = sd.get(key, sd.get(str(det.panjang_produk), 0))
                    # Jika stok panjang 0, coba total (untuk REQUEST custom)
                    if stok_panjang < qty and float(det.panjang_produk) not in [3.0,4.0,5.0,6.0]:
                        # untuk custom, cek total atau REQUEST
                        stok_panjang = sd.get('REQUEST', 0) + sd.get(str(det.panjang_produk), 0)
                        # Jika masih kurang, cek stok global sebagai fallback
                        if stok_panjang < qty:
                            stok_panjang = float(barang.stok_akhir or 0)
                    if stok_panjang + 0.001 < qty:
                        flash(f"Stok {barang.nama_barang} panjang {det.panjang_produk}M tidak cukup! Stok: {stok_panjang}, butuh: {qty}", "danger")
                        return redirect(url_for('transaksi_pengiriman'))
            except Exception as e:
                print(f"stok check error: {e}")
            pairs.append((det, qty))
            total_qty += qty

        if not pairs:
            flash("Tidak ada item yang dikirim! Isi Qty Kirim minimal 1.", "warning")
            return redirect(url_for('transaksi_pengiriman'))

        # Buat header pengiriman - status langsung TERKIRIM (potong stok)
        kirim = PengirimanPelanggan(
            no_pengiriman=no_sj_input,
            tanggal_kirim=tgl_kirim,
            id_pesanan=pesanan.id_pesanan,
            id_pelanggan=pesanan.id_pelanggan,
            alamat_kirim=alamat_kirim or (pesanan.pelanggan.alamat if pesanan.pelanggan else ''),
            sopir=sopir,
            no_polisi=no_polisi,
            ekspedisi=ekspedisi,
            keterangan=keterangan,
            status_kirim='TERKIRIM',
            total_qty=total_qty
        )
        db.session.add(kirim)
        db.session.flush()

        # Buat detail + potong stok per panjang + update jumlah_terkirim
        for det, qty in pairs:
            det_kirim = PengirimanPelangganDetail(
                id_pengiriman=kirim.id_pengiriman,
                id_detail_pesanan=det.id_detail,
                id_barang_jadi=det.id_barang_jadi,
                panjang_produk=det.panjang_produk,
                jumlah_kirim=qty,
                keterangan_item=det.keterangan_item
            )
            db.session.add(det_kirim)

            # Update jumlah_terkirim di pesanan detail
            det.jumlah_terkirim = float(det.jumlah_terkirim or 0) + qty

            # Potong stok master
            master = db.session.get(BarangJadi, det.id_barang_jadi)
            if master:
                master.stok_akhir = float(master.stok_akhir or 0) - qty
                if master.stok_akhir < 0:
                    master.stok_akhir = 0

                # Potong saldo per panjang
                try:
                    key_cari = str(int(det.panjang_produk)) if float(det.panjang_produk).is_integer() else str(det.panjang_produk)
                    if key_cari == '99':
                        key_cari = 'REQUEST'
                    sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det.id_barang_jadi, panjang=key_cari).first()
                    if not sp and key_cari != 'REQUEST':
                        # coba cari dengan format float
                        sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det.id_barang_jadi, panjang=str(det.panjang_produk)).first()
                    if not sp and float(det.panjang_produk) not in [3.0,4.0,5.0,6.0]:
                        # custom panjang -> potong REQUEST jika ada, atau potong dari panjang custom itu sendiri
                        sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det.id_barang_jadi, panjang='REQUEST').first()
                        if not sp:
                            sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det.id_barang_jadi, panjang=str(det.panjang_produk)).first()
                    if sp:
                        sp.saldo_awal = float(sp.saldo_awal or 0) - qty
                        if sp.saldo_awal < 0:
                            sp.saldo_awal = 0
                except Exception as e:
                    print(f"saldo per panjang deduct error: {e}")

                # Log penyesuaian
                try:
                    log = PenyesuaianBarangJadi(
                        tanggal=tgl_kirim,
                        kategori='PENJUALAN',
                        jenis_saklar='KELUAR',
                        id_barang_jadi=det.id_barang_jadi,
                        panjang_produk=float(det.panjang_produk or 4.0),
                        jumlah_input=qty,
                        jumlah_efektif=-qty,
                        alasan_keterangan=f"SJ {no_sj_input} - PO {pesanan.no_pesanan} - {pesanan.pelanggan.nama_pelanggan if pesanan.pelanggan else ''}"
                    )
                    db.session.add(log)
                except Exception as e:
                    print(f"log error: {e}")

        # Update status PO otomatis
        sisa_total = sum(max(0.0, float(d.jumlah_pesan or 0) - float(d.jumlah_terkirim or 0)) for d in pesanan.items_pesanan)
        if sisa_total <= 0.001:
            pesanan.status = 'DIKIRIM'
        else:
            # Jika masih ada sisa, tetap SIAP KIRIM / DIPROSES
            if pesanan.status in ['DRAFT']:
                pesanan.status = 'DIPROSES'

        db.session.commit()
        flash(f"Surat Jalan {no_sj_input} berhasil dibuat untuk {pesanan.no_pesanan} - Total {total_qty} LBR - Status PO: {pesanan.status}", "success")
        return redirect(url_for('transaksi_pengiriman'))
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        flash(f"Gagal buat SJ: {str(e)}", "danger")
        return redirect(url_for('transaksi_pengiriman'))

@app.route('/transaksi/pengiriman/detail/<int:id_pengiriman>')
@app.route('/transaksi/pengiriman-pelanggan/detail/<int:id_pengiriman>')
def detail_pengiriman_pelanggan(id_pengiriman):
    kirim = db.session.get(PengirimanPelanggan, id_pengiriman)
    if not kirim:
        flash("Surat Jalan tidak ditemukan!", "danger")
        return redirect(url_for('transaksi_pengiriman'))
    try:
        return render_template('detail_surat_jalan.html', kirim=kirim)
    except Exception:
        # fallback jika template di subfolder
        return render_template('pengiriman/detail_surat_jalan.html', kirim=kirim)

@app.route('/transaksi/pengiriman/update-status/<int:id_pengiriman>', methods=['POST'])
@app.route('/transaksi/pengiriman-pelanggan/update-status/<int:id_pengiriman>', methods=['POST'])
def update_status_pengiriman(id_pengiriman):
    kirim = db.session.get(PengirimanPelanggan, id_pengiriman)
    if not kirim:
        flash("SJ tidak ditemukan!", "danger")
        return redirect(url_for('transaksi_pengiriman'))
    new_status = request.form.get('status_kirim','').upper().strip()
    if new_status not in ['DRAFT','DALAM PERJALANAN','TERKIRIM','BATAL']:
        flash("Status tidak valid!", "warning")
        return redirect(url_for('detail_pengiriman_pelanggan', id_pengiriman=id_pengiriman))
    try:
        old_status = kirim.status_kirim
        if old_status == new_status:
            flash(f"Status sudah {new_status}", "warning")
            return redirect(url_for('detail_pengiriman_pelanggan', id_pengiriman=id_pengiriman))

        # TERKIRIM -> BATAL : kembalikan stok + kurangi jumlah_terkirim
        if old_status == 'TERKIRIM' and new_status == 'BATAL':
            for det_kirim in kirim.items_kirim:
                master = db.session.get(BarangJadi, det_kirim.id_barang_jadi)
                if master:
                    master.stok_akhir = float(master.stok_akhir or 0) + float(det_kirim.jumlah_kirim or 0)
                    # kembalikan saldo per panjang
                    try:
                        key_cari = str(int(det_kirim.panjang_produk)) if float(det_kirim.panjang_produk).is_integer() else str(det_kirim.panjang_produk)
                        if key_cari == '99':
                            key_cari = 'REQUEST'
                        sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det_kirim.id_barang_jadi, panjang=key_cari).first()
                        if not sp:
                            sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det_kirim.id_barang_jadi, panjang=str(det_kirim.panjang_produk)).first()
                        if sp:
                            sp.saldo_awal = float(sp.saldo_awal or 0) + float(det_kirim.jumlah_kirim or 0)
                    except Exception as e:
                        print(f"return per panjang error: {e}")
                    # log masuk
                    try:
                        log = PenyesuaianBarangJadi(
                            tanggal=date.today(),
                            kategori='RETUR BATAL SJ',
                            jenis_saklar='MASUK',
                            id_barang_jadi=det_kirim.id_barang_jadi,
                            panjang_produk=float(det_kirim.panjang_produk or 4.0),
                            jumlah_input=float(det_kirim.jumlah_kirim or 0),
                            jumlah_efektif=float(det_kirim.jumlah_kirim or 0),
                            alasan_keterangan=f"BATAL SJ {kirim.no_pengiriman} - PO {kirim.pesanan.no_pesanan if kirim.pesanan else ''}"
                        )
                        db.session.add(log)
                    except Exception as e:
                        print(f"log batal error: {e}")
                # kurangi jumlah_terkirim di PO detail
                if det_kirim.id_detail_pesanan:
                    det_po = db.session.get(PesananBarangJadiDetail, det_kirim.id_detail_pesanan)
                    if det_po:
                        det_po.jumlah_terkirim = max(0.0, float(det_po.jumlah_terkirim or 0) - float(det_kirim.jumlah_kirim or 0))
            # update status PO jadi SIAP KIRIM lagi jika ada sisa
            if kirim.pesanan:
                sisa = sum(max(0.0, float(d.jumlah_pesan or 0) - float(d.jumlah_terkirim or 0)) for d in kirim.pesanan.items_pesanan)
                if sisa > 0.001:
                    kirim.pesanan.status = 'SIAP KIRIM'
                else:
                    kirim.pesanan.status = 'DIKIRIM'

        # BATAL/DRAFT -> TERKIRIM : potong stok lagi + tambah jumlah_terkirim
        elif old_status in ['BATAL','DRAFT','DALAM PERJALANAN'] and new_status == 'TERKIRIM':
            for det_kirim in kirim.items_kirim:
                master = db.session.get(BarangJadi, det_kirim.id_barang_jadi)
                if master:
                    if float(master.stok_akhir or 0) < float(det_kirim.jumlah_kirim or 0) - 0.001:
                        flash(f"Stok {master.nama_barang} tidak cukup untuk TERKIRIM kembali!", "danger")
                        return redirect(url_for('detail_pengiriman_pelanggan', id_pengiriman=id_pengiriman))
                    master.stok_akhir = float(master.stok_akhir or 0) - float(det_kirim.jumlah_kirim or 0)
                    try:
                        key_cari = str(int(det_kirim.panjang_produk)) if float(det_kirim.panjang_produk).is_integer() else str(det_kirim.panjang_produk)
                        if key_cari == '99':
                            key_cari = 'REQUEST'
                        sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det_kirim.id_barang_jadi, panjang=key_cari).first()
                        if not sp:
                            sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det_kirim.id_barang_jadi, panjang=str(det_kirim.panjang_produk)).first()
                        if sp:
                            sp.saldo_awal = float(sp.saldo_awal or 0) - float(det_kirim.jumlah_kirim or 0)
                            if sp.saldo_awal < 0:
                                sp.saldo_awal = 0
                    except Exception as e:
                        print(f"deduct per panjang error: {e}")
                    try:
                        log = PenyesuaianBarangJadi(
                            tanggal=date.today(),
                            kategori='PENJUALAN',
                            jenis_saklar='KELUAR',
                            id_barang_jadi=det_kirim.id_barang_jadi,
                            panjang_produk=float(det_kirim.panjang_produk or 4.0),
                            jumlah_input=float(det_kirim.jumlah_kirim or 0),
                            jumlah_efektif=-float(det_kirim.jumlah_kirim or 0),
                            alasan_keterangan=f"TERKIRIM ULANG SJ {kirim.no_pengiriman}"
                        )
                        db.session.add(log)
                    except Exception as e:
                        print(f"log terkirim ulang error: {e}")
                if det_kirim.id_detail_pesanan:
                    det_po = db.session.get(PesananBarangJadiDetail, det_kirim.id_detail_pesanan)
                    if det_po:
                        det_po.jumlah_terkirim = float(det_po.jumlah_terkirim or 0) + float(det_kirim.jumlah_kirim or 0)
            if kirim.pesanan:
                sisa = sum(max(0.0, float(d.jumlah_pesan or 0) - float(d.jumlah_terkirim or 0)) for d in kirim.pesanan.items_pesanan)
                if sisa <= 0.001:
                    kirim.pesanan.status = 'DIKIRIM'

        kirim.status_kirim = new_status
        db.session.commit()
        flash(f"Status SJ {kirim.no_pengiriman} diubah menjadi {new_status}", "success")
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        flash(f"Gagal update status: {str(e)}", "danger")
    return redirect(url_for('detail_pengiriman_pelanggan', id_pengiriman=id_pengiriman))

@app.route('/transaksi/pengiriman/hapus/<int:id_pengiriman>', methods=['POST'])
@app.route('/transaksi/pengiriman-pelanggan/hapus/<int:id_pengiriman>', methods=['POST'])
def hapus_pengiriman_pelanggan(id_pengiriman):
    kirim = db.session.get(PengirimanPelanggan, id_pengiriman)
    if not kirim:
        flash("SJ tidak ditemukan!", "danger")
        return redirect(url_for('transaksi_pengiriman'))
    try:
        # Jika TERKIRIM, kembalikan stok dulu
        if kirim.status_kirim == 'TERKIRIM':
            for det_kirim in kirim.items_kirim:
                master = db.session.get(BarangJadi, det_kirim.id_barang_jadi)
                if master:
                    master.stok_akhir = float(master.stok_akhir or 0) + float(det_kirim.jumlah_kirim or 0)
                    try:
                        key_cari = str(int(det_kirim.panjang_produk)) if float(det_kirim.panjang_produk).is_integer() else str(det_kirim.panjang_produk)
                        if key_cari == '99':
                            key_cari = 'REQUEST'
                        sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det_kirim.id_barang_jadi, panjang=key_cari).first()
                        if not sp:
                            sp = BarangJadiSaldoPanjang.query.filter_by(id_barang_jadi=det_kirim.id_barang_jadi, panjang=str(det_kirim.panjang_produk)).first()
                        if sp:
                            sp.saldo_awal = float(sp.saldo_awal or 0) + float(det_kirim.jumlah_kirim or 0)
                    except Exception as e:
                        print(f"return hapus error: {e}")
                if det_kirim.id_detail_pesanan:
                    det_po = db.session.get(PesananBarangJadiDetail, det_kirim.id_detail_pesanan)
                    if det_po:
                        det_po.jumlah_terkirim = max(0.0, float(det_po.jumlah_terkirim or 0) - float(det_kirim.jumlah_kirim or 0))
            if kirim.pesanan:
                sisa = sum(max(0.0, float(d.jumlah_pesan or 0) - float(d.jumlah_terkirim or 0)) for d in kirim.pesanan.items_pesanan)
                if sisa > 0.001:
                    kirim.pesanan.status = 'SIAP KIRIM'
        db.session.delete(kirim)
        db.session.commit()
        flash(f"SJ {kirim.no_pengiriman} berhasil dihapus & stok dikembalikan", "success")
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        flash(f"Gagal hapus SJ: {str(e)}", "danger")
    return redirect(url_for('transaksi_pengiriman'))


@app.route('/api/get-barang-jadi-info/<string:id_barang>')
def api_get_barang_jadi_info(id_barang):
    bj = db.session.get(BarangJadi, id_barang)
    if not bj:
        return jsonify({'error':'not found'}),404
    return jsonify({
        'id_barang_jadi': bj.id_barang_jadi,
        'nama_barang': bj.nama_barang,
        'kategori': bj.kategori,
        'stok_akhir': bj.stok_akhir,
        'satuan': bj.satuan
    })

# GERBANG HULU RUNNER: JANTUNG UTAMA PENGENDALI SERVER INTERNAL WINDOWS
# ==============================================================================
import os

if __name__ == '__main__':
    # Membuka konteks aplikasi untuk membuat database jika belum ada
    with app.app_context():
        db.create_all()           
    
    # Membaca port dinamis dari server internet secara otomatis, 
    # jika tidak ada (seperti di laptop Anda), akan kembali menggunakan port 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Jalankan aplikasi dengan konfigurasi aman untuk server internet
    app.run(host='0.0.0.0', port=port, debug=False)


