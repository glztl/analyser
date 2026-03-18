import React from 'react';
import { Upload, message } from 'antd';
import type { UploadProps } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

const { Dragger } = Upload;

interface FileUploadProps {
    onFileUploaded: (filePath: string, filename: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded }) => {
    // Removed unused uploading state

    const uploadProps: UploadProps = {
        name: 'file',
        multiple: false,
        accept: '.csv,.xlsx,.xls',
        beforeUpload: (file) => {
            const isValidType =
                file.type === 'text/csv' ||
                file.type === 'application/vnd.ms-excel' ||
                file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

            if (!isValidType) {
                message.error('只能上传 CSV 或 Excel 文件!');
                return false;
            }

            const isLt10M = file.size / 1024 / 1024 < 10;
            if (!isLt10M) {
                message.error('文件大小不能超过 10MB!');
                return false;
            }

            return true;
        },
        customRequest: async ({ file, onSuccess, onError }) => {
            // setUploading(true); // Removed unused uploading state
            try {
                const formData = new FormData();
                formData.append('file', file as File);

                const response = await fetch('http://localhost:8000/files/upload', {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    throw new Error('上传失败');
                }

                const data = await response.json();
                message.success(`${(file as File).name} 上传成功`);
                onFileUploaded(data.file_path, data.filename);
                onSuccess?.(data);
            } catch (error) {
                message.error('上传失败');
                onError?.(error as Error);
            } finally {
                // setUploading(false); // Removed unused uploading state
            }
        },
    };

    return (
        <Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
                <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
                支持 CSV、XLSX、XLS 格式，文件大小不超过 10MB
            </p>
        </Dragger>
    );
};

export default FileUpload;