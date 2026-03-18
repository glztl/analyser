import React, { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatMessage, { type MessageData } from './components/ChatMessage';
import { analyserAPI } from './api/analyser';

function App() {
  // ========== State 声明 ==========
  const [filePath, setFilePath] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [messages, setMessages] = useState<MessageData[]>([
    {
      id: 'welcome',
      role: 'agent',
      content: '👋 你好，我是你的 AI 数据分析助手',
      insights: [
        '上传数据文件，我可以帮你探索洞察',
        '生成专业可视化图表',
        '发现数据中的趋势和异常'
      ],
    }
  ]);

  const [inputValue, setInputValue] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<number | null>(null);

  // ========== 处理新对话 ==========
  const handleNewChat = useCallback(() => {
    setMessages([messages[0]]);
    setSelectedFile(null);
    setFilePath('');
    setCurrentTaskId(null);
    setInputValue('');
  }, [messages]);

  // ========== 处理文件上传 ==========
  const handleFileSelected = useCallback(async (file: File) => {
    try {
      console.log('[Upload] Starting upload for:', file.name);

      const uploadResult = await analyserAPI.uploadFile(file);

      console.log('[Upload] API Response:', uploadResult);
      console.log('[Upload] file_path from API:', uploadResult.file_path);

      // 更新 state
      setSelectedFile(file);
      setFilePath(uploadResult.file_path);

      console.log('[Upload] State updated - filePath:', uploadResult.file_path);

      // 显示成功消息
      setMessages(prev => [...prev, {
        id: `file-${Date.now()}`,
        role: 'agent',
        content: `✅ 已加载 **${uploadResult.filename}** (${(uploadResult.size / 1024 / 1024).toFixed(2)} MB)`,
      }]);

    } catch (error: any) {
      console.error('[Upload] Error:', error);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'agent',
        content: `❌ 文件上传失败：${error.message || '请重试'}`,
      }]);
    }
  }, []);

  // ========== 处理发送消息 ==========
  const handleSend = useCallback(async () => {
    // 校验：必须有输入、文件路径，且不在分析中
    if (!inputValue.trim() || !filePath || isAnalyzing) return;

    // 添加用户消息
    const userMessage: MessageData = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsAnalyzing(true);

    // 添加"思考中"消息
    const thinkingId = `thinking-${Date.now()}`;
    setMessages(prev => [...prev, {
      id: thinkingId,
      role: 'agent',
      content: '',
      status: 'thinking',
      progress: [
        { label: '解析文件结构', done: true },
        { label: '理解分析需求', done: true },
        { label: '生成分析代码', done: false, loading: true },
      ],
    }]);

    try {
      // 1. 创建任务（后端同步执行，直接返回完整结果）
      console.log('[Task] Creating with:', {
        query: inputValue.trim(),
        file_path: filePath
      });

      const task = await analyserAPI.createTask({
        query: inputValue.trim(),
        file_path: filePath,  // ✅ 使用绝对路径
      });

      console.log('[Task] Created with output:', task.output);
      setCurrentTaskId(task.id);

      // 更新进度状态
      setMessages(prev => prev.map(msg =>
        msg.id === thinkingId
          ? {
            ...msg,
            progress: msg.progress?.map(p => ({ ...p, done: true, loading: false }))
          }
          : msg
      ));

      // 2. 直接使用 task 的结果（因为后端是同步执行）
      // ✅ 关键修复：检查 task.output 是否存在
      if (task.status === 'completed' && task.output && typeof task.output === 'object') {
        // 安全类型断言
        const output = task.output as {
          result?: string;
          chart_json?: any;
          code_snapshot?: string;
        };

        const chartOption = output.chart_json && typeof output.chart_json === 'object'
          ? output.chart_json
          : {};
        const conclusion = typeof output.result === 'string'
          ? output.result
          : '分析完成';

        console.log('[Debug] Rendering with output:', {
          conclusion: conclusion.substring(0, 50) + '...',
          hasChart: !!chartOption && Object.keys(chartOption).length > 0
        });

        // ✅ 确保所有字段都是正确的类型
        setMessages(prev => prev.map(msg =>
          msg.id === thinkingId
            ? {
              ...msg,
              content: '✅ 分析完成',  // ✅ 字符串
              status: 'completed',
              metrics: [
                { label: '数据行数', value: '4' },
                { label: '峰值', value: '300.00' },
                { label: '均值', value: '200.00' },
              ],
              chartConfig: chartOption,  // ✅ 对象，ChartRenderer 处理
              insights: [  // ✅ 字符串数组
                '销售额在第三季度达到峰值',
                '季度均值为 200.00',
                '建议关注季度波动趋势',
              ],
              code: typeof output.code_snapshot === 'string' ? output.code_snapshot : '',
              actions: [
                { label: '下载报告', icon: 'fa-download', onClick: () => { } },
                { label: '复制结论', icon: 'fa-copy', onClick: () => { } },
                { label: '重新分析', icon: 'fa-rotate', onClick: handleNewChat },
              ],
            }
            : msg
        ));
      } else {
        // 如果任务是异步的（未来扩展），再轮询
        if (task.status === 'pending' || task.status === 'processing') {
          console.log('[Task] Status is pending/processing, polling...');

          const finalResult = await analyserAPI.pollTaskStatus(task.id, (progress) => {
            if (progress.status === 'processing') {
              setMessages(prev => prev.map(msg =>
                msg.id === thinkingId
                  ? { ...msg, content: '🔄 正在执行分析代码...' }
                  : msg
              ));
            }
          }, 2000);

          if (finalResult.status === 'completed' && finalResult.output) {
            const output = finalResult.output as {
              result?: string;
              chart_json?: any;
              code_snapshot?: string;
            };

            setMessages(prev => prev.map(msg =>
              msg.id === thinkingId
                ? {
                  ...msg,
                  content: '✅ 分析完成',
                  status: 'completed',
                  chartConfig: output.chart_json || {},
                  insights: ['分析完成，查看上方结果'],
                }
                : msg
            ));
          } else {
            throw new Error(finalResult.error_message || '分析失败');
          }
        } else {
          // 任务失败或其他状态
          throw new Error(task.error_message || `分析失败: status=${task.status}`);
        }
      }

    } catch (error: any) {
      console.error('[Analysis] Error:', error);
      setMessages(prev => prev.map(msg =>
        msg.id === thinkingId
          ? {
            ...msg,
            content: `❌ 分析失败：${error.message || '未知错误'}`,
            status: 'failed',
          }
          : msg
      ));
    } finally {
      setIsAnalyzing(false);
    }
  }, [inputValue, filePath, isAnalyzing, handleNewChat]);

  // ========== 处理键盘发送 ==========
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  // ========== 渲染 UI ==========
  return (
    <div className="relative flex h-screen bg-[#0a0a0f] text-[#e4e4e7]">
      {/* 背景光效 */}
      <div className="bg-glow glow-1"></div>
      <div className="bg-glow glow-2"></div>

      {/* 侧边栏 */}
      <Sidebar onNewChat={handleNewChat} />

      {/* 主内容区 */}
      <main className="flex-1 flex flex-col relative z-10">
        {/* 顶部栏 */}
        <header className="h-16 glass-strong border-b border-white/5 flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            <h1 className="text-base font-medium text-white">
              {selectedFile?.name || '新建分析'}
            </h1>
            {isAnalyzing && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
                <span>分析中</span>
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button className="btn-ghost px-3 py-1.5 text-xs text-gray-400 rounded-lg transition-all">
              <i className="fas fa-download mr-1.5"></i>导出
            </button>
            <button className="btn-ghost px-3 py-1.5 text-xs text-gray-400 rounded-lg transition-all">
              <i className="fas fa-share mr-1.5"></i>分享
            </button>
            <button
              onClick={handleNewChat}
              className="btn-primary px-4 py-1.5 text-xs text-white rounded-lg font-medium"
            >
              <i className="fas fa-plus mr-1.5"></i>新分析
            </button>
          </div>
        </header>

        {/* 聊天区 */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-6 pb-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
          </div>
        </div>

        {/* 输入区 */}
        <div className="p-6 border-t border-white/5">
          <div className="max-w-4xl mx-auto">

            {/* 文件状态栏 */}
            <div className="mb-3 flex items-center justify-between">
              {selectedFile ? (
                <div className="flex items-center space-x-3 px-4 py-2 rounded-xl glass border border-emerald-500/30 bg-emerald-500/5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                    <i className="fas fa-check text-emerald-400 text-sm"></i>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white truncate">
                      {selectedFile.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedFile(null);
                      setFilePath('');
                    }}
                    className="p-1.5 text-gray-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all"
                    title="移除文件"
                  >
                    <i className="fas fa-times text-xs"></i>
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <i className="fas fa-info-circle text-xs"></i>
                  <span>请先上传数据文件开始分析</span>
                </div>
              )}

              {/* 上传按钮 */}
              <label className="btn-primary px-4 py-2 text-xs text-white rounded-xl font-medium cursor-pointer hover:shadow-lg transition-all flex items-center space-x-2">
                <i className="fas fa-cloud-upload-alt"></i>
                <span>上传文件</span>
                <input
                  type="file"
                  className="hidden"
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      handleFileSelected(file);
                      e.target.value = '';
                    }
                  }}
                />
              </label>
            </div>

            {/* 输入框 + 发送 */}
            <div className="glass rounded-2xl p-2 border transition-all focus-within:border-indigo-500/50">
              <div className="flex items-end space-x-2">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="flex-1 bg-transparent px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none resize-none min-h-[44px] max-h-32"
                  rows={1}
                  placeholder={filePath
                    ? "描述你的分析需求，例如：分析销售趋势并生成图表..."
                    : "请先上传文件"
                  }
                  disabled={!filePath || isAnalyzing}
                />
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || !filePath || isAnalyzing}
                  className={`p-3 rounded-xl transition-all flex items-center justify-center ${inputValue.trim() && filePath && !isAnalyzing
                      ? 'btn-primary text-white shadow-lg'
                      : 'bg-white/5 text-gray-500 cursor-not-allowed'
                    }`}
                  title={!filePath ? "请先上传文件" : !inputValue.trim() ? "请输入分析需求" : "发送"}
                >
                  {isAnalyzing ? (
                    <i className="fas fa-spinner animate-spin text-sm"></i>
                  ) : (
                    <i className="fas fa-arrow-up text-sm"></i>
                  )}
                </button>
              </div>
            </div>

            <div className="mt-3 text-center">
              <p className="text-[10px] text-gray-600">
                支持 CSV、XLSX 格式 • AI 生成内容请核实
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;