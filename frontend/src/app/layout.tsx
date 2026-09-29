import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Predictive Cyber Defense & SOC Portal",
  description: "National Cyber Defense Operations - Government of India",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased h-screen overflow-hidden flex flex-col">
        {children}
      </body>
    </html>
  );
}
