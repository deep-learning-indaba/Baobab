import React from "react";
import ReactMarkdown from 'react-markdown';
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import 'katex/dist/katex.min.css';
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";

function MarkdownRenderer({ source, children, components, ...props }) {
    return (
        <div className="markdown-container">
            <ReactMarkdown
                {...props}
                remarkPlugins={[remarkMath, remarkGfm, remarkBreaks]}
                rehypePlugins={[rehypeKatex]}
                components={{
                    a: ({ href, children: linkChildren }) => (
                        <a href={href} target="_blank" rel="noopener noreferrer">{linkChildren}</a>
                    ),
                    ...components
                }}
            >
                {source || children}
            </ReactMarkdown>
        </div>
    );
}

export default MarkdownRenderer;
