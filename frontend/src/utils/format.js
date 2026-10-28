// Prices render as $12.34, or N/A when the API has no value
export const formatPrice = (value) =>
  value === null || value === undefined ? 'N/A' : `$${value.toFixed(2)}`;
