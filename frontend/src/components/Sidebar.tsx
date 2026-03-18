import React from 'react';
// import { Link } from 'react-router-dom';

interface SidebarProps {
    onNewChat: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onNewChat }) => {
    const recentFiles = [
        { name: 'sales_q4_2024.csv', size: '2.4 MB', date: '昨天', type: 'csv' },
        { name: 'user_metrics.xlsx', size: '1.1 MB', date: '3 天前', type: 'excel' },
    ];

    const navItems = [
        { icon: 'fa-message', label: '新对话', active: true, action: onNewChat },
        { icon: 'fa-clock', label: '历史记录', href: '#' },
        { icon: 'fa-folder', label: '数据集', href: '#' },
        { icon: 'fa-chart-pie', label: '仪表板', href: '#' },
    ];

    return (
        <aside className="w-72 glass-strong flex flex-col border-r border-white/5">
            {/* Logo */}
            <div className="h-20 flex items-center px-6 border-b border-white/5">
                <div className="flex items-center space-x-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center animate-pulse-glow">
                        <i className="fas fa-sparkles text-white text-sm"></i>
                    </div>
                    <div>
                        <span className="font-semibold text-white tracking-tight">Analyser</span>
                        <div className="text-xs text-gray-500">AI Data Analytics</div>
                    </div>
                </div>
            </div>

            {/* 导航 */}
            <nav className="flex-1 py-6 px-3">
                <div className="space-y-1">
                    {navItems.map((item, index) => (
                        <button
                            key={index}
                            onClick={item.action}
                            className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all text-left ${item.active
                                ? 'bg-white/5 border border-white/10 text-white'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            <i className={`fas ${item.icon} ${item.active ? 'text-indigo-400' : ''}`}></i>
                            <span className="text-sm font-medium">{item.label}</span>
                        </button>
                    ))}
                </div>

                {/* 最近文件 */}
                <div className="mt-8">
                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3 px-3">
                        最近上传
                    </div>
                    <div className="space-y-1">
                        {recentFiles.map((file, index) => (
                            <a
                                key={index}
                                href="#"
                                className="flex items-center space-x-3 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                            >
                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${file.type === 'csv' ? 'bg-green-500/10' : 'bg-blue-500/10'
                                    }`}>
                                    <i className={`fas ${file.type === 'csv' ? 'fa-file-csv text-green-400' : 'fa-file-excel text-blue-400'} text-xs`}></i>
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm truncate">{file.name}</div>
                                    <div className="text-xs text-gray-500">{file.size} • {file.date}</div>
                                </div>
                            </a>
                        ))}
                    </div>
                </div>
            </nav>

            {/* 用户 */}
            <div className="p-4 border-t border-white/5">
                <div className="flex items-center space-x-3 p-2 rounded-lg hover:bg-white/5 transition-all cursor-pointer">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center">
                        <span className="text-white text-sm font-semibold">U</span>
                    </div>
                    <div className="flex-1">
                        <div className="text-sm font-medium text-white">User</div>
                        <div className="text-xs text-gray-500">Pro Plan</div>
                    </div>
                    <i className="fas fa-chevron-right text-gray-500 text-xs"></i>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;