import type { Metadata } from "next";
import { Space_Grotesk, Inter } from "next/font/google";
import { TopNav } from "@/components/TopNav";
import { BottomNav } from "@/components/BottomNav";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-headline",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "MatchPrism | Cricket Match Intelligence",
  description:
    "Data-driven match previews, player analytics, and captain picks for every IPL 2026 match. See every match through a data lens.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://matchprism.com"
  ),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${inter.variable}`}>
      <body className="min-h-screen pb-24 md:pb-0">
        <TopNav />
        <main className="mt-16 px-4 md:px-8 max-w-7xl mx-auto">
          {children}
        </main>
        <BottomNav />
      </body>
    </html>
  );
}
