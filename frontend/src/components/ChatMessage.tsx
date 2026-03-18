import React from 'react';
import ChartRenderer from './ChartRenderer';
import CodeBlock from './CodeBlock';
import MetricCard from './MetricCard';

export interface MessageData {
    id: string;
    role: 'user' | 'agent';
    content: string;  // ✅ 确保 content 永远是字符串
    timestamp?: Date;
    status?: 'thinking' | 'processing' | 'completed' | 'failed';
    progress?: Array<{ label: string; done: boolean; loading?: boolean }>;
    metrics?: Array<{ label: string; value: string; trend?: { value: string; up: boolean } }>;
    chartConfig?: any;
    insights?: string[];  // ✅ 确保 insights 是字符串数组
    code?: string;
    actions?: Array<{ label: string; icon: string; onClick: () => void }>;
}

interface ChatMessageProps {
    message: MessageData;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    const isAgent = message.role === 'agent';

    // ✅ 安全获取字符串内容
    const safeContent = typeof message.content === 'string'
        ? message.content
        : String(message.content || '');

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
                <div className={`rounded-2xl px-5 py-4 max-w-2xl ${isAgent ? 'message-agent rounded-tl-sm' : 'message-user rounded-tr-sm'
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

                    {/* ✅ 安全渲染 content */}
                    <p className={`text-sm leading-relaxed ${isAgent ? 'text-gray-300' : 'text-gray-200'}`}>
                        {safeContent}
                    </p>

                    {/* 指标卡片 */}
                    {message.metrics && message.metrics.length > 0 && (
                        <div className="grid grid-cols-3 gap-3 mt-4">
                            {message.metrics.map((metric, index) => (
                                <MetricCard key={index} {...metric} />
                            ))}
                        </div>
                    )}

                    {/* 图表 - 只渲染 chartConfig，不渲染 title 等子字段 */}
                    {message.chartConfig && typeof message.chartConfig === 'object' && (
                        <div className="glass rounded-xl p-4 mt-4">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-sm font-medium text-white">
                                    {/* ✅ 安全获取标题文本 */}
                                    {typeof message.chartConfig.title === 'string'
                                        ? message.chartConfig.title
                                        : message.chartConfig.title?.text || '数据可视化'}
                                </span>
                                <div className="flex items-center space-x-2">
                                    <button className="p-1.5 text-gray-400 hover:text-white hover:bg-white/5 rounded transition-all">
                                        <i className="fas fa-expand text-xs"></i>
                                    </button>
                                    <button className="p-1.5 text-gray-400 hover:text-white hover:bg-white/5 rounded transition-all">
                                        <i className="fas fa-download text-xs"></i>
                                    </button>
                                </div>
                            </div>
                            <ChartRenderer option={message.chartConfig} height="300px" />
                        </div>
                    )}

                    {/* 关键洞察 - 确保是字符串数组 */}
                    {message.insights && message.insights.length > 0 && (
                        <div className="glass rounded-xl p-4 mt-4">
                            <div className="flex items-center space-x-2 mb-3">
                                <i className="fas fa-lightbulb text-amber-400 text-sm"></i>
                                <span className="text-sm font-medium text-white">关键洞察</span>
                            </div>
                            <ul className="space-y-2">
                                {message.insights.map((insight, index) => (
                                    <li key={index} className="flex items-start space-x-2 text-xs text-gray-400">
                                        <i className="fas fa-circle text-[4px] text-indigo-400 mt-1.5"></i>
                                        {/* ✅ 安全渲染 insight */}
                                        <span>{typeof insight === 'string' ? insight : String(insight)}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* 代码块 */}
                    {message.code && (
                        <details className="group mt-4">
                            <summary className="flex items-center space-x-2 text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition-all">
                                <i className="fas fa-chevron-right text-[10px] group-open:rotate-90 transition-transform"></i>
                                <span>查看生成的分析代码</span>
                            </summary>
                            <CodeBlock code={message.code || ''} language="python" className="mt-3" />
                        </details>
                    )}

                    {/* 操作按钮 */}
                    {message.actions && message.actions.length > 0 && (
                        <div className="flex items-center space-x-2 mt-4 pt-3 border-t border-white/5">
                            {message.actions.map((action, index) => (
                                <button
                                    key={index}
                                    onClick={action.onClick}
                                    className="btn-ghost px-3 py-1.5 text-xs text-gray-400 rounded-lg transition-all flex items-center space-x-1.5"
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

export default ChatMessage;