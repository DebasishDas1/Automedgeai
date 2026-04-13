"use client";

import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { useDomainNavigation } from "@/hook/useDomainNavigation";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import { Equal } from "lucide-react";
import React from "react";

const navItems = [
  { title: "The Problem", href: "/#problem" },
  { title: "How It Works", href: "/#how-it-works" },
  { title: "The Solution", href: "/#solution" },
  { title: "The Engine", href: "/#the-engine" },
  { title: "Impact", href: "/#impact" },
];

function NavLinks({
  className = "",
  closeOnClick = false,
}: {
  className?: string;
  closeOnClick?: boolean;
}) {
  const Wrapper = closeOnClick ? DrawerClose : React.Fragment;

  return (
    <div className={`flex flex-col lg:flex-row gap-6 ${className}`}>
      {navItems.map((item) => (
        <Wrapper key={item.title} {...(closeOnClick ? { asChild: true } : {})}>
          <Link
            href={item.href}
            className="font-semibold hover:text-accent lg:py-4"
          >
            {item.title}
          </Link>
        </Wrapper>
      ))}
    </div>
  );
}

export function Navbar() {
  const { goHome } = useDomainNavigation();

  return (
    <nav className="fixed top-0 z-50 w-full bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        {/* Logo */}
        <button
          onClick={goHome}
          className="relative w-35 h-10 flex items-center"
        >
          <Image
            src="/AutomEdge-logo-light-1.png"
            alt="AutomEdge logo"
            fill
            priority
            sizes="140px"
            className="object-contain dark:hidden select-none pointer-events-none"
          />
          <Image
            src="/AutomEdge-logo-light-1.png"
            alt="AutomEdge logo"
            fill
            priority
            sizes="140px"
            className="object-contain hidden dark:block select-none pointer-events-none"
          />
        </button>

        {/* Desktop Navigation */}
        <NavLinks className="hidden lg:flex items-center gap-8 font-bold" />

        {/* Desktop CTA */}
        <Link href="/#contact" className="hidden lg:block">
          <Button className="bg-cta text-black font-semibold hover:bg-cta-hover rounded-xl">
            Get a Free Demo
          </Button>
        </Link>

        {/* Mobile Menu */}
        <Drawer direction="top">
          <DrawerTrigger className="lg:hidden p-2 rounded-md hover:bg-muted">
            <Equal className="h-6 w-6" aria-label="Menu" />
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

            <div className="text-3xl font-bold py-10 text-primary ml-3">
              <NavLinks closeOnClick />
            </div>

            <DrawerFooter className="flex justify-start">
              <DrawerClose asChild>
                <Link
                  href="/#contact"
                  className="text-3xl font-black text-accent dark:text-cta"
                >
                  Get a Free Demo
                </Link>
              </DrawerClose>
            </DrawerFooter>
          </DrawerContent>
        </Drawer>
      </div>
    </nav>
  );
}
