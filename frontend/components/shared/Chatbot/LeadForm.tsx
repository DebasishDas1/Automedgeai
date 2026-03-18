import { motion } from "framer-motion";
import { User, Mail, Phone, ArrowRight, ShieldCheck } from "lucide-react";
import { UserInfo } from "./types";
import { Button } from "@/components/ui/button";

interface LeadFormProps {
  userInfo: UserInfo;
  isSubmitting: boolean;
  accentColor: string;
  onUserInfoChange: (info: UserInfo) => void;
  onSubmit: (e: React.FormEvent) => void;
}

export function LeadForm({
  userInfo,
  isSubmitting,
  accentColor,
  onUserInfoChange,
  onSubmit,
}: LeadFormProps) {
  const fields = [
    {
      label: "Full Name",
      icon: User,
      type: "text",
      placeholder: "e.g. Alexander Pierce",
      key: "name",
    },
    {
      label: "Email Portfolio",
      icon: Mail,
      type: "email",
      placeholder: "alex@bespoke.com",
      key: "email",
    },
    {
      label: "Secure Line",
      icon: Phone,
      type: "tel",
      placeholder: "+1 (555) 777-0000",
      key: "phone",
    },
  ];

  return (
    <motion.div
      key="form"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="flex-1 flex flex-col p-6 overflow-y-auto chat-scrollbar"
    >
      <div className="mb-5">
        <motion.h2
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="text-2xl font-black text-slate-800 dark:text-white mb-2"
        >
          Begin Your Journey
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-[14px] text-slate-500 dark:text-slate-400 leading-relaxed font-medium"
        >
          Experience unparalleled service. Provide your details to unlock elite
          assistance.
        </motion.p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        {fields.map((field, i) => (
          <motion.div
            key={field.key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 + i * 0.05 }}
            className="space-y-2"
          >
            <label className="text-[11px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">
              {field.label}
            </label>
            <div className="group relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 transition-colors group-focus-within:text-emerald-500">
                <field.icon
                  size={18}
                  className="text-slate-300 dark:text-slate-600"
                />
              </div>
              <input
                required
                type={field.type}
                placeholder={field.placeholder}
                value={userInfo[field.key as keyof UserInfo]}
                onChange={(e) =>
                  onUserInfoChange({ ...userInfo, [field.key]: e.target.value })
                }
                className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-white/10 focus:border-emerald-500/50 focus:ring-4 focus:ring-emerald-500/10 rounded-2xl py-3 pl-12 pr-4 text-[15px] font-medium text-slate-700 dark:text-white outline-none transition-all duration-300"
              />
            </div>
          </motion.div>
        ))}

        <Button
          type="submit"
          disabled={
            isSubmitting || !userInfo.name || !userInfo.email || !userInfo.phone
          }
          className="w-full mt-4 h-12 bg-accent text-white"
          // style={{
          //   background: `linear-gradient(135deg, ${accentColor}, #0F2A47)`,
          // }}
        >
          {isSubmitting ? (
            <span className="tracking-wide text-sm opacity-80">
              Processing...
            </span>
          ) : (
            <div className="flex items-center justify-center gap-2">
              Request Access
              <ArrowRight size={18} className="opacity-80" />
            </div>
          )}
        </Button>
      </form>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-auto pt-4 flex items-center justify-center gap-3 grayscale opacity-40 hover:grayscale-0 hover:opacity-100 transition-all duration-500"
      >
        <ShieldCheck size={14} className="text-emerald-500" />
        <p className="text-[10px] text-slate-500 dark:text-slate-400 font-bold tracking-widest uppercase">
          powered by AutomEdge
        </p>
      </motion.div>
    </motion.div>
  );
}
