// enlace de invitación (iteración 45): /unete/<código al azar>

const INVITE_PATH = /^\/unete\/([\w-]+)\/?$/;

export const inviteCodeFromPath = (path: string): string | null => INVITE_PATH.exec(path)?.[1] ?? null;

export const inviteLink = (origin: string, code: string): string => `${origin}/unete/${code}`;

export const inviteShareText = (link: string): string =>
  `Hola, compro las verduras de la semana con Yapa: pagamos precio de mayorista entre vecinos y lo que ahorramos nos vuelve. Entra con mi enlace, te registras en un minuto y quedas en mi zona: ${link}`;

export const whatsappShareUrl = (text: string): string => `https://wa.me/?text=${encodeURIComponent(text)}`;

const PHONE = /^9\d{8}$/;
export const isValidPhone = (phone: string): boolean => PHONE.test(phone);
export const isWeakPin = (pin: string): boolean => {
  if (!/^\d{6}$/.test(pin)) return true;
  const steps = new Set([...pin].slice(1).map((digit, index) => Number(digit) - Number(pin[index])));
  return steps.size === 1 && [0, 1, -1].includes([...steps][0]);
};
