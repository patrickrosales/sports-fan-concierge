import { useState } from 'react'

const EXAMPLES = [
  'A Raptors night with good seats and dinner nearby',
  'Leafs game with transit tips from downtown',
  'Cheapest Blue Jays tickets this month',
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
        className="flex items-center gap-2 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 px-4 py-3 shadow-sm focus-within:ring-2 focus-within:ring-indigo-500/40"
      >
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="I want to catch a game next week…"
          disabled={disabled}
          className="flex-1 bg-transparent outline-none text-sm text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="shrink-0 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-neutral-300 dark:disabled:bg-neutral-700"
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
            className="rounded-full border border-neutral-200 dark:border-neutral-800 px-3 py-1 text-xs text-neutral-500 dark:text-neutral-400 transition-colors hover:border-indigo-400 hover:text-indigo-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  )
}
