import React from 'react';

interface MetricCardProps {
    label: string;
    value: string;
    trend?: {
        value: string;
        up: boolean;
    };
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, trend }) => {
    // ✅ 安全转换
    const safeLabel = String(label || '');
    const safeValue = String(value || '');

    return (
        <div className="metric-card rounded-xl p-4">
            <div className="text-xs text-gray-500 mb-1">{safeLabel}</div>
            <div className="text-xl font-semibold text-white">{safeValue}</div>
            {trend && (
                <div className={`text-xs mt-1 flex items-center space-x-1 ${trend.up ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                    <i className={`fas fa-arrow-${trend.up ? 'up' : 'down'} text-[10px]`}></i>
                    <span>{String(trend.value)} 环比</span>
                </div>
            )}
        </div>
    );
};

export default MetricCard;