"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { useDomainNavigation } from "@/hook/useDomainNavigation";
import { Menu, X, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const NAV_LINKS = [
  { label: "How it Works", href: "#how-it-works" },
  { label: "ROI Calculator", href: "#roi" },
  { label: "FAQ", href: "#faq" },
];

export const DemoPageNavbar = () => {
  const { goHome } = useDomainNavigation();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrolled = window.scrollY > 20;
      setIsScrolled(scrolled);

      const totalHeight =
        document.documentElement.scrollHeight - window.innerHeight;
      const progress = totalHeight > 0 ? (window.scrollY / totalHeight) * 100 : 0;
      setScrollProgress(progress);
    };
    
    // Initial call
    handleScroll();
    
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    setIsMobileMenuOpen(false);
    const element = document.getElementById(id.replace("#", ""));
    element?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <>
      <nav
        className={`fixed top-0 z-50 w-full transition-all duration-300 border-b ${
          isScrolled
            ? "bg-background/80 backdrop-blur-xl border-border/50 py-3 shadow-[0_8px_30px_rgb(0,0,0,0.04)]"
            : "bg-transparent border-transparent py-5"
        }`}
      >
        {/* Scroll Progress Bar */}
        {/* Scroll Progress Bar (Subtle) */}
        <div
          className="absolute top-0 left-0 h-px bg-accent/50 transition-all duration-300 pointer-events-none"
          style={{ width: `${scrollProgress}%` }}
        />
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 lg:px-8">
          {/* Logo */}
          <div className="flex items-center gap-8">
            <Link
              href="/"
              onClick={(e) => {
                // Optional: only override if using subdomains
                e.preventDefault();
                goHome();
              }}
              className="relative flex items-center w-[140px] h-[40px] cursor-pointer hover:opacity-80 transition-opacity"
            >
              <Image
                src="/AutomEdge-logo-light.png"
                alt="AutomEdge logo"
                fill
                sizes="140px"
                priority
                className="object-contain dark:hidden select-none"
              />
              <Image
                src="/AutomEdge-logo.png"
                alt="AutomEdge logo"
                fill
                sizes="140px"
                priority
                className="object-contain hidden dark:block select-none"
              />
            </Link>
          </div>

          {/* Desktop CTA & Mobile Toggle */}
          <div className="flex items-center gap-4">
            <div className="hidden sm:block">
              <Link href="#calendar">
                <Button className="px-6 py-5 bg-cta glow-cta text-[#412402] font-bold shadow-xl hover:-translate-y-0.5 transition-all rounded-xl">
                  Book My Demo
                </Button>
              </Link>
            </div>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle Mobile Menu"
              className="p-2 -mr-2 md:hidden text-foreground hover:bg-muted/50 rounded-lg transition-colors"
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileMenuOpen(false)}
              className="fixed inset-0 z-60 bg-background/60 backdrop-blur-sm md:hidden"
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed right-0 top-0 z-70 h-full w-[280px] bg-card border-l border-border/50 p-8 shadow-2xl md:hidden"
            >
              <div className="flex flex-col h-full">
                <div className="flex justify-between items-center mb-10">
                  <span className="font-outfit font-black text-xl tracking-tight">
                    Menu
                  </span>
                  <button
                    onClick={() => setIsMobileMenuOpen(false)}
                    aria-label="Close Mobile Menu"
                  >
                    <X size={24} className="text-muted-foreground" />
                  </button>
                </div>

                <div className="flex flex-col gap-6">
                  {NAV_LINKS.map((link) => (
                    <a
                      key={link.label}
                      href={link.href}
                      onClick={(e) => {
                        e.preventDefault();
                        scrollToSection(link.href);
                      }}
                      className="text-xl font-bold text-foreground text-left flex items-center justify-between group cursor-pointer"
                    >
                      {link.label}
                      <ChevronRight className="w-5 h-5 text-accent opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0" />
                    </a>
                  ))}
                </div>

                <div className="mt-auto">
                  <Link
                    href="#calendar"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Button className="w-full py-6 bg-cta glow-cta text-black font-bold shadow-xl rounded-2xl hover:bg-cta-hover">
                      Book My Demo
                    </Button>
                  </Link>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};
