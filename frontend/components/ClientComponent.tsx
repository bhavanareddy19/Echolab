"use client";

import { createClient } from "@/utils/supabase/client";
import { User } from "@supabase/supabase-js";
import { useEffect, useState } from "react";

export default function ClientComponent() {
  
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    async function getUser() {
      const supabase = await createClient();
      const {data, error} = await supabase.auth.getUser();
      if (error || !data.user) {
        console.error("Error getting user");
      } else {
        setUser(data.user);
      }
    }
    getUser();
  }, []);

  return <h2>{user?.email}</h2>;
}