import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { FileQuestion, Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="max-w-lg w-full border-border">
        <CardHeader>
          <div className="flex items-center gap-2 mb-2">
            <div className="rounded-full bg-muted p-2">
              <FileQuestion className="h-6 w-6 text-muted-foreground" />
            </div>
            <CardTitle className="text-foreground">Page Not Found</CardTitle>
          </div>
          <CardDescription>
            The page you are looking for does not exist or has been moved.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Error Code: <span className="font-mono font-medium">404</span>
          </p>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button asChild variant="default" className="flex-1">
            <Link href="/">
              <Home className="mr-2 h-4 w-4" />
              Go Home
            </Link>
          </Button>
          <Button asChild variant="outline" className="flex-1">
            <Link href="/parse">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Parse Document
            </Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
