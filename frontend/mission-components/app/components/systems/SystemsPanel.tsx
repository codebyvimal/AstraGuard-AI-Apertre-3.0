import React, { useState, useEffect } from 'react';
import systemsData from '../../mocks/systems.json';
import telemetryData from '../../mocks/telemetry.json';
import { KPICard } from './KPICard';
import { BreakerMatrix } from './BreakerMatrix';
import { MetricsCharts } from './MetricsCharts';
import { HealthTable } from './HealthTable';
import { KPI, BreakerState } from '../../types/systems';
import { ChartSeries, HealthRow } from '../../types/telemetry';

export const SystemsPanel: React.FC = () => {
    const [kpis, setKpis] = useState<KPI[]>(systemsData.kpis as KPI[]);
    const [breakers, setBreakers] = useState<BreakerState[]>(systemsData.breakers as BreakerState[]);
    /* eslint-disable @typescript-eslint/no-unused-vars */
    const [telemetry, setTelemetry] = useState<Record<string, ChartSeries>>(telemetryData.charts as unknown as Record<string, ChartSeries>);
    const [healthData] = useState<HealthRow[]>(telemetryData.health as HealthRow[]);
    /* eslint-enable @typescript-eslint/no-unused-vars */

    // 30s drift simulation for KPIs
    useEffect(() => {
        const interval = setInterval(() => {
            setKpis(prev => prev.map(kpi => ({
                ...kpi,
                value: kpi.id === 'latency'
                    ? `${Math.floor(Math.max(120, 142 + (Math.random() - 0.5) * 20))}ms`
                    : kpi.id === 'cpu'
                        ? `${Math.floor(47 + (Math.random() - 0.5) * 10)}%`
                        : kpi.value,
                trend: (Math.random() - 0.5) * (kpi.id === 'latency' ? 10 : 1),
                progress: kpi.id === 'latency' ? Math.min(100, Math.max(50, 71 + (Math.random() - 0.5) * 10)) : kpi.progress
            })));
        }, 30000);

        return () => clearInterval(interval);
    }, []);

    // 5s live append for Charts
    useEffect(() => {
        const interval = setInterval(() => {
            setTelemetry(prev => {
                const next = { ...prev };
                Object.keys(next).forEach(chartId => {
                    const chart = next[chartId];
                    const lastValue = chart.data[chart.data.length - 1]?.value || 50;
                    const newValue = Math.max(0, Math.min(100, lastValue + (Math.random() - 0.5) * 10)); // Constraints

                    next[chartId] = {
                        ...chart,
                        data: [
                            ...chart.data.slice(1), // Keep fixed window size
                            {
                                timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                                value: newValue
                            }
                        ]
                    };
                });
                return next;
            });
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-12 max-w-7xl mx-auto">
            {/* KPI Row */}
            <section className="glow-magenta/50">
                <h2 className="text-2xl font-bold mb-8 text-magenta-400 glow-magenta">System Health Overview</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
                    {kpis.map(kpi => <KPICard key={kpi.id} {...kpi} />)}
                </div>
            </section>

            {/* Charts Grid */}
            <section className="glow-teal/50">
                <h2 className="text-2xl font-bold mb-8 text-teal-400 glow-teal">Telemetry Trends (Last 1h)</h2>
                <MetricsCharts data={telemetry} />
            </section>

            {/* Health Table */}
            <section>
                <h2 className="text-2xl font-bold mb-8 text-teal-400 glow-teal flex items-center">
                    Component Health <span className="ml-3 text-sm bg-teal-500/0 px-3 py-1 rounded-full font-mono text-teal-300 border border-teal-500/30">
                        {healthData.filter(h => h.status !== 'healthy').length} degraded
                    </span>
                </h2>
                <HealthTable data={healthData} />
            </section>

            {/* Breaker Matrix */}
            <BreakerMatrix breakers={breakers} services={systemsData.services} />
        </div>
    );
};
