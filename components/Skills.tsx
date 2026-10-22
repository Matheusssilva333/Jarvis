"use client";
import React, { useState } from "react";
import { Skill } from "../types";

const META: Record<string,{label:string;color:string}> = { Tech:{label:"Tecnologia",color:"text-sky-400"}, Planning:{label:"Planejamento",color:"text-emerald-400"}, Industrial:{label:"Industrial",color:"text-orange-400"} };
const tags = ["Python","FastAPI","IA Generativa","Gemini API","React","Next.js","TypeScript","Java","HTML/CSS","APIs REST","SQL","Git & GitHub","Automação","Planejamento Industrial","Caldeiraria","Segurança Industrial"];

const Skills: React.FC<{skills:Skill[]}> = ({skills}) => {
 const [active,setActive]=useState("Tech");
 const list=skills.filter(s=>s.category===active);
 return <section id="stack" className="relative py-28 md:py-36"><div className="section-shell">
  <div className="grid lg:grid-cols-[.8fr_1.2fr] gap-10 items-end"><div><span className="section-kicker">Competências</span><h2 className="section-title">Conhecimento organizado por <span className="text-primary-gradient">domínio.</span></h2></div><p className="section-copy mt-0">Uma combinação deliberada de base industrial, planejamento e competências tecnológicas complementares.</p></div>
  <div className="mt-14 grid lg:grid-cols-12 gap-5">
   <div className="lg:col-span-7 glass-morphism rounded-3xl p-7 md:p-9"><div className="flex flex-wrap gap-2 mb-10">{Object.keys(META).map(k=><button key={k} onClick={()=>setActive(k)} className={`px-4 py-2.5 rounded-lg border text-[10px] font-bold uppercase tracking-[.16em] transition-all ${active===k?'border-orange-500/40 bg-orange-500/10 text-orange-300':'border-white/5 text-slate-500 hover:text-slate-300'}`}>{META[k].label}</button>)}</div><div className="space-y-7">{list.map(s=><div key={s.name}><div className="flex justify-between mb-2"><span className={`text-xs font-bold uppercase tracking-wider ${META[s.category].color}`}>{s.name}</span><span className="font-mono text-xs text-slate-400">{s.proficiency}%</span></div><div className="h-1 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-orange-500 to-amber-300 rounded-full" style={{width:`${s.proficiency}%`}}/></div>{s.details&&<div className="flex flex-wrap gap-2 mt-3">{s.details.map(d=><span key={d} className="font-mono text-[9px] text-slate-500 border border-white/5 rounded px-2 py-1">{d}</span>)}</div>}</div>)}</div></div>
   <div className="lg:col-span-5 glass-morphism rounded-3xl p-7 md:p-9"><span className="section-kicker">Domínios</span><h3 className="mt-4 text-2xl font-black text-white">Stack de conhecimento</h3><div className="flex flex-wrap gap-2 mt-7">{tags.map(t=><span key={t} className="rounded-lg border border-white/8 bg-white/[.025] px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 hover:border-orange-500/30 hover:text-orange-300 transition-colors">{t}</span>)}</div><div className="mt-10 pt-7 border-t border-white/10"><p className="eyebrow">Diferencial</p><p className="mt-3 text-sm leading-7 text-slate-300">A combinação mais relevante é conectar <span className="text-white font-semibold">experiência industrial real → lógica de automação → soluções com Python e IA</span>.</p></div></div>
  </div>
 </div></section>
};
export default React.memo(Skills);
