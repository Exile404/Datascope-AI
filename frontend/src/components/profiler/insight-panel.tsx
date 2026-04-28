"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Sparkles, Brain, ChevronDown, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface InsightPanelProps {
  thinking: string | null;
  answer: string;
}

export function InsightPanel({ thinking, answer }: InsightPanelProps) {
  const [showThinking, setShowThinking] = useState(false);

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-border bg-gradient-to-r from-violet-500/5 via-purple-500/5 to-blue-500/5 px-6 py-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-violet-500" />
          <h3 className="text-sm font-semibold uppercase tracking-wider">
            AI Analysis
          </h3>
        </div>
      </div>

      <div className="p-6">
        {thinking && (
          <div className="mb-6">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowThinking((v) => !v)}
              className="-ml-2 h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
            >
              {showThinking ? (
                <ChevronDown className="h-3.5 w-3.5" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5" />
              )}
              <Brain className="h-3.5 w-3.5" />
              <span>Reasoning trace</span>
            </Button>

            {showThinking && (
              <div className="mt-3 rounded-lg border border-border bg-muted/30 p-4">
                <div className="prose prose-sm prose-neutral max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {thinking}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="prose prose-neutral max-w-none dark:prose-invert prose-headings:font-semibold prose-h2:mt-8 prose-h2:mb-4 prose-h2:text-lg prose-h2:first:mt-0 prose-p:text-muted-foreground prose-li:text-muted-foreground prose-strong:text-foreground">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
        </div>
      </div>
    </Card>
  );
}