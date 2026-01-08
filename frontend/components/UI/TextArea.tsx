import { TextAreaProps } from '@/types';

export default function TextArea({
  hypothesis,
  handleChange,
  field,
}: TextAreaProps) {
  return (
    <input
      type="text"
      value={
        hypothesis.editMode[field]
          ? hypothesis.temp[field]
          : hypothesis.current[field]
      }
      className={`w-full p-2.5 font-normal text-sm tracking-[0.5%] leading-[16px] text-black rounded-md
                  ${
                    hypothesis.editMode[field]
                      ? 'bg-white border border-transparent focus:border-[#5927FF] outline-none'
                      : 'bg-transparent border-none'
                  }
                `}
      onChange={(e) => handleChange(field, e.target.value)}
      disabled={!hypothesis.editMode[field]}
    />
  );
}
