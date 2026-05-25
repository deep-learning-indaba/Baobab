import * as React from "react"
import { cva } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2 whitespace-nowrap",
    "font-sans font-semibold text-sm leading-none",
    "rounded-lg transition-all duration-150 cursor-pointer",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    "disabled:pointer-events-none disabled:opacity-50",
    "border border-transparent",
  ],
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground border-primary hover:bg-primary-container hover:border-primary-container shadow-sm hover:shadow-md",
        secondary:
          "bg-transparent text-primary border-primary hover:bg-surface-low",
        ghost:
          "bg-transparent text-primary hover:bg-surface-low border-transparent",
        destructive:
          "bg-error text-error-foreground border-error hover:opacity-90",
        outline:
          "bg-transparent text-foreground border-border hover:bg-surface-low",
        link:
          "bg-transparent text-action border-transparent underline-offset-4 hover:underline p-0! h-auto!",
      },
      size: {
        default: "px-5 py-2.5",
        sm:      "px-3 py-1.5 text-xs rounded-md",
        lg:      "px-8 py-3.5 text-base rounded-xl",
        icon:    "h-9 w-9 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size:    "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, ...props }, ref) => (
  <button
    ref={ref}
    className={cn(buttonVariants({ variant, size }), className)}
    {...props}
  />
))
Button.displayName = "Button"

export { Button, buttonVariants }
