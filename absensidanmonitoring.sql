-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 05 Sep 2025 pada 15.07
-- Versi server: 10.4.27-MariaDB
-- Versi PHP: 8.1.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `absensidanmonitoring`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `absensi_pegawai`
--

CREATE TABLE `absensi_pegawai` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) NOT NULL,
  `pegawai_id` int(11) NOT NULL,
  `tanggal` date NOT NULL,
  `presensi_datang` time NOT NULL,
  `presensi_pulang` time DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `jam_kerja` time NOT NULL,
  `jam_selesai_kerja` time NOT NULL,
  `jam_lembur` time DEFAULT NULL,
  `foto_datang` varchar(255) DEFAULT NULL,
  `foto_pulang` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `absensi_pegawai`
--

INSERT INTO `absensi_pegawai` (`id`, `admin_id`, `pegawai_id`, `tanggal`, `presensi_datang`, `presensi_pulang`, `status`, `jam_kerja`, `jam_selesai_kerja`, `jam_lembur`, `foto_datang`, `foto_pulang`) VALUES
(79, 2, 9, '2025-08-07', '15:03:15', NULL, 'Belumpulang', '08:47:00', '13:50:00', NULL, 'images/d26dfb4a-ed14-4aec-b60a-e4230188012b.jpg', NULL),
(85, 2, 2, '2025-08-08', '14:11:43', NULL, 'Belumpulang', '08:47:00', '13:50:00', NULL, 'images/1dbeedc0-b841-4b2a-9c91-97aed5b01030.jpg', NULL),
(90, 2, 9, '2025-08-08', '16:47:20', NULL, 'Belumpulang', '08:47:00', '13:50:00', NULL, 'images/16cfd089-35a5-49b6-b515-fa4604e50b71.jpg', NULL),
(91, 2, 9, '2025-08-15', '19:18:24', NULL, 'Belumpulang', '08:47:00', '13:50:00', NULL, 'images/76fe7159-38e1-4dd7-95bc-a1ab1415fdcd.jpg', NULL);

-- --------------------------------------------------------

--
-- Struktur dari tabel `admin`
--

