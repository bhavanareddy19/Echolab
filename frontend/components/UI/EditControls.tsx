import { EditControlsProps } from '@/types';
import { BiSolidEditAlt } from 'react-icons/bi';



export default function EditControls({
  onSave,
  onCancel,
  onEdit,
  editMode,
}: EditControlsProps) {
  return (
    <>
      {editMode ? (
        <div className="flex self-start gap-2.5">
          <button
            className="bg-primary py-2.5 px-3 tracking-[0.5%] leading-[16px] rounded-lg font-medium text-sm cursor-pointer w-18 text-center"
            onClick={onCancel}>
            Cancel
          </button>
          <button
            className="brand-gradient py-2.5 px-3 tracking-[0.5%] leading-[16px] rounded-lg font-medium text-sm cursor-pointer w-18 text-center text-white"
            onClick={onSave}>
            Save
          </button>
        </div>
      ) : (
        <button
          className="self-start cursor-pointer transition-transform duration-200 hover:scale-110"
          onClick={onEdit}
          aria-label="Edit hypothesis">
          <BiSolidEditAlt className="w-4.5 h-4.5" />
        </button>
      )}
    </>
  );
}
