import React from 'react';

interface CodeBlockProps {
    code: string;
    language?: string;
    className?: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ code, className = '' }) => {
    // 简单的高亮处理（生产环境可用 prismjs）
    const highlightCode = (code: string) => {
        return code
            .replace(/(import|from|as|def|return|if|else|for|in|try|except)/g, '<span class="text-purple-400">$1</span>')
            .replace(/('.*?'|".*?")/g, '<span class="text-green-400">$1</span>')
            .replace(/\b(\d+)\b/g, '<span class="text-orange-400">$1</span>')
            .replace(/(#.*)/g, '<span class="text-gray-500">$1</span>');
    };

    return (
        <div className={`code-block rounded-xl p-4 text-xs overflow-x-auto ${className}`}>
            <pre className="text-gray-400 font-mono">
                <code dangerouslySetInnerHTML={{ __html: highlightCode(code) }} />
            </pre>
        </div>
    );
};

export default CodeBlock;