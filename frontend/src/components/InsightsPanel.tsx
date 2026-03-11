import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { useEffect, useState } from 'react';

interface DefectCost {
	defect: string;
	cost: number;
}

interface InsightsData {
	total_recalls: number;
	class_i_count: number;
	avg_resolution_days: number;
	most_common_defect: string;
	total_cost_impact: number;
	top_defects: { defect: string; count: number }[];
	cost_by_defect: DefectCost[];
	labeling_count: number;
	quality_count: number;
	packaging_count: number;
}

export default function InsightsPanel() {
	const [data, setData] = useState<InsightsData | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		fetch('/api/recalls/insights')
			.then((res) => {
				if (!res.ok) throw new Error(`HTTP ${res.status}`);
				return res.json();
			})
			.then(setData)
			.catch((err) => setError(err.message));
	}, []);

	if (error) {
		return (
			<Card>
				<CardContent className="p-6 text-danger">Failed to load insights: {error}</CardContent>
			</Card>
		);
	}

	if (!data) {
		return (
			<Card>
				<CardContent className="flex items-center justify-center p-12 text-text-muted">
					Loading...
				</CardContent>
			</Card>
		);
	}

	return (
		<div className="grid grid-cols-1 gap-6 md:grid-cols-2">
			<Card>
				<CardHeader>
					<CardTitle>Key Findings</CardTitle>
				</CardHeader>
				<CardContent>
					<div className="space-y-4">
						<InsightRow label="Total Recalls Analyzed" value={formatNumber(data.total_recalls)} />
						<InsightRow
							label="Class I (Most Serious)"
							value={formatNumber(data.class_i_count)}
							color="#ff6b6b"
						/>
						<InsightRow
							label="Avg Resolution Time"
							value={`${(data.avg_resolution_days ?? 0).toFixed(1)} days`}
						/>
						<InsightRow
							label="Most Common Defect"
							value={data.most_common_defect}
							color="#1f77b4"
						/>
						<InsightRow
							label="Total Estimated Cost Impact"
							value={formatCurrency(data.total_cost_impact)}
							color="#ffcc00"
						/>
						<div className="mt-6 border-t border-border pt-4">
							<p className="mb-3 text-sm font-semibold text-text-muted">
								Defect Category Breakdown
							</p>
							<InsightRow label="Labeling Issues" value={formatNumber(data.labeling_count)} />
							<InsightRow label="Quality Issues" value={formatNumber(data.quality_count)} />
							<InsightRow label="Packaging Issues" value={formatNumber(data.packaging_count)} />
						</div>
					</div>
				</CardContent>
			</Card>
			<div className="space-y-6">
				<Card>
					<CardHeader>
						<CardTitle>Top Defects</CardTitle>
					</CardHeader>
					<CardContent>
						<table className="w-full">
							<thead>
								<tr className="border-b border-border text-left text-sm text-text-muted">
									<th className="pb-2">Defect Type</th>
									<th className="pb-2 text-right">Count</th>
								</tr>
							</thead>
							<tbody>
								{data.top_defects.map((d) => (
									<tr key={d.defect} className="border-b border-border/50">
										<td className="py-2 text-sm">{d.defect}</td>
										<td className="py-2 text-right text-sm font-medium">{formatNumber(d.count)}</td>
									</tr>
								))}
							</tbody>
						</table>
					</CardContent>
				</Card>
				<Card>
					<CardHeader>
						<CardTitle>Cost by Defect Type</CardTitle>
					</CardHeader>
					<CardContent>
						<table className="w-full">
							<thead>
								<tr className="border-b border-border text-left text-sm text-text-muted">
									<th className="pb-2">Defect Type</th>
									<th className="pb-2 text-right">Est. Cost</th>
								</tr>
							</thead>
							<tbody>
								{data.cost_by_defect.map((d) => (
									<tr key={d.defect} className="border-b border-border/50">
										<td className="py-2 text-sm">{d.defect}</td>
										<td className="py-2 text-right text-sm font-medium text-warning">
											{formatCurrency(d.cost)}
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</CardContent>
				</Card>
			</div>
		</div>
	);
}

function InsightRow({ label, value, color }: { label: string; value: string; color?: string }) {
	return (
		<div className="flex items-center justify-between py-1">
			<span className="text-sm text-text-muted">{label}</span>
			<span className="text-sm font-semibold" style={color ? { color } : undefined}>
				{value}
			</span>
		</div>
	);
}