CREATE TABLE `admin` (
  `id` int(11) NOT NULL,
  `id_instansi` int(11) NOT NULL,
  `nama_instansi` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `model_path` varchar(255) DEFAULT NULL,
  `model_makanminum` varchar(255) DEFAULT NULL,
  `role` varchar(20) NOT NULL,
  `photo` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `admin`
--

INSERT INTO `admin` (`id`, `id_instansi`, `nama_instansi`, `username`, `password`, `model_path`, `model_makanminum`, `role`, `photo`) VALUES
(2, 1, 'uns madiun', 'uns madiun', 'unsmadiun123', 'models/uns madiun_model.pt', 'models/uns madiun_makanminum_model.pt', 'admin', NULL);

-- --------------------------------------------------------

--
-- Struktur dari tabel `divisi`
--

CREATE TABLE `divisi` (
  `id` int(11) NOT NULL,
  `nama_divisi` varchar(50) NOT NULL,
  `admin_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `divisi`
--

INSERT INTO `divisi` (`id`, `nama_divisi`, `admin_id`) VALUES
(1, 'staff', 2),
(2, 'Dosen', 2),
(3, 'Office Boy', 2),
(4, 'Satpam', 2);

-- --------------------------------------------------------

--
-- Struktur dari tabel `konfigurasi_kamerapelacakankerja`
--

CREATE TABLE `konfigurasi_kamerapelacakankerja` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) NOT NULL,
  `nama_kamera` varchar(100) NOT NULL,
  `ip_rtsp` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `konfigurasi_kamerapelacakankerja`
--

INSERT INTO `konfigurasi_kamerapelacakankerja` (`id`, `admin_id`, `nama_kamera`, `ip_rtsp`) VALUES
(1, 2, 'lab mikro', 'rtsp://192.168.1.22:8080/h264_ulaw.sdp');

-- --------------------------------------------------------

--
-- Struktur dari tabel `konfigurasi_kamerapresensi`
--

CREATE TABLE `konfigurasi_kamerapresensi` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) NOT NULL,
  `nama_kamera` varchar(100) NOT NULL,
  `role_kamera` enum('IN','OUT') NOT NULL,
  `ip_rtsp` varchar(255) NOT NULL,
  `jam_mulai_kedatangan` time NOT NULL,
  `jam_berakhir_kedatangan` time NOT NULL,
  `jam_mulai_pulang` time NOT NULL,
  `jam_berakhir_pulang` time NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `konfigurasi_kamerapresensi`
--

INSERT INTO `konfigurasi_kamerapresensi` (`id`, `admin_id`, `nama_kamera`, `role_kamera`, `ip_rtsp`, `jam_mulai_kedatangan`, `jam_berakhir_kedatangan`, `jam_mulai_pulang`, `jam_berakhir_pulang`) VALUES
(10, 2, 'kamera 2', 'OUT', 'rtsp://admin:bismillah9x@192.168.4.2:554/Streaming/Channels/101', '06:00:00', '07:30:00', '15:00:00', '16:00:00'),
(11, 2, 'Kamera 1', 'IN', 'rtsp://admin:admin@10.2.4.130:8554/Streaming/Channels/102', '07:47:00', '08:47:00', '13:47:00', '13:50:00');

-- --------------------------------------------------------

--
-- Struktur dari tabel `lama_kerja`
--

CREATE TABLE `lama_kerja` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) DEFAULT NULL,
  `pegawai_id` int(11) DEFAULT NULL,
  `tanggal` date DEFAULT NULL,
  `nama_pegawai` varchar(100) DEFAULT NULL,
  `divisi` varchar(100) DEFAULT NULL,
  `lama_terdeteksi` int(11) DEFAULT NULL,
  `area_cctv` varchar(100) DEFAULT NULL,
  `foto_bukti` varchar(255) DEFAULT NULL,
  `pelanggaran` varchar(100) DEFAULT NULL,
  `foto_pelanggaran` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `pegawai`
--

CREATE TABLE `pegawai` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) NOT NULL,
  `nama_pegawai` varchar(100) NOT NULL,
  `nomor_pegawai` varchar(50) NOT NULL,
  `divisi_id` int(11) DEFAULT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(20) NOT NULL,
  `folder_path` varchar(255) DEFAULT NULL,
  `photo` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `pegawai`
--

INSERT INTO `pegawai` (`id`, `admin_id`, `nama_pegawai`, `nomor_pegawai`, `divisi_id`, `username`, `password`, `role`, `folder_path`, `photo`) VALUES
(2, 2, 'bagus', '+6283654672273', 4, 'bagus', 'bagus123', 'pegawai', 'static\\foto_dataset\\admin_2\\bagus', NULL),
(3, 2, 'anjar', '+6283654672', 4, 'anjar', 'anjar123', 'pegawai', 'static\\foto_dataset\\admin_2\\anjar', NULL),
(4, 2, 'arnanto', '+628365467220', 4, 'arnanto', 'arnanto123', 'pegawai', 'static\\foto_dataset\\admin_2\\arnanto', NULL),
(5, 2, 'gustomi', '+6285859805284', 4, 'gustomi', 'gustomi123', 'pegawai', NULL, NULL),
(6, 2, 'yono', '+6285859805284', 3, 'yono', 'yono123', 'pegawai', NULL, NULL),
(7, 2, 'yuda', '+628365467210', 3, 'yuda', 'yuda123', 'pegawai', NULL, NULL),
(8, 2, 'candra', '+628585980527', 3, 'candra', 'candra123', 'pegawai', NULL, NULL),
(9, 2, 'angga', '+6287863292219', 1, 'angga', 'angga123', 'pegawai', 'static\\foto_dataset\\admin_2\\angga', NULL),
(12, 2, 'surya', '+6281935698267', 1, 'surya', 'surya123', 'pegawai', 'static\\foto_dataset\\admin_2\\surya', NULL);

-- --------------------------------------------------------

--
-- Struktur dari tabel `superadmin`
--

CREATE TABLE `superadmin` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(20) NOT NULL,
  `photo` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `superadmin`
--

INSERT INTO `superadmin` (`id`, `username`, `password`, `role`, `photo`) VALUES
(1, 'superadmin', 'superadmin123', 'superadmin', NULL);

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `absensi_pegawai`
--
ALTER TABLE `absensi_pegawai`
  ADD PRIMARY KEY (`id`),
  ADD KEY `admin_id` (`admin_id`),
  ADD KEY `pegawai_id` (`pegawai_id`);

--
-- Indeks untuk tabel `admin`
--
ALTER TABLE `admin`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indeks untuk tabel `divisi`
--
ALTER TABLE `divisi`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nama_divisi` (`nama_divisi`),
  ADD KEY `admin_id` (`admin_id`);

--
-- Indeks untuk tabel `konfigurasi_kamerapelacakankerja`
--
ALTER TABLE `konfigurasi_kamerapelacakankerja`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nama_kamera` (`nama_kamera`),
  ADD UNIQUE KEY `ip_rtsp` (`ip_rtsp`),
  ADD KEY `admin_id` (`admin_id`);

--
-- Indeks untuk tabel `konfigurasi_kamerapresensi`
--
ALTER TABLE `konfigurasi_kamerapresensi`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nama_kamera` (`nama_kamera`),
  ADD UNIQUE KEY `ip_rtsp` (`ip_rtsp`),
  ADD KEY `admin_id` (`admin_id`);

--
-- Indeks untuk tabel `lama_kerja`
--
ALTER TABLE `lama_kerja`
  ADD PRIMARY KEY (`id`),
  ADD KEY `admin_id` (`admin_id`),
  ADD KEY `pegawai_id` (`pegawai_id`);

--
-- Indeks untuk tabel `pegawai`
--
ALTER TABLE `pegawai`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `admin_id` (`admin_id`),
  ADD KEY `divisi_id` (`divisi_id`);

--
-- Indeks untuk tabel `superadmin`
--
ALTER TABLE `superadmin`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `absensi_pegawai`
--
ALTER TABLE `absensi_pegawai`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=92;

--
-- AUTO_INCREMENT untuk tabel `admin`
--
ALTER TABLE `admin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT untuk tabel `divisi`
--
ALTER TABLE `divisi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT untuk tabel `konfigurasi_kamerapelacakankerja`
--
ALTER TABLE `konfigurasi_kamerapelacakankerja`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT untuk tabel `konfigurasi_kamerapresensi`
--
ALTER TABLE `konfigurasi_kamerapresensi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT untuk tabel `lama_kerja`
--
ALTER TABLE `lama_kerja`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `pegawai`
--
ALTER TABLE `pegawai`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT untuk tabel `superadmin`
--
ALTER TABLE `superadmin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `absensi_pegawai`
--
ALTER TABLE `absensi_pegawai`
  ADD CONSTRAINT `absensi_pegawai_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`),
  ADD CONSTRAINT `absensi_pegawai_ibfk_2` FOREIGN KEY (`pegawai_id`) REFERENCES `pegawai` (`id`);

--
-- Ketidakleluasaan untuk tabel `divisi`
--
ALTER TABLE `divisi`
  ADD CONSTRAINT `divisi_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`);

--
-- Ketidakleluasaan untuk tabel `konfigurasi_kamerapelacakankerja`
--
ALTER TABLE `konfigurasi_kamerapelacakankerja`
  ADD CONSTRAINT `konfigurasi_kamerapelacakankerja_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`);

--
-- Ketidakleluasaan untuk tabel `konfigurasi_kamerapresensi`
--
ALTER TABLE `konfigurasi_kamerapresensi`
  ADD CONSTRAINT `konfigurasi_kamerapresensi_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`);

--
-- Ketidakleluasaan untuk tabel `lama_kerja`
--
ALTER TABLE `lama_kerja`
  ADD CONSTRAINT `lama_kerja_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`),
  ADD CONSTRAINT `lama_kerja_ibfk_2` FOREIGN KEY (`pegawai_id`) REFERENCES `pegawai` (`id`);

--
-- Ketidakleluasaan untuk tabel `pegawai`
--
ALTER TABLE `pegawai`
  ADD CONSTRAINT `pegawai_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`),
  ADD CONSTRAINT `pegawai_ibfk_2` FOREIGN KEY (`divisi_id`) REFERENCES `divisi` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
