import Hero from "@/components/Hero";
import Header from "@/components/Header";
import About from "@/components/About";
import Experience from "@/components/Experience";
import Skills from "@/components/Skills";
import Projects from "@/components/Projects";
import Education from "@/components/Education";
import WorkArticles from "@/components/WorkArticles";
import Clients from "@/components/Clients";
import Footer from "@/components/Footer";
import { EXPERIENCE, SKILLS, PROJECTS, EDUCATION, IDIOMAS } from "@/constants";

export default function Home() {
  return (
    <div id="top" className="flex min-h-screen flex-col">
      <Header resumeFilePath="/Curriculo-Matheus-Silva.pdf" />
      <main className="flex-grow">
        <Hero />
        <div className="section-divider" />
        <About />
        <Experience experiences={EXPERIENCE} />
        <WorkArticles />
        <Projects projects={PROJECTS} />
        <Skills skills={SKILLS} />
        <Education education={EDUCATION} idiomas={IDIOMAS} />
        <div className="section-divider" />
        <Clients />
      </main>
      <Footer />
    </div>
  );
}
