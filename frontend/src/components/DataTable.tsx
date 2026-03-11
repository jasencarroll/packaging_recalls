import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency } from '@/lib/utils';
import { useCallback, useEffect, useState } from 'react';

interface RecallRecord {
	recall_number: string;
	recalling_firm: string;
	classification_clean: string;
	primary_defect: string;
	reason_for_recall: string;
	recall_initiation_date: string;
	risk_level: string;
	estimated_cost_impact: number;
	days_to_resolution: number;
	state: string;
	product_description: string;
}

interface TableResponse {
	total: number;
	page: number;
	limit: number;
	pages: number;
	records: RecallRecord[];
}

const LIMIT = 25;

export default function DataTable() {
	const [data, setData] = useState<TableResponse | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [page, setPage] = useState(1);
	const [search, setSearch] = useState('');
	const [classFilter, setClassFilter] = useState('');

	const fetchData = useCallback(() => {
		const params = new URLSearchParams();
		params.set('page', String(page));
		params.set('limit', String(LIMIT));
		if (classFilter) params.set('class', classFilter);

		fetch(`/api/recalls/table?${params.toString()}`)
			.then((res) => {
				if (!res.ok) throw new Error(`HTTP ${res.status}`);
				return res.json();
			})
			.then(setData)
			.catch((err) => setError(err.message));
	}, [page, classFilter]);

	useEffect(() => {
		fetchData();
	}, [fetchData]);

	// Client-side search across visible records
	const filtered =
		data?.records.filter((r) => {
			if (!search) return true;
			const term = search.toLowerCase();
			return (
				r.recalling_firm?.toLowerCase().includes(term) ||
				r.recall_number?.toLowerCase().includes(term) ||
				r.reason_for_recall?.toLowerCase().includes(term) ||
				r.product_description?.toLowerCase().includes(term) ||
				r.state?.toLowerCase().includes(term)
			);
		}) ?? [];

	if (error) {
		return (
			<Card>
				<CardContent className="p-6 text-danger">Failed to load table data: {error}</CardContent>
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
		<Card>
			<CardHeader>
				<div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
					<CardTitle>Recall Records</CardTitle>
					<div className="flex flex-col gap-2 sm:flex-row sm:items-center">
						<input
							type="text"
							placeholder="Search records..."
							value={search}
							onChange={(e) => setSearch(e.target.value)}
							className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary"
						/>
						<select
							value={classFilter}
							onChange={(e) => {
								setClassFilter(e.target.value);
								setPage(1);
							}}
							className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary"
						>
							<option value="">All Classes</option>
							<option value="I">Class I</option>
							<option value="II">Class II</option>
							<option value="III">Class III</option>
						</select>
					</div>
				</div>
			</CardHeader>
			<CardContent>
				<div className="overflow-x-auto">
					<table className="w-full text-sm">
						<thead>
							<tr className="border-b border-border text-left text-text-muted">
								<th className="whitespace-nowrap pb-3 pr-4">Recall #</th>
								<th className="whitespace-nowrap pb-3 pr-4">Firm</th>
								<th className="whitespace-nowrap pb-3 pr-4">Class</th>
								<th className="whitespace-nowrap pb-3 pr-4">Defect</th>
								<th className="whitespace-nowrap pb-3 pr-4">State</th>
								<th className="whitespace-nowrap pb-3 pr-4">Date</th>
								<th className="whitespace-nowrap pb-3 pr-4">Risk</th>
								<th className="whitespace-nowrap pb-3 pr-4 text-right">Est. Cost</th>
								<th className="whitespace-nowrap pb-3 text-right">Days</th>
							</tr>
						</thead>
						<tbody>
							{filtered.map((r) => (
								<tr key={r.recall_number} className="border-b border-border/50">
									<td className="whitespace-nowrap py-2 pr-4 font-mono text-xs">
										{r.recall_number}
									</td>
									<td className="max-w-48 truncate py-2 pr-4">{r.recalling_firm}</td>
									<td className="py-2 pr-4">
										<ClassBadge value={r.classification_clean} />
									</td>
									<td className="max-w-40 truncate py-2 pr-4">{r.primary_defect}</td>
									<td className="py-2 pr-4">{r.state}</td>
									<td className="whitespace-nowrap py-2 pr-4">
										{r.recall_initiation_date?.split('T')[0] ?? ''}
									</td>
									<td className="py-2 pr-4">
										<RiskBadge value={r.risk_level} />
									</td>
									<td className="whitespace-nowrap py-2 pr-4 text-right font-medium">
										{formatCurrency(r.estimated_cost_impact)}
									</td>
									<td className="py-2 text-right">{r.days_to_resolution ?? '-'}</td>
								</tr>
							))}
							{filtered.length === 0 && (
								<tr>
									<td colSpan={9} className="py-8 text-center text-text-muted">
										No records found.
									</td>
								</tr>
							)}
						</tbody>
					</table>
				</div>

				{/* Pagination */}
				<div className="mt-4 flex items-center justify-between text-sm text-text-muted">
					<span>
						Page {data.page} of {data.pages} ({data.total} total records)
					</span>
					<div className="flex gap-2">
						<button
							type="button"
							disabled={data.page <= 1}
							onClick={() => setPage((p) => p - 1)}
							className="rounded-md border border-border px-3 py-1 text-text transition-colors hover:bg-surface disabled:opacity-40 disabled:hover:bg-transparent"
						>
							Previous
						</button>
						<button
							type="button"
							disabled={data.page >= data.pages}
							onClick={() => setPage((p) => p + 1)}
							className="rounded-md border border-border px-3 py-1 text-text transition-colors hover:bg-surface disabled:opacity-40 disabled:hover:bg-transparent"
						>
							Next
						</button>
					</div>
				</div>
			</CardContent>
		</Card>
	);
}

function ClassBadge({ value }: { value: string }) {
	const colors: Record<string, string> = {
		I: 'bg-red-500/15 text-red-400',
		II: 'bg-yellow-500/15 text-yellow-400',
		III: 'bg-green-500/15 text-green-400',
	};
	return (
		<span
			className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${colors[value] ?? 'bg-surface text-text-muted'}`}
		>
			{value}
		</span>
	);
}

function RiskBadge({ value }: { value: string }) {
	const lower = value?.toLowerCase() ?? '';
	let colorClass = 'bg-surface text-text-muted';
	if (lower.includes('high')) colorClass = 'bg-red-500/15 text-red-400';
	else if (lower.includes('medium')) colorClass = 'bg-yellow-500/15 text-yellow-400';
	else if (lower.includes('low')) colorClass = 'bg-green-500/15 text-green-400';
	return (
		<span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}>
			{value}
		</span>
	);
}
