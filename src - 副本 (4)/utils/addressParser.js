/**
 * Simple address parsing helper.
 * Tries to split a single-line address into components that
 * match the AMLO report fields (number, road, district, province, postal code).
 * The implementation is heuristic-based to avoid blocking behaviour.
 */

export function splitAddress(address = '') {
  const result = {
    number: '',
    village: '',
    lane: '',
    road: '',
    subdistrict: '',
    district: '',
    province: '',
    postalcode: ''
  }

  if (!address || typeof address !== 'string') {
    return result
  }

  let working = address.trim()

  // Extract postal code (last 5 digits pattern)
  const postalMatch = working.match(/(\d{5})(?!.*\d{5})/)
  if (postalMatch) {
    result.postalcode = postalMatch[1]
    working = working.replace(postalMatch[1], '').trim()
  }

  // Split by comma or Thai punctuation
  const parts = working
    .split(/[,，]/)
    .map(part => part.trim())
    .filter(Boolean)

  if (parts.length === 0) {
    result.number = working
    return result
  }

  // Assign from rear: province, district, subdistrict if available
  if (parts.length >= 1) {
    result.province = parts.pop()
  }
  if (parts.length >= 1) {
    result.district = parts.pop()
  }
  if (parts.length >= 1) {
    result.subdistrict = parts.pop()
  }
  if (parts.length >= 1) {
    result.road = parts.pop()
  }

  // Remaining (if any) treat as number / building description
  if (parts.length > 0) {
    result.number = parts.join(', ')
  } else if (!result.number) {
    // fallback to the trimmed original if nothing assigned
    result.number = working
  }

  return result
}
