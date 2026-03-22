"use client";

import { m as motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type DemoFullSystemProp = {
  steps: {
    title: string;
    description: string;
    message: string;
    smallWin: string;
  }[];
};

export const DemoFullSystem = ({ steps }: DemoFullSystemProp) => {
  return (
    <section
      id="how-it-works"
      className="py-28 px-6 max-w-6xl mx-auto scroll-mt-24 w-full flex flex-col items-center"
    >
      {/* Heading */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center mb-24 max-w-3xl"
      >
        <h2 className="text-4xl md:text-6xl font-outfit tracking-tight leading-tight text-balance">
          From first text to
          <span className="text-accent underline decoration-accent/20 decoration-8 underline-offset-4"> 5-star review</span>
          <br />
          all automated.
        </h2>
      </motion.div>

      {/* Workflow container */}
      <div className="relative w-full max-w-5xl">
        {/* map-style dashed line - DESKTOP CENTER */}
        <div className="absolute left-[20px] md:left-1/2 top-0 h-full w-px md:w-1 -translate-x-1/2 border-l-4 border-dashed border-accent/30 hidden sm:block" />

        <div className="space-y-12 md:space-y-24">
          {steps.map((step, index) => {
            const isLeft = index % 2 === 0;

            return (
              <div
                key={index}
                className="relative flex flex-col items-center md:items-start w-full group"
              >
                {/* node dot - MAP STOP ICON */}
                <div className="hidden md:flex absolute left-1/2 -translate-x-1/2 w-10 h-10 rounded-full bg-background border-[5px] border-accent shadow-[0_0_20px_rgba(29,158,117,0.4)] z-20 items-center justify-center transition-all duration-500 group-hover:scale-125 group-hover:border-white group-hover:bg-accent ring-8 ring-accent/5">
                  <div className="w-2.5 h-2.5 rounded-full bg-accent group-hover:bg-white" />
                  {/* Pin Pointer */}
                  <div className="absolute -top-1 w-1 h-3 bg-accent rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>

                {/* horizontal trail line (Desktop only) */}
                <div 
                  className={`hidden md:block absolute top-[28px] h-[3px] border-t-2 border-dashed border-accent/30 -z-10 transition-all duration-700 group-hover:border-accent/60
                    ${isLeft ? "right-1/2 w-[100px]" : "left-1/2 w-[100px]"}
                  `} 
                />

                <div className={`w-full flex ${isLeft ? "md:justify-start" : "md:justify-end"} justify-center`}>
                  {/* card */}
                  <motion.div
                    initial={{ opacity: 0, y: 20, x: isLeft ? -20 : 20 }}
                    whileInView={{ opacity: 1, y: 0, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                    className="w-full max-w-lg"
                  >
                    <Card className="border-2 border-border/50 bg-card/70 backdrop-blur-xl hover:border-accent/60 transition-all duration-500 shadow-2xl hover:shadow-[0_30px_60px_-15px_rgba(29,158,117,0.15)] overflow-hidden rounded-[2.5rem] relative">
                      <div className="bg-accent/5 px-8 py-4 border-b border-border/40 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] font-black tracking-[0.3em] text-accent/60 uppercase">Waypoint</span>
                          <Badge className="bg-accent text-white font-black text-xs px-4 py-1.5 rounded-xl border-none shadow-[0_0_20px_rgba(29,158,117,0.4)] hover:shadow-[0_0_25px_rgba(29,158,117,0.6)] transition-all">
                            STOP {index + 1}
                          </Badge>
                        </div>
                        <span className="text-[11px] font-extrabold text-accent/80 tracking-widest uppercase bg-accent/10 py-1 px-3 rounded-full">Route Optimized</span>
                      </div>
                      
                      <CardHeader className="p-8 pb-4">
                        <h3 className="text-2xl md:text-3xl font-outfit font-black text-foreground mb-3 leading-[1.15] tracking-tight">
                          {step.title}
                        </h3>
                        <CardDescription className="text-lg text-muted-foreground/90 leading-relaxed font-medium">
                          {step.description}
                        </CardDescription>
                      </CardHeader>

                      <CardContent className="pb-6">
                        <div className="bg-background/80 border border-border/50 rounded-2xl p-4 relative group-hover:bg-background transition-colors">
                          <p className="font-sans font-medium text-foreground/90 italic italic-none leading-relaxed">
                            "{step.message}"
                          </p>
                          {/* small bubble tail */}
                          <div className="absolute -bottom-2 left-6 w-4 h-4 bg-background border-r border-b border-border/50 rotate-45 transform" />
                        </div>
                      </CardContent>

                      <CardFooter className="px-8 pt-2 pb-8 flex items-center gap-3">
                        <div className="flex -space-x-1">
                          {[1,2,3].map(i => (
                            <div key={i} className="w-2.5 h-2.5 rounded-full bg-accent animate-pulse" style={{ animationDelay: `${i*200}ms` }} />
                          ))}
                        </div>
                        <p className="text-sm font-black text-accent uppercase tracking-widest bg-accent/5 px-3 py-1 rounded-md">{step.smallWin}</p>
                      </CardFooter>
                    </Card>
                  </motion.div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
