'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from '@/components/ui/drawer';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Menu, X } from 'lucide-react';
import { TableOfContents } from './TableOfContents';

interface MobileTOCProps {
  content: string;
}

export function MobileTOC({ content }: MobileTOCProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="lg:hidden fixed bottom-4 right-4 z-50">
      <Drawer open={open} onOpenChange={setOpen}>
        <DrawerTrigger asChild>
          <Button
            size="icon"
            className="h-12 w-12 rounded-full shadow-lg bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Menu className="h-5 w-5" />
            <span className="sr-only">Open table of contents</span>
          </Button>
        </DrawerTrigger>
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle className="text-foreground">Table of Contents</DrawerTitle>
            <DrawerDescription>
              Navigate through document sections
            </DrawerDescription>
          </DrawerHeader>
          <div className="px-4 max-h-[60vh]">
            <ScrollArea className="h-full">
              <div onClick={() => setOpen(false)}>
                <TableOfContents content={content} />
              </div>
            </ScrollArea>
          </div>
          <DrawerFooter>
            <DrawerClose asChild>
              <Button variant="outline">
                <X className="mr-2 h-4 w-4" />
                Close
              </Button>
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </div>
  );
}
