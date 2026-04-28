import Link from "next/link";

export function TopNav() {
  return (
    <header className="fixed top-0 w-full flex justify-between items-center px-4 md:px-6 h-16 bg-surface/70 backdrop-blur-xl z-50">
      <div className="flex items-center gap-6 md:gap-8">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="text-2xl font-black tracking-tighter text-primary font-headline">
            MatchPrism
          </span>
          <span className="text-[11px] text-outline uppercase tracking-widest hidden sm:inline">
            T20 Intelligence
          </span>
        </Link>
        <nav className="hidden md:flex items-center gap-5 font-headline font-bold text-[15px]">
          <Link
            href="/matches"
            className="text-on-surface/60 hover:text-primary transition-colors"
          >
            Matches
          </Link>
          <Link
            href="/players"
            className="text-on-surface/60 hover:text-primary transition-colors"
          >
            Players
          </Link>
          <Link
            href="/venues"
            className="text-on-surface/60 hover:text-primary transition-colors"
          >
            Venues
          </Link>
          <Link
            href="/value"
            className="text-on-surface/60 hover:text-primary transition-colors"
          >
            Value
          </Link>
        </nav>
      </div>
      <div className="flex items-center gap-3">
        <Link
          href="/match/rcb-vs-srh"
          className="hidden sm:flex items-center gap-2 bg-primary/10 text-primary px-3 py-1.5 rounded-full text-[12px] font-bold uppercase tracking-wider hover:bg-primary/20 transition-colors"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
          </span>
          Live: RCB vs SRH
        </Link>
      </div>
    </header>
  );
}
