"""
sinopsis_data.py — Sinopsis tulisan tangan untuk buku yang tidak punya deskripsi
asli dari Google Books.

Sebelumnya 238 buku memakai satu kalimat template yang sama persis
("... membahas <bidang> untuk jenjang SMP. Buku ini merupakan koleksi
Perpustakaan SMPN 1 Kemang pada kategori X"). Itu bermasalah bukan hanya karena
terlihat seragam, tapi karena kolom sinopsis ikut masuk FULLTEXT index ft_buku —
238 baris yang berbagi kata identik membuat pencarian kata seperti "koleksi"
atau "SMP" mengembalikan hampir seluruh katalog tanpa relevansi.

Sinopsis di bawah diturunkan dari judul dan kategori saja. Sengaja deskriptif
tentang TOPIK buku, bukan tentang isi spesifik (tokoh, alur, angka bab) yang
tidak bisa diverifikasi tanpa memegang bukunya.

Dipakai oleh apply_sinopsis.py.
"""

# judul persis seperti di tabel buku -> sinopsis
SINOPSIS = {

    # ── Agama ────────────────────────────────────────────────────────────────
    "Bahtera Penyelamat Nabi Nuh a.s":
        "Mengisahkan perjalanan Nabi Nuh a.s. membangun bahtera atas perintah Allah "
        "dan menyelamatkan pengikutnya dari banjir besar. Disajikan dengan bahasa "
        "sederhana untuk pembaca usia sekolah.",
    "Gampang Menulis Huruf Arab Menggunakan Microsoft Word":
        "Panduan praktis mengetik dan menata huruf Arab di Microsoft Word, mulai dari "
        "pengaturan bahasa, pemilihan font, hingga penulisan harakat. Berguna untuk "
        "tugas pelajaran agama dan Bahasa Arab.",
    "Ketentuan Salat Jamaah dan Salat Jumat":
        "Menjelaskan tata cara, syarat, dan ketentuan salat berjamaah serta salat Jumat, "
        "termasuk kedudukan imam dan makmum. Dilengkapi penjelasan yang mudah diikuti "
        "siswa tingkat SMP.",
    "Khabab bin Arats":
        "Kisah Khabab bin Arats, salah satu sahabat Nabi Muhammad yang dikenal karena "
        "keteguhannya menghadapi siksaan di masa awal Islam. Ditulis sebagai bacaan "
        "keteladanan bagi remaja.",
    "Kisah-kisah Teladan Nabi Muhammad":
        "Kumpulan kisah kehidupan Nabi Muhammad yang menonjolkan sifat jujur, sabar, dan "
        "kasih sayang. Setiap kisah ditutup dengan pesan moral yang dapat diterapkan "
        "sehari-hari.",
    "Mahir Bahasa Arab":
        "Materi dasar Bahasa Arab meliputi kosakata, pola kalimat, dan latihan membaca. "
        "Disusun bertahap sebagai pegangan siswa dan guru madrasah.",
    "Nabi Ilyasa a.s, Murid Nabi Ilyas a.s":
        "Menceritakan Nabi Ilyasa a.s. dan hubungannya sebagai murid Nabi Ilyas a.s., "
        "beserta dakwah yang dijalankannya. Bagian dari seri kisah nabi untuk pembaca muda.",
    "Nama-Nama Neraka dan Penghuninya":
        "Memaparkan nama-nama neraka menurut sumber keislaman beserta golongan yang "
        "disebut sebagai penghuninya. Ditujukan sebagai bahan renungan dan pengingat.",
    "Raden Fatah":
        "Riwayat Raden Fatah, pendiri Kesultanan Demak dan tokoh penting penyebaran Islam "
        "di Jawa. Menelusuri asal-usul, perjuangan, dan warisannya.",
    "Sejarah Khulafaurrasyidin":
        "Menelusuri masa kepemimpinan empat khalifah setelah Nabi Muhammad — Abu Bakar, "
        "Umar, Utsman, dan Ali — beserta kebijakan dan tantangan pada zamannya.",
    "Seni Mengajarkan Matematika Berbasis Kecerdasan Majemuk":
        "Menawarkan cara mengajar matematika dengan pendekatan kecerdasan majemuk, agar "
        "siswa dengan gaya belajar berbeda dapat memahami konsep yang sama. Ditujukan "
        "bagi guru dan calon guru.",
    "Subhanallah Allah Menciptakan Burung":
        "Mengajak pembaca mengamati keajaiban penciptaan burung — bentuk paruh, bulu, dan "
        "kemampuan terbang — sebagai bahan renungan atas kebesaran Sang Pencipta.",
    "Subhanallah Allah Menciptakan Lalat":
        "Menyoroti keunikan lalat yang sering dianggap remeh, mulai dari struktur mata "
        "hingga perannya di alam, sebagai pengantar mengagumi ciptaan Allah.",
    "Subhanallah Allah Menciptakan Lebah":
        "Membahas kehidupan lebah, cara membangun sarang, dan manfaat madu bagi manusia, "
        "dikaitkan dengan penyebutan lebah dalam Al-Qur'an.",

    # ── Bahasa Inggris ───────────────────────────────────────────────────────
    "A Shepherd's Dream":
        "Cerita berbahasa Inggris tentang seorang gembala dan mimpinya. Disusun dengan "
        "kalimat sederhana dan ilustrasi, cocok untuk melatih membaca pemula.",
    "Bob's Pranks and Other Stories":
        "Kumpulan cerita pendek berbahasa Inggris yang dibuka dengan kisah kenakalan Bob. "
        "Setiap cerita singkat dan membawa pesan sederhana bagi pembaca muda.",
    "English is Fun":
        "Buku latihan Bahasa Inggris yang mengemas kosakata dan tata bahasa dasar lewat "
        "permainan dan aktivitas ringan, agar belajar terasa menyenangkan.",
    "Rhino's Best Friend and Other Stories":
        "Kumpulan cerita hewan berbahasa Inggris yang diawali kisah persahabatan seekor "
        "badak. Menekankan nilai persahabatan dan tolong-menolong.",
    "Story of The Magic Flute":
        "Cerita berbahasa Inggris tentang seruling ajaib dan kekuatan yang dibawanya. "
        "Ditulis dengan kosakata terbatas untuk pembelajar tingkat dasar.",
    "The Angel's Lake":
        "Kisah berbahasa Inggris berlatar sebuah danau yang dikaitkan dengan bidadari. "
        "Menggabungkan unsur dongeng dengan latihan membaca.",
    "Baby Squirrel Learnt A Lesson and Other Stories":
        "Kumpulan cerita berbahasa Inggris yang dibuka dengan kisah bayi tupai belajar "
        "dari kesalahannya. Ditulis dengan kalimat pendek untuk pembaca pemula.",
    "The Axe and the Two Travellers and Other Stories":
        "Kumpulan fabel berbahasa Inggris yang dibuka dengan kisah kapak dan dua musafir, "
        "mengangkat tema kejujuran dan kesetiakawanan.",
    "The Bear and the Fox and Other Stories":
        "Kumpulan cerita hewan berbahasa Inggris yang menampilkan beruang dan rubah "
        "sebagai tokoh utama, lengkap dengan pesan moral di tiap akhir cerita.",
    "The Beast Prince":
        "Cerita berbahasa Inggris tentang seorang pangeran yang berwujud buas dan "
        "perjalanannya menemukan penerimaan. Disajikan dalam bahasa yang mudah diikuti.",
    "The Careless Prince":
        "Mengisahkan seorang pangeran yang ceroboh dan akibat dari sikapnya. Cerita "
        "berbahasa Inggris dengan pesan tentang tanggung jawab.",
    "The Crab and The Fox and Other Stories":
        "Kumpulan fabel berbahasa Inggris yang diawali kisah kepiting dan rubah. Cocok "
        "untuk latihan membaca sekaligus mengenal nilai kehidupan.",
    "The Crane and The Fox and Other Stories":
        "Fabel berbahasa Inggris tentang bangau dan rubah beserta cerita-cerita lain, "
        "menyoroti akal cerdik dan balas budi.",
    "The Fish and the Tortoise and Other Stories":
        "Kumpulan cerita berbahasa Inggris yang dibuka dengan kisah ikan dan kura-kura, "
        "membawa pesan tentang kesabaran dan persahabatan.",
    "The Games Board Map":
        "Cerita berbahasa Inggris bertema petualangan yang berpusat pada sebuah papan "
        "permainan. Ditujukan bagi pembaca remaja yang sedang mengasah Bahasa Inggris.",
    "The Goat's Secret and Other Stories":
        "Kumpulan cerita berbahasa Inggris yang diawali rahasia seekor kambing. Setiap "
        "kisah pendek dan diakhiri pelajaran sederhana.",
    "The Mouse Deer and His Magic Flute and Other Stories":
        "Cerita si kancil dan seruling ajaibnya, disajikan dalam Bahasa Inggris bersama "
        "beberapa cerita rakyat lain yang akrab bagi pembaca Indonesia.",
    "The Mouse Deer Cheats the Farmer and Other Stories":
        "Kisah kecerdikan si kancil mengelabui seorang petani, dituturkan dalam Bahasa "
        "Inggris bersama cerita-cerita pendek lainnya.",
    "The Peach Boy":
        "Adaptasi berbahasa Inggris dari cerita rakyat Jepang tentang anak laki-laki yang "
        "lahir dari buah persik. Disederhanakan untuk pembaca pemula.",
    "The Snake and the Man and Other Stories":
        "Kumpulan fabel berbahasa Inggris yang dibuka dengan kisah ular dan manusia, "
        "mengangkat tema balas budi dan kewaspadaan.",
    "The Story of The Frog Prince":
        "Versi berbahasa Inggris dari dongeng pangeran katak, ditulis ulang dengan "
        "kosakata sederhana dan ilustrasi pendukung.",
    "The Tadpoles Look for Their Mother and Other Stories":
        "Kisah berudu yang mencari induknya beserta cerita lain, disajikan dalam Bahasa "
        "Inggris sambil memperkenalkan tahap pertumbuhan katak.",
    "The Tears of A Giant Turtle and Other Stories":
        "Kumpulan cerita berbahasa Inggris yang diawali kisah air mata penyu raksasa, "
        "menyentuh tema kasih sayang dan pengorbanan.",

    # ── Biologi ──────────────────────────────────────────────────────────────
    "Ayo Mempelajari Lumut":
        "Mengenalkan lumut sebagai tumbuhan tidak berpembuluh: ciri-ciri, tempat hidup, "
        "dan perannya di lingkungan. Dilengkapi gambar pengamatan.",
    "Bagaimana Tubuh Kita Mencerna Makanan":
        "Menelusuri perjalanan makanan dari mulut hingga usus, beserta fungsi tiap organ "
        "pencernaan. Menjelaskan mengapa mengunyah dan pola makan sehat itu penting.",
    "Budi Daya Cacing Tanah":
        "Panduan membudidayakan cacing tanah, mulai dari menyiapkan media, pemberian "
        "pakan, hingga pemanenan. Membahas juga manfaat cacing bagi kesuburan tanah.",
    "Cara Menentukan Golongan Darah":
        "Menjelaskan sistem golongan darah ABO dan rhesus serta cara pengujiannya. "
        "Menguraikan mengapa kecocokan golongan darah penting dalam transfusi.",
    "Flora Lima Benua":
        "Memperkenalkan tumbuhan khas dari lima benua beserta ciri lingkungan yang "
        "membentuknya. Mengajak pembaca melihat keragaman flora dunia.",
    "Hewan Berbahaya di Sekitar Kita":
        "Mengenali hewan berbisa dan berbahaya yang dapat dijumpai di sekitar rumah, "
        "ciri-cirinya, serta cara menghindari dan menangani jika terjadi kontak.",
    "Kandungan Sayur-sayuran dan Buah-buahan":
        "Menguraikan kandungan gizi berbagai sayur dan buah serta manfaatnya bagi tubuh. "
        "Membantu pembaca menyusun pilihan makanan yang lebih sehat.",
    "Keanekaragaman Biota Laut":
        "Memaparkan ragam makhluk hidup di laut Indonesia, dari terumbu karang hingga "
        "ikan dan mamalia laut, beserta pentingnya menjaga kelestariannya.",
    "Kelangsungan Hidup Organisme":
        "Membahas cara makhluk hidup mempertahankan kelangsungan jenisnya melalui "
        "adaptasi, seleksi alam, dan perkembangbiakan.",
    "Makanan Materi Ekologi":
        "Menjelaskan rantai dan jaring-jaring makanan serta aliran energi dalam "
        "ekosistem, termasuk peran produsen, konsumen, dan pengurai.",
    "Makhluk-Makhluk Uniseluler":
        "Mengenalkan makhluk hidup bersel satu seperti bakteri dan protozoa: bentuk, "
        "cara hidup, serta perannya yang menguntungkan maupun merugikan.",
    "Manusia (Seri Dasar IPA)":
        "Pengantar tentang tubuh manusia dan sistem organ penyusunnya, disajikan sebagai "
        "bacaan dasar IPA dengan ilustrasi yang membantu pemahaman.",
    "Mengenal Coelenterata":
        "Membahas hewan berongga seperti ubur-ubur dan karang: bentuk tubuh, cara "
        "menangkap mangsa, dan perannya membentuk terumbu.",
    "Mengenal Herbarium Flora":
        "Menjelaskan apa itu herbarium dan cara membuat koleksi tumbuhan kering yang "
        "benar, dari pengambilan sampel hingga pengawetan dan pelabelan.",
    "Mengenal Hewan Australia 2":
        "Melanjutkan pengenalan satwa khas Australia beserta ciri dan habitatnya, "
        "termasuk kelompok berkantung yang tidak dijumpai di benua lain.",
    "Mengenal Manfaat Hutan Bakau":
        "Menguraikan fungsi hutan bakau sebagai penahan abrasi, tempat berkembang biak "
        "biota laut, dan penyerap karbon, serta ancaman yang dihadapinya.",
    "Mengenal Mata dan Cara Merawatnya":
        "Menjelaskan bagian-bagian mata dan cara kerjanya, disertai kebiasaan menjaga "
        "kesehatan penglihatan dan gangguan mata yang umum terjadi.",
    "Mengenal Moluska":
        "Memperkenalkan kelompok hewan bertubuh lunak seperti siput, kerang, dan cumi: "
        "ciri tubuh, tempat hidup, dan manfaatnya bagi manusia.",
    "Mengenal Ragam Tumbuhan Air":
        "Membahas jenis-jenis tumbuhan air, cara bertahan hidup di lingkungan berair, "
        "dan perannya menjaga keseimbangan ekosistem perairan.",
    "Mengenal Serangga di Sekitar Kita":
        "Mengenali serangga yang biasa ditemui sehari-hari, ciri tubuh, daur hidup, serta "
        "peranannya sebagai penyerbuk maupun hama.",
    "Panduan Bersahabat dengan Kucing":
        "Panduan merawat kucing peliharaan: pemberian makan, kebersihan, kesehatan, dan "
        "cara memahami perilakunya.",
    "Peranan Mikroorganisme dalam Kehidupan Manusia":
        "Menjelaskan peran mikroorganisme dalam pembuatan makanan, obat, dan penguraian "
        "limbah, sekaligus jenis yang menimbulkan penyakit.",
    "Sistem Pernapasan Makhluk Hidup":
        "Membandingkan cara bernapas berbagai makhluk hidup, dari insang hingga paru-paru, "
        "beserta organ dan mekanisme pertukaran gasnya.",
    "Struktur Luar Tumbuhan":
        "Mengurai bagian luar tumbuhan — akar, batang, daun, bunga, dan buah — beserta "
        "fungsi masing-masing bagi kehidupan tumbuhan.",

    # ── Fiksi ────────────────────────────────────────────────────────────────
    "Air Mata Sang Pohon Purba":
        "Novel yang mengangkat hubungan manusia dengan pohon tua dan alam di sekitarnya. "
        "Menyampaikan pesan kepedulian lingkungan lewat jalinan cerita.",
    "Ask Tinkerbell":
        "Cerita remaja yang berpusat pada tokoh Tinkerbell sebagai tempat bertanya soal "
        "persoalan sehari-hari. Ditulis dengan gaya ringan khas pembaca muda.",
    "Jika Pertiwi Memanggil":
        "Karya bertema kecintaan pada tanah air dan panggilan untuk berbakti kepada "
        "bangsa. Mengangkat semangat kebangsaan lewat penuturan naratif.",
    "Kumpulan Fabel Aesop Seri 2":
        "Lanjutan kumpulan fabel Aesop yang menampilkan hewan sebagai tokoh utama. Tiap "
        "cerita pendek dan ditutup dengan pesan moral.",
    "Lord of the Shadows: Penguasa Kegelapan":
        "Bagian dari seri fantasi Darren Shan yang mengikuti perjalanan sang tokoh utama "
        "menghadapi kekuatan kegelapan. Edisi terjemahan Bahasa Indonesia.",
    "Nu Ngageugeuh Legok Kiara":
        "Karya sastra berbahasa Sunda yang berlatar Legok Kiara. Menjadi bacaan untuk "
        "mengenal dan melestarikan sastra daerah.",
    "Patepung di Bandung":
        "Cerita berbahasa Sunda berlatar Kota Bandung yang berpusat pada sebuah "
        "pertemuan. Menampilkan warna budaya dan keseharian masyarakat Sunda.",
    "Perjalanan Sebatang Kayu Jati":
        "Menuturkan perjalanan sebatang kayu jati dari hutan hingga menjadi barang "
        "berguna. Mengajak pembaca menghargai proses dan hasil alam.",
    "Pohon dalam Perut":
        "Cerita bergaya imajinatif yang berangkat dari gagasan tumbuhnya pohon di dalam "
        "perut. Mengemas pesan tentang kebiasaan dan akibatnya.",
    "Pudarnya Pesona Cleopatra":
        "Novel karya Habiburrahman El Shirazy tentang pergulatan batin seorang lelaki "
        "antara bayangan ideal dan kenyataan rumah tangganya.",
    "Puisi Lan Larasati":
        "Kumpulan karya sastra bernuansa Jawa yang memadukan puisi dengan penuturan "
        "tokoh Larasati. Menjadi bahan apresiasi sastra daerah.",
    "Rindu Tanah Jeruk: Palestina!":
        "Karya yang mengangkat kerinduan dan keprihatinan terhadap Palestina. Menyentuh "
        "tema kemanusiaan lewat penuturan yang menggugah.",
    "Si Paser":
        "Cerita berbahasa Sunda dengan tokoh utama bernama Si Paser. Menampilkan nilai "
        "keseharian masyarakat lewat alur yang sederhana.",

    # ── Fisika ───────────────────────────────────────────────────────────────
    "Biasa dengan Sains Energi Matahari":
        "Mengenalkan matahari sebagai sumber energi utama bumi dan cara memanfaatkannya, "
        "mulai dari pengering alami hingga panel surya sederhana.",
    "Cakrawala Sains: Serba Serbi Energi":
        "Membahas berbagai bentuk energi, perubahannya dari satu bentuk ke bentuk lain, "
        "serta pemanfaatannya dalam kehidupan sehari-hari.",
    "Energi":
        "Pengantar konsep energi: pengertian, jenis, sumber, dan hukum kekekalan energi, "
        "disertai contoh yang dekat dengan keseharian siswa.",
    "Energi dan Aplikasinya dalam Kehidupan Sehari-hari":
        "Menghubungkan konsep energi dengan penerapannya di rumah, transportasi, dan "
        "industri, termasuk cara menggunakan energi secara hemat.",
    "Energi Kalor":
        "Menjelaskan kalor sebagai bentuk energi, perpindahannya secara konduksi, "
        "konveksi, dan radiasi, serta pengaruhnya pada suhu dan wujud benda.",
    "Gaya dan Hukum Newton":
        "Membahas pengertian gaya dan tiga hukum Newton tentang gerak, dilengkapi contoh "
        "penerapannya pada peristiwa sehari-hari.",
    "Konduktor dan Isolator":
        "Membedakan bahan penghantar dan penghambat panas maupun listrik, beserta alasan "
        "pemilihan bahan pada peralatan yang kita pakai.",
    "Kreasiku Seri Tata Surya":
        "Mengenalkan susunan tata surya — matahari, planet, dan benda langit lain — "
        "melalui penjelasan dan kegiatan kreatif.",
    "Mari Mengenal Gerak dan Air":
        "Membahas konsep gerak serta sifat dan perilaku air, dikemas dengan percobaan "
        "sederhana yang bisa dilakukan siswa.",
    "Matahari Bumi dan Bulan":
        "Menjelaskan hubungan matahari, bumi, dan bulan: rotasi, revolusi, fase bulan, "
        "serta terjadinya siang-malam dan gerhana.",
    "Mengenal Gerak":
        "Pengantar konsep gerak meliputi jarak, perpindahan, kecepatan, dan percepatan, "
        "dengan contoh yang mudah diamati di sekitar.",
    "Sains untuk Pemula 3: Mari Bermain Tumbukan dan Gesekan":
        "Mengajak siswa memahami tumbukan dan gaya gesek lewat percobaan sederhana. "
        "Bagian dari seri sains praktik untuk pemula.",
    "Sains untuk Pemula 4: Mari Bermain Pesawat Sederhana":
        "Mengenalkan pengungkit, katrol, bidang miring, dan roda sebagai pesawat "
        "sederhana yang meringankan kerja, melalui kegiatan langsung.",
    "Sains untuk Pemula 9: Mari Bermain Elektromagnet":
        "Membahas hubungan listrik dan magnet lewat percobaan membuat elektromagnet "
        "sederhana beserta penerapannya pada alat sehari-hari.",
    "Seri Jelajah Sains: Antariksa":
        "Mengajak pembaca menjelajahi antariksa: bintang, galaksi, dan penjelajahan luar "
        "angkasa, disertai gambar pendukung.",
    "Teknik Pengerjaan Listrik":
        "Panduan dasar pekerjaan kelistrikan, dari pengenalan alat dan komponen hingga "
        "pemasangan instalasi sederhana serta keselamatan kerja.",

    # ── IPS ──────────────────────────────────────────────────────────────────
    "Belajar Mandiri Melalui Pramuka":
        "Menguraikan kegiatan kepramukaan sebagai sarana melatih kemandirian, "
        "kedisiplinan, dan kerja sama, lengkap dengan keterampilan dasar regu.",
    "Berpikir dengan IQ, EQ, dan SQ":
        "Membahas tiga jenis kecerdasan — intelektual, emosional, dan spiritual — serta "
        "cara mengembangkannya secara seimbang dalam kehidupan sehari-hari.",
    "Budaya Hidup Sehat untuk Anak":
        "Mengenalkan kebiasaan hidup sehat sejak dini: pola makan, kebersihan diri, "
        "istirahat cukup, dan aktivitas fisik yang teratur.",
    "Etiket Pergaulan (Sebuah Buku Pegangan)":
        "Pegangan praktis tentang tata krama bergaul: cara menyapa, berbicara, dan "
        "bersikap sopan di lingkungan sekolah maupun masyarakat.",
    "Jenis-Jenis Pekerjaan":
        "Memperkenalkan beragam jenis pekerjaan beserta tugas dan manfaatnya bagi "
        "masyarakat, membantu siswa mengenali pilihan masa depan.",
    "Kearifan Lokal: Benteng Kerukunan":
        "Menunjukkan bagaimana nilai dan tradisi lokal berperan menjaga kerukunan antar "
        "warga, dengan contoh dari berbagai daerah di Indonesia.",
    "Kesehatan Jiwa":
        "Menjelaskan pentingnya kesehatan jiwa, tanda-tanda gangguan yang perlu "
        "diwaspadai, serta cara menjaga keseimbangan emosi.",
    "Ketenagakerjaan di Indonesia":
        "Membahas kondisi ketenagakerjaan di Indonesia: angkatan kerja, pengangguran, "
        "dan upaya peningkatan mutu tenaga kerja.",
    "Membiasakan Hidup Sehat":
        "Mengajak pembaca membentuk kebiasaan sehat setiap hari, dari menjaga kebersihan "
        "hingga mengatur pola makan dan olahraga.",
    "Mengenal Kewirausahaan":
        "Pengantar dunia wirausaha: ciri wirausahawan, cara melihat peluang, dan langkah "
        "awal merintis usaha kecil.",
    "Menggali Potensi Diri Menggapai Puncak":
        "Membimbing pembaca mengenali bakat dan potensi dirinya, lalu mengembangkannya "
        "secara terarah untuk meraih cita-cita.",
    "Narkoba: Bahaya dan Upaya Pencegahannya":
        "Menjelaskan jenis-jenis narkoba, dampaknya terhadap tubuh dan masa depan, serta "
        "langkah pencegahan di lingkungan keluarga dan sekolah.",
    "Norma-Norma yang Berlaku di Masyarakat":
        "Menguraikan norma agama, kesusilaan, kesopanan, dan hukum beserta contoh "
        "penerapan dan sanksinya dalam kehidupan bermasyarakat.",
    "Pendidikan Karakter Bangsa":
        "Membahas nilai-nilai karakter yang perlu ditanamkan pada generasi muda dan "
        "peran sekolah serta keluarga dalam membentuknya.",
    "Serunya Punya Masa Depan":
        "Mengajak remaja merancang masa depan dengan mengenali minat, menetapkan tujuan, "
        "dan menyiapkan langkah yang realistis.",
    "Upaya Menjaga Diri dari Bahaya Narkoba":
        "Memberi bekal cara menolak ajakan penyalahgunaan narkoba dan membangun "
        "lingkungan pergaulan yang sehat.",

    # ── Kimia ────────────────────────────────────────────────────────────────
    "Bahan Kimia di Industri":
        "Mengenalkan bahan kimia yang dipakai dalam berbagai industri, kegunaannya, serta "
        "penanganan yang aman terhadap limbah dan risikonya.",
    "Bahan Kimia Di Sekitar Kita":
        "Membahas bahan kimia dalam produk sehari-hari seperti sabun, pemutih, dan "
        "pengawet makanan, beserta cara menggunakannya dengan aman.",
    "Ikatan Kimia":
        "Menjelaskan bagaimana atom bergabung membentuk senyawa melalui ikatan ion dan "
        "kovalen, disertai contoh senyawa yang umum dijumpai.",
    "Sains untuk Pemula 10: Mari Bermain Molekul":
        "Mengenalkan molekul dan susunan atom penyusunnya lewat kegiatan dan model "
        "sederhana. Bagian dari seri sains praktik untuk pemula.",
    "Seputar Pengawetan Ikan dan Daging":
        "Membahas cara mengawetkan ikan dan daging — pendinginan, pengasinan, "
        "pengasapan, dan pengeringan — beserta prinsip di baliknya.",

    # ── Komik ────────────────────────────────────────────────────────────────
    "Bleach 10: Tattoo on the Sky":
        "Volume kesepuluh seri manga Bleach karya Tite Kubo, melanjutkan petualangan "
        "Ichigo Kurosaki sebagai Shinigami pengganti.",

    # ── Matematika ───────────────────────────────────────────────────────────
    "Asyiknya Belajar Bangun Datar dan Bangun Ruang":
        "Mengenalkan bentuk bangun datar dan bangun ruang beserta sifat-sifatnya, "
        "dikemas dengan ilustrasi agar mudah dibayangkan siswa.",
    "Asyiknya Bermain Bangun Segitiga":
        "Membahas jenis-jenis segitiga, sifat sudut dan sisinya, serta cara menghitung "
        "keliling dan luasnya lewat kegiatan yang menyenangkan.",
    "Asyiknya Bermain Kubus dan Balok":
        "Menguraikan unsur kubus dan balok — rusuk, sisi, dan titik sudut — hingga cara "
        "menghitung luas permukaan dan volumenya.",
    "Ayo Mengenal Diagram":
        "Mengenalkan cara menyajikan data dalam diagram batang, garis, dan lingkaran, "
        "serta membaca informasi yang terkandung di dalamnya.",
    "Ayo Menghitung Luas Permukaan Benda":
        "Melatih menghitung luas permukaan berbagai bangun ruang melalui jaring-jaring "
        "dan contoh benda nyata di sekitar.",
    "Ayo, Mengukur Jarak":
        "Membahas satuan panjang dan cara mengukur jarak, dari alat ukur sederhana "
        "hingga pembacaan skala pada peta.",
    "Belajar Bangun Ruang Sisi Lengkung":
        "Menjelaskan tabung, kerucut, dan bola: unsur pembentuk, luas permukaan, dan "
        "volume, disertai contoh soal bertahap.",
    "Belajar Konsep Kesebangunan":
        "Mengenalkan konsep bangun yang sebangun dan kongruen beserta syarat-syaratnya, "
        "serta penerapannya pada perbandingan ukuran.",
    "Belajar Matematika dari Lingkungan Sekitar":
        "Mengaitkan konsep matematika dengan benda dan peristiwa di sekitar siswa, agar "
        "materi terasa nyata dan mudah dipahami.",
    "Belajar Mudah Jarimatika":
        "Mengajarkan teknik berhitung cepat menggunakan jari tangan untuk operasi "
        "perkalian dan pembagian, lengkap dengan latihan bertahap.",
    "Berhitung Cepat dengan Metode Horisontal (Metris)":
        "Memperkenalkan metode horisontal sebagai cara berhitung cepat tanpa "
        "susun ke bawah, disertai contoh dan latihan.",
    "Berhitung Matematika Lanjutan":
        "Melanjutkan keterampilan berhitung ke operasi yang lebih kompleks, dengan "
        "latihan bertingkat untuk memperkuat ketelitian.",
    "Bermain dengan Angka":
        "Mengemas pengenalan bilangan dan operasi hitung dalam bentuk permainan dan "
        "teka-teki, agar berlatih terasa ringan.",
    "Cara Praktis Belajar Sempoa Sendiri 2":
        "Lanjutan panduan belajar sempoa secara mandiri, memuat teknik penjumlahan dan "
        "pengurangan tingkat lanjut beserta latihannya.",
    "Fungsi dan Pythagoras":
        "Membahas konsep fungsi beserta grafiknya, dilanjutkan teorema Pythagoras dan "
        "penerapannya pada segitiga siku-siku.",
    "Keliling dan Luas Bangun Datar":
        "Menghitung keliling dan luas persegi, persegi panjang, segitiga, jajargenjang, "
        "dan lingkaran melalui rumus dan contoh penerapan.",
    "Kreasi Matematikawan Cilik: Seri Bangun Datar":
        "Mengajak siswa mengenal bangun datar lewat kegiatan kreatif seperti menggambar, "
        "melipat, dan menyusun bentuk.",
    "Kreatif dengan Permainan Matematika":
        "Kumpulan permainan dan tantangan matematika yang melatih logika serta "
        "keterampilan berhitung secara menyenangkan.",
    "Kupas Tuntas Matematika":
        "Merangkum materi matematika tingkat SMP dari bilangan hingga geometri, "
        "dilengkapi pembahasan soal untuk persiapan ujian.",
    "Mari Mengenal Lambang Matematika":
        "Mengenalkan arti berbagai lambang dan notasi matematika serta cara membacanya "
        "dengan benar dalam soal dan rumus.",
    "Mengenal Bangun dan Belajar Pecahan":
        "Menggabungkan pengenalan bangun datar dengan konsep pecahan, memakai gambar "
        "bagian bangun untuk menjelaskan nilai pecahan.",
    "Mengenal Bilangan":
        "Pengantar jenis-jenis bilangan dan cara membaca, menulis, serta mengurutkannya, "
        "sebagai dasar sebelum masuk ke operasi hitung.",
    "Mengenal Garis-Garis pada Segitiga":
        "Membahas garis tinggi, garis bagi, garis berat, dan garis sumbu pada segitiga "
        "beserta cara melukisnya.",
    "Mengenal Himpunan dan Diagram Venn":
        "Menjelaskan konsep himpunan, anggota, dan operasinya, serta cara menyajikan "
        "hubungan antar himpunan dengan diagram Venn.",
    "Mengenal Lebih Dekat Bilangan":
        "Menelusuri sifat dan keunikan bilangan, dari bilangan bulat hingga pecahan, "
        "dengan penjelasan yang mengundang rasa ingin tahu.",
    "Mengenal Lebih Dekat Ilmuwan Matematika":
        "Memperkenalkan tokoh-tokoh matematika dunia beserta penemuan yang membentuk "
        "ilmu matematika seperti yang dipelajari sekarang.",
    "Mengenal Pangkat Tak Sebenarnya":
        "Membahas bilangan berpangkat pecahan dan negatif beserta kaitannya dengan "
        "bentuk akar, dilengkapi contoh penyelesaian.",
    "Mengenal Persen dan Permil":
        "Menjelaskan konsep persen dan permil serta penerapannya pada perhitungan "
        "diskon, bunga, dan perbandingan sehari-hari.",
    "Mengenal Statistika":
        "Pengantar statistika: mengumpulkan, menyajikan, dan menafsirkan data, termasuk "
        "menghitung rata-rata, median, dan modus.",
    "Mengenal Waktu dan Pengukuran":
        "Membahas satuan waktu dan cara mengukurnya, serta pengukuran besaran lain "
        "seperti panjang dan berat dengan alat yang sesuai.",
    "Menggambar dengan Jangka":
        "Panduan menggunakan jangka untuk melukis lingkaran dan konstruksi geometri "
        "dasar, dari membagi sudut hingga membuat segi banyak beraturan.",
    "Operasi Bentuk Aljabar":
        "Menjelaskan penjumlahan, pengurangan, perkalian, dan pembagian bentuk aljabar, "
        "termasuk penyederhanaan suku sejenis.",
    "Pangkat dan Akar Pangkat":
        "Membahas bilangan berpangkat dan bentuk akar beserta sifat-sifat operasinya, "
        "dilengkapi latihan bertahap.",
    "Penerapan KPK dan FPB":
        "Menjelaskan cara menentukan KPK dan FPB serta menerapkannya pada soal cerita "
        "sehari-hari seperti pembagian dan penjadwalan.",
    "Penerapan Pengolahan Data Siswa":
        "Menunjukkan cara mengumpulkan, menyusun, dan menyajikan data siswa dalam tabel "
        "dan diagram sebagai latihan pengolahan data.",
    "Penjumlahan dan Pengurangan":
        "Memperkuat keterampilan dasar penjumlahan dan pengurangan, mulai dari cara "
        "susun hingga soal cerita penerapannya.",
    "Perkalian Matematika Secara Cepat dan Tepat":
        "Memaparkan teknik perkalian cepat beserta pola-pola yang memudahkan, dilengkapi "
        "latihan untuk melatih ketepatan.",
    "Persamaan dan Pertidaksamaan Linear Satu Variabel":
        "Menjelaskan cara menyelesaikan persamaan dan pertidaksamaan linear satu "
        "variabel serta menyajikan penyelesaiannya pada garis bilangan.",
    "Persamaan Kuadrat":
        "Membahas bentuk umum persamaan kuadrat dan cara menyelesaikannya melalui "
        "pemfaktoran, melengkapkan kuadrat, dan rumus abc.",
    "Seluk-Beluk Lingkaran":
        "Menguraikan unsur lingkaran — jari-jari, diameter, busur, juring — beserta "
        "perhitungan keliling, luas, dan sudut pusat.",
    "Serba-Serbi Bilangan":
        "Menyajikan beragam jenis bilangan dan sifat menariknya, dari bilangan prima "
        "hingga pola barisan bilangan.",
    "Siapa Bilang Matematika Sulit 3":
        "Menyanggah anggapan bahwa matematika itu sulit dengan menyajikan materi secara "
        "bertahap dan contoh yang mudah diikuti.",
    "Simetri dan Pencerminan":
        "Membahas simetri lipat dan simetri putar serta pencerminan bangun datar pada "
        "bidang koordinat.",
    "Sistem Koordinat":
        "Mengenalkan bidang koordinat Cartesius, cara menentukan letak titik, dan "
        "membaca posisi berdasarkan sumbu x dan y.",
    "Sistem Persamaan Linear Dua Variabel":
        "Menjelaskan penyelesaian SPLDV dengan metode substitusi, eliminasi, dan grafik, "
        "beserta penerapannya pada soal cerita.",
    "Sudut dan Luas Segi Banyak":
        "Membahas jenis sudut, hubungan antar sudut, dan cara menghitung luas segi "
        "banyak dengan memecahnya menjadi bangun sederhana.",
    "Tempat Kedudukan":
        "Menjelaskan konsep tempat kedudukan titik yang memenuhi syarat tertentu, "
        "disertai cara melukis dan contohnya.",
    "Tempat Kedudukan dalam Matematika":
        "Menguraikan tempat kedudukan titik dalam geometri beserta kaitannya dengan "
        "garis, lingkaran, dan bangun lain.",
    "Transformasi Matematika":
        "Membahas translasi, refleksi, rotasi, dan dilatasi beserta pengaruhnya terhadap "
        "kedudukan dan ukuran bangun.",

    # ── Non-Fiksi ────────────────────────────────────────────────────────────
    "Ensiklopedia":
        "Bacaan rujukan yang memuat penjelasan ringkas berbagai topik pengetahuan, "
        "disusun agar mudah ditelusuri sebagai teman belajar sehari-hari.",
    "Jati Diri di Antara Tunas Bangsa":
        "Mengajak generasi muda mengenali jati diri dan perannya sebagai penerus bangsa, "
        "lewat renungan tentang nilai dan tanggung jawab.",
    "Pandangan Hidup Manusia":
        "Membahas berbagai pandangan hidup yang dianut manusia dan bagaimana pandangan "
        "itu memengaruhi cara bersikap serta mengambil keputusan.",

    # ── Olahraga ─────────────────────────────────────────────────────────────
    "Atletik Cabang Lempar":
        "Membahas nomor lempar dalam atletik — lempar lembing, cakram, dan tolak peluru — "
        "beserta teknik dasar dan peraturannya.",
    "Belajar Karate Secara Sistematis":
        "Menyusun pembelajaran karate secara bertahap, dari kuda-kuda dan pukulan dasar "
        "hingga rangkaian gerakan, disertai gambar peraga.",
    "Bergembira dengan Senam":
        "Mengenalkan gerakan senam yang menyenangkan untuk menjaga kebugaran, lengkap "
        "dengan urutan pemanasan hingga pendinginan.",
    "Bermain Bulu Tangkis":
        "Menjelaskan teknik dasar bulu tangkis — pegangan raket, servis, dan pukulan — "
        "serta peraturan permainan tunggal dan ganda.",
    "Bermain Sepak Takraw":
        "Memperkenalkan sepak takraw: teknik sepakan, posisi pemain, dan aturan "
        "pertandingan, sebagai olahraga khas Asia Tenggara.",
    "Bermain Tenis Meja":
        "Membahas teknik dasar tenis meja mulai dari cara memegang bet, servis, hingga "
        "pola pukulan, beserta peraturan pertandingan.",
    "Binaraga":
        "Mengenalkan olahraga binaraga: prinsip latihan beban, pembentukan otot, serta "
        "pentingnya asupan gizi dan istirahat.",
    "Dasar-Dasar Senam":
        "Menguraikan gerakan dasar senam dan prinsip keselamatannya, sebagai bekal "
        "sebelum mempelajari rangkaian yang lebih kompleks.",
    "Ensiklomini Olahraga: Olahraga Atletik":
        "Rangkuman ringkas cabang atletik — lari, lompat, dan lempar — beserta sejarah "
        "dan peraturan dasar tiap nomornya.",
    "Futsal":
        "Mengenalkan futsal: ukuran lapangan, jumlah pemain, teknik dasar, dan peraturan "
        "yang membedakannya dari sepak bola lapangan.",
    "Futsal: Sepak Bola dalam Ruangan":
        "Membahas futsal sebagai sepak bola dalam ruangan, meliputi teknik mengumpan, "
        "menggiring, dan strategi bermain di lapangan sempit.",
    "Karate":
        "Pengantar bela diri karate: sejarah, filosofi, teknik dasar pukulan dan "
        "tendangan, serta tingkatan sabuk.",
    "Kebugaran dan Kesehatan":
        "Menjelaskan komponen kebugaran jasmani dan cara melatihnya, serta hubungan "
        "antara aktivitas fisik dengan kesehatan tubuh.",
    "Langkah Menjadi Pemain Basket Hebat":
        "Menuntun pembaca menguasai bola basket secara bertahap, dari dribel dan "
        "menembak hingga kerja sama tim.",
    "Langkah Menjadi Pemain Voli Hebat":
        "Membahas teknik dasar bola voli — servis, passing, smash, dan blok — beserta "
        "latihan untuk meningkatkan kemampuan bermain.",
    "Mempersiapkan Pemain Sepak Bola Berprestasi (1)":
        "Bagian pertama panduan pembinaan pemain sepak bola, mencakup teknik dasar dan "
        "program latihan bagi pemain pemula.",
    "Mempersiapkan Pemain Sepak Bola Berprestasi (2)":
        "Lanjutan panduan pembinaan sepak bola dengan penekanan pada taktik, kondisi "
        "fisik, dan mental bertanding.",
    "Mempersiapkan Pemain Voli Berprestasi":
        "Panduan membina pemain bola voli, dari penguasaan teknik hingga penyusunan "
        "program latihan menuju prestasi.",
    "Mempersiapkan Perenang Berprestasi":
        "Membahas pembinaan atlet renang: gaya renang, teknik pernapasan, dan program "
        "latihan untuk meningkatkan catatan waktu.",
    "Mengenal Aneka Cabang Olahraga":
        "Memperkenalkan berbagai cabang olahraga beserta peralatan, aturan pokok, dan "
        "manfaatnya bagi kesehatan.",
    "Mengenal Olahraga Balap Sepeda":
        "Mengulas balap sepeda: jenis lomba, peralatan, teknik mengayuh, dan aspek "
        "keselamatan yang perlu diperhatikan.",
    "Mengenal Olahraga Gulat":
        "Mengenalkan gulat sebagai olahraga bela diri: teknik kuncian dan bantingan, "
        "kelas pertandingan, serta peraturannya.",
    "Mengenal Olahraga Sepatu Roda":
        "Membahas sepatu roda mulai dari perlengkapan, teknik meluncur dan berhenti, "
        "hingga nomor perlombaan yang dipertandingkan.",
    "Olahraga Boling":
        "Menjelaskan permainan boling: cara memegang dan melempar bola, penataan pin, "
        "serta sistem penghitungan skor.",
    "Penjelajahan dan Olahraga Alam":
        "Membahas kegiatan penjelajahan alam seperti hiking dan berkemah, beserta "
        "persiapan, peralatan, dan keselamatan di lapangan.",
    "Permainan Bulu Tangkis":
        "Mengulas permainan bulu tangkis dari sejarah, perlengkapan, teknik pukulan, "
        "hingga sistem penilaian pertandingan.",
    "Permainan Tenis Lapangan":
        "Memperkenalkan tenis lapangan: ukuran lapangan, jenis pukulan, dan aturan "
        "penghitungan angka dalam pertandingan.",
    "Pola Gerak dalam Senam 1":
        "Bagian pertama seri pola gerak senam, memuat gerakan dasar dan rangkaian "
        "sederhana beserta cara melakukannya dengan aman.",
    "Pola Gerak dalam Senam 2":
        "Melanjutkan pola gerak senam ke rangkaian yang lebih beragam, dengan penekanan "
        "pada keseimbangan dan kelenturan.",
    "Pola Gerak dalam Senam 3":
        "Bagian ketiga seri pola gerak senam, menyajikan rangkaian gerakan tingkat lanjut "
        "beserta panduan latihannya.",
    "Senam Aerobik":
        "Membahas senam aerobik: manfaat bagi jantung dan kebugaran, tahapan gerakan, "
        "serta pengaturan irama latihan.",
    "Sepak Bola":
        "Mengulas sepak bola dari sejarah, posisi pemain, teknik dasar, hingga peraturan "
        "pertandingan yang berlaku.",
    "Teknik Bermain Catur (Tingkat Permulaan)":
        "Panduan catur untuk pemula: pengenalan buah dan langkahnya, pembukaan dasar, "
        "serta taktik sederhana untuk memenangkan permainan.",
    "Teori Bermain Catur":
        "Membahas teori permainan catur meliputi pembukaan, permainan tengah, dan akhir, "
        "beserta prinsip strategi yang mendasarinya.",

    # ── Sains ────────────────────────────────────────────────────────────────
    "Air Hujan sebagai Air Bersih":
        "Membahas pemanenan air hujan sebagai sumber air bersih, mulai dari cara "
        "menampung, menyaring, hingga menyimpannya dengan aman.",
    "Air Udara Cuaca":
        "Menjelaskan keterkaitan air, udara, dan cuaca, termasuk siklus air serta "
        "unsur-unsur yang membentuk kondisi cuaca.",
    "Alam Semesta":
        "Mengajak pembaca mengenal alam semesta: benda-benda langit, galaksi, dan teori "
        "tentang asal mulanya.",
    "Atmosfer dan Pengaruhnya terhadap Kehidupan":
        "Menguraikan lapisan atmosfer dan fungsinya melindungi bumi, serta pengaruhnya "
        "terhadap cuaca dan kehidupan makhluk hidup.",
    "Ayo Siaga Bencana!":
        "Membekali pembaca dengan pengetahuan menghadapi bencana: mengenali ancaman, "
        "menyiapkan perlengkapan, dan langkah evakuasi yang tepat.",
    "Belajar Sains dengan Komputer":
        "Menunjukkan cara memanfaatkan komputer untuk mempelajari sains, dari simulasi "
        "sederhana hingga pengolahan data percobaan.",
    "Bentuk - Bentuk Muka Bumi":
        "Mengenalkan ragam bentuk permukaan bumi seperti gunung, lembah, dan dataran, "
        "beserta proses alam yang membentuknya.",
    "Berat, Waktu dan Pengukuran":
        "Membahas pengukuran berat dan waktu beserta satuan dan alat ukurnya, dilengkapi "
        "latihan konversi antar satuan.",
    "Berpetualang di Dasar Laut":
        "Mengajak pembaca menyelami dasar laut untuk mengenal terumbu karang, palung, "
        "dan makhluk yang hidup di kedalaman.",
    "Biogas Kotoran Ternak":
        "Menjelaskan pembuatan biogas dari kotoran ternak sebagai energi alternatif, "
        "mulai dari prinsip kerja hingga manfaat bagi lingkungan.",
    "Gurun dan Gunung":
        "Membahas ciri lingkungan gurun dan pegunungan, serta bagaimana tumbuhan, hewan, "
        "dan manusia menyesuaikan diri di dalamnya.",
    "Hutan":
        "Mengenalkan jenis-jenis hutan, kehidupan di dalamnya, dan perannya bagi iklim "
        "serta ketersediaan air.",
    "Indahnya Hujan dan Pelangi":
        "Menjelaskan proses terjadinya hujan dan pelangi, dari penguapan hingga "
        "pembiasan cahaya oleh titik air.",
    "Kehidupan di Air":
        "Membahas kehidupan di perairan tawar dan laut, mulai dari rantai makanan hingga "
        "penyesuaian makhluk hidup terhadap lingkungannya.",
    "Konservasi Lingkungan":
        "Menguraikan upaya pelestarian lingkungan, penyebab kerusakan alam, dan langkah "
        "nyata yang dapat dilakukan sehari-hari.",
    "Memahami Sains dari Alam: Gunung":
        "Mengulas gunung dari sudut pandang sains: proses pembentukan, jenis, dan "
        "gejala vulkanik yang menyertainya.",
    "Memahami Sains di Sekitar Rumah":
        "Menunjukkan penerapan prinsip sains pada benda dan peristiwa di rumah, dari "
        "peralatan dapur hingga instalasi listrik sederhana.",
    "Mengenal Laut Indonesia":
        "Memperkenalkan laut Indonesia: luas wilayah, kekayaan hayati, dan perannya bagi "
        "kehidupan serta perekonomian.",
    "Pemanasan Global dan Dampaknya":
        "Menjelaskan penyebab pemanasan global, dampaknya pada iklim dan permukaan laut, "
        "serta upaya menekan emisi gas rumah kaca.",
    "Tanaman Penghasil Bahan Bakar":
        "Membahas tanaman yang dapat diolah menjadi bahan bakar nabati, proses "
        "pengolahannya, dan potensinya sebagai energi terbarukan.",
    "Tanaman: Proyek Sains yang Menarik":
        "Menyajikan rangkaian proyek sains seputar tanaman yang bisa dikerjakan siswa, "
        "dari perkecambahan hingga pengaruh cahaya pada pertumbuhan.",
    "Yuk Belajar Peta":
        "Mengenalkan cara membaca peta: simbol, skala, arah mata angin, dan koordinat, "
        "beserta latihan menentukan lokasi.",

    # ── Sejarah ──────────────────────────────────────────────────────────────
    "Amangkurat: Mendung Memekat di Langit Mataram":
        "Menelusuri masa pemerintahan Amangkurat di Kesultanan Mataram beserta gejolak "
        "politik yang menyertainya.",
    "Kutukan Firaun":
        "Mengulas kisah dan kepercayaan seputar kutukan firaun yang dikaitkan dengan "
        "pembukaan makam kuno Mesir, ditelusuri dari catatan peristiwanya.",
    "Mohammad Hatta":
        "Riwayat Mohammad Hatta, proklamator dan wakil presiden pertama Indonesia, "
        "beserta pemikirannya tentang ekonomi kerakyatan dan koperasi.",
    "Peradaban Inggris":
        "Menelusuri perkembangan peradaban Inggris: sejarah, budaya, dan pengaruhnya "
        "terhadap dunia. Bagian dari seri peradaban bangsa.",
    "Peradaban Jepang":
        "Mengulas peradaban Jepang mulai dari pola pikir, budaya, hingga adat yang masih "
        "dipelihara sampai kini, disertai ilustrasi pendukung.",
    "Peradaban Nusantara":
        "Menelusuri jejak peradaban di Nusantara, dari kerajaan-kerajaan awal hingga "
        "warisan budaya yang membentuk Indonesia.",
    "Peradaban Skotlandia":
        "Memperkenalkan sejarah dan budaya Skotlandia, termasuk tradisi khas yang "
        "membedakannya dari wilayah lain di Britania.",
    "Peradaban Turki":
        "Mengulas peradaban Turki sebagai persimpangan Asia dan Eropa, meliputi sejarah, "
        "budaya, dan peninggalannya.",
    "Tokoh Penerima Penghargaan Nobel":
        "Memperkenalkan tokoh-tokoh peraih Nobel dari berbagai bidang beserta penemuan "
        "dan sumbangan mereka bagi kemanusiaan.",

    # ── Teknologi ────────────────────────────────────────────────────────────
    "Belajar Memperbaiki Sepeda":
        "Panduan praktis merawat dan memperbaiki sepeda, dari menambal ban hingga "
        "menyetel rem dan rantai.",
    "Industri Kecil dan Menengah":
        "Membahas peran industri kecil dan menengah bagi perekonomian, jenis usahanya, "
        "serta tantangan yang dihadapi pelakunya.",
    "Industrialisasi":
        "Menjelaskan proses industrialisasi, dampaknya terhadap masyarakat dan "
        "lingkungan, serta arah perkembangannya di Indonesia.",
    "Memahami Teknologi Populer 5":
        "Mengulas teknologi yang akrab dalam keseharian beserta cara kerjanya, disajikan "
        "ringkas untuk pembaca pemula.",
    "Membuat Gambar Vektor dengan CorelDRAW X3":
        "Panduan menggambar vektor menggunakan CorelDRAW X3, dari pengenalan perkakas "
        "hingga membuat objek dan mengatur warna.",
    "Mengenal Istilah Komputer A-Z":
        "Kamus ringkas istilah komputer yang disusun menurut abjad, membantu pembaca "
        "memahami kata-kata teknis yang sering dijumpai.",
    "Menyunting Video dengan Adobe Premiere":
        "Panduan dasar menyunting video di Adobe Premiere, meliputi pemotongan klip, "
        "transisi, penambahan teks, dan proses ekspor.",
    "Teknik Membuat Kompor":
        "Menjelaskan prinsip kerja dan cara membuat kompor sederhana, termasuk pemilihan "
        "bahan dan aspek keselamatan penggunaannya.",
}
