import { getUser } from '@/actions/auth';
import { redirect } from 'next/navigation';

export default async function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const response = await getUser();
  if (response.status === 'User fetched successfully' && response.user) {
    redirect('/');
  }
  return <>{children}</>;
}
