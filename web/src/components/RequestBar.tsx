import { useState } from 'react'

const EXAMPLES = [
  'A Raptors night with good seats and dinner nearby',
  'Leafs game with transit tips from downtown',
  'Cheapest Blue Jays tickets this month',
  'Raptors or Leafs this weekend -- which is the better night out?',
]

interface Props {
  onSubmit: (query: string) => void
  disabled: boolean
}

export function RequestBar({ onSubmit, disabled }: Props) {
  const [value, setValue] = useState('')

  function submit(text: string) {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit(value)
        }}
        className="flex items-center gap-2 rounded-lg border border-linear-border bg-linear-surface/60 px-4 py-3 shadow-sm backdrop-blur-sm focus-within:ring-2 focus-within:ring-accent-500/40 focus-within:border-accent-700"
      >
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="I want to catch a game next week…"
          disabled={disabled}
          className="flex-1 bg-transparent outline-none text-sm text-linear-text placeholder:text-linear-text-quaternary"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="shrink-0 rounded-md bg-accent-500 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-accent-400 disabled:cursor-not-allowed disabled:bg-linear-surface-hover disabled:text-linear-text-quaternary"
        >
          Plan my night
        </button>
      </form>

      <div className="mt-3 flex flex-wrap justify-center gap-2">
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            disabled={disabled}
            onClick={() => {
              setValue(example)
              submit(example)
            }}
            className="rounded-full border border-linear-border px-3 py-1 text-xs text-linear-text-tertiary transition-colors hover:border-accent-600 hover:text-accent-300 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  )
}
