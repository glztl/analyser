import React from 'react';
import ChartRenderer from './ChartRenderer';
import CodeBlock from './CodeBlock';
import MetricCard from './MetricCard';

// ========== 类型定义 ==========

export interface MessageData {
    id: string;
    role: 'user' | 'agent';
    content: string;
    timestamp?: Date;

    // Agent 专属字段
    status?: 'thinking' | 'processing' | 'completed' | 'failed';
    progress?: Array<{ label: string; done: boolean; loading?: boolean }>;
    metrics?: Array<{ label: string; value: string; trend?: { value: string; up: boolean } }>;
    chartConfig?: any;
    insights?: string[];
    code?: string;
    actions?: Array<{ label: string; icon: string; onClick: () => void }>;

    // 文件分析相关
    metadata?: {
        file_info?: {
            filename?: string;
            size_human?: string;
        };
        structure?: {
            num_rows?: number;
            num_columns?: number;
            table_orientation?: string;
            columns?: Array<{ name: string; dtype: string; is_numeric?: boolean }>;
        };
        quality?: {
            completeness?: number;
            quality_score?: number;
            quality_level?: string;
        };
        strategy?: {
            type?: string;
            description?: string;
            max_series?: number;
        };
    };
    preview?: {
        headers?: string[];
        rows?: Array<Record<string, any>>;
    };
}

interface ChatMessageProps {
    message: MessageData;
}

