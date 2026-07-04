import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TipsterAI Pro - Analizador de Momios",
  description: "Análisis de apuestas deportivas con inteligencia artificial.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
