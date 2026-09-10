import { SessionProvider } from "@/components/session-provider";
import { AccountProfile } from "@/components/account-profile";
export const metadata = {
  title: "My account",
  robots: { index: false, follow: false },
};
export default function Page() {
  return (
    <SessionProvider>
      <AccountProfile />
    </SessionProvider>
  );
}
