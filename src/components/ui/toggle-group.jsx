import * as React from "react";
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import { cn } from "@/lib/utils";
import { toggleVariants } from "@/components/ui/toggle";
import { jsx as _jsx } from "react/jsx-runtime";
const ToggleGroupContext = /*#__PURE__*/React.createContext({
  size: "default",
  variant: "default"
});
const ToggleGroup = /*#__PURE__*/React.forwardRef(({
  className,
  variant,
  size,
  children,
  ...props
}, ref) => /*#__PURE__*/_jsx(ToggleGroupPrimitive.Root, {
  ref: ref,
  className: cn("flex items-center justify-center gap-1", className),
  ...props,
  children: /*#__PURE__*/_jsx(ToggleGroupContext.Provider, {
    value: {
      variant,
      size
    },
    children: children
  })
}));
ToggleGroup.displayName = ToggleGroupPrimitive.Root.displayName;
const ToggleGroupItem = /*#__PURE__*/React.forwardRef(({
  className,
  children,
  variant,
  size,
  ...props
}, ref) => {
  const context = React.useContext(ToggleGroupContext);
  return /*#__PURE__*/_jsx(ToggleGroupPrimitive.Item, {
    ref: ref,
    className: cn(toggleVariants({
      variant: context.variant || variant,
      size: context.size || size
    }), className),
    ...props,
    children: children
  });
});
ToggleGroupItem.displayName = ToggleGroupPrimitive.Item.displayName;
export { ToggleGroup, ToggleGroupItem };