// 完全匹配你后端返回的状态（小写/大写以你实际为准，这里用你之前返回的小写）
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

export interface TaskResponse {
    id: number;
    query: string;
    status: TaskStatus;
    file_path: string;
    result_path: string | null;
    error_message: string | null;
    output?: {
        result: string;
        chart_json: unknown;
    };
}