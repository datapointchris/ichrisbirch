import type { RecipeIngredient } from '@/api/client'

const FRACTIONS: Record<number, string> = {
  0.125: '1/8',
  0.25: '1/4',
  0.375: '3/8',
  0.5: '1/2',
  0.625: '5/8',
  0.75: '3/4',
  0.875: '7/8',
}

/** The quantity at the current servings, as a cook reads it: 1/2 rather than 0.5, 2 rather than 2.0. */
export function displayQuantity(ing: Pick<RecipeIngredient, 'quantity' | 'scaled_quantity'>): string {
  const qty = ing.scaled_quantity ?? ing.quantity
  if (qty === null || qty === undefined) return ''
  const fraction = FRACTIONS[qty]
  if (fraction) return fraction
  if (Number.isInteger(qty)) return String(qty)
  return String(Math.round(qty * 100) / 100)
}

/** A unit key spelled for reading: `fl_oz` is fl oz. */
export function formatUnit(unit: string | null): string {
  if (!unit) return ''
  if (unit === 'to_taste') return 'to taste'
  if (unit === 'fl_oz') return 'fl oz'
  return unit
}

/** Quantity and unit together, empty when the ingredient has neither. */
export function ingredientAmount(ing: Pick<RecipeIngredient, 'quantity' | 'scaled_quantity' | 'unit'>): string {
  return [displayQuantity(ing), formatUnit(ing.unit)].filter(Boolean).join(' ')
}
