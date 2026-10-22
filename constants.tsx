import { Project, Skill, Experience, Education, Feedback, Idioma, Client } from "./types";

export const PROJECTS: Project[] = [
  {
    id: "1",
    title: "SENTINELA SAO | Padronizador de Arquivos",
    description: "Solução digital criada para organizar e padronizar arquivos e planilhas operacionais. Automatiza o processamento de dados estruturados, reduzindo trabalho manual e melhorando a leitura de informações em ambientes industriais e corporativos.",
    tags: ["Python", "FastAPI", "Automação", "Dados"],
    imageUrl: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=800",
    link: "https://padronizador-nine.vercel.app/",
  },
  {
    id: "2",
    title: "Relatório Médico — Sistema de Cadastro",
    description: "Aplicação em Java para cadastro de pacientes e geração de relatórios clínicos. O sistema processa dados como nome, sexo, peso, idade e altura, gerando estatísticas precisas — demonstrando estrutura de código orientado a objetos e lógica de algoritmos.",
    tags: ["Java", "POO", "Algoritmos", "CLI"],
    imageUrl: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&q=80&w=800",
    link: "https://github.com/Matheusssilva333/relatoriomedico.git",
  },
  {
    id: "3",
    title: "Portfólio Profissional — Em Desenvolvimento",
    description: "Este próprio portfólio, construído com Next.js, TypeScript e Tailwind CSS. Inclui assistente de IA integrado via Gemini API, design responsivo, SEO otimizado e identidade visual tecnológica.",
    tags: ["Next.js", "TypeScript", "React", "IA Generativa", "Tailwind"],
    imageUrl: "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=800",
    link: "https://github.com/Matheusssilva333/Portfolio-MatheusDev",
  },
];

export const SKILLS: Skill[] = [
  // Tech
  {
    name: "Python & Automação",
    category: "Tech",
    proficiency: 72,
    details: ["Scripts de automação", "FastAPI", "Processamento de dados", "Integração de APIs"],
  },
  {
    name: "IA Generativa & APIs",
    category: "Tech",
    proficiency: 65,
    details: ["Gemini API", "Agentes LLM", "Integração de fluxos", "Experimentação prática"],
  },
  {
    name: "Desenvolvimento Web",
    category: "Tech",
    proficiency: 68,
    details: ["React / Next.js", "TypeScript", "HTML & CSS", "Java (POO)"],
  },
  // Planning
  {
    name: "Planejamento de Manutenção",
    category: "Planning",
    proficiency: 80,
    details: ["Planejamento de paradas", "Permissão de Trabalho (PT)", "Acompanhamento de atividades", "Programação para equipes"],
  },
  {
    name: "Controle de Documentação",
    category: "Planning",
    proficiency: 82,
    details: ["Planilhas de controle", "Organização de PTs", "Acompanhamento de avanço", "Excel avançado"],
  },
  // Industrial
  {
    name: "Caldeiraria & Processos Industriais",
    category: "Industrial",
    proficiency: 88,
    details: ["Experiência em refinaria (RPBC)", "UGAV e UT2", "Traçagem e fabricação", "Segurança industrial"],
  },
  {
    name: "Processos & Segurança",
    category: "Industrial",
    proficiency: 82,
    details: ["Rotinas de SMS", "Permissões de Trabalho", "Procedimentos de segurança", "Ambiente de parada"],
  },
];

export const EDUCATION: Education[] = [
  {
    id: "1",
    institution: "Universidade Santa Cecília — Unisanta",
    degree: "Análise e Desenvolvimento de Sistemas (ADS)",
    period: "2025 – 2026 · Em andamento",
    description: "Graduação em tecnologia com foco em programação, banco de dados, engenharia de software, estruturas de dados e desenvolvimento de aplicações. Formação prevista para 2026.",
  },
  {
    id: "2",
    institution: "SENAI Cubatão",
    degree: "Técnico em Manutenção de Máquinas Industriais",
    period: "Concluído",
    description: "Formação técnica industrial com base em planejamento de manutenção, metrologia, desenho técnico e processos industriais.",
  },
  {
    id: "3",
    institution: "Programa Autonomia e Renda Petrobras / SENAI",
    degree: "Caldeiraria Industrial",
    period: "Concluído",
    description: "Formação prática complementar em caldeiraria e atuação em ambiente industrial de alta responsabilidade.",
  },
  {
    id: "4",
    institution: "SENAI",
    degree: "Desenvolvimento de aplicações com IA generativa — Google Antigravity",
    period: "Concluído",
    description: "Exploração prática de IA generativa com ferramentas do ecossistema Google, desenvolvimento de agentes e integração de APIs.",
  },
  {
    id: "5",
    institution: "Oracle / SENAI",
    degree: "Oracle Java Foundations",
    period: "Concluído",
    description: "Fundamentos de programação Java com ênfase em lógica, orientação a objetos e resolução de problemas.",
  },
];

