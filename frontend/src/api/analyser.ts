import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface UploadFileResponse {
    file_id: string;
    filename: string;
    file_path: string;
    size: number;
}

export interface CreateTaskRequest {
    query: string;
    file_path: string;
}

export interface TaskResponse {
    id: number;
    query: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    file_path: string;
    result_path: string;
    error_message: string | null;
    output?: {
        result: string;
        chart_json: any;
    };
}

export interface AnalysisResult {
    conclusion: string;
    chartConfig: any;
}

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const analyserAPI = {
    // 上传文件
    uploadFile: async (file: File): Promise<UploadFileResponse> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post<UploadFileResponse>('/files/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // 创建任务
    createTask: async (data: CreateTaskRequest): Promise<TaskResponse> => {
        const response = await api.post<TaskResponse>('/tasks/', data);
        return response.data;
    },

    // 获取任务状态
    getTaskStatus: async (taskId: number): Promise<TaskResponse> => {
        const response = await api.get<TaskResponse>(`/tasks/${taskId}`);
        return response.data;
    },

    // 启动分析
    startAnalysis: async (taskId: number): Promise<void> => {
        await api.post('/analysis/start', { task_id: taskId });
    },

    // 轮询任务状态（直到完成或失败）
    pollTaskStatus: async (
        taskId: number,
        onProgress?: (status: TaskResponse) => void,
        interval: number = 2000
    ): Promise<TaskResponse> => {
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const task = await analyserAPI.getTaskStatus(taskId);

                    if (onProgress) {
                        onProgress(task);
                    }

                    if (task.status === 'completed' || task.status === 'failed') {
                        resolve(task);
                    } else {
                        setTimeout(poll, interval);
                    }
                } catch (error) {
                    reject(error);
                }
            };

            poll();
        });
    },
};

export default analyserAPI;