import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface FileDropzoneProps {
    onFileSelected: (file: File) => void;
    acceptedTypes?: string;
    maxSize?: number;
}

const FileDropzone: React.FC<FileDropzoneProps> = ({
    onFileSelected,
    acceptedTypes = '.csv,.xlsx,.xls',
    maxSize = 10 * 1024 * 1024, // 10MB
}) => {
    const [error, setError] = useState<string>('');

    const onDrop = useCallback((acceptedFiles: File[]) => {
        setError('');
        const file = acceptedFiles[0];

        if (!file) return;

        if (file.size > maxSize) {
            setError(`文件大小不能超过 ${maxSize / 1024 / 1024}MB`);
            return;
        }

        onFileSelected(file);
    }, [onFileSelected, maxSize]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv'],
            'application/vnd.ms-excel': ['.xls'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        },
        multiple: false,
        maxSize,
    });

    return (
        <div className="space-y-3">
            <div
                {...getRootProps()}
                className={`upload-dropzone rounded-2xl p-8 text-center cursor-pointer transition-all ${isDragActive ? 'drag-over' : ''
                    }`}
            >
                <input {...getInputProps()} />

                <div className="flex flex-col items-center space-y-4">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
                        <i className="fas fa-cloud-upload-alt text-2xl text-indigo-400"></i>
                    </div>

                    <div>
                        <p className="text-sm font-medium text-white">
                            {isDragActive ? '释放文件以上传' : '拖拽文件到此处'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                            支持 CSV、XLSX、XLS 格式，最大 10MB
                        </p>
                    </div>

                    <button className="btn-primary px-4 py-2 text-xs text-white rounded-lg font-medium">
                        <i className="fas fa-folder-open mr-1.5"></i>
                        浏览文件
                    </button>
                </div>
            </div>

            {error && (
                <p className="text-xs text-rose-400 text-center">{error}</p>
            )}
        </div>
    );
};

export default FileDropzone;