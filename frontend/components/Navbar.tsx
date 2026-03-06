import Link from 'next/link';
import { Phone } from 'lucide-react';

export function Navbar() {
    return (
        <nav className="fixed top-0 w-full z-50 px-6 py-4 flex items-center justify-between border-b border-border/10 bg-background/80 backdrop-blur-md">
            <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center">
                    <div className="w-4 h-4 rounded-full border-2 border-background"></div>
                </div>
                <span className="font-outfit font-[800] text-xl tracking-tighter">AUTOMEDGE</span>
            </div>

            <div className="hidden lg:flex items-center gap-8 text-[10px] font-sans font-black tracking-[0.25em]">
                <Link href="#problem" className="hover:text-accent transition-colors">THE PROBLEM</Link>
                <Link href="#solution" className="hover:text-accent transition-colors">THE SOLUTION</Link>
                <Link href="#impact" className="hover:text-accent transition-colors">IMPACT</Link>
                <Link href="#faq" className="hover:text-accent transition-colors">FAQ</Link>
                <Link href="#contact" className="hover:text-accent transition-colors">CONTACT</Link>
            </div>

            <div className="flex items-center gap-3">
                <a href="tel:+1234567890" className="hidden sm:flex items-center gap-2 px-4 py-2 border border-border rounded-full hover:bg-muted transition-colors text-[10px] font-sans font-black">
                    <Phone className="w-3 h-3 text-accent" />
                    CALL US
                </a>
                <Link href="#contact">
                    <button className="px-6 py-2 bg-primary text-primary-foreground rounded-full text-[10px] font-sans font-black hover:opacity-90 transition-opacity tracking-widest">
                        GET STARTED
                    </button>
                </Link>
            </div>
        </nav>
    );
}
