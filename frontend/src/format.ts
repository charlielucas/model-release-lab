export function percent(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

export function shortDigest(value: string): string {
  return `${value.slice(0, 10)}...${value.slice(-6)}`;
}
