// iteraciones 77 y 78: la foto que va a la IA sale siempre como JPEG sobre fondo blanco y de tamaño acotado.
// Un PNG o WebP con fondo transparente se leyó mal (S-387); achicarla gasta menos cupo y sube más rápido (S-378).
export const BAG_SIDE = 1024;
export const QUOTE_SIDE = 1600; // la cotización necesita que se lean los precios
const SMALL_ENOUGH = 1_500_000; // bytes

export async function photoForAI(file: File, maxSide = BAG_SIDE): Promise<File> {
  if (typeof createImageBitmap !== 'function' || typeof document === 'undefined') return file;
  try {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
    if (file.type === 'image/jpeg' && scale === 1 && file.size < SMALL_ENOUGH) {
      bitmap.close();
      return file; // un JPEG no tiene transparencia: si ya es chico, va tal cual
    }
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    const context = canvas.getContext('2d');
    if (!context) return file;
    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.85));
    return blob ? new File([blob], 'foto.jpg', { type: 'image/jpeg' }) : file;
  } catch {
    return file; // si el navegador no puede, va la original
  }
}
