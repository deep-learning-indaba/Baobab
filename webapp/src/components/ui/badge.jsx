import * as React from "react"
import { cva } from "class-variance-authority"
import { cn } from "@/utils/styling/styling"

const badgeVariants = cva(
  "inline-flex items-center rounded-full font-sans text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default:     "bg-primary/10 text-primary border border-primary/20 px-2.5 py-0.5",
        success:     "bg-primary/10 text-primary border border-primary/20 px-2.5 py-0.5",
        secondary:   "bg-surface-high text-muted-foreground px-2.5 py-0.5",
        warning:     "bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5",
        destructive: "bg-error-container text-on-error-container border border-error/20 px-2.5 py-0.5",
        outline:     "border border-border text-foreground px-2.5 py-0.5",
        action:      "bg-action/10 text-action border border-action/20 px-2.5 py-0.5",
      },
    },
    defaultVariants: { variant: "default" },
  }
)

const Badge = React.forwardRef(({ className, variant, ...props }, ref) => (
  <span
    ref={ref}
    className={cn(badgeVariants({ variant }), className)}
    {...props}
  />
))
Badge.displayName = "Badge"

export { Badge, badgeVariants }
