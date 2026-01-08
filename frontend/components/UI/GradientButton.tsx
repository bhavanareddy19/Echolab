import { cn } from '@/lib/utils';
import { ButtonProps } from '@/types';

export default function GradientButton({
  label,
  isLoading = false,
}: ButtonProps) {
  return (
    <div className="w-full">
      <button
        type="submit"
        disabled={isLoading}
        className={cn(
          'w-full py-2.5 px-3 tracking-[0.5%] leading-[16px] rounded-lg font-medium text-white text-sm cursor-pointer',
          'brand-gradient',
          'focus:outline-none',
          'transition-all duration-200 transform hover:scale-[1.02]',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none'
        )}>
        {isLoading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
          </div>
        ) : (
          label
        )}
      </button>
    </div>
  );
}
