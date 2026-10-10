import { AccountForm } from "@/components/account-form";
import { accountIntent } from "@/lib/account-return";

export const metadata = { title: "Create account" };

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  return (
    <AccountForm mode="register" intent={accountIntent(await searchParams)} />
  );
}