export const IDIOMAS: Idioma[] = [
  { name: "Português", category: "Nativo", proficiency: 100 },
  { name: "Inglês", category: "Em desenvolvimento", proficiency: 50 },
];

export const EXPERIENCE: Experience[] = [
  {
    id: "1",
    company: "C3 Engenharia & Soluções · Refinaria Presidente Bernardes (RPBC/Petrobras)",
    position: "Apoio ao Planejamento de Obras de Manutenção",
    period: "2026 · transferência interna",
    description: "Após experiência de campo como caldeireiro, fui transferido internamente para o setor de planejamento, atuando na organização, controle e acompanhamento de atividades de manutenção em ambiente industrial de alta responsabilidade.",
    achievements: [
      "Elaboração e emissão de Permissões de Trabalho (PTs) conforme normas de segurança.",
      "Acompanhamento de atividades de manutenção em campo.",
      "Entrega da programação de atividades para equipes de campo.",
      "Criação de planilhas de controle de PTs no Excel com gráfico de evolução do avanço da obra.",
    ],
  },
  {
    id: "2",
    company: "C3 Engenharia & Soluções · Refinaria Presidente Bernardes (RPBC/Petrobras)",
    position: "Caldeireiro — Setor UGAV & UT2",
    period: "jun 2026 – ago 2026 · 3 meses",
    description: "Atuação nas unidades UGAV e UT2 durante manutenção e parada em refinaria. Experiência com execução industrial sob procedimentos rigorosos de segurança, documentação operacional e comunicação entre equipes.",
    achievements: [
      "UGAV: apoio, coleta e movimentação de ferramentas e materiais na ferramentaria durante parada.",
      "UT2: traçagem de raquetes e componentes de caldeiraria com medições e marcações para fabricação.",
      "Trabalho em altura em torres e reatores conforme procedimentos de segurança (NR-35).",
      "Atuação em área com risco de exposição a HF, seguindo protocolos de segurança.",
    ],
  },
  {
    id: "3",
    company: "Projetos Independentes em Tecnologia",
    position: "Desenvolvimento & Automação",
    period: "2024 – atual",
    description: "Desenvolvimento de aplicações, automações e experimentos com Python, Java, JavaScript, IA generativa e APIs. Projetos focados em automação de processos, organização de dados e soluções digitais de uso prático.",
    achievements: [
      "SENTINELA SAO: aplicação Python/FastAPI para padronização e organização de arquivos operacionais.",
      "Relatório Médico: sistema Java para cadastro de pacientes e geração de relatórios clínicos.",
      "Portfólio com IA integrada: Next.js + TypeScript com assistente Gemini API.",
      "Exploração de agentes LLM, integração de APIs REST e ferramentas no-code/low-code.",
    ],
  },
  {
    id: "4",
    company: "Franciscon Infraestrutura",
    position: "Aprendiz Industrial — SENAI",
    period: "2023 – 2024",
    description: "Início da trajetória profissional, conciliando formação no SENAI com experiência prática em ambiente industrial. Desenvolvimento de fundamentos técnicos de manutenção e disciplina operacional.",
    achievements: [
      "Formação técnica e prática em ambiente industrial estruturado.",
      "Contato com fundamentos de manutenção de máquinas industriais.",
      "Desenvolvimento de metrologia, desenho técnico e processos de manutenção.",
      "Primeiro contato com planejamento de manutenção — área que despertou interesse profissional.",
    ],
  },
];

export const FEEDBACKS: Feedback[] = [];

export const CLIENTS: Client[] = [
  {
    id: "1",
    name: "Icaro Soares",
    role: "Advogado · Especialista em Direito Empresarial & Previdenciário · Dev & Cybersecurity · Empreendedor",
    tags: ["Direito Empresarial", "Direito Previdenciário", "Cybersecurity", "Desenvolvimento", "Empreendedorismo"],
    avatarUrl: "/social-proof/icaro.png",
  },
  {
    id: "2",
    name: "Seraf, o Astuto",
    role: "Empreendedor · Youtuber",
    tags: ["YouTube", "Empreendedorismo", "Conteúdo Digital"],
    avatarUrl: "",
  },
  {
    id: "3",
    name: "Lojas de Roblox",
    role: "Negócio Digital · Plataforma Roblox",
    tags: ["Roblox", "E-commerce Digital", "Game Economy"],
    avatarUrl: "",
  },
];
