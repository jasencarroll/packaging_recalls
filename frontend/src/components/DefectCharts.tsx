import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEffect, useState } from 'react';
import {
	Bar,
	BarChart,
	CartesianGrid,
	Cell,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from 'recharts';

interface DefectItem {
	defect: string;
	count: number;
}

interface RiskLevel {
	level: string;
	count: number;
}

interface DefectsData {
	top_defects: DefectItem[];
	risk_levels: RiskLevel[];
}

const RISK_COLORS: Record<string, string> = {
	Critical: '#ff4444',
	High: '#ff8c00',
	Medium: '#ffcc00',
	Low: '#44ff44',
};

const DEFECT_GRADIENT = [
	'#ff6b6b',
	'#ff8787',
	'#ffa3a3',
	'#4ecdc4',
	'#6dd5cd',
	'#8cddd6',
	'#45b7d1',
	'#67c5da',
	'#89d3e3',
	'#1f77b4',
];

export default function DefectCharts() {
	const [data, setData] = useState<DefectsData | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		fetch('/api/recalls/defects')
			.then((res) => {
				if (!res.ok) throw new Error(`HTTP ${res.status}`);
				return res.json();
			})
			.then(setData)
			.catch((err) => setError(err.message));
	}, []);

	if (error) {
		return (
			<div className="grid grid-cols-1 gap-6 md:grid-cols-2">
				<Card>
					<CardContent className="p-6 text-danger">Failed to load defect data: {error}</CardContent>
				</Card>
			</div>
		);
	}

	if (!data) {
		return (
			<div className="grid grid-cols-1 gap-6 md:grid-cols-2">
				<Card>
					<CardContent className="flex items-center justify-center p-12 text-text-muted">
						Loading...
					</CardContent>
				</Card>
				<Card>
					<CardContent className="flex items-center justify-center p-12 text-text-muted">
						Loading...
					</CardContent>
				</Card>
			</div>
		);
	}

	const defectsData = [...data.top_defects].sort((a, b) => a.count - b.count);
	const riskData = data.risk_levels;

	return (
		<div className="grid grid-cols-1 gap-6 md:grid-cols-2">
			<Card>
				<CardHeader>
					<CardTitle>Top Defects by Count</CardTitle>
				</CardHeader>
				<CardContent>
					<ResponsiveContainer width="100%" height={360}>
						<BarChart data={defectsData} layout="vertical" margin={{ left: 20 }}>
							<CartesianGrid strokeDasharray="3 3" stroke="#2a2d35" />
							<XAxis type="number" tick={{ fill: '#e0e0e0' }} />
							<YAxis
								dataKey="defect"
								type="category"
								tick={{ fill: '#e0e0e0', fontSize: 12 }}
								width={140}
							/>
							<Tooltip
								contentStyle={{
									backgroundColor: '#1e2028',
									border: '1px solid #2a2d35',
									borderRadius: '8px',
									color: '#e0e0e0',
								}}
							/>
							<Bar dataKey="count" name="Count" radius={[0, 4, 4, 0]}>
								{defectsData.map((entry, index) => (
									<Cell key={entry.defect} fill={DEFECT_GRADIENT[index % DEFECT_GRADIENT.length]} />
								))}
							</Bar>
						</BarChart>
					</ResponsiveContainer>
				</CardContent>
			</Card>
			<Card>
				<CardHeader>
					<CardTitle>Risk Level Distribution</CardTitle>
				</CardHeader>
				<CardContent>
					<ResponsiveContainer width="100%" height={360}>
						<BarChart data={riskData}>
							<CartesianGrid strokeDasharray="3 3" stroke="#2a2d35" />
							<XAxis dataKey="level" tick={{ fill: '#e0e0e0' }} />
							<YAxis tick={{ fill: '#e0e0e0' }} />
							<Tooltip
								contentStyle={{
									backgroundColor: '#1e2028',
									border: '1px solid #2a2d35',
									borderRadius: '8px',
									color: '#e0e0e0',
								}}
							/>
							<Bar dataKey="count" name="Count" radius={[4, 4, 0, 0]}>
								{riskData.map((entry) => (
									<Cell key={entry.level} fill={RISK_COLORS[entry.level] ?? '#888'} />
								))}
							</Bar>
						</BarChart>
					</ResponsiveContainer>
				</CardContent>
			</Card>
		</div>
	);
}
