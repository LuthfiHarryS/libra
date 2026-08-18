// CHAT-01: Floating chat widget — FAB + panel, visible to authenticated siswa only
// Chatbot: layanan Flask pada port 5001, endpoint /chat.
// Request  {message, riwayat} -> Response {intent, confidence, reply, sumber}
// Balasan disusun dari tabel REPLIES per intent di sisi layanan, bukan model generatif.
import { useState, useEffect, useRef } from 'react'
import { MessageCircle, X, Send } from 'lucide-react'
import axios from 'axios'
import type { ChatMessage } from '../types'

// Default relatif: di produksi Nginx mem-proxy /chat ke Flask:5001 pada origin yang
// sama, sehingga tidak ada mixed-content (halaman HTTPS memanggil HTTP) dan tidak
// perlu CORS. Untuk dev, override lewat VITE_CHATBOT_URL di .env.local.
const CHATBOT_URL = (import.meta.env.VITE_CHATBOT_URL as string | undefined)
  ?? '/chat'

interface ChatResponse {
  intent: string
  confidence: number
  reply: string
}

function TypingDots() {
  return (
    <div className="flex gap-1 items-center px-3.5 py-2.5 w-fit" style={{ background: 'var(--bg-subtle)', borderRadius: '18px', borderBottomLeftRadius: '4px' }}>
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="block rounded-full animate-bounce"
          style={{ width: 6, height: 6, background: 'var(--text-3)', animationDelay: `${i * 0.15}s`, animationDuration: '0.8s' }}
        />
      ))}
    </div>
  )
}

// Contoh pertanyaan yang ditampilkan sebagai tombol saat chat pertama dibuka.
//
// Dipilih bentuk tombol, bukan paragraf panduan: siswa SMP cenderung mengetuk
// daripada membaca instruksi. Tiap tombol juga mencontohkan SATU kemampuan bot,
// sehingga siswa belajar apa yang bisa ditanyakan hanya dengan melihatnya.
//
// Kalimatnya sengaja memakai bahasa sehari-hari ("ada ... nggak") — persis
// bentuk yang dilatih di dataset, jadi peluang dikenali paling tinggi.
const SARAN_PERTANYAAN = [
  'Ada buku komik nggak?',
  'Gimana cara pinjam buku?',
  'Buku apa yang bagus?',
  'Perpus buka jam berapa?',
]