// ========== 主组件 ==========

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    const isAgent = message.role === 'agent';

    return (
        <div className={`flex items-start space-x-4 ${isAgent ? '' : 'justify-end'}`}>
            {/* Agent 头像 */}
            {isAgent && (
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0 animate-float">
                    <i className="fas fa-sparkles text-white text-sm"></i>
                </div>
            )}

            {/* 消息内容 */}
            <div className={`flex-1 ${isAgent ? '' : 'flex justify-end'}`}>
                <div className={`rounded-2xl px-5 py-4 max-w-3xl ${isAgent
                    ? 'message-agent rounded-tl-sm'
                    : 'message-user rounded-tr-sm'
                    }`}>

                    {/* 状态指示器 */}
                    {message.status === 'thinking' && (
                        <div className="flex items-center space-x-2 text-sm text-indigo-400 mb-3">
                            <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></div>
                            <span>正在思考...</span>
                        </div>
                    )}

                    {/* 进度步骤 */}
                    {message.progress && (
                        <div className="space-y-2 mb-4">
                            {message.progress.map((step, index) => (
                                <div key={index} className="flex items-center space-x-2.5 text-xs text-gray-400">
                                    <div className={`w-4 h-4 rounded flex items-center justify-center ${step.done ? 'bg-emerald-500/10' : step.loading ? 'bg-indigo-500/10 animate-pulse' : 'bg-white/5'
                                        }`}>
                                        {step.done ? (
                                            <i className="fas fa-check text-emerald-400 text-[10px]"></i>
                                        ) : step.loading ? (
                                            <i className="fas fa-circle-notch text-indigo-400 text-[10px] animate-spin"></i>
                                        ) : (
                                            <div className="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                                        )}
                                    </div>
                                    <span className={step.done ? 'text-gray-300' : ''}>{step.label}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* 主要内容 */}
                    <p className={`text-sm leading-relaxed ${isAgent ? 'text-gray-300' : 'text-gray-200'
                        }`} dangerouslySetInnerHTML={{ __html: formatContent(message.content) }} />

                    {/* ========== 文件预览（上传后显示） ========== */}
                    {message.preview && message.preview.headers && message.preview.headers.length > 0 && (
                        <div className="glass rounded-xl p-4 mt-4 border border-white/10">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center space-x-2">
                                    <i className="fas fa-table text-indigo-400 text-sm"></i>
                                    <span className="text-sm font-medium text-white">📋 文件预览</span>
                                </div>
                                <span className="text-xs text-gray-500">
                                    {message.metadata?.structure?.num_rows || 0} 行 × {message.metadata?.structure?.num_columns || 0} 列
                                </span>
                            </div>

                            {/* 数据质量指示器 */}
                            <div className="flex flex-wrap items-center gap-3 mb-3 text-xs">
                                <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-white/5">
                                    <div className={`w-2 h-2 rounded-full ${(message.metadata?.quality?.quality_score || 0) >= 90 ? 'bg-emerald-400' :
                                        (message.metadata?.quality?.quality_score || 0) >= 70 ? 'bg-amber-400' : 'bg-rose-400'
                                        }`}></div>
                                    <span className="text-gray-400">质量：{message.metadata?.quality?.quality_level || '未知'}</span>
                                </div>
                                <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-white/5">
                                    <i className="fas fa-check-circle text-emerald-400 text-[10px]"></i>
                                    <span className="text-gray-400">完整度：{message.metadata?.quality?.completeness || 0}%</span>
                                </div>
                                {message.metadata?.strategy?.description && (
                                    <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10">
                                        <i className="fas fa-lightbulb text-indigo-400 text-[10px]"></i>
                                        <span className="text-indigo-300">{message.metadata.strategy.description}</span>
                                    </div>
                                )}
                            </div>

                            {/* 预览表格 */}
                            <div className="overflow-x-auto rounded-lg border border-white/5">
                                <table className="w-full text-xs">
                                    <thead>
                                        <tr className="bg-white/5 border-b border-white/10">
                                            {message.preview.headers.map((header, i) => (
                                                <th key={i} className="text-left py-2.5 px-3 text-gray-400 font-medium whitespace-nowrap">
                                                    {header}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {message.preview.rows && message.preview.rows.map((row, i) => (
                                            <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                                {message.preview?.headers?.map((header, j) => (
                                                    <td key={j} className="py-2 px-3 text-gray-300 whitespace-nowrap">
                                                        {row[header] ?? <span className="text-gray-600">-</span>}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* 列信息提示 */}
                            {message.metadata?.structure?.columns && message.metadata.structure.columns.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-white/5">
                                    <div className="text-xs text-gray-500">
                                        <i className="fas fa-info-circle mr-1.5"></i>
                                        检测到 {message.metadata.structure.columns.filter(c => c.is_numeric).length} 个数值列，
                                        {message.metadata.structure.columns.length - message.metadata.structure.columns.filter(c => c.is_numeric).length} 个文本列
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ========== 指标卡片 ========== */}
                    {message.metrics && message.metrics.length > 0 && (
                        <div className="grid grid-cols-3 gap-3 mt-4">
                            {message.metrics.map((metric, index) => (
                                <MetricCard key={index} {...metric} />
                            ))}
                        </div>
                    )}

                    {/* ========== 图表 ========== */}
                    {message.chartConfig && typeof message.chartConfig === 'object' && Object.keys(message.chartConfig).length > 0 && (
                        <div className="glass rounded-xl p-4 mt-4 border border-white/10">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center space-x-2">
                                    <i className="fas fa-chart-line text-indigo-400 text-sm"></i>
                                    <span className="text-sm font-medium text-white">
                                        {message.chartConfig?.title?.text || '数据可视化'}
                                    </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <button className="p-1.5 text-gray-400 hover:text-white hover:bg-white/5 rounded transition-all" title="全屏查看">
                                        <i className="fas fa-expand text-xs"></i>
                                    </button>
                                    <button className="p-1.5 text-gray-400 hover:text-white hover:bg-white/5 rounded transition-all" title="下载图表">
                                        <i className="fas fa-download text-xs"></i>
                                    </button>
                                </div>
                            </div>
                            <ChartRenderer option={message.chartConfig} height="350px" />

                            {/* 图表说明 */}
                            {message.metadata?.strategy && (
                                <div className="mt-3 pt-3 border-t border-white/5 text-xs text-gray-500">
                                    <i className="fas fa-info-circle mr-1.5"></i>
                                    {message.metadata.strategy.description}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ========== 关键洞察 ========== */}
                    {message.insights && message.insights.length > 0 && (
                        <div className="glass rounded-xl p-4 mt-4 border border-white/10">
                            <div className="flex items-center space-x-2 mb-3">
                                <i className="fas fa-lightbulb text-amber-400 text-sm"></i>
                                <span className="text-sm font-medium text-white">关键洞察</span>
                            </div>
                            <ul className="space-y-2">
                                {message.insights.map((insight, index) => (
                                    <li key={index} className="flex items-start space-x-2 text-xs text-gray-400">
                                        <i className="fas fa-circle text-[4px] text-indigo-400 mt-1.5 flex-shrink-0"></i>
                                        <span className="leading-relaxed">{insight}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* ========== 代码块 ========== */}
                    {message.code && (
                        <details className="group mt-4">
                            <summary className="flex items-center space-x-2 text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition-all">
                                <i className="fas fa-chevron-right text-[10px] group-open:rotate-90 transition-transform"></i>
                                <span>查看生成的分析代码</span>
                                <span className="ml-2 px-2 py-0.5 rounded-full bg-white/5 text-[10px]">Python</span>
                            </summary>
                            <CodeBlock code={message.code} language="python" className="mt-3" />
                        </details>
                    )}

                    {/* ========== 操作按钮 ========== */}
                    {message.actions && message.actions.length > 0 && (
                        <div className="flex flex-wrap items-center gap-2 mt-4 pt-3 border-t border-white/5">
                            {message.actions.map((action, index) => (
                                <button
                                    key={index}
                                    onClick={action.onClick}
                                    className="btn-ghost px-3 py-1.5 text-xs text-gray-400 rounded-lg transition-all flex items-center space-x-1.5 hover:bg-white/10"
                                >
                                    <i className={`fas ${action.icon} text-[10px]`}></i>
                                    <span>{action.label}</span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* 用户头像 */}
            {!isAgent && (
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center flex-shrink-0">
                    <span className="text-white text-sm font-semibold">U</span>
                </div>
            )}
        </div>
    );
};

// ========== 工具函数 ==========

/**
 * 格式化消息内容（支持简单的 Markdown）
 */
function formatContent(content: string): string {
    if (!content) return '';

    return content
        // 加粗 **text**
        .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
        // 换行
        .replace(/\n/g, '<br/>')
        // 链接 [text](url)
        .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" class="text-indigo-400 hover:underline" target="_blank">$1</a>');
}

export default ChatMessage;