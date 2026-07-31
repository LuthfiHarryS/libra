import { useEffect } from 'react'

const SUFIKS = 'LIBRA — Perpustakaan Digital SMPN 1 Kemang'

/**
 * Menetapkan <title> dan <meta name="description"> per halaman.
 *
 * index.html hanya memuat satu judul statis, sehingga seluruh halaman buku
 * tampil dengan judul yang sama di hasil pencarian. Mesin telusur umumnya
 * memperlakukan halaman berjudul kembar tanpa deskripsi sebagai duplikat dan
 * tidak mengindeksnya, sehingga sitemap berisi ratusan URL buku menjadi
 * percuma tanpa pembeda ini.
 *
 * Judul dikembalikan ke nilai semula saat komponen dilepas, supaya berpindah
 * halaman lewat navigasi sisi klien tidak meninggalkan judul halaman lama.
 */
export function useJudulHalaman(judul?: string | null, deskripsi?: string | null) {
  useEffect(() => {
    const sebelumnya = document.title
    document.title = judul ? `${judul} — ${SUFIKS}` : SUFIKS

    let tag = document.querySelector<HTMLMetaElement>('meta[name="description"]')
    const adaSebelumnya = tag !== null
    const isiSebelumnya = tag?.content ?? ''

    if (deskripsi) {
      if (!tag) {
        tag = document.createElement('meta')
        tag.name = 'description'
        document.head.appendChild(tag)
      }
      tag.content = deskripsi
    }

    return () => {
      document.title = sebelumnya
      if (!tag) return
      if (adaSebelumnya) tag.content = isiSebelumnya
      else tag.remove()
    }
  }, [judul, deskripsi])
}

export default useJudulHalaman
