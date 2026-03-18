import React from 'react';
import { Card, Spin, Alert, Typography, Space } from 'antd';
import ChartRenderer from './ChartRenderer';
import type { TaskResponse } from '../api/analyser';

const { Title, Paragraph } = Typography;

interface AnalysisResultProps {
    task: TaskResponse | null;
    loading: boolean;
    error: string | null;
}

const AnalysisResult: React.FC<AnalysisResultProps> = ({ task, loading, error }) => {
    if (loading) {
        return (
            <div className="flex justify-center items-center py-16">
                <Space direction="vertical" style={{ width: '100%' }} align="center">
                    <Spin size="large" />
                    <Paragraph className="text-gray-500">
                        AI 正在分析数据，请稍候...
                    </Paragraph>
                </Space>
            </div>
        );
    }

    if (error) {
        return (
            <Alert
                title="分析失败"  // message → title
                description={error}
                type="error"
                showIcon
            />
        );
    }

    if (!task || task.status !== 'completed' || !task.output) {
        return null;
    }

    const { result, chart_json } = task.output;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 分析结论 */}
            <Card
                title={<Title level={4}>📊 分析结论</Title>}
                className="card-shadow"
            >
                <Paragraph className="text-gray-700 leading-relaxed text-lg">
                    {result}
                </Paragraph>
            </Card>

            {/* 交互式图表 */}
            {chart_json && (
                <Card
                    title={<Title level={4}>📈 可视化图表</Title>}
                    className="card-shadow"
                >
                    <ChartRenderer option={chart_json} height="450px" />
                </Card>
            )}

            {/* 任务信息 */}
            <Card
                title={<Title level={5}>任务信息</Title>}
                size="small"
                className="bg-gray-50"
            >
                <Space direction="vertical" size="small">
                    <Paragraph><strong>任务ID:</strong> {task.id}</Paragraph>
                    <Paragraph><strong>查询:</strong> {task.query}</Paragraph>
                    <Paragraph><strong>状态:</strong>
                        <span className={`ml-2 px-2 py-1 rounded text-sm ${task.status === 'completed' ? 'bg-green-100 text-green-800' :
                            task.status === 'failed' ? 'bg-red-100 text-red-800' :
                                'bg-blue-100 text-blue-800'
                            }`}>
                            {task.status}
                        </span>
                    </Paragraph>
                </Space>
            </Card>
        </div>
    );
};

export default AnalysisResult;