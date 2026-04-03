"use client";

import Link from "next/link";
import Image from "next/image";
import { useState, useEffect } from "react";

import { Button } from "@/components/ui/button";
import { useDomainNavigation } from "@/hook/useDomainNavigation";

import {
  Drawer,
  DrawerTrigger,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerFooter,
  DrawerClose,
} from "@/components/ui/drawer";

import { Equal } from "lucide-react";

const navItems = [
  { label: "How it Works", href: "#how-it-works" },
  { label: "Roi Calculator", href: "#roi" },
  { label: "Faq", href: "#faq" },
];

function NavLinks({
  className = "",
  closeOnClick = false,
}: {
  className?: string;
  closeOnClick?: boolean;
}) {
  return (
    <div className={`flex flex-col lg:flex-row gap-6 ${className}`}>
      {navItems.map((item) => {
        const linkEl = (
          <Link
            href={item.href}
            className="font-semibold hover:text-accent lg:py-4"
          >
            {item.label}
          </Link>
        );

        return closeOnClick ? (
          <DrawerClose key={item.label} asChild>
            {linkEl}
          </DrawerClose>
        ) : (
          <div key={item.label}>{linkEl}</div>
        );
      })}
    </div>
  );
}

export const DemoPageNavbar = () => {
  const { goHome } = useDomainNavigation();

  const [isScrolled, setIsScrolled] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const updateScroll = () => {
      const y = window.scrollY;
      setIsScrolled(y > 20);

      const total = document.documentElement.scrollHeight - window.innerHeight;
      setScrollProgress(total ? (y / total) * 100 : 0);
    };

    updateScroll();
    window.addEventListener("scroll", updateScroll, { passive: true });
    return () => window.removeEventListener("scroll", updateScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 w-full z-50 transition-all duration-300 border-b ${
        isScrolled
          ? "bg-background/80 backdrop-blur-xl border-border/50 py-3 shadow-[0_8px_30px_rgb(0,0,0,0.04)]"
          : "bg-transparent border-transparent py-5"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 lg:px-8">
        {/* Logo */}
        <button
          onClick={goHome}
          className="relative w-[140px] h-[40px] cursor-pointer hover:opacity-80 transition-opacity"
        >
          <Image
            src="/AutomEdge-logo-light.png"
            alt="AutomEdge logo"
            fill
            priority
            sizes="140px"
            className="object-contain dark:hidden select-none pointer-events-none"
          />
          <Image
            src="/AutomEdge-logo.png"
            alt="AutomEdge logo"
            fill
            priority
            sizes="140px"
            className="object-contain hidden dark:block select-none pointer-events-none"
          />
        </button>

        {/* Desktop CTA + Mobile Menu */}
        <div className="flex items-center gap-4">
          {/* Desktop CTA */}
          <Link href="#calendar" className="hidden sm:block">
            <Button className="px-6 py-5 bg-cta text-[#412402] font-bold shadow-xl glow-cta hover:-translate-y-0.5 transition-all rounded-xl">
              Book My Demo
            </Button>
          </Link>

          {/* Mobile Drawer */}
          <Drawer direction="top">
            <DrawerTrigger className="md:hidden p-2 rounded-md hover:bg-muted">
              <Equal className="h-6 w-6" />
            </DrawerTrigger>

            <DrawerContent className="pt-10 px-10 bg-background/60 backdrop-blur-xl">
              <DrawerHeader onClick={goHome}>
                <DrawerTitle className="text-start text-muted-foreground text-base">
                  AutomEdge
                </DrawerTitle>
                <DrawerDescription className="text-start text-muted-foreground font-thin text-sm">
                  AI-Powered Lead Response for Home Service Businesses
                </DrawerDescription>
              </DrawerHeader>

              <NavLinks
                closeOnClick
                className="text-3xl font-bold py-10 text-primary ml-3"
              />

              <DrawerFooter className="mt-auto flex justify-start pb-10">
                <DrawerClose asChild>
                  <Link href="#calendar">
                    <Button className="text-3xl font-black text-accent dark:text-cta bg-transparent p-0">
                      Book My Demo
                    </Button>
                  </Link>
                </DrawerClose>
              </DrawerFooter>
            </DrawerContent>
          </Drawer>
        </div>
      </div>
    </nav>
  );
};
