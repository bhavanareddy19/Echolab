'use client';

import { signInWithGoogle } from '@/actions/auth';
import { images } from '@/constants';
import Image from 'next/image';
import { useRouter } from 'next/navigation';

export default function GoogleSignIn() {
  const router = useRouter();

  const handleSignInWithGoogle = async () => {
    try {
      const response = await signInWithGoogle();
      if (response?.status === 'OAuth URL not available') {
        console.error('OAuth URL not available');
      }
      // The redirect should happen automatically if successful
    } catch (error) {
      // This catch block will handle the redirect response
      // The redirect is working correctly
    }
  };

  return (
    <div
      className="flex justify-center items-center bg-primary gap-2 border py-2.5 px-3 rounded-lg cursor-pointer transition-all duration-200 transform hover:scale-[1.02]"
      onClick={() => handleSignInWithGoogle()}>
      <div className="w-4 h-4">
        <Image src={images.google} alt={'Google-Icon'} />
      </div>
      <div className="text-sm font-normal tracking-[0.5%] leading-[14px]">
        Continue with Google
      </div>
    </div>
  );
}
