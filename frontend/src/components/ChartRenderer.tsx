import React, { useEffect, useRef, memo } from 'react';
import * as echarts from 'echarts';

interface ChartRendererProps {
    option: echarts.EChartsOption;
    height?: string;
}

const ChartRenderer: React.FC<ChartRendererProps> = memo(({ option, height = '400px' }) => {
    const chartRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!chartRef.current) return;

        // 初始化图表
        const chart = echarts.init(chartRef.current);

        // 设置配置
        chart.setOption(option);

        // 响应式 resize
        const handleResize = () => chart.resize();
        window.addEventListener('resize', handleResize);

        // 清理
        return () => {
            window.removeEventListener('resize', handleResize);
            chart.dispose();
        };
    }, [option]);

    return (
        <div
            ref={chartRef}
            style={{ width: '100%', height }}
            className="rounded-lg bg-white"
        />
    );
});

ChartRenderer.displayName = 'ChartRenderer';
export default ChartRenderer;