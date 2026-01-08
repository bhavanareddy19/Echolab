'use server';

import { revalidatePath } from 'next/cache';
import { createClient } from '@/utils/supabase/server';
import { redirect } from 'next/navigation';

export async function getUser() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getUser();
  if (error) {
    return { status: 'Error getting user', user: null };
  }
  return { status: 'User fetched successfully', user: data?.user };
}

export async function signUp(userData: FormData) {
  const supabase = await createClient();
  const credentials = {
    email: userData.get('email') as string,
    password: userData.get('password') as string,
    firstName: userData.get('firstName') as string,
    lastName: userData.get('lastName') as string,
    companyName: userData.get('companyName') as string,
    role: userData.get('role') as string,
  };

  const { error, data } = await supabase.auth.signUp({
    email: credentials.email,
    password: credentials.password,
    options: {
      data: {
        firstName: credentials.firstName,
      },
    },
  });

  if (error) {
    return {
      status: error?.message,
      user: null,
    };
  } else if (data?.user?.identities?.length === 0) {
    return {
      status: 'User already exists',
      user: null,
    };
  }
  // Create user in database

  revalidatePath('/', 'layout');
  return { status: 'User created successfully', user: data?.user };
}

export async function signIn(userData: FormData) {
  const supabase = await createClient();
  const credentials = {
    email: userData.get('email') as string,
    password: userData.get('password') as string,
  };

  const { error, data } = await supabase.auth.signInWithPassword({
    email: credentials.email,
    password: credentials.password,
  });

  if (error) {
    return { status: error?.message, user: null };
  }

  revalidatePath('/', 'layout');
  return { status: 'User logged in successfully', user: data?.user };
}

export async function signOut() {
  const supabase = await createClient();
  const { error } = await supabase.auth.signOut();

  if (error) {
    redirect('/error');
  }
  revalidatePath('/', 'layout');
  redirect('/login');
  return { status: 'User logged out successfully', user: null };
}

export async function signInWithGoogle() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${process.env.NEXT_PUBLIC_APP_URL}/auth/callback`,
    },
  });
  if (error) {
    return { status: error?.message };
  }
  if (data?.url) {
    redirect(data.url);
  }
  return { status: 'OAuth URL not available' };
}
