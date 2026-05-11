import type { Metadata } from "next";
import "./globals.css";
import SiteHeader from "./components/SiteHeader";

export const metadata: Metadata = {
  title: "Canada Picks — Independent Product Recommendations",
  description:
    "Reviewer-backed product recommendations verified for Canadian availability and pricing.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col">
        <div className="h-[3px] bg-[var(--color-red)]" />
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
