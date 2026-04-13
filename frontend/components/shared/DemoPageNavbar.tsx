"use client";

import Link from "next/link";
import Image from "next/image";
import { useState, useEffect, useCallback, useMemo } from "react";

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

function NavLinks({
  className = "",
  closeOnClick = false,
  navItems = [],
}: {
  className?: string;
  closeOnClick?: boolean;
  navItems?: { label: string; href: string }[];
}) {
  const links = useMemo(
    () =>
      navItems.map((item) => {
        const link = (
          <Link
            href={item.href}
            className="font-semibold hover:text-accent transition-colors lg:py-4"
          >
            {item.label}
          </Link>
        );

        return closeOnClick ? (
          <DrawerClose key={item.label} asChild>
            {link}
          </DrawerClose>
        ) : (
          <Link
            key={item.label}
            href={item.href}
            className="font-semibold hover:text-accent transition-colors lg:py-4"
          >
            {item.label}
          </Link>
        );
      }),
    [navItems, closeOnClick],
  );

  return (
    <div className={`flex flex-col lg:flex-row gap-6 ${className}`}>
      {links}
    </div>
  );
}

type DemoPageNavbarProps = {
  iconLink?: string;
  navItems?: { label: string; href: string }[];
};

export const DemoPageNavbar = ({ iconLink, navItems }: DemoPageNavbarProps) => {
  const { goTo } = useDomainNavigation();
  const [isScrolled, setIsScrolled] = useState(false);

  const handleScroll = useCallback(() => {
    setIsScrolled(window.scrollY > 20);
  }, []);

  useEffect(() => {
    handleScroll(); // initial check
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

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
          onClick={() => goTo(iconLink)}
          aria-label="Go to home"
          className="relative w-36 h-10 hover:opacity-80 transition-opacity"
        >
          <Image
            src="/AutomEdge-logo-light-1.png"
            alt="AutomEdge logo"
            fill
            priority
            sizes="140px"
            className="object-contain dark:hidden pointer-events-none"
          />
          <Image
            src="/AutomEdge-logo-light-1.png"
            alt="AutomEdge logo"
            fill
            priority
            sizes="140px"
            className="object-contain hidden dark:block pointer-events-none"
          />
        </button>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {/* Desktop CTA */}
          <Link href="#calendar" className="hidden sm:block">
            <Button className="px-6 py-5 bg-cta text-[#412402] font-bold shadow-xl hover:-translate-y-0.5 transition-all rounded-xl">
              Book My Demo
            </Button>
          </Link>

          {/* Mobile Drawer */}
          <Drawer direction="top">
            <DrawerTrigger
              aria-label="Open menu"
              className="md:hidden p-2 rounded-md hover:bg-muted transition"
            >
              <Equal className="h-6 w-6" />
            </DrawerTrigger>

            <DrawerContent className="pt-10 px-10 bg-background/60 backdrop-blur-xl">
              <DrawerHeader onClick={() => goTo(iconLink)}>
                <DrawerTitle className="text-start text-muted-foreground text-base">
                  AutomEdgeAi
                </DrawerTitle>
                <DrawerDescription className="text-start text-muted-foreground font-thin text-sm">
                  AI-Powered Lead Response for Home Service Businesses
                </DrawerDescription>
              </DrawerHeader>

              <NavLinks
                closeOnClick
                className="text-3xl font-bold py-5 text-primary ml-3"
                navItems={navItems}
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
