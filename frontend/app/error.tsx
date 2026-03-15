"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCcw, Home } from "lucide-react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
    setMounted(true);
  }, [error]);

  if (!mounted) return null;

  return (
    <main className="min-h-screen flex flex-col relative bg-background">
      <Navbar />

      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center relative z-10">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-red-500/5 rounded-full blur-[100px] -z-10 pointer-events-none" />

        <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mb-8 border border-red-500/20">
          <AlertCircle className="w-10 h-10 text-red-500" />
        </div>

        <h1 className="text-4xl md:text-5xl font-outfit font-black tracking-tight mb-4">
          Something went wrong
        </h1>
        
        <p className="text-lg text-muted-foreground max-w-md mx-auto mb-10">
          An unexpected error occurred while processing your request. Our team has been notified.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <Button 
            onClick={() => reset()} 
            className="px-8 py-6 text-base bg-foreground text-background hover:bg-foreground/90 group"
          >
            <RefreshCcw className="w-5 h-5 mr-2 transition-transform group-hover:rotate-180 duration-500" />
            Try again
          </Button>
          <Link href="/">
            <Button variant="outline" className="px-8 py-6 text-base text-muted-foreground border-border hover:bg-accent/5">
              <Home className="w-5 h-5 mr-2" />
              Go home
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
