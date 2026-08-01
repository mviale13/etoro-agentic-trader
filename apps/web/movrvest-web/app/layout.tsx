import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { PageIntegrityProvider } from "@/components/system-integrity/PageIntegrityContext";
import { SystemIntegrityLegend } from "@/components/system-integrity/SystemIntegrityLegend";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MOVRvest — Artificial Chief Investment Officer",
  description: "Transparent, explainable investment intelligence built around conviction.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <PageIntegrityProvider>
          {children}

          <SystemIntegrityLegend />
        </PageIntegrityProvider>
      </body>
    </html>
  );
}
