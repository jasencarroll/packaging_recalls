import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface KPICardProps {
	label: string;
	value: string;
	accentColor?: string;
}

export default function KPICard({ label, value, accentColor }: KPICardProps) {
	return (
		<Card className="relative overflow-hidden">
			{accentColor && (
				<div
					className="absolute top-0 left-0 h-1 w-full"
					style={{ backgroundColor: accentColor }}
				/>
			)}
			<CardContent className="p-6">
				<p className="text-sm text-text-muted">{label}</p>
				<p
					className={cn('mt-2 text-3xl font-bold')}
					style={accentColor ? { color: accentColor } : undefined}
				>
					{value}
				</p>
			</CardContent>
		</Card>
	);
}
