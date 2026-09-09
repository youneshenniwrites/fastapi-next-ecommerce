import { AccountForm } from "@/components/account-form";
export const metadata = { title: "Create account" };
export default function Page() {
  return <AccountForm mode="register" />;
}
