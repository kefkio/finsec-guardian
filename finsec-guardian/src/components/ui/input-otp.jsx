import * as React from "react";
import { OTPInput, OTPInputContext } from "input-otp";
import { Dot } from "lucide-react";
import { cn } from "@/lib/utils";
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const InputOTP = /*#__PURE__*/React.forwardRef(({
  className,
  containerClassName,
  ...props
}, ref) => /*#__PURE__*/_jsx(OTPInput, {
  ref: ref,
  containerClassName: cn("flex items-center gap-2 has-[:disabled]:opacity-50", containerClassName),
  className: cn("disabled:cursor-not-allowed", className),
  ...props
}));
InputOTP.displayName = "InputOTP";
const InputOTPGroup = /*#__PURE__*/React.forwardRef(({
  className,
  ...props
}, ref) => /*#__PURE__*/_jsx("div", {
  ref: ref,
  className: cn("flex items-center", className),
  ...props
}));
InputOTPGroup.displayName = "InputOTPGroup";
const InputOTPSlot = /*#__PURE__*/React.forwardRef(({
  index,
  className,
  ...props
}, ref) => {
  const inputOTPContext = React.useContext(OTPInputContext);
  const {
    char,
    hasFakeCaret,
    isActive
  } = inputOTPContext.slots[index];
  return /*#__PURE__*/_jsxs("div", {
    ref: ref,
    className: cn("relative flex h-10 w-10 items-center justify-center border-y border-r border-input text-sm transition-all first:rounded-l-md first:border-l last:rounded-r-md", isActive && "z-10 ring-2 ring-ring ring-offset-background", className),
    ...props,
    children: [char, hasFakeCaret && /*#__PURE__*/_jsx("div", {
      className: "pointer-events-none absolute inset-0 flex items-center justify-center",
      children: /*#__PURE__*/_jsx("div", {
        className: "animate-caret-blink h-4 w-px bg-foreground duration-1000"
      })
    })]
  });
});
InputOTPSlot.displayName = "InputOTPSlot";
const InputOTPSeparator = /*#__PURE__*/React.forwardRef(({
  ...props
}, ref) => /*#__PURE__*/_jsx("div", {
  ref: ref,
  role: "separator",
  ...props,
  children: /*#__PURE__*/_jsx(Dot, {})
}));
InputOTPSeparator.displayName = "InputOTPSeparator";
export { InputOTP, InputOTPGroup, InputOTPSlot, InputOTPSeparator };