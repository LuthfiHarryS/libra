// Password field dengan toggle show/hide (icon mata). Konsisten styling
// dengan FormInput di Login/Register sehingga bisa drop-in.
import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

interface Props {
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  placeholder?: string
  hasError?: boolean
  autoComplete?: string
}

function PasswordInput({ value, onChange, placeholder, hasError, autoComplete }: Props) {
  const [focused, setFocused]   = useState(false)
  const [visible, setVisible]   = useState(false)

  return (
    <div className="relative">
      <input
        type={visible ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        style={{
          width: '100%',
          padding: '12px 44px 12px 14px',
          border: `1.5px solid ${hasError ? 'var(--unavail)' : focused ? 'var(--accent)' : 'var(--border)'}`,
          borderRadius: '10px',
          background: 'var(--bg-input)',
          color: 'var(--text)',
          fontFamily: 'var(--font-ui)',
          fontSize: '14px',
          fontWeight: 500,
          outline: 'none',
          transition: 'border-color var(--transition), box-shadow var(--transition)',
          boxShadow: focused && !hasError ? '0 0 0 3px rgba(217,119,6,.15)' : 'none',
        }}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
      />
      <button
        type="button"
        onClick={() => setVisible(v => !v)}
        aria-label={visible ? 'Sembunyikan password' : 'Tampilkan password'}
        tabIndex={-1}
        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded transition-colors"
        style={{ color: 'var(--text-3)' }}
        onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--text)' }}
        onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-3)' }}
      >
        {visible ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  )
}

export default PasswordInput
