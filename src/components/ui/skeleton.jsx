import { cn } from "@/lib/utils";
import { jsx as _jsx } from "react/jsx-runtime";
function Skeleton({
  className,
  ...props
}) {
  return /*#__PURE__*/_jsx("div", {
    className: cn("animate-pulse rounded-md bg-muted", className),
    ...props
  });
}
export { Skeleton };