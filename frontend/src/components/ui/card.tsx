import { cn } from '@/lib/utils';
import type { HTMLAttributes } from 'react';

function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			className={cn('rounded-lg border border-border bg-card text-text shadow-sm', className)}
			{...props}
		/>
	);
}

function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
	return <div className={cn('flex flex-col space-y-1.5 p-6', className)} {...props} />;
}

function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
	return (
		<h3 className={cn('text-lg font-semibold leading-none tracking-tight', className)} {...props} />
	);
}

function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
	return <p className={cn('text-sm text-text-muted', className)} {...props} />;
}

function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
	return <div className={cn('p-6 pt-0', className)} {...props} />;
}

export { Card, CardContent, CardDescription, CardHeader, CardTitle };
