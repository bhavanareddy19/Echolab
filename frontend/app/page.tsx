'use client';

import BugsAndFeatures from '@/components/BugsAndFeatures';
import CustomerPainPoints from '@/components/CustomerPainPoints';
import { Dashboard } from '@/components/Dashboard';
import Overview from '@/components/Overview';

export default function Home() {
  return (
    <Dashboard>
      <div className="flex flex-col gap-10">
        <div className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
          Dashboard
        </div>
        <Overview />
        <CustomerPainPoints />
        <BugsAndFeatures />
      </div>
    </Dashboard>
  );
}
