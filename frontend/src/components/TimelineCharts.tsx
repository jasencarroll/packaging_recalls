import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEffect, useState } from 'react';
import {
	Bar,
	BarChart,
	CartesianGrid,
	Legend,
	Line,
	LineChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from 'recharts';

interface MonthlyData {
	month: string;
	count: number;
}

interface AnnualData {
	year: number;
	class_i: number;
	class_ii: number;
	class_iii: number;
}

interface TimelineData {
	monthly: MonthlyData[];
	annual_by_class: AnnualData[];
}

export default function TimelineCharts() {
	const [data, setData] = useState<TimelineData | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		fetch('/api/recalls/timeline')
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
						Failed to load timeline data: {error}
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

	return (
		<div className="grid grid-cols-1 gap-6 md:grid-cols-2">
			<Card>
				<CardHeader>
					<CardTitle>Monthly Recall Trend</CardTitle>
				</CardHeader>
				<CardContent>
					<ResponsiveContainer width="100%" height={320}>
						<LineChart data={data.monthly}>
							<CartesianGrid strokeDasharray="3 3" stroke="#2a2d35" />
							<XAxis
								dataKey="month"
								tick={{ fill: '#e0e0e0', fontSize: 11 }}
								angle={-45}
								textAnchor="end"
								height={60}
							/>
							<YAxis tick={{ fill: '#e0e0e0' }} />
							<Tooltip
								contentStyle={{
									backgroundColor: '#1e2028',
									border: '1px solid #2a2d35',
									borderRadius: '8px',
									color: '#e0e0e0',
								}}
							/>
							<Line
								type="monotone"
								dataKey="count"
								name="Recalls"
								stroke="#1f77b4"
								strokeWidth={2}
								dot={{ fill: '#1f77b4', r: 3 }}
								activeDot={{ r: 6 }}
							/>
						</LineChart>
					</ResponsiveContainer>
				</CardContent>
			</Card>
			<Card>
				<CardHeader>
					<CardTitle>Annual Recalls by Classification</CardTitle>
				</CardHeader>
				<CardContent>
					<ResponsiveContainer width="100%" height={320}>
						<BarChart data={data.annual_by_class}>
							<CartesianGrid strokeDasharray="3 3" stroke="#2a2d35" />
							<XAxis dataKey="year" tick={{ fill: '#e0e0e0' }} />
							<YAxis tick={{ fill: '#e0e0e0' }} />
							<Tooltip
								contentStyle={{
									backgroundColor: '#1e2028',
									border: '1px solid #2a2d35',
									borderRadius: '8px',
									color: '#e0e0e0',
								}}
							/>
							<Legend wrapperStyle={{ color: '#e0e0e0' }} />
							<Bar
								dataKey="class_i"
								name="Class I"
								stackId="a"
								fill="#ff6b6b"
								radius={[0, 0, 0, 0]}
							/>
							<Bar
								dataKey="class_ii"
								name="Class II"
								stackId="a"
								fill="#4ecdc4"
								radius={[0, 0, 0, 0]}
							/>
							<Bar
								dataKey="class_iii"
								name="Class III"
								stackId="a"
								fill="#45b7d1"
								radius={[4, 4, 0, 0]}
							/>
						</BarChart>
					</ResponsiveContainer>
				</CardContent>
			</Card>
		</div>
	);
}
