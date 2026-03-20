import React, { useEffect, useRef, memo } from 'react';
import * as echarts from 'echarts';

// 深色主题配置
const DARK_THEME = {
    backgroundColor: 'transparent',
    textStyle: { color: '#e4e4e7' },
    title: { textStyle: { color: '#e4e4e7' } },
    legend: { textStyle: { color: '#a1a1aa' } },
    tooltip: {
        backgroundColor: 'rgba(15, 15, 20, 0.9)',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        textStyle: { color: '#e4e4e7' },
    },
    xAxis: {
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
        axisLabel: { color: '#a1a1aa' },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
    },
    yAxis: {
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
        axisLabel: { color: '#a1a1aa' },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
    },
    grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
    },
};

interface ChartRendererProps {
    option: echarts.EChartsOption;
    height?: string;
    theme?: 'dark' | 'light';
}

const ChartRenderer: React.FC<ChartRendererProps> = memo(({
    option,
    height = '300px'
}) => {
    const chartRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!chartRef.current) return;

        // 合并主题配置
        const finalOption = {
            ...DARK_THEME,
            ...option,
            tooltip: { ...DARK_THEME.tooltip, ...option.tooltip },
            xAxis: { ...DARK_THEME.xAxis, ...option.xAxis },
            yAxis: { ...DARK_THEME.yAxis, ...option.yAxis },
        };

        const chart = echarts.init(chartRef.current, undefined, { renderer: 'svg' });
        chart.setOption(finalOption);

        // 响应式
        const handleResize = () => chart.resize();
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.dispose();
        };
    }, [option]);

    return (
        <div
            ref={chartRef}
            style={{ width: '100%', height }}
            className="echarts-container"
        />
    );
});

ChartRenderer.displayName = 'ChartRenderer';
export default ChartRenderer;