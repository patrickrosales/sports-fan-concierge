/**
 * Renders `**bold**` spans in otherwise-plain agent-generated text. The coordinator's
 * summary/recommendation fields are plain strings (not full markdown output_types), but
 * the model still reaches for ** occasionally -- this covers that one case without pulling
 * in a full markdown parser for a single inline mark.
 */
export function renderBold(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    return part
  })
}
