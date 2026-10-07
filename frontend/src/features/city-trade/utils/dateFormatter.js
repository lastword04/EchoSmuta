import { parseUtcDate } from '../../../shared/lib/utils/utcDate';

export const formatLicenseTime = (endLicense) => {
  if (!endLicense) return "—";
  const now = Date.now();
  const end = parseUtcDate(endLicense);
  const diff = end - now;
  if (diff <= 0) return "истёк";
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  return `${days}дн. ${String(hours).padStart(2, '0')}ч. ${String(minutes).padStart(2, '0')}мин.`;
};

export const formatWear = (item) => {
  const maxWear = item.max_wear ?? item.parameters?.max_wear;
  if (maxWear === null || maxWear === undefined) return "—";
  const wear = item.wear ?? 0;
  return `[${wear}/${maxWear}]`;
};