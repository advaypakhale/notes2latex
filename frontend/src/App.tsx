import { Suspense, lazy } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { ErrorBoundary } from "react-error-boundary";
import { Spinner } from "@/components/ui/spinner";
import { Header } from "@/components/header";
import { ErrorFallback } from "@/components/error-fallback";

const Home = lazy(() =>
  import("@/routes/home").then((m) => ({ default: m.Home })),
);
const JobDetail = lazy(() =>
  import("@/routes/job-detail").then((m) => ({ default: m.JobDetail })),
);
const Settings = lazy(() =>
  import("@/routes/settings").then((m) => ({ default: m.Settings })),
);
const NotFound = lazy(() =>
  import("@/routes/not-found").then((m) => ({ default: m.NotFound })),
);

export default function App() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <ErrorBoundary FallbackComponent={ErrorFallback} resetKeys={[location]}>
        <Suspense
          fallback={
            <div className="flex justify-center py-16">
              <Spinner className="size-6 text-muted-foreground" />
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/jobs/:id" element={<JobDetail />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}