function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Saran hanya muncul sebelum siswa mengirim pesan pertama, supaya tidak
  // memenuhi layar saat percakapan sudah berjalan.
  const tampilkanSaran = messages.length <= 1 && !isLoading

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{
        role: 'bot',
        text: 'Hai! Aku asisten LIBRA 📚\n\nAku bisa bantu kamu cari buku, kasih rekomendasi, atau jelaskan cara pinjam. Coba ketuk salah satu pertanyaan di bawah, atau tulis sendiri pakai bahasamu.',
      }])
    }
  }, [isOpen, messages.length])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async (pesanLangsung?: string) => {
    const userMsg = (pesanLangsung ?? input).trim()
    if (!userMsg || isLoading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setIsLoading(true)

    try {
      // Riwayat ikut dikirim supaya pertanyaan lanjutan seperti "jelaskan
      // lebih detail" punya rujukan. Layanan chat tidak menyimpan sesi, jadi
      // percakapan hanya hidup selama panel ini terbuka.
      const riwayat = messages.map(m => ({
        peran: m.role === 'user' ? 'siswa' : 'libra',
        teks: m.text,
      }))
      const res = await axios.post<ChatResponse>(CHATBOT_URL, {
        message: userMsg,
        riwayat,
      })
      setMessages(prev => [...prev, { role: 'bot', text: res.data.reply }])
    } catch (err) {
      console.error('[ChatWidget] chatbot error:', err)
      setMessages(prev => [...prev, { role: 'bot', text: 'Maaf, asisten sedang tidak tersedia. Coba lagi nanti.' }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* Chat panel */}
      <div
        className={`fixed bottom-[76px] right-4 z-50 flex flex-col transition-all duration-200 origin-bottom-right ${
          isOpen ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'
        }`}
        style={{ width: 340, height: 440, background: 'var(--bg-card)', border: '1.5px solid var(--border)', borderRadius: '24px', boxShadow: 'var(--shadow-lg)', overflow: 'hidden' }}
      >
        {/* Header */}
        <div className="flex items-center gap-2.5 px-4 py-3 flex-shrink-0 border-b" style={{ background: 'var(--bg-subtle)', borderColor: 'var(--border)' }}>
          <div
            className="w-9 h-9 rounded-full flex items-center justify-center text-lg flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--accent) 0%, var(--brand) 100%)' }}
          >
            
          </div>
          <div>
            <p className="text-sm font-extrabold" style={{ color: 'var(--text)' }}>Asisten LIBRA</p>
            <p className="text-[11px] font-semibold" style={{ color: 'var(--avail)' }}>● Online</p>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="ml-auto p-1.5 rounded-full transition-colors"
            style={{ color: 'var(--text-3)' }}
            aria-label="Tutup chat"
          >
            <X size={16} />
          </button>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2.5">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className="max-w-[78%] text-[13px] font-medium leading-relaxed px-3.5 py-2.5 whitespace-pre-line"
                style={msg.role === 'user'
                  ? { background: 'var(--accent)', color: '#fff', borderRadius: '18px', borderBottomRightRadius: '4px' }
                  : { background: 'var(--bg-subtle)', color: 'var(--text)', borderRadius: '18px', borderBottomLeftRadius: '4px' }
                }
              >
                {msg.text}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <TypingDots />
            </div>
          )}

          {/* Tombol saran — mengajarkan kemampuan bot tanpa perlu dibaca */}
          {tampilkanSaran && (
            <div className="flex flex-col gap-1.5 mt-1">
              {SARAN_PERTANYAAN.map(saran => (
                <button
                  key={saran}
                  onClick={() => handleSend(saran)}
                  className="text-left text-[12.5px] font-semibold px-3 py-2 transition-all duration-150 w-fit max-w-[85%]"
                  style={{
                    background: 'transparent',
                    color: 'var(--accent)',
                    border: '1.5px solid var(--accent)',
                    borderRadius: '14px',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'var(--accent)'
                    e.currentTarget.style.color = '#fff'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'transparent'
                    e.currentTarget.style.color = 'var(--accent)'
                  }}
                >
                  {saran}
                </button>
              ))}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="flex gap-2 items-center px-3 py-3 flex-shrink-0 border-t" style={{ borderColor: 'var(--border)' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Tanya apa aja soal buku..."
            className="flex-1 px-3.5 py-2 text-[13px] font-medium transition-all duration-200"
            style={{
              background: 'var(--bg-input)',
              border: '1.5px solid var(--border)',
              borderRadius: '999px',
              color: 'var(--text)',
              fontFamily: 'var(--font-ui)',
              outline: 'none',
            }}
            onFocus={e => { e.currentTarget.style.borderColor = 'var(--accent)' }}
            onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)' }}
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 text-white transition-all duration-200 disabled:opacity-40"
            style={{ background: 'var(--accent)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent-h)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent)' }}
          >
            <Send size={15} />
          </button>
        </div>
      </div>

      {/* FAB button */}
      <button
        onClick={() => setIsOpen(prev => !prev)}
        className="fixed bottom-4 right-4 z-50 w-14 h-14 rounded-full flex items-center justify-center text-white transition-all duration-200"
        style={{ background: 'var(--accent)', boxShadow: '0 4px 20px rgba(217,119,6,.4)' }}
        onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1.08)'; (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent-h)' }}
        onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)'; (e.currentTarget as HTMLButtonElement).style.background = 'var(--accent)' }}
        aria-label={isOpen ? 'Tutup chat' : 'Buka chat'}
      >
        <MessageCircle size={24} />
      </button>
    </>
  )
}

export default ChatWidget
