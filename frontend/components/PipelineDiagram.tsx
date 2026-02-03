'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

const PIPELINE_MERMAID = `
flowchart TD
    Entry([Message]) --> Scout[Scout]
    Scout -->|is_news| Librarian[Librarian]
    Scout -->|not news| End1([End])
    Librarian -->|not duplicate| Translator[Translator]
    Librarian -->|duplicate| End2([End])
    Translator --> Analyst[Analyst]
    Analyst --> Editor[Editor]
    Editor --> Save([Save])
`;

export default function PipelineDiagram() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !containerRef.current) return;

    mermaid.initialize({
      startOnLoad: false,
      theme: 'neutral',
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
      },
    });

    const id = 'pipeline-diagram-' + Math.random().toString(36).slice(2);
    containerRef.current.id = id;

    mermaid
      .render(id, PIPELINE_MERMAID)
      .then(({ svg }) => {
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      })
      .catch((err) => {
        if (containerRef.current) {
          containerRef.current.innerHTML = `<p class="text-sm text-red-600">Diagram failed to render: ${err.message}</p>`;
        }
      });
  }, [mounted]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 overflow-x-auto">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Diagram</h2>
      <div className="flex justify-center min-h-[200px] items-center text-gray-500 text-sm">
        {!mounted ? (
          'Loading diagram…'
        ) : (
          <div ref={containerRef} className="mermaid w-full flex justify-center" />
        )}
      </div>
    </div>
  );
}
