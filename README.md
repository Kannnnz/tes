Document Summarizer - README
Overview
Document Summarizer adalah aplikasi web untuk menganalisis dan bertanya jawab tentang dokumen penelitian/paper dan informasi terkait Universitas Negeri Semarang (UNNES). Aplikasi ini menggunakan model AI lokal melalui LM Studio, sehingga tidak memerlukan biaya API eksternal.
Fitur Utama
* Unggah hingga 5 dokumen sekaligus (PDF, DOCX, TXT)
* Tanya jawab tentang isi dokumen
* Pertanyaan yang telah disediakan atau custom question
* Fokus pada paper/penelitian dan Universitas Negeri Semarang
* Manajemen riwayat chat
* Sistem manajemen pengguna dengan autentikasi
Teknologi yang Digunakan
* **Backend**: Python dengan FastAPI
* **Database**: SQLite
* **Model AI**: mistral-nemo-instruct-2407 di LM Studio
* **Ekstraksi Dokumen**: PyPDF2, python-docx
* **Autentikasi**: JWT (JSON Web Tokens)
Cara Kerja
1. User mendaftar dan login untuk mendapatkan token akses
2. User mengunggah dokumen penelitian atau paper
3. User dapat memilih pertanyaan dari daftar yang disediakan atau mengetik pertanyaan sendiri
4. Sistem memeriksa relevansi pertanyaan dengan paper atau UNNES
5. Jika relevan, sistem mengekstrak teks dari dokumen dan mengirimkannya ke model AI
6. Model AI memberikan jawaban berdasarkan konten dokumen dan/atau pengetahuan tentang UNNES
7. Jawaban dan riwayat interaksi disimpan untuk referensi di masa mendatang
Persyaratan Sistem
* Python 3.8+
* LM Studio dengan model mistral-nemo-instruct-2407
* Min 8GB RAM (direkomendasikan 16GB)
* Ruang disk min 10GB (untuk model dan dokumen)
Struktur Project

```
document-summarizer/
├── app.py                   # Main application file
├── setup.py                 # Database and environment setup
├── text_extractor.py        # Utility for text extraction testing
├── test_lm_studio.py        # LM Studio API testing tool
├── database.db              # SQLite database
├── uploads/                 # Directory for uploaded documents
└── requirements.txt         # Python dependencies
```

Panduan Instalasi
1. Pastikan Python 3.8+ terinstall
2. Clone repository ini
3. Install LM Studio dari https://lmstudio.ai/
4. Download model mistral-nemo-instruct-2407
5. Install dependensi Python:

```
pip install -r requirements.txt
```

6. Jalankan setup script:

```
python setup.py
```

7. Jalankan aplikasi:

```
python app.py
```

Penggunaan API
Registrasi Pengguna

```
POST /register
Content-Type: application/json

{
  "username": "user1",
  "password": "password123"
}
```

Login

```
POST /token
Content-Type: application/x-www-form-urlencoded

username=user1&password=password123
```

Unggah Dokumen

```
POST /upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

files=@document1.pdf&files=@document2.docx
```

Kirim Pesan Chat

```
POST /chat
Authorization: Bearer {token}
Content-Type: application/json

{
  "message": "Apa metode penelitian yang digunakan dalam paper?",
  "document_ids": ["doc_id_1", "doc_id_2"]
}
```

Pengembangan Backend
Untuk mengembangkan backend, Anda dapat:
1. Menambahkan endpoint API baru di `app.py`
2. Memodifikasi skema database di `setup.py`
3. Menambahkan fungsi ekstraksi teks baru di `text_extractor.py`
4. Mengoptimalkan prompt engineering di `test_lm_studio.py`
Integrasi dengan Frontend
Frontend dapat terhubung ke backend melalui API endpoints yang tersedia. Tim frontend perlu mengimplementasikan:
1. Halaman login dan registrasi
2. Interface upload dokumen
3. Chat UI dengan pilihan pertanyaan predefined
4. Tampilan riwayat chat
5. Manajemen sesi dan token autentikasi
Troubleshooting
Masalah Koneksi LM Studio
1. Pastikan LM Studio berjalan
2. Verifikasi model mistral-nemo-instruct-2407 dimuat
3. Periksa alamat API lokal (http://127.0.0.1:1234)
Masalah Ekstraksi Dokumen
1. Gunakan `text_extractor.py` untuk menguji ekstraksi teks
2. Periksa format dokumen yang didukung
3. Pastikan dokumen tidak terproteksi password
Lisensi
Proyek ini bersifat pribadi dan tidak untuk distribusi publik tanpa izin.
Kontributor
* Backend Developer: [Nama Anda]
* Frontend Developer: [Tim Frontend]
