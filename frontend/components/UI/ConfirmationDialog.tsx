interface ConfirmationDialogProps {
  isOpen: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  cancelText?: string;
  confirmText?: string;
}

export default function ConfirmationDialog({
  isOpen,
  onCancel,
  onConfirm,
  title,
  message,
  cancelText = 'Cancel',
  confirmText = 'Leave',
}: ConfirmationDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="absolute w-fit border border-neutral-300 flex items-center justify-center z-50 rounded-lg top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
      <div className="flex flex-col gap-3.5 bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="font-semibold text-[14px] tracking-[0.5%] leading-[16px] mb-2">
          {title}
        </h3>
        <p className="font-normal text-[12px] tracking-[0.5%] leading-[14px]">
          {message}
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-3 py-2 bg-[#E8E8E8] text-black rounded-[8px] font-medium text-[14px] tracking-[0.5%] leading-[16px] w-18 cursor-pointer transition-transform duration-200 hover:scale-105">
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className="px-3 py-2 brand-gradient text-white rounded-[8px] font-medium text-[14px] tracking-[0.5%] leading-[16px] w-18 cursor-pointer transition-transform duration-200 hover:scale-105">
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
