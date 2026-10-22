import React from "react";

const journey = [
  ["01", "2023 – 2024", "Aprendiz Industrial SENAI", "Franciscon Infraestrutura", "Base técnica industrial, disciplina operacional e primeiros contatos com manutenção, metrologia e processos industriais."],
  ["02", "2026", "Caldeireiro & Planejamento", "C3 Engenharia · Petrobras RPBC", "Experiência de campo em caldeiraria nas unidades UGAV e UT2, seguida de transferência interna para apoio ao planejamento de obras de manutenção."],
  ["03", "2024 – atual", "Desenvolvimento & Automação", "Projetos Independentes", "Desenvolvimento de aplicações com Python, Java e IA generativa. Automação de processos, APIs e soluções digitais aplicadas a problemas reais."],
];

const pillars = [
  ["01", "Tecnologia aplicada", "Python, automação, APIs, IA generativa e soluções digitais para problemas reais."],
  ["02", "Experiência industrial", "Vivência em refinaria, planejamento de manutenção e documentação operacional em ambiente de alta responsabilidade."],
  ["03", "Formação contínua", "Estudante de ADS (Unisanta), formação técnica no SENAI e aprendizado constante em desenvolvimento e IA."],
];

const About: React.FC = () => (
  <section id="sobre" className="relative py-28 md:py-36">
    <div className="section-shell">
      <div className="grid lg:grid-cols-[.8fr_1.2fr] gap-12 lg:gap-24 items-end">
        <div>
          <span className="section-kicker">Sobre / trajetória</span>
          <h2 className="section-title mt-5">
            Tecnologia, automação e{" "}
            <span className="text-primary-gradient">experiência industrial.</span>
          </h2>
        </div>
        <p className="section-copy mt-0">
          Minha trajetória une experiência prática na indústria, formação em tecnologia e interesse
          constante por Inteligência Artificial e automação. Estudo Análise e Desenvolvimento de
          Sistemas e desenvolvo projetos com Python, APIs e ferramentas de IA. A vivência industrial
          me ajuda a compreender problemas operacionais reais e propor soluções tecnológicas mais
          úteis, organizadas e aplicáveis.
        </p>
      </div>

      <div className="mt-16 grid lg:grid-cols-12 gap-5">
        <div className="lg:col-span-7 glass-morphism rounded-3xl p-7 md:p-9 hover-lift">
          <div className="flex items-center justify-between border-b border-white/10 pb-5 mb-7">
            <span className="eyebrow">perfil profissional</span>
            <span className="font-mono text-[10px] text-emerald-400">● EM DESENVOLVIMENTO</span>
          </div>
          <div className="font-mono text-sm leading-8">
            <div className="text-orange-400">profile <span className="text-slate-500">=</span> {'{'}</div>
            <div className="pl-5 md:pl-8 space-y-1 text-slate-300">
              <div><span className="text-slate-500">foco</span>: <span className="text-white">"Python, IA & Automação"</span>,</div>
              <div><span className="text-slate-500">stack</span>: <span className="text-orange-300">["Python", "FastAPI", "React", "Java"]</span>,</div>
              <div><span className="text-slate-500">ia</span>: <span className="text-amber-300">["Gemini API", "Agentes LLM", "IA Generativa"]</span>,</div>
              <div><span className="text-slate-500">formação</span>: <span className="text-amber-300">["ADS - Unisanta", "SENAI"]</span>,</div>
              <div><span className="text-slate-500">diferencial</span>: <span className="text-sky-300">"Experiência industrial real"</span></div>
            </div>
            <div className="text-orange-400">{'}'}</div>
          </div>
        </div>
        <div className="lg:col-span-5 grid gap-4">
          {pillars.map(([n, title, text]) => (
            <div key={n} className="glass-morphism rounded-2xl p-6 hover-lift">
              <div className="flex gap-4">
                <span className="font-mono text-xs text-orange-400">{n}</span>
                <div>
                  <h3 className="font-bold text-white">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-24">
        <div className="flex items-center gap-5 mb-8">
          <span className="section-kicker">Evolução</span>
          <div className="section-divider flex-1" />
        </div>
        <div className="grid md:grid-cols-3 gap-px bg-white/10 rounded-3xl overflow-hidden border border-white/10">
          {journey.map(([n, period, role, company, text]) => (
            <article key={n} className="bg-[#08121b] p-7 md:p-8 hover:bg-[#0c1923] transition-colors">
              <div className="flex justify-between items-start">
                <span className="font-mono text-4xl font-bold text-white/10">{n}</span>
                <span className="font-mono text-[10px] text-orange-400">{period}</span>
              </div>
              <h3 className="mt-10 text-lg font-extrabold text-white">{role}</h3>
              <p className="mt-2 text-[10px] font-bold uppercase tracking-[.16em] text-slate-500">{company}</p>
              <p className="mt-5 text-sm leading-7 text-slate-400">{text}</p>
            </article>
          ))}
        </div>
      </div>
    </div>
  </section>
);

export default About;
