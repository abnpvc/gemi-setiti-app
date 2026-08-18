FIX SALDO PER PANJANG - ANTI NGUMPUL 4 METER
Penyebab: saldo_master_alokasi = b.saldo_awal if panjang==4 else 0
Solusi: baca dari barang_jadi_saldo_panjang per panjang 3M/4M/5M/6M/REQUEST

- app.py -> file utama
- pesanan_barang_jadi.html -> templates/pesanan_barang_jadi.html
- pesanan_detail.html -> templates/pesanan_detail.html
- kartu_stok_barang_jadi.html -> templates/monitoring/kartu_stok_barang_jadi.html

Cara: backup, replace, restart python app.py
API baru: /api/get-stok-barang-jadi-per-panjang/<id>
