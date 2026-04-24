import MarkdownIt from 'markdown-it'

/**
 * Shared markdown renderer. Configured for permissive content (linkify, typographer)
 * with safe defaults (html disabled — untrusted sources are possible).
 *
 * Used by cooking technique bodies and available for future adoption by articles,
 * recipe notes, and book reviews.
 */
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: false,
})

export function renderMarkdown(text: string): string {
  return md.render(text ?? '')
}

export function renderMarkdownInline(text: string): string {
  return md.renderInline(text ?? '')
}
