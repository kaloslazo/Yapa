import { describe, expect, it } from 'vitest';
import { inviteCodeFromPath, inviteLink, inviteShareText, isValidPhone, isWeakPin, whatsappShareUrl } from './invite';

describe('enlace de invitación', () => {
  it('reconoce el código en la dirección', () => {
    expect(inviteCodeFromPath('/unete/aB3-x_9Zq')).toBe('aB3-x_9Zq');
    expect(inviteCodeFromPath('/unete/aB3-x_9Zq/')).toBe('aB3-x_9Zq');
  });

  it('no confunde otras direcciones', () => {
    for (const path of ['/', '/unete', '/unete/', '/unete/a/b', '/otra/abc', '/#unete/abc']) expect(inviteCodeFromPath(path)).toBeNull();
  });

  it('arma el enlace y el mensaje para WhatsApp con el enlace dentro', () => {
    const link = inviteLink('https://holayapa.app', 'abc123XY');
    expect(link).toBe('https://holayapa.app/unete/abc123XY');
    expect(inviteShareText(link)).toContain(link);
    expect(decodeURIComponent(whatsappShareUrl(inviteShareText(link)).split('text=')[1])).toContain(link);
  });
});

describe('datos del registro', () => {
  it('el celular son 9 dígitos y empieza con 9', () => {
    expect(isValidPhone('987654321')).toBe(true);
    for (const phone of ['812345678', '98765432', '9876543210', '98765432a', '']) expect(isValidPhone(phone)).toBe(false);
  });

  it('el PIN no puede ser flojo (como en el motor)', () => {
    for (const pin of ['123456', '654321', '111111', '12345', 'abcdef']) expect(isWeakPin(pin)).toBe(true);
    for (const pin of ['739104', '482915']) expect(isWeakPin(pin)).toBe(false);
  });
});
