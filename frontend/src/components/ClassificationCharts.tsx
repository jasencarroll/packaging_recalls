import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEffect, useState } from 'react';
import {
	Bar,
	BarChart,
	CartesianGrid,
	Cell,
	Legend,
	Pie,
	PieChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from 'recharts';

interface ClassDistribution {
	class: string;
	count: number;
	percent: number;
}

interface CostByClass {
	class: string;
	min: number;
	q1: number;
	median: number;
	q3: number;
	max: number;
}

interface ClassificationData {
	distribution: ClassDistribution[];
	cost_by_class: CostByClass[];
}

const CLASS_COLORS: Record<string, string> = {
	'Class I': '#ff6b6b',
	'Class II': '#4ecdc4',
	'Class III': '#45b7d1',
	I: '#ff6b6b',
	II: '#4ecdc4',
	III: '#45b7d1',
};

function getClassColor(cls: string): string {
	return CLASS_COLORS[cls] ?? '#888';
}

export default function ClassificationCharts() {
	const [data, setData] = useState<ClassificationData | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		fetch('/api/recalls/classification')
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
					<CardContent className="p-6 text-danger">
						Failed to load classification data: {error}
					</CardContent>
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

	const pieData = data.distribution.map((d) => ({
		name: d.class,
		value: d.count,
		percent: d.percent,
	}));

	const costData = data.cost_by_class.map((d) => ({
		name: d.class,
		min: d.min,
		q1: d.q1,
		median: d.median,
		q3: d.q3,
		max: d.max,
		range: d.q3 - d.q1,
	}));

	return (
		<div className="grid grid-cols-1 gap-6 md:grid-cols-2">
			<Card>
				<CardHeader>
					<CardTitle>Classification Distribution</CardTitle>
				</CardHeader>
				<CardContent>
					<ResponsiveContainer width="100%" height={320}>
						<PieChart>
							<Pie
								data={pieData}
								cx="50%"
								cy="50%"
								outerRadius={110}
								dataKey="value"
								label={({ name, percent }) => `${name} (${percent.toFixed(1)}%)`}
								labelLine={true}
								stroke="none"
							>
								{pieData.map((entry) => (
									<Cell key={entry.name} fill={getClassColor(entry.name)} />
								))}
							</Pie>
							<Tooltip
								contentStyle={{
									backgroundColor: '#1e2028',
									border: '1px solid #2a2d35',
									borderRadius: '8px',
									color: '#e0e0e0',
								}}
							/>
							<Legend wrapperStyle={{ color: '#e0e0e0' }} />
						</PieChart>
					</ResponsiveContainer>
				</CardContent>
			</Card>
			<Card>
				<CardHeader>
					<CardTitle>Cost Impact by Classification</CardTitle>
				</CardHeader>
				<CardContent>
					<ResponsiveContainer width="100%" height={320}>
						<BarChart data={costData}>
							<CartesianGrid strokeDasharray="3 3" stroke="#2a2d35" />
							<XAxis dataKey="name" tick={{ fill: '#e0e0e0' }} />
							<YAxis
								tick={{ fill: '#e0e0e0' }}
								tickFormatter={(v: number) =>
									v >= 1_000_000 ? `$${(v / 1_000_000).toFixed(0)}M` : `$${(v / 1_000).toFixed(0)}K`
								}
							/>
							<Tooltip
								contentStyle={{
									backgroundColor: '#1e2028',
									border: '1px solid #2a2d35',
									borderRadius: '8px',
									color: '#e0e0e0',
								}}
								formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
							/>
							<Bar dataKey="median" name="Median Cost" radius={[4, 4, 0, 0]}>
								{costData.map((entry) => (
									<Cell key={entry.name} fill={getClassColor(entry.name)} />
								))}
							</Bar>
							<Bar dataKey="q3" name="75th Percentile" radius={[4, 4, 0, 0]} fillOpacity={0.4}>
								{costData.map((entry) => (
									<Cell key={entry.name} fill={getClassColor(entry.name)} />
								))}
							</Bar>
						</BarChart>
					</ResponsiveContainer>
				</CardContent>
			</Card>
		</div>
	);
}
