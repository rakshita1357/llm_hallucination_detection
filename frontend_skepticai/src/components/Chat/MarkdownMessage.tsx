import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CodeBlock } from './CodeBlock.tsx';

interface MarkdownMessageProps {
  content: string;
  className?: string;
}

export const MarkdownMessage: React.FC<MarkdownMessageProps> = ({ content, className = '' }) => {
  return (
    <div className={`prose-skeptic text-slate-200 ${className}`}>
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className: codeClassName, children, ...props }: any) {
            const match = /language-(\w+)/.exec(codeClassName || '');
            const codeText = String(children).replace(/\n$/, '');

            if (!inline && (match || codeText.includes('\n'))) {
              return (
                <CodeBlock
                  language={match ? match[1] : 'text'}
                  value={codeText}
                />
              );
            }

            return (
              <code
                className="px-1.5 py-0.5 rounded bg-slate-800 text-blue-300 font-mono text-[13px] border border-slate-700/50"
                {...props}
              >
                {children}
              </code>
            );
          },
          a({ node, href, children, ...props }: any) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noreferrer noopener"
                className="text-blue-400 hover:text-blue-300 underline underline-offset-2 transition inline-flex items-center gap-1 font-medium"
                {...props}
              >
                {children}
              </a>
            );
          },
          table({ children }: any) {
            return (
              <div className="overflow-x-auto my-3 rounded-lg border border-slate-700">
                <table className="w-full text-left text-xs border-collapse divide-y divide-slate-700">
                  {children}
                </table>
              </div>
            );
          },
          th({ children }: any) {
            return <th className="bg-slate-800 px-3 py-2 font-semibold text-slate-200 border-b border-slate-700">{children}</th>;
          },
          td({ children }: any) {
            return <td className="px-3 py-2 text-slate-300 border-b border-slate-800/80">{children}</td>;
          }
        }}
      >
        {content}
      </Markdown>
    </div>
  );
};
