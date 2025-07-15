📌 Project Title: Sistem Absensi kehadiran Berbasis Deteksi Wajah dan monitoring makan atau minum dengan Flask dan YOLO

📖 Deskripsi

Proyek ini merupakan sistem absensi otomatis dan monitoring makan atau minum berbasis web menggunakan **Flask** sebagai backend, dengan integrasi deteksi wajah dan makanan atau minuman berbasis YOLO (You Only Look Once). Sistem ini memungkinkan pencatatan kehadiran secara otomatis melalui kamera RTSP/Webcam, pengolahan data, dan pengunduhan laporan kehadiran dalam bentuk PDF serta monitoring deteksi makanan atau minuman dan lamakerja .



⚙️ Fitur Utama

👤 Deteksi wajah menggunakan YOLO
📷 Dukungan kamera RTSP & webcam
🗂️ Manajemen data admin, pengguna, absensi, monitoring dan lamakerja
🧾 Ekspor laporan kehadiran ke PDF
📁 Upload dan pengelolaan dataset wajah
🔒 Sistem login aman
📢 Peringatan suara dan integrasi dengan WhatsApp API 
🧠 Dukungan threading untuk performa deteksi real-time
🍽️ Pencatatan data pelanggaran makanan/minuman saat di area kerja 
⏱️ Pencatatan presensi secara otomatis berdasarkan waktu terdeteksi dan kamera role in dan out
⏱️ Pencatatan lama kerja secara otomatis berdasarkan waktu terdeteksi
📥 Impor data pegawai dari file Excel (.xlsx) untuk mempercepat input data pegawai secara massal


🧩 Library

* Python 3.11.5
* Flask
* SQLAlchemy
* Flask-Migrate
* Pandas
* OpenCV
* NumPy
* Ultralytics (YOLOv11)
* Pygame (sound)
* FPDF (PDF export)
* Requests (API WhatsApp)
* Werkzeug (auth & security)


🛠️ Instalasi

1. Clone repo:

bash
git clone https://github.com/anggayn/absensidanmonitoring.git
cd absensidanmonitoring


2. Buat virtual environment:

bash
python -m venv venv

Aktifkan:
venv\Scripts\activate         # Windows
source venv/bin/activate      # Linux/Mac


3. Install dependencies:

bash
pip install -r requirements.txt


Jika belum ada file `requirements.txt`, gunakan ini:

bash
pip install flask flask_sqlalchemy flask_migrate sqlalchemy werkzeug pandas pygame opencv-python numpy ultralytics requests fpdf


4. Set environment variabel (opsional):

bash
set FLASK_APP=app.py
set FLASK_ENV=development

5. WhatsApp API Integration (Ultramsg)
ULTRAMSG_INSTANCE_ID = 'instance109410'
ULTRAMSG_API_TOKEN = 'fe469dynm6jlqgaj'

6. Jalankan aplikasi:

bash
flask run atau python app.py

🗄️ Struktur Direktori 

├── migrations/
├── pages/
│   └── index.html
├── static/
│   ├── models/
│   ├── bukti/
│   ├── foto_dataset/
│   ├── images/
│   └── pelanggaran/
├── app.py
├── requirements.txt
└── README.md


💾 Database & Migrasi

bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade


