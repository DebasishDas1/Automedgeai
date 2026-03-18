"use client";

import Image from "next/image";
import { Button } from "@/components/ui/button";
import { useDomainNavigation } from "@/hook/useDomainNavigation";
import Link from "next/link";

const MAIN_DOMAIN = process.env.NEXT_PUBLIC_MAIN_DOMAIN || "/";

export const DemoPageNavbar = () => {
  const { goHome } = useDomainNavigation();
  return (
    <nav className="fixed top-0 z-50 w-full bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        {/* Logo */}
        <a
          onClick={() => goHome()}
          className="relative flex items-center w-[140px] h-[40px]"
        >
          {/* Light Mode Logo */}
          <Image
            src="/AutomEdge-logo-light.png"
            alt="AutomEdge logo"
            fill
            sizes="140px"
            priority
            className="object-contain dark:hidden select-none pointer-events-none"
          />

          {/* Dark Mode Logo */}
          <Image
            src="/AutomEdge-logo.png"
            alt="AutomEdge logo"
            fill
            sizes="140px"
            priority
            className="object-contain hidden dark:block select-none pointer-events-none"
          />
        </a>

        {/* CTA */}
        <Link href="#calendar">
          <Button className="bg-cta px-4 py-2 rounded-full font-semibold">
            Get a Free Demo
          </Button>
        </Link>
      </div>
    </nav>
  );
};
