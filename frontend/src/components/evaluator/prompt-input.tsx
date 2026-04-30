"use client";

import { useState } from "react";
import { Sparkles, Zap } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

type Mode = "single" | "compare";

interface PromptInputProps {
  onSubmit: (mode: Mode, payload: {
    prompt: string;
    system: string;
    temperature?: number;
    temperatures?: number[];
  }) => void;
  loading?: boolean;
}

export function PromptInput({ onSubmit, loading }: PromptInputProps) {
  const [system, setSystem] = useState("You are a senior data scientist.");
  const [prompt, setPrompt] = useState("");
  const [temperature, setTemperature] = useState(0.3);
  const [mode, setMode] = useState<Mode>("single");

  const canSubmit = prompt.trim().length > 0 && !loading;

  const handleSubmit = () => {
    if (!canSubmit) return;
    if (mode === "single") {
      onSubmit("single", { prompt, system, temperature });
    } else {
      onSubmit("compare", {
        prompt,
        system,
        temperatures: [0.1, 0.5, 0.9],
      });
    }
  };

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="system">System Prompt</Label>
          <Input
            id="system"
            value={system}
            onChange={(e) => setSystem(e.target.value)}
            placeholder="Define the assistant's role"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="prompt">Test Prompt</Label>
          <Textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter a prompt to evaluate..."
            rows={4}
          />
        </div>

        {mode === "single" && (
          <div className="space-y-2">
            <Label htmlFor="temp" className="flex justify-between">
              <span>Temperature</span>
              <span className="font-mono text-violet-500">{temperature.toFixed(1)}</span>
            </Label>
            <input
              id="temp"
              type="range"
              min={0}
              max={2}
              step={0.1}
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              className="w-full accent-violet-500"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Precise</span>
              <span>Creative</span>
            </div>
          </div>
        )}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-1 rounded-lg bg-muted/50 p-1">
            <button
              onClick={() => setMode("single")}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                mode === "single"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Single
            </button>
            <button
              onClick={() => setMode("compare")}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                mode === "compare"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Compare 3 Temperatures
            </button>
          </div>

          <Button onClick={handleSubmit} disabled={!canSubmit}>
            {mode === "single" ? (
              <>
                <Sparkles className="mr-2 h-3.5 w-3.5" />
                Evaluate
              </>
            ) : (
              <>
                <Zap className="mr-2 h-3.5 w-3.5" />
                Compare All
              </>
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
}