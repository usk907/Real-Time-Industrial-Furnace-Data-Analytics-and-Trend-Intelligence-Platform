/**
 * IEIP Industrial Formatters & Utility Functions
 */

export function formatNumber(val: number | null | undefined, decimals = 1): string {
  if (val === null || val === undefined || isNaN(val)) return '0.0';
  return Number(val).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

export function formatPower(kw: number | null | undefined): string {
  if (kw === null || kw === undefined || isNaN(kw)) return '0.0 kW';
  if (Math.abs(kw) >= 1000) {
    return `${(kw / 1000).toFixed(2)} MW`;
  }
  return `${kw.toFixed(1)} kW`;
}

export function formatEnergy(kwh: number | null | undefined): string {
  if (kwh === null || kwh === undefined || isNaN(kwh)) return '0.0 kWh';
  if (Math.abs(kwh) >= 1_000_000) {
    return `${(kwh / 1_000_000).toFixed(2)} GWh`;
  }
  if (Math.abs(kwh) >= 1000) {
    return `${(kwh / 1000).toFixed(2)} MWh`;
  }
  return `${kwh.toFixed(1)} kWh`;
}

export function formatCurrency(amount: number | null | undefined, symbol = '₹'): string {
  if (amount === null || amount === undefined || isNaN(amount)) return `${symbol}0`;
  return `${symbol}${Number(amount).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

export function formatTimestamp(dateInput: string | Date | null | undefined): string {
  if (!dateInput) return '-';
  const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
  if (isNaN(d.getTime())) return '-';
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

export function formatPercent(val: number | null | undefined, decimals = 1): string {
  if (val === null || val === undefined || isNaN(val)) return '0.0%';
  return `${val.toFixed(decimals)}%`;
}

export function formatPf(pf: number | null | undefined): string {
  if (pf === null || pf === undefined || isNaN(pf)) return '0.000';
  return pf.toFixed(3);
}
