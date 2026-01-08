import { BreadcrumbProps } from '@/types';
import { useEditMode } from '@/contexts/EditModeContext';
import { useState } from 'react';
import ConfirmationDialog from './ConfirmationDialog';

export default function Breadcrumb({ items }: BreadcrumbProps) {
  const { isEditing } = useEditMode();
  const [showLeaveDialog, setShowLeaveDialog] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState<string | null>(
    null
  );

  const handleBreadcrumbClick = (href: string, e: React.MouseEvent) => {
    e.preventDefault();

    if (isEditing) {
      setPendingNavigation(href);
      setShowLeaveDialog(true);
    } else {
      window.location.href = href;
    }
  };

  return (
    <>
      <nav className="flex items-center gap-2 text-sm">
        {items.map((item, index) => (
          <div key={index} className="flex items-center gap-2">
            {index > 0 && <span className="text-[#8C8C8C] font-normal">/</span>}
            {item.href && !item.isActive ? (
              <a
                href={item.href}
                onClick={(e) => handleBreadcrumbClick(item.href!, e)}
                className="text-black font-normal cursor-pointer transition-colors text-[12px] tracking-[0.5%] leading-[14px]">
                {item.label}
              </a>
            ) : (
              <span className="font-normal text-black text-[12px] tracking-[0.5%] leading-[14px]">
                {item.label}
              </span>
            )}
          </div>
        ))}
      </nav>

      <ConfirmationDialog
        isOpen={showLeaveDialog}
        onCancel={() => setShowLeaveDialog(false)}
        onConfirm={() => {
          setShowLeaveDialog(false);
          if (pendingNavigation) {
            window.location.href = pendingNavigation;
          }
        }}
        title="Unsaved Changes"
        message="You haven't finished editing. Leaving now will erase all edits. Are you sure you want to proceed?"
        cancelText="Cancel"
        confirmText="Leave"
      />
    </>
  );
}
