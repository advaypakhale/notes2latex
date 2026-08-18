import { Link } from "react-router-dom";
import { useTheme } from "next-themes";
import { MoonIcon, SettingsIcon, SunIcon } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";

export function Header() {
  const { resolvedTheme, setTheme } = useTheme();

  return (
    <header className="border-b">
      <div className="container mx-auto flex h-14 max-w-4xl items-center justify-between px-4">
        <Link to="/" className="text-lg font-semibold tracking-tight">
          notes2latex
        </Link>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Toggle dark mode"
            onClick={() =>
              setTheme(resolvedTheme === "dark" ? "light" : "dark")
            }
          >
            <SunIcon className="hidden dark:block" />
            <MoonIcon className="dark:hidden" />
          </Button>
          <Link
            to="/settings"
            aria-label="Settings"
            className={buttonVariants({ variant: "ghost", size: "icon" })}
          >
            <SettingsIcon />
          </Link>
        </div>
      </div>
    </header>
  );
}
