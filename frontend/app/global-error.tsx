"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCcw } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log fatal errors here (ex: Sentry)
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen flex items-center justify-center p-6">
        <div className="flex flex-col items-center justify-center text-center max-w-lg mx-auto">
          <div className="w-24 h-24 rounded-full bg-red-500/10 flex items-center justify-center mb-8 border-2 border-red-500/20 shadow-[0_0_40px_rgba(239,68,68,0.15)]">
            <AlertTriangle className="w-12 h-12 text-red-500" />
          </div>

          <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
            Critical System Error
          </h1>
          
          <p className="text-lg text-slate-400 mb-10 leading-relaxed">
            A fatal error occurred at the root level of the application. The engineering team has been triggered automatically.
          </p>

          <Button 
            onClick={() => reset()} 
            className="px-8 py-6 text-base bg-white text-black hover:bg-slate-200 group font-bold"
          >
            <RefreshCcw className="w-5 h-5 mr-2 transition-transform group-hover:-rotate-180 duration-500" />
            Restart Application
          </Button>
        </div>
      </body>
    </html>
  );
}
