import { NavLink as RouterNavLink } from "react-router-dom";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";
import { jsx as _jsx } from "react/jsx-runtime";
const NavLink = /*#__PURE__*/forwardRef(({
  className,
  activeClassName,
  pendingClassName,
  to,
  ...props
}, ref) => {
  return /*#__PURE__*/_jsx(RouterNavLink, {
    ref: ref,
    to: to,
    className: ({
      isActive,
      isPending
    }) => cn(className, isActive && activeClassName, isPending && pendingClassName),
    ...props
  });
});
NavLink.displayName = "NavLink";
export { NavLink };