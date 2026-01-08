import { InputProps } from '@/types';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { VscEye, VscEyeClosed } from 'react-icons/vsc';

export default function InputField({
  placeholder,
  onValueChange,
  value,
  type,
  className,
  onFocus,
}: InputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const inputType = isPassword && showPassword ? 'text' : type;

  return (
    <div className="w-full relative">
      <input
        id="email"
        type={inputType}
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        onFocus={onFocus}
        required
        className={cn(
          'w-full h-10.5 p-2.5 rounded-lg border border-primary',
          'focus:outline-none focus:ring-1 focus:ring-[var(--primary-brand-color)]  focus:border-transparent',
          'bg-primary placeholder-placeholder-text font-normal text-sm tracking-[0.5%] leading-[16px]',
          'transition-all duration-200',
          isPassword && 'pr-10',
          className
        )}
        placeholder={placeholder}
      />
      {isPassword && (
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-2.5 top-1/2 transform -translate-y-1/2 text-tertiary hover:text-primary transition-colors">
          {showPassword ? <VscEye size={18} /> : <VscEyeClosed size={18} />}
        </button>
      )}
    </div>
  );
}
