import type { Metadata } from 'next';
import { Plus_Jakarta_Sans, Space_Grotesk } from 'next/font/google';
import type { ReactNode } from 'react';

import './globals.css';

const bodyFont = Plus_Jakarta_Sans({ subsets: ['latin'], variable: '--font-body' });
const headingFont = Space_Grotesk({ subsets: ['latin'], variable: '--font-heading' });

export const metadata: Metadata = {
  title: 'Watchers',
  description: 'Public incident intelligence dashboard'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={`${bodyFont.variable} ${headingFont.variable} bg-bg text-ink [font-family:var(--font-body)]`}>
        {children}
      </body>
    </html>
  );
}
