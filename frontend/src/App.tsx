import React, { useState } from 'react';
import { Layout, Typography, Input, Button, message, Divider, Card } from 'antd';
import { SendOutlined, FileTextOutlined, RocketOutlined } from '@ant-design/icons';
import FileUpload from './components/FileUpload';
import AnalysisResult from './components/AnalysisResult';
import { analyserAPI, type TaskResponse } from './api/analyser';

const { Header, Content } = Layout;
const { Title, Paragraph } = Typography;
const { TextArea } = Input;

function App() {
  const [filePath, setFilePath] = useState<string>('');
  const [filename, setFilename] = useState<string>('');
  const [query, setQuery] = useState<string>('');
  const [currentTask, setCurrentTask] = useState<TaskResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUploaded = (path: string, name: string) => {
    setFilePath(path);
    setFilename(name);
    message.success('文件上传成功，请输入您的问题');
  };

  const handleAnalyze = async () => {
    if (!filePath) {
      message.error('请先上传文件');
      return;
    }
    if (!query.trim()) {
      message.error('请输入分析问题');
      return;
    }

    setLoading(true);
    setError(null);
    setCurrentTask(null);

    try {
      // 1. 创建任务（后端会自动执行分析）
      const task = await analyserAPI.createTask({
        query,
        file_path: filePath,
      });

      // 2. 如果任务已经是 completed，直接显示结果
      if (task.status === 'completed') {
        message.success('分析完成！');
        setCurrentTask(task);
        return;
      }

      // 3. 如果是 pending/processing，轮询等待完成
      if (task.status === 'pending' || task.status === 'processing') {
        const completedTask = await analyserAPI.pollTaskStatus(
          task.id,
          (progressTask) => {
            setCurrentTask(progressTask);
            if (progressTask.status === 'processing') {
              message.loading('AI 正在分析数据...', 0);
            }
          }
        );

        message.destroy(); // 关闭加载提示

        if (completedTask.status === 'completed') {
          message.success('分析完成！');
          setCurrentTask(completedTask);
        } else {
          message.error('分析失败');
          setError(completedTask.error_message || '未知错误');
        }
      }
    } catch (err: any) {
      message.destroy();
      console.error(err);
      setError(err.message || '分析过程中出现错误');
      message.error('分析失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout className="min-h-screen bg-gray-50">
      <Header className="bg-white shadow-sm flex items-center px-8">
        <RocketOutlined className="text-3xl text-blue-600 mr-3" />
        <Title level={2} className="m-0 text-blue-600">
          Analyser - AI 数据分析助手
        </Title>
      </Header>

      <Content className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* 上传区域 */}
          <div className="mb-8">
            <Card
              title={<Title level={4}><FileTextOutlined className="mr-2" />上传数据文件</Title>}
              className="card-shadow mb-6"
            >
              <FileUpload onFileUploaded={handleFileUploaded} />

              {filename && (
                <div className="mt-4 p-3 bg-green-50 rounded border border-green-200">
                  <Paragraph className="m-0 text-green-800">
                    <strong>已上传:</strong> {filename}
                  </Paragraph>
                </div>
              )}
            </Card>

            {/* 问题输入 */}
            <Card
              title={<Title level={4}><SendOutlined className="mr-2" />输入分析问题</Title>}
              className="card-shadow"
            >
              <TextArea
                rows={4}
                placeholder="例如：分析销售趋势、计算季度增长率、找出最高销售额的季度..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="mb-4"
                disabled={!filePath || loading}
              />

              <Button
                type="primary"
                size="large"
                icon={<RocketOutlined />}
                onClick={handleAnalyze}
                loading={loading}
                disabled={!filePath || !query.trim()}
                className="w-full"
              >
                开始分析
              </Button>
            </Card>
          </div>

          <Divider />

          {/* 结果展示 */}
          <AnalysisResult
            task={currentTask}
            loading={loading}
            error={error}
          />
        </div>
      </Content>
    </Layout>
  );
}

export default App;