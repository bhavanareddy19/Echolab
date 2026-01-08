import { DropdownInputProps } from "@/types";


export default function DropdownInput({
  label = '',
  value,
  onChange,
  options,
}: DropdownInputProps) {
  return (
    <div className="flex flex-col gap-2.5 w-full">
      <div className="font-medium text-[14px] tracking-[0.5%] leading-[16px] text-[#7F7F7F]">
        {label}
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-2.5 font-normal text-sm tracking-[0.5%] leading-[16px] text-black rounded-[8px] border border-[#E8E8E8] bg-primary focus:outline-none focus:ring-1 focus:ring-[#5927FF] focus:border-transparent transition-all duration-200">
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
