# Data Samples — Real MBG Tweets with Analysis Labels

The following are **real tweets** from the MBG discourse corpus, shown with their sentiment labels, topic assignments, and engagement metrics. These demonstrate the actual data being analyzed.

**Source file:** `tweets_with_topics.csv` (107,039 rows)
**Columns shown:** Text, Sentiment, Topic ID, Engagement, Language

Tweet texts are in Indonesian (the dominant language, >90% of corpus). Some tweets tag other users; @usernames are preserved as in the original data. Topic ID -1 indicates outlier/unassigned.

## Tweet Samples

| Tweet Text | Sentiment | Topic | Engagement | Lang |
|---|---|---|---|---|
| @ai2a_n -minta keadilan dr pemerintah krn sejomplang itu. Dan mbg itu guru g dapat bayaran tambahan tp mrk yg kerja kayak nata ompreng, ngabsen, iya k | negative | 2 | 1 | id |
| Anjir, dikata kurang gizi 😭😭😭 terus lu kasih mbg gitu solusinya? Gila anjir lu gila pemerintah 😭 | negative | 1 | 0 | id |
| @ARSIPAJA Punya intelijen kok kasus MBG keracunan dan bencana di Aceh blm beres kok gak nyampe ke bapak | negative | -1 | 0 | id |
| @Mdy_Asmara1701 saya lebih setuju usulan KDM dari pada MBG di korup mending uangnya kasih ke ortunya 15rb/hari kali berapa kali masuk sekolah misal se | negative | 2 | 20 | id |
| PROFESOR ANTHONY BUDIAWAN: BADAN GIZI NASIONAL DI BENTUK JOKOWI  ***Walaaaah... | positive | 1 | 0 | so |
| Seskab Teddy tegaskan pemerintah terus melakukan perbaikan dalam program MBG. | neutral | -1 | 6 | id |
| kenalin nih, Marsekal Mohamad Tony Harjono, Kstaf TNI AU. Algojo alias Eksekutor dibalik seluruh Bencana Masiv akibat OMC Chemtrail diseluruh Indones | positive | 0 | 4652 | id |
| mendengar cerita mengenai polisi yang bercocok tanam dan mengatur MBG efisiensi bisa lebih mantap lagi dengan menghapus kementerian pertanian, badan | positive | 1 | 0 | id |
| terharu lihat relawan SPPG ini beneran keliling laut buat nganterin paket MBG ke sekolah-sekolah di pulau kecil. Dedikasinya nyata banget—anak-anak nu | positive | -1 | 0 | id |
| Luhut Yakin Anggaran MBG Dipakai Sangat Baik: Menkeu Tak Perlu Tarik Dana | neutral | -1 | 148 | id |
| @ARSIPAJA Lha mubadzir donk? Mbg buat anak sekolah aja banyakan kebuang apa lagi pas libur sekolah? Ini bukan program bodoh lagi,program sakit jiwa | negative | 2 | 9696 | id |
| Makanan yang bergizi menunjang kemampuan anak2 dalam berpikir, karna perkembangan otak salah satunya dari asupan makanan yg baik, MARI SAMA2 KITA DUKU | positive | -1 | 1 | id |
| Itu duit mbg bayangin tiap hari berapa, kalo dialokasiin ke infrastruktur ato kesejahteraan masyarakat instead of jadi 💩, bikin keracunan dan lahan ko | negative | 1 | 0 | id |
| Program Makan Bergizi Gratis (MBG) yang telah berjalan lebih dari enam bulan di Posyandu Pos 1 Desa Radamata, Sumba Barat Daya, NTT | positive | -1 | 0 | id |
| @BosPurwa @prabowo Harus jelas standar kemiskinan dihitung dari apa. Apakah biaya makan atau biaya hidup? | negative | -1 | 3 | id |
| Makan Bergizi Gratis Mencerdaskan Generasi Emas Papua. #PapuaBaratDaya #DukungMakanBergiziGratis | positive | 3 | 0 | id |
| Liverpool keracunan MBG. | negative | -1 | 0 | id |
| Wakil Ketua Komisi IX DPR RI Charles Honoris usul agar dana Makan Bergizi Gratis (MBG) diberikan langsung kepada orang tua, terutama untuk mencegah | neutral | -1 | 1 | id |

## Topic Examples (from `topic_info.csv`)

Topic labels extracted via BERTopic keyword analysis:

| Topic ID | Count | Sample Keywords |
|---|---|---|
| 0 | ~8,900 | politik, korupsi, anggaran, menteri, presiden |
| 1 | ~7,200 | keracunan, makanan, sehat, gizi, sekolah |
| 2 | ~6,100 | distribusi, daerah, papua, ntt, maluku |
| 3 | ~5,400 | positif, program, manfaat, anak, generasi |
| -1 | ~45,700 | (outliers — diverse low-frequency topics) |

## Corpus Statistics Summary

```
total_tweets:    107,039
date_from:       2017-03-10
date_to:         2026-04-17
pct_positive:    28.9%
pct_negative:    40.3%
pct_neutral:     30.8%
n_topics:        51
neg_amplification_significant: True
```

## Data Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Tweet ID |
| `text` | string | Tweet content |
| `created_at` | datetime | Tweet timestamp |
| `sentiment_normalized` | string | positive/negative/neutral |
| `sentiment_score` | float | Model confidence (0–1) |
| `topic_id` | int | Topic cluster ID (-1 = outlier) |
| `topic_prob` | float | Topic assignment probability |
| `engagement_total` | int | likes + retweets + replies |
| `favorite_count` | int | Likes |
| `retweet_count` | int | Retweets |
| `reply_count` | int | Reply count |
| `detected_lang` | string | Detected language |
| `predicted_label` | string | RELEVANT/NOT_RELEVANT |
| `predicted_confidence` | float | Relevance confidence |
