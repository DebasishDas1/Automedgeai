import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Search, Construction, ArrowLeft } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/ui/large-name-footer";

export const metadata = {
  title: "404 - Page Not Found | Automedge",
};

export default function NotFound() {
  return (
    <main className="min-h-screen relative flex flex-col bg-background selection:bg-accent/30">
      <Navbar />
      
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center relative z-10 my-32">
        {/* Background blobs */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/5 rounded-full blur-[120px] -z-10 pointer-events-none" />
        
        <div className="w-24 h-24 rounded-full bg-muted/50 flex items-center justify-center mb-8 border-2 border-border">
          <Search className="w-10 h-10 text-muted-foreground" />
        </div>

        <h1 className="font-display font-black text-6xl md:text-8xl tracking-tight mb-4 text-foreground">
          404
        </h1>
        
        <h2 className="text-2xl md:text-3xl font-outfit font-bold mb-6">
          Lost in the <span className="text-accent">pipeline.</span>
        </h2>
        
        <p className="text-lg text-muted-foreground max-w-md mx-auto mb-10 leading-relaxed">
          The page you're trying to reach doesn't exist or has been moved. 
          Let's get you back to booking jobs.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 items-center justify-center">
          <Link href="/">
            <Button className="bg-cta glow-cta shadow-xl px-8 py-6 text-base group">
              <ArrowLeft className="w-5 h-5 mr-2 transition-transform group-hover:-translate-x-1" />
              Return Home
            </Button>
          </Link>
          <Link href="/#contact">
            <Button variant="outline" className="px-8 py-6 text-base group">
              <Construction className="w-5 h-5 mr-2" />
              Contact Support
            </Button>
          </Link>
        </div>
      </div>

      <Footer />
    </main>
  );
}
