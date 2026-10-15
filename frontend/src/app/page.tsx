import { redirect } from "next/navigation";

/**
 * Root landing route: redirects unauthenticated/direct entries to login page.
 */
export default function RootPage() {
  redirect("/login");
}
