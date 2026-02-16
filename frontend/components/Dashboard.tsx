'use client';
import Navbar from '@/components/UI/Navbar';
import React, { useState } from 'react';
import { usePathname } from 'next/navigation';
import {
  Sidebar,
  SidebarBody,
  SidebarLink,
  SidebarProvider,
} from '@/components/UI/Sidebar';
import {
  IconFlask,
  IconLayoutDashboard,
  IconSparkles,
  IconTool,
} from '@tabler/icons-react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';
import Image from 'next/image';
import { images } from '@/constants';
import { useEditMode, EditModeProvider } from '@/contexts/EditModeContext';
import ConfirmationDialog from '@/components/UI/ConfirmationDialog';

export function Dashboard({ children }: { children: React.ReactNode }) {
  return (
    <EditModeProvider>
      <DashboardContent>{children}</DashboardContent>
    </EditModeProvider>
  );
}

function DashboardContent({ children }: { children: React.ReactNode }) {
  const [showLeaveDialog, setShowLeaveDialog] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState<string | null>(
    null
  );
  const { isEditing } = useEditMode();
  const pathname = usePathname();

  const links = [
    {
      label: 'Dashboard',
      href: '/',
      icon: (
        <IconLayoutDashboard className="h-5.5 w-5.5 shrink-0 text-primary" />
      ),
    },
    {
      label: 'Painpoints',
      href: '/painpoints',
      icon: <IconTool className="h-5.5 w-5.5 shrink-0 text-primary" />,
    },
    {
      label: 'Hypothesis',
      href: '/hypothesis',
      icon: <IconSparkles className="h-5.5 w-5.5 shrink-0 text-primary" />,
    },
    {
      label: 'Experiments',
      href: '/experiments',
      icon: <IconFlask className="h-5.5 w-5.5 shrink-0 text-primary" />,
    },
  ];
  const [open, setOpen] = useState(false);

  // Find the active link based on current pathname
  const getActiveLinkIndex = () => {
    return links.findIndex((link) => link.href === pathname);
  };

  const activeLink = getActiveLinkIndex();

  const handleLinkClick = (href: string, e?: React.MouseEvent) => {
    // Prevent default navigation
    if (e) {
      e.preventDefault();
    }

    if (isEditing) {
      setPendingNavigation(href);
      setShowLeaveDialog(true);
    } else {
      window.location.href = href;
    }
  };

  return (
    <SidebarProvider open={open} setOpen={setOpen}>
      <div
        className={cn(
          'grid grid-rows-[60px_1fr] grid-cols-[auto_1fr] h-screen w-screen'
        )}>
        <div className="col-span-2">
          <Navbar />
        </div>
        <Sidebar open={open} setOpen={setOpen}>
          <SidebarBody className="justify-between gap-10">
            <div className="flex flex-1 flex-col overflow-x-hidden overflow-y-auto gap-4">
              {open ? <Logo /> : <LogoIcon />}
              <div className="mt-8 flex flex-col gap-2">
                {links.map((link, idx) => (
                  <SidebarLink
                    key={idx}
                    link={link}
                    active={idx === activeLink}
                    onClick={(e) => handleLinkClick(link.href, e)}
                  />
                ))}
              </div>
            </div>
            <div>
              <SidebarLink
                className="px-1"
                active={false}
                link={{
                  label: 'Profile',
                  href: '/profile',
                  icon: (
                    <Image
                      src={images.user}
                      className="h-6 w-6 shrink-0 rounded-full"
                      width={32}
                      height={32}
                      alt="Avatar"
                    />
                  ),
                }}
              />
            </div>
          </SidebarBody>
        </Sidebar>
        <MainContent>{children}</MainContent>
      </div>

      {/* Confirmation dialog */}
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
    </SidebarProvider>
  );
}
export const Logo = () => {
  return (
    <div className="bg-unconnected flex items-center border border-unconnected rounded-lg p-1.5 gap-1.5 w-fit">
      <div className="h-2 w-2 rounded-full unconnected-dot flex-none shrink-0" />
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="whitespace-pre text-xs text-unconnected font-medium tracking-[0.5%] leading-2.5">
        Connected to Zendesk
      </motion.span>
    </div>
  );
};
export const LogoIcon = () => {
  return (
    <div className="bg-unconnected flex items-center justify-center border border-unconnected rounded-full p-1.5 w-fit self-center mx-auto">
      <div className="h-2 w-2 rounded-full unconnected-dot flex-none shrink-0" />
    </div>
  );
};

const MainContent = ({ children }: { children: React.ReactNode }) => {
  return <div className="overflow-auto p-4">{children}</div>;
};
