import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Matheus Silva | Python, IA & Automação",
  description: "Portfólio de Matheus Silva, estudante de Análise e Desenvolvimento de Sistemas e desenvolvedor com foco em Python, Inteligência Artificial, automação e soluções digitais aplicadas à indústria.",
  openGraph: {
    title: "Matheus Silva | Python, IA & Automação",
    description: "Desenvolvedor Python em formação, com experiência industrial real e foco em IA, automação e transformação digital.",
    locale: "pt_BR",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={`${inter.className} industrial-grid min-h-screen antialiased`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
