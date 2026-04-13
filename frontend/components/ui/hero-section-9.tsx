"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Users, Briefcase, Link as LinkIcon } from "lucide-react";

// 1. Define the props interface to fix the TypeScript error
export interface HeroSectionProps {
  title: React.ReactNode;
  subtitle: string;
  actions: {
    text: string;
    onClick: () => void;
    variant?:
      | "default"
      | "destructive"
      | "outline"
      | "secondary"
      | "ghost"
      | "link";
  }[];
  stats: {
    value: string;
    label: string;
    icon: React.ReactNode;
  }[];
  images: string[];
}

// 2. The HeroSection component itself
const HeroSection = ({
  title,
  subtitle,
  actions,
  stats,
  images,
}: HeroSectionProps) => {
  return (
    <section className="relative overflow-hidden py-24 lg:py-32">
      <div className="container relative z-10 mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-16 lg:grid-cols-2 lg:items-center">
          <div className="flex flex-col items-start space-y-8">
            <h1 className="text-5xl font-black tracking-tight text-foreground sm:text-6xl md:text-7xl font-outfit">
              {title}
            </h1>
            <p className="max-w-xl text-md text-muted-foreground md:text-xl font-medium leading-relaxed">
              {subtitle}
            </p>
            <p className="max-w-xl text-md text-primary md:text-xl font-medium leading-relaxed">
              30% more patients booked in first month
            </p>

            <div className="flex gap-4 flex-row flex-nowrap justify-center">
              {actions.map((action, i) => (
                <Button
                  key={i}
                  onClick={action.onClick}
                  variant={action.variant as any}
                  className="rounded-2xl px-6 py-5 text-base font-semibold whitespace-nowrap hover:text-cta/80"
                >
                  {action.text}
                </Button>
              ))}
            </div>

            <div className="flex gap-8 pt-8 flex-nowrap">
              {stats.map((stat, i) => (
                <div key={i} className="flex flex-col gap-2 whitespace-nowrap">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/5 rounded-lg">
                      {stat.icon}
                    </div>
                    <span className="text-2xl font-black">{stat.value}</span>
                  </div>
                  <span className="text-sm font-bold text-muted-foreground opacity-70">
                    {stat.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="relative grid grid-cols-2 gap-4">
            {images.slice(0, 3).map((img, i) => (
              <div
                key={i}
                className={`overflow-hidden rounded-[2.5rem] shadow-3xl border-4 border-border/10 ${
                  i === 0 ? "col-span-2 aspect-16/10" : "aspect-square"
                }`}
              >
                <img
                  src={img}
                  alt="Hero Image"
                  className="h-full w-full object-cover transition-transform hover:scale-105 duration-1000 ease-out"
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

// 3. The Demo component (now internal to the file, no circular import needed)
export const HeroSectionDemo = () => {
  const heroData: HeroSectionProps = {
    title: (
      <>
        A new way to learn <br /> & get knowledge
      </>
    ),
    subtitle:
      "EduFlex is here for you with various courses & materials from skilled tutors all around the world.",
    actions: [
      {
        text: "Join the Class",
        onClick: () => alert("Join the Class clicked!"),
        variant: "default",
      },
      {
        text: "Learn more",
        onClick: () => alert("Learn More clicked!"),
        variant: "outline",
      },
    ],
    stats: [
      {
        value: "15,2K",
        label: "Active students",
        icon: <Users className="h-5 w-5 text-primary" />,
      },
      {
        value: "4,5K",
        label: "Tutors",
        icon: <Briefcase className="h-5 w-5 text-primary" />,
      },
      {
        value: "Resources",
        label: "Quality content",
        icon: <LinkIcon className="h-5 w-5 text-primary" />,
      },
    ],
    images: [
      "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=2071&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1543269865-cbf427effbad?q=80&w=2070&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=2070&auto=format&fit=crop",
    ],
  };

  return (
    <div className="w-full bg-background min-h-screen">
      <HeroSection {...heroData} />
    </div>
  );
};

export default HeroSection;
