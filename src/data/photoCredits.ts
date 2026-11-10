// fotos de productos tomadas de Wikimedia Commons (2026-11-10); las licencias CC piden nombrar al autor y la licencia
export interface PhotoCredit {
  product: string;
  author: string;
  license: string;
  licenseUrl: string | null;
  source: string;
}

export const photoCredits: PhotoCredit[] = [
  { product: 'Papa blanca', author: 'ZooFari', license: 'Dominio público', licenseUrl: null, source: 'https://commons.wikimedia.org/wiki/File:Potato_with_sprouts.jpg' },
  { product: 'Cebolla roja', author: 'Anja', license: 'CC BY-SA 4.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0', source: 'https://commons.wikimedia.org/wiki/File:Three_whole_red_onions.jpg' },
  { product: 'Ajo criollo', author: 'Dubravko Sorić (SoraZG en Flickr)', license: 'CC BY 2.0', licenseUrl: 'https://creativecommons.org/licenses/by/2.0', source: 'https://commons.wikimedia.org/wiki/File:Opened_garlic_bulb_with_garlic_clove.jpg' },
  { product: 'Limón', author: 'Jiafei Slay Queen', license: 'CC0', licenseUrl: 'https://creativecommons.org/publicdomain/zero/1.0/', source: 'https://commons.wikimedia.org/wiki/File:Limes_with_halves.jpg' },
  { product: 'Camote amarillo', author: 'Petr Kratochvil', license: 'Libre con atribución', licenseUrl: null, source: 'https://commons.wikimedia.org/wiki/File:SweetPotato.jpg' },
  { product: 'Zanahoria', author: 'Collegestudent33', license: 'CC BY-SA 4.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0', source: 'https://commons.wikimedia.org/wiki/File:Carrot-fb.jpg' },
];
