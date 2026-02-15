'use client';

import { images } from '@/constants';
import { IconMenu2 } from '@tabler/icons-react';
import Image from 'next/image';
import { useSidebar } from './Sidebar';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { triggerAnalysis } from '@/lib/api';

export default function Navbar() {
  const { setOpen } = useSidebar();
  const router = useRouter();
  const [analyzing, setAnalyzing] = useState(false);

  const toggleSidebar = () => {
    setOpen(prevOpen => !prevOpen);
  };

  const handleNewAnalysis = async () => {
    setAnalyzing(true);
    try {
      const result = await triggerAnalysis();
      alert(`Analysis complete: ${result.message}`);
      // Refresh current page
      router.refresh();
    } catch {
      // If backend isn't running, navigate to tickets page instead
      router.push('/tickets');
    }
    setAnalyzing(false);
  };

  return (
    <div
      className={`h-full w-full flex items-center justify-between bg-primary px-5`}>
      <div className="flex items-center justify-center gap-1">
        <div className='p-1.5 cursor-pointer' onClick={toggleSidebar}>
          <IconMenu2 className='w-5.5 h-5.5'/>
        </div>
        <div className='flex items-center justify-center gap-1 cursor-pointer group' onClick={() => router.push('/')}>
           <div className="h-6 w-8 flex items-center justify-center">
          <Image src={images.logo} alt="Echolab Logo" />
        </div>
        <div className="font-logo font-semibold text-xl tracking-[0] leading-[100%] group-hover:text-gray-400 transition-colors duration-200">echolab</div>
        </div>

      </div>
      <button
        onClick={handleNewAnalysis}
        disabled={analyzing}
        className="brand-gradient text-secondary py-2 px-3 rounded-lg font-medium text-sm tracking-[0.5%] leading-4 cursor-pointer disabled:opacity-50">
        {analyzing ? 'Analyzing...' : 'New Analysis'}
      </button>
    </div>
  );
}
