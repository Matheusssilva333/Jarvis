"use client";

import React from "react";
import { CLIENTS } from "../constants";

function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

const Clients: React.FC = () => {
  return (
    <section id="clientes" className="relative py-28 md:py-36">
      {/* Background glow */}
      <div className="pointer-events-none absolute left-1/2 top-0 h-64 w-[600px] -translate-x-1/2 rounded-full bg-orange-500/5 blur-[120px]" />

      <div className="section-shell">
        {/* Header */}
        <div className="grid lg:grid-cols-[.8fr_1.2fr] gap-12 lg:gap-24 items-end">
          <div>
            <span className="section-kicker">Clientes atendidos</span>
            <h2 className="section-title mt-5">
              Quem já confio no{" "}
              <span className="text-primary-gradient">trabalho.</span>
            </h2>
          </div>
          <p className="section-copy mt-0">
            Profissionais e empreendedores que já foram atendidos, utilizando
            tecnologia como alavanca estratégica para os seus negócios e carreiras.
          </p>
        </div>

        {/* Divider */}
        <div className="section-divider mt-12 mb-14" />

        {/* Client cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {CLIENTS.map((client, index) => (
            <article
              key={client.id}
              className="glass-morphism hover-lift rounded-3xl p-7 md:p-8 relative overflow-hidden group"
            >
              {/* Subtle top-right glow per card */}
              <div className="absolute -right-6 -top-6 h-28 w-28 rounded-full bg-orange-500/8 blur-2xl transition-opacity duration-500 group-hover:opacity-100 opacity-0" />

              {/* Index number watermark */}
              <span className="absolute right-7 top-7 font-mono text-5xl font-bold text-white/5 select-none">
                {String(index + 1).padStart(2, "0")}
              </span>

              {/* Avatar */}
              <div className="mb-6 flex items-center gap-4">
                {client.avatarUrl ? (
                  <div className="relative h-14 w-14 flex-shrink-0 overflow-hidden rounded-2xl border border-orange-500/20 shadow-lg shadow-orange-500/10">
                    <img
                      src={client.avatarUrl}
                      alt={`Foto de ${client.name}`}
                      className="h-full w-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-2xl border border-orange-500/20 bg-gradient-to-br from-orange-500/15 to-amber-500/10 shadow-lg shadow-orange-500/10">
                    <span className="font-mono text-sm font-black text-orange-400">
                      {getInitials(client.name)}
                    </span>
                  </div>
                )}

                <div>
                  <p className="font-mono text-[9px] uppercase tracking-[.22em] text-orange-400 mb-1">
                    Cliente verificado
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,.8)]" />
                    <span className="font-mono text-[9px] uppercase tracking-widest text-emerald-400">
                      Atendido
                    </span>
                  </div>
                </div>
              </div>

              {/* Name & Role */}
              <div className="mb-5 border-b border-white/10 pb-5">
                <h3 className="text-lg font-extrabold text-white leading-tight">
                  {client.name}
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  {client.role}
                </p>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-2">
                {client.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-lg border border-orange-500/12 bg-orange-500/5 px-3 py-1 font-mono text-[9px] uppercase tracking-[.14em] text-orange-400/80 transition-colors hover:border-orange-500/30 hover:text-orange-300"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>

        {/* Footer note */}
        <div className="mt-14 flex items-center justify-center gap-3">
          <div className="h-px flex-1 bg-gradient-to-r from-transparent to-white/10" />
          <p className="font-mono text-[9px] uppercase tracking-[.22em] text-slate-600">
            Evidência de entrega · Rank em expansão
          </p>
          <div className="h-px flex-1 bg-gradient-to-l from-transparent to-white/10" />
        </div>
      </div>
    </section>
  );
};

export default React.memo(Clients);
