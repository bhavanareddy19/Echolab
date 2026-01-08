'use client';
import { useState } from 'react';
import { images } from '@/constants';
import Image from 'next/image';
import InputField from './UI/InputField';
import GradientButton from './UI/GradientButton';
import { signIn } from '@/actions/auth';
import { useRouter } from 'next/navigation';
import GoogleSignIn from './Oauth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    console.log('Login attempt:', { email, password });
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);
    const { status } = await signIn(formData);

    if (status === 'User logged in successfully') {
      setIsLoading(false);
      router.push('/');
    } else {
      setIsLoading(false);
      console.error('Login failed:', status);
    }
  };

  return (
    <div className="h-full w-full flex flex-col items-center justify-center">
      <div className="w-full max-w-[280px] px-4 flex flex-col items-center justify-center gap-7.5">
        <div className="h-6 w-8.5">
          <Image src={images.logo} alt="Echolab Logo" />
        </div>
        <div className="w-full flex flex-col items-center justify-center gap-3.5">
          {/* Login Form */}
          <form
            onSubmit={handleSubmit}
            className="w-full flex flex-col items-center justify-center gap-2">
            {/* Email Input */}
            <InputField
              value={email}
              onValueChange={setEmail}
              placeholder="Email"
            />

            {/* Password Input */}
            <InputField
              value={password}
              onValueChange={setPassword}
              placeholder="Password"
              type="password"
            />

            {/* Forgot Password Link */}
            <div className="self-end">
              <div className="text-xs font-normal tracking-[0.5%] leading-[12px] text-primary-brand transition-transform duration-200 hover:scale-105 cursor-pointer">
                Forgot password?
              </div>
            </div>

            {/* Login Button */}
            <GradientButton label="Login" isLoading={isLoading} />
          </form>

          {/* Sign Up Link */}
          <div className="flex items-center gap-2 self-start">
            <p className="text-xs font-normal tracking-[0.5%] leading-[12px] text-tertiary">
              Don&apos;t have an account?{' '}
            </p>
            <p
              onClick={() => router.push('/register')}
              className="text-secondary-brand font-bold cursor-pointer transition-transform duration-200 hover:scale-105 text-xs  tracking-[0.5%] leading-[12px]">
              Create Account
            </p>
          </div>
        </div>
        <div className="w-full flex items-center justify-center gap-2.5">
          <div className="w-full border border-tertiary" />
          <div className="text-xs font-normal tracking-[0.5%] leading-[14px] placeholder-text">
            or
          </div>
          <div className="w-full border border-tertiary" />
        </div>
        <GoogleSignIn />
      </div>
    </div>
  );
}
