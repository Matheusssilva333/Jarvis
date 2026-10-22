import React from "react";

interface HeaderProps {
  resumeFilePath: string;
}

const Header: React.FC<HeaderProps> = ({ resumeFilePath }) => {
  const downloadIcon = (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 3v12" />
      <path d="M7 10l5 5 5-5" />
      <path d="M4 20h16" />
    </svg>
  );

  const navLinks = [
    { href: "#sobre", label: "Sobre" },
    { href: "#carreira", label: "Trajetória" },
    { href: "#trabalho", label: "Atuação" },
    { href: "#artigos", label: "Artigos" },
    { href: "#projetos", label: "Projetos" },
    { href: "#stack", label: "Competências" },
    { href: "#formacao", label: "Formação" },
    { href: "#clientes", label: "Clientes" },
  ];

  return (
    <header className="fixed inset-x-0 top-0 z-50 px-3 pt-3 md:px-6 md:pt-5">
      <nav className="nav-blur nav-frame mx-auto max-w-7xl rounded-2xl border border-white/10 shadow-2xl shadow-black/20">
        <div className="flex h-[68px] items-center justify-between px-4 md:px-6">
          <a href="#top" className="group flex items-center gap-3" aria-label="Voltar ao início">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500 text-xs font-black tracking-tight text-slate-950 shadow-lg shadow-orange-500/10 transition-transform group-hover:-rotate-3">MS</span>
            <span className="hidden sm:block">
              <span className="block text-sm font-black tracking-tight text-white">MATHEUS SILVA</span>
              <span className="mt-0.5 block font-mono text-[8px] font-bold uppercase tracking-[.2em] text-orange-400">Planejamento Industrial</span>
            </span>
          </a>

          <div className="hidden items-center gap-5 xl:flex">
            {navLinks.map((link) => (
              <a key={link.href} href={link.href} className="group relative py-2 text-[9px] font-black uppercase tracking-[.16em] text-slate-500 transition-colors hover:text-white">
                {link.label}
                <span className="absolute inset-x-0 bottom-0 mx-auto h-px w-0 bg-orange-400 transition-all duration-300 group-hover:w-full" />
              </a>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <a href={resumeFilePath} download className="hidden items-center gap-2 rounded-xl border border-orange-500/25 bg-orange-500/10 px-4 py-2.5 text-[9px] font-black uppercase tracking-[.15em] text-orange-300 transition hover:border-orange-400/50 hover:bg-orange-500/15 sm:flex">
              CV {downloadIcon}
            </a>
            <details className="relative xl:hidden">
              <summary className="flex h-10 w-10 cursor-pointer list-none items-center justify-center rounded-xl border border-white/10 bg-white/[.03] text-slate-300 hover:text-white">
                <span className="text-lg leading-none">☰</span>
              </summary>
              <div className="absolute right-0 top-12 w-64 rounded-2xl border border-white/10 bg-slate-950/95 p-3 shadow-2xl backdrop-blur-xl">
                {navLinks.map((link) => (
                  <a key={link.href} href={link.href} className="block rounded-xl px-4 py-3 text-[10px] font-black uppercase tracking-[.16em] text-slate-400 transition hover:bg-white/5 hover:text-white">
                    {link.label}
                  </a>
                ))}
                <a href={resumeFilePath} download className="mt-2 block rounded-xl bg-orange-500 px-4 py-3 text-center text-[10px] font-black uppercase tracking-[.16em] text-slate-950">Baixar CV</a>
              </div>
            </details>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default React.memo(Header);
