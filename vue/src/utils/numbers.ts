const decimalNumber = new Intl.NumberFormat('nl-BE', {
  style: 'decimal',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatCurrency(amount: number, symbol?: string): string {
  if (!symbol) symbol = '€';
  return `${symbol} ${amount.toLocaleString('nl-BE')}`;
}

export function formatDecimal(amount: number): string {
  return decimalNumber.format(amount);
}
