export interface PhotoCandidate { id: string; name: string; unit?: string }
export function photoKind(text: string): string {
  const plain = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  for (const kind of ['zanahoria', 'cebolla', 'camote', 'limon', 'papa', 'ajo']) if (plain.includes(kind)) return kind;
  return 'otro';
}
export function matchPhotoProduct(detected: string, candidates: PhotoCandidate[]): string {
  const matches = candidates.filter(p => photoKind(p.name) === detected || photoKind(p.id) === detected);
  return matches.length === 1 ? matches[0].id : '';
}
