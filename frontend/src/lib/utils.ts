import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export function formatCurrency(value: number | undefined): string {
	const v = value ?? 0;
	if (v >= 1_000_000_000) {
		return `$${(v / 1_000_000_000).toFixed(1)}B`;
	}
	if (v >= 1_000_000) {
		return `$${(v / 1_000_000).toFixed(1)}M`;
	}
	if (v >= 1_000) {
		return `$${(v / 1_000).toFixed(1)}K`;
	}
	return `$${v.toFixed(0)}`;
}

export function formatNumber(value: number | undefined): string {
	return (value ?? 0).toLocaleString();
}

export function formatPercent(value: number | undefined): string {
	return `${(value ?? 0).toFixed(1)}%`;
}
