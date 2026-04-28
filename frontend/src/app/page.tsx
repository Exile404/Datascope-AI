import Link from "next/link";
import { ArrowRight, BarChart3, Brain, Activity, DollarSign, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ROUTES } from "@/lib/constants";

const FEATURES = [
  {
    title: "Data Profiler",
    description: "Upload any CSV. Get automated EDA, AI-generated insights, and ML recommendations in seconds.",
    href: ROUTES.PROFILER,
    icon: BarChart3,
    color: "from-violet-500 to-purple-500",
    available: true,
  },
  {
    title: "LLM Evaluator",
    description: "Compare model outputs across temperature settings with automated quality scoring.",
    href: ROUTES.EVALUATOR,
    icon: Brain,
    color: "from-cyan-500 to-blue-500",
    available: false,
  },
  {
    title: "Drift Monitor",
    description: "Track LLM output drift, hallucination rates, and performance degradation over time.",
    href: ROUTES.DRIFT,
    icon: Activity,
    color: "from-amber-500 to-orange-500",
    available: false,
  },
  {
    title: "Cost Analyzer",
    description: "Token cost projections across models. Make informed deployment decisions.",
    href: ROUTES.COST,
    icon: DollarSign,
    color: "from-emerald-500 to-teal-500",
    available: false,
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      {/* Hero */}
      <div className="mx-auto max-w-3xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-xs">
          <Sparkles className="h-3.5 w-3.5 text-violet-500" />
          <span className="text-muted-foreground">Powered by a fine-tuned Llama 3.1 8B</span>
        </div>

        <h1 className="bg-gradient-to-br from-foreground via-foreground to-muted-foreground bg-clip-text text-5xl font-bold tracking-tight text-transparent sm:text-6xl">
          Intelligent Data Analysis
        </h1>

        <p className="mt-6 text-lg text-muted-foreground">
          Upload any CSV. Get production-grade exploratory data analysis,
          statistical insights, and ML recommendations from a custom-trained model.
        </p>

        <div className="mt-10 flex items-center justify-center gap-4">
          <Button size="lg" asChild>
            <Link href={ROUTES.PROFILER}>
              Try the Profiler
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <a
              href="https://github.com/exile404/datascope-ai"
              target="_blank"
              rel="noopener noreferrer"
            >
              View on GitHub
            </a>
          </Button>
        </div>
      </div>

      {/* Features grid */}
      <div className="mt-24 grid gap-6 md:grid-cols-2">
        {FEATURES.map(({ title, description, href, icon: Icon, color, available }) => (
          <Link
            key={href}
            href={available ? href : "#"}
            className={
              available
                ? "group"
                : "pointer-events-none opacity-60"
            }
          >
            <Card className="relative overflow-hidden p-6 transition-all group-hover:border-foreground/20 group-hover:shadow-lg">
              <div className="flex items-start gap-4">
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${color}`}
                >
                  <Icon className="h-6 w-6 text-white" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold">{title}</h3>
                    {!available && (
                      <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                        Coming Soon
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {description}
                  </p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
              </div>
            </Card>
          </Link>
        ))}
      </div>

      {/* Tech stack */}
      <div className="mt-24 border-t border-border pt-12 text-center">
        <p className="text-xs uppercase tracking-widest text-muted-foreground">
          Built with
        </p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-sm text-muted-foreground">
          <span>Llama 3.1 8B</span>
          <span>·</span>
          <span>Unsloth + LoRA</span>
          <span>·</span>
          <span>FastAPI</span>
          <span>·</span>
          <span>LangChain</span>
          <span>·</span>
          <span>Next.js 15</span>
          <span>·</span>
          <span>shadcn/ui</span>
        </div>
      </div>
    </div>
  );
}