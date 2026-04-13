"use client";

type ServicesSectionProps = {
  services: {
    icon: React.ReactNode;
    title: string;
    description: string;
  }[];
};

export function ServicesSection({ services }: ServicesSectionProps) {
  return (
    <section id="services" className="py-24 md:py-32 px-4 md:px-8 scroll-mt-24">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-primary/20 bg-primary/5 text-primary font-black text-[10px] uppercase tracking-[0.2em]">
            The Solution
          </div>

          <h2 className="mt-6 text-4xl md:text-6xl font-outfit font-semibold tracking-tight leading-[1.1]">
            Automedge AI
            <br className="hidden md:block" />
            <span className="text-cta">Your 24/7 AI Sales System</span>
          </h2>

          <p className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
            Capture, qualify, and convert every lead automatically.
          </p>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {services.map((item, index) => (
            <div
              key={index}
              className="group p-8 md:p-10 rounded-3xl border border-border/40 bg-card backdrop-blur-sm transition-all duration-300 hover:border-cta/50"
            >
              {/* Icon */}
              <div className="mb-6 text-primary/80 group-hover:text-cta transition-colors [&_svg]:w-6 [&_svg]:h-6 p-2">
                {item.icon}
              </div>

              {/* Content */}
              <h3 className="text-xl md:text-2xl font-medium tracking-tight mb-3">
                {item.title}
              </h3>

              <p className="text-muted-foreground leading-relaxed text-sm md:text-base">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
