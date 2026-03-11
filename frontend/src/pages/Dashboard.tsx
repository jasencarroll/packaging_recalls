import ClassificationCharts from '@/components/ClassificationCharts';
import DataTable from '@/components/DataTable';
import DefectCharts from '@/components/DefectCharts';
import InsightsPanel from '@/components/InsightsPanel';
import KPICard from '@/components/KPICard';
import TimelineCharts from '@/components/TimelineCharts';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/utils';
import { useEffect, useState } from 'react';

interface KPIData {
	total_recalls: number;
	avg_cost_impact: number;
	class_i_percent: number;
	total_cost_impact: number;
}

export default function Dashboard() {
	const [kpis, setKpis] = useState<KPIData | null>(null);
	const [kpiError, setKpiError] = useState<string | null>(null);

	useEffect(() => {
		fetch('/api/recalls/kpis')
			.then((res) => {
				if (!res.ok) throw new Error(`HTTP ${res.status}`);
				return res.json();
			})
			.then(setKpis)
			.catch((err) => setKpiError(err.message));
	}, []);

	return (
		<div className="min-h-screen bg-background">
			<header className="border-b border-border bg-surface px-6 py-5">
				<h1 className="text-2xl font-bold text-text">FDA Packaging Recall Analytics</h1>
				<p className="mt-1 text-sm text-text-muted">
					Comprehensive analysis of FDA packaging-related recalls
				</p>
			</header>

			<main className="mx-auto max-w-7xl space-y-8 p-6">
				{/* KPI Row */}
				<section>
					<h2 className="mb-4 text-lg font-semibold text-text">Overview</h2>
					{kpiError ? (
						<p className="text-danger">Failed to load KPIs: {kpiError}</p>
					) : (
						<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
							<KPICard
								label="Total Recalls"
								value={kpis ? formatNumber(kpis.total_recalls) : '---'}
								accentColor="#1f77b4"
							/>
							<KPICard
								label="Avg Cost Impact"
								value={kpis ? formatCurrency(kpis.avg_cost_impact) : '---'}
								accentColor="#ffcc00"
							/>
							<KPICard
								label="Class I Critical"
								value={kpis ? formatPercent(kpis.class_i_percent) : '---'}
								accentColor="#ff4444"
							/>
							<KPICard
								label="Total Est. Impact"
								value={kpis ? formatCurrency(kpis.total_cost_impact) : '---'}
								accentColor="#44ff44"
							/>
						</div>
					)}
				</section>

				{/* Classification Section */}
				<section>
					<h2 className="mb-4 text-lg font-semibold text-text">Recall Classification Analysis</h2>
					<ClassificationCharts />
				</section>

				{/* Defects Section */}
				<section>
					<h2 className="mb-4 text-lg font-semibold text-text">Defect Analysis</h2>
					<DefectCharts />
				</section>

				{/* Timeline Section */}
				<section>
					<h2 className="mb-4 text-lg font-semibold text-text">Recall Timeline</h2>
					<TimelineCharts />
				</section>

				{/* Data Table Section */}
				<section>
					<h2 className="mb-4 text-lg font-semibold text-text">Data Table</h2>
					<DataTable />
				</section>

				{/* Insights Section */}
				<section>
					<h2 className="mb-4 text-lg font-semibold text-text">Insights & Details</h2>
					<InsightsPanel />
				</section>
			</main>

			<footer className="border-t border-border px-6 py-4 text-center text-sm text-text-muted">
				FDA Packaging Recall Analytics Dashboard
			</footer>
		</div>
	);
}
