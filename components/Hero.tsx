import React from "react";

const Hero: React.FC = () => {
  const pillars = [
    { value: "01", label: "Foco principal", detail: "Python, IA & Automação" },
    { value: "02", label: "Experiência real", detail: "Processos industriais" },
    { value: "03", label: "Formação", detail: "ADS — Unisanta · 2026" },
  ];

  return (
    <section id="top" className="hero-section relative overflow-hidden px-6 pb-28 pt-36 md:pb-36 md:pt-48">
      <div className="pointer-events-none absolute -left-32 top-24 h-96 w-96 rounded-full bg-orange-500/10 blur-[130px]" />
      <div className="pointer-events-none absolute right-0 top-10 h-[520px] w-[520px] rounded-full bg-slate-500/5 blur-[120px]" />

      <div className="section-shell">
        <div className="grid items-end gap-14 lg:grid-cols-[1.25fr_.75fr]">
          <div className="relative z-10">
            <div className="badge-industrial mb-8 inline-flex items-center gap-3 rounded-full px-4 py-2 text-[10px] font-black uppercase tracking-[.24em]">
              <span className="h-1.5 w-1.5 rounded-full bg-orange-400 shadow-[0_0_12px_rgba(251,146,60,.9)]" />
              Disponível · Tecnologia, IA & Automação
            </div>

            <p className="mb-5 font-mono text-[10px] uppercase tracking-[.35em] text-slate-500">
              MATHEUS SILVA / PORTFÓLIO 2026
            </p>
            <h1 className="max-w-5xl text-6xl font-black leading-[.86] tracking-[-.065em] md:text-8xl lg:text-[9.2rem]">
              <span className="text-gradient block">PYTHON.</span>
              <span className="text-primary-gradient block">IA &</span>
              <span className="text-gradient block">AUTOMAÇÃO.</span>
            </h1>
            <p className="mt-9 max-w-3xl text-lg leading-8 text-slate-300 md:text-2xl md:leading-10">
              Desenvolvedor em formação, estudante de{" "}
              <strong className="font-semibold text-white">Análise e Desenvolvimento de Sistemas</strong> e
              profissional com{" "}
              <strong className="font-semibold text-orange-400">experiência industrial real</strong>.
              Desenvolvo soluções digitais para automatizar processos, organizar informações e
              transformar problemas operacionais em sistemas práticos.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-4">
              <a href="#projetos" className="btn-primary rounded-xl px-7 py-4 text-xs font-black uppercase tracking-[.18em]">
                Ver projetos
              </a>
              <a href="#sobre" className="btn-outline rounded-xl px-7 py-4 text-xs font-black uppercase tracking-[.18em]">
                Sobre mim
              </a>
              <span className="hidden h-8 w-px bg-slate-800 md:block" />
              <span className="font-mono text-[10px] uppercase tracking-[.18em] text-slate-500">
                Industrial → Tecnologia → IA
              </span>
            </div>
          </div>

          <aside className="glass-morphism hero-profile-card relative overflow-hidden rounded-3xl p-6 md:p-7">
            <div className="absolute right-0 top-0 h-24 w-24 bg-orange-500/10 blur-3xl" />
            <div className="mb-8 flex items-center justify-between border-b border-white/10 pb-5">
              <div>
                <p className="font-mono text-[9px] uppercase tracking-[.25em] text-orange-400">Perfil profissional</p>
                <p className="mt-2 text-sm font-semibold text-white">Python · IA · Automação</p>
              </div>
              <span className="rounded-full border border-emerald-400/20 bg-emerald-400/5 px-3 py-1 font-mono text-[9px] uppercase tracking-widest text-emerald-400">
                Disponível
              </span>
            </div>
            <div className="space-y-6">
              {pillars.map((p) => (
                <div key={p.value} className="grid grid-cols-[42px_1fr] gap-4">
                  <span className="font-mono text-xs text-orange-400">{p.value}</span>
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[.16em] text-slate-500">{p.label}</p>
                    <p className="mt-1 text-sm font-semibold text-slate-200">{p.detail}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 border-t border-white/10 pt-5">
              <p className="font-mono text-[9px] uppercase tracking-[.22em] text-slate-600">OBJETIVO 2026</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Oportunidades em desenvolvimento, automação, IA e transformação digital.
              </p>
            </div>
          </aside>
        </div>

        <div className="mt-16 grid border-y border-white/10 md:grid-cols-3">
          {pillars.map((p, index) => (
            <div
              key={p.label}
              className={`flex items-center gap-4 py-5 ${index > 0 ? "border-t border-white/10 md:border-l md:border-t-0 md:pl-7" : ""}`}
            >
              <span className="font-mono text-[10px] text-orange-400">{p.value}</span>
              <div>
                <p className="text-xs font-bold text-white">{p.label}</p>
                <p className="mt-1 text-[10px] uppercase tracking-wider text-slate-600">{p.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default React.memo(Hero);
